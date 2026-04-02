# server.py
import io
import uuid
import threading
import tempfile
import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from faster_whisper import WhisperModel
import opencc
import analyzer
import storage
import pdf_translator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
jobs: dict = {}
jobs_lock = threading.Lock()

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB

# Load model once at startup to avoid reloading on every transcription
_whisper_model = WhisperModel("turbo", device="cpu", compute_type="int8")
_converter = opencc.OpenCC('s2t')


def _run_transcription(job_id: str, file_path: str):
    with jobs_lock:
        jobs[job_id]["status"] = "processing"
    try:
        segments_gen, _ = _whisper_model.transcribe(
            file_path,
            language="zh",
            initial_prompt="以下是繁體中文的會議記錄。",
        )
        segments = [
            {"id": i, "text": _converter.convert(seg.text.strip()), "tag": None}
            for i, seg in enumerate(segments_gen)
        ]

        # AI analysis
        transcript = "\n".join(s["text"] for s in segments)
        pending_items = storage.get_pending_action_items()
        analysis, ollama_available = analyzer.analyze(transcript, pending_items)

        # Assign IDs to decisions and action items
        decisions = [
            {"id": f"d-{i+1}", "status": "confirmed", **d}
            for i, d in enumerate(analysis["decisions"])
        ]
        action_items = [
            {"id": f"a-{i+1}", "status": "pending", **a}
            for i, a in enumerate(analysis["action_items"])
        ]

        # Save meeting
        meeting_id = datetime.now().strftime("%Y-%m-%d_%H-%M")
        meeting = {
            "id": meeting_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "transcript": transcript,
            "decisions": decisions,
            "action_items": action_items,
        }
        storage.save_meeting(meeting)

        # Resolve historical items
        item_id_to_meeting = {item["id"]: item["meeting_id"] for item in pending_items}
        for item_id in analysis["resolved_action_item_ids"]:
            source_meeting = item_id_to_meeting.get(item_id)
            if source_meeting:
                storage.resolve_action_item(source_meeting, item_id)

        with jobs_lock:
            jobs[job_id]["segments"] = segments
            jobs[job_id]["decisions"] = decisions
            jobs[job_id]["action_items"] = action_items
            jobs[job_id]["resolved_item_ids"] = analysis["resolved_action_item_ids"]
            jobs[job_id]["meeting_id"] = meeting_id
            jobs[job_id]["ollama_available"] = ollama_available
            jobs[job_id]["status"] = "done"
    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="檔案過大，上限為 200 MB。")
    suffix = ext
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {
            "status": "pending",
            "segments": [],
            "decisions": [],
            "action_items": [],
            "resolved_item_ids": [],
            "meeting_id": None,
            "ollama_available": None,
            "error": None,
        }
    thread = threading.Thread(target=_run_transcription, args=(job_id, tmp_path), daemon=True)
    thread.start()
    return {"job_id": job_id}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status/{job_id}")
def status(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job["status"], "error": job.get("error")}


@app.get("/result/{job_id}")
def result(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=202, detail="Not ready yet")
    return {
        "segments": job["segments"],
        "decisions": job["decisions"],
        "action_items": job["action_items"],
        "resolved_item_ids": job["resolved_item_ids"],
        "meeting_id": job["meeting_id"],
        "ollama_available": job["ollama_available"],
    }


@app.get("/meetings")
def list_meetings(
    page: int = 1,
    limit: int = 20,
    q: str = "",
    category_id: str = "",
    tag: str = "",
):
    if page < 1:
        page = 1
    if limit < 1 or limit > 200:
        limit = 20
    meetings, total = storage.list_meetings(
        page=page, limit=limit, q=q, category_id=category_id, tag=tag
    )
    return {"meetings": meetings, "total": total, "page": page, "limit": limit}


@app.get("/meetings/search")
def search_meetings_endpoint(q: str = ""):
    meetings, _ = storage.list_meetings(q=q, limit=10_000)
    return {"meetings": meetings}


@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: str):
    meeting = storage.load_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@app.delete("/meetings/{meeting_id}")
def delete_meeting_endpoint(meeting_id: str):
    ok = storage.delete_meeting(meeting_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"status": "deleted"}


@app.patch("/meetings/{meeting_id}/decisions/{decision_id}")
def patch_decision(meeting_id: str, decision_id: str, body: dict = Body(...)):
    result = storage.update_decision(meeting_id, decision_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return result


@app.post("/meetings/{meeting_id}/decisions")
def create_decision(meeting_id: str, body: dict = Body(...)):
    try:
        result = storage.add_decision(meeting_id, body)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return result


@app.post("/meetings/{meeting_id}/action-items")
def create_action_item(meeting_id: str, body: dict = Body(...)):
    try:
        result = storage.add_action_item(meeting_id, body)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return result


@app.patch("/meetings/{meeting_id}/action-items/{item_id}")
def patch_action_item(meeting_id: str, item_id: str, body: dict = Body(...)):
    result = storage.update_action_item(meeting_id, item_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Action item not found")
    return result


@app.get("/action-items/pending")
def get_pending_action_items():
    return {"items": storage.get_pending_action_items()}


@app.post("/action-items/{meeting_id}/{item_id}/resolve")
def resolve_action_item(meeting_id: str, item_id: str):
    ok = storage.resolve_action_item(meeting_id, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "done"}


@app.get("/categories")
def list_categories():
    return storage.load_categories()


@app.post("/categories")
def create_category(body: dict = Body(...)):
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")
    return storage.add_category(name)


@app.delete("/categories/{cat_id}")
def delete_category_endpoint(cat_id: str):
    ok = storage.delete_category(cat_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"status": "deleted"}


@app.patch("/meetings/{meeting_id}/title")
def patch_meeting_title(meeting_id: str, body: dict = Body(...)):
    title = body.get("title", "").strip()
    result = storage.update_meeting_title(meeting_id, title)
    if result is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return result


@app.patch("/meetings/{meeting_id}/tags")
def patch_meeting_tags(meeting_id: str, body: dict = Body(...)):
    result = storage.update_meeting_tags(meeting_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return result


@app.post("/meetings/{meeting_id}/summary")
def generate_summary_endpoint(meeting_id: str):
    meeting = storage.load_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    transcript = meeting.get("transcript", "")
    if not transcript:
        raise HTTPException(status_code=422, detail="No transcript available")
    summary, ollama_available = analyzer.generate_summary(transcript)
    if not ollama_available:
        raise HTTPException(status_code=503, detail="Ollama 不可用，無法產生摘要")
    storage.update_meeting_summary(meeting_id, summary)
    return {"summary": summary}


@app.get("/meetings/{meeting_id}/export/docx")
def export_docx(meeting_id: str):
    from docx import Document
    from docx.shared import Pt

    meeting = storage.load_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    doc = Document()
    title = meeting.get("title") or meeting["id"]
    doc.add_heading(title, 0)
    doc.add_paragraph(f"日期：{meeting['created_at'][:10]}")

    tags = meeting.get("tags", [])
    if tags:
        doc.add_paragraph(f"標籤：{', '.join(tags)}")

    summary = meeting.get("summary", "")
    if summary:
        doc.add_heading("摘要", level=1)
        doc.add_paragraph(summary)

    decisions = meeting.get("decisions", [])
    if decisions:
        doc.add_heading("決策", level=1)
        for d in decisions:
            doc.add_paragraph(d["content"], style="List Bullet")
            if d.get("rationale"):
                p = doc.add_paragraph(f"原因：{d['rationale']}")
                p.paragraph_format.left_indent = Pt(24)

    items = meeting.get("action_items", [])
    if items:
        doc.add_heading("待辦事項", level=1)
        for a in items:
            status = "✓" if a.get("status") == "done" else "○"
            assignee = f"（{a['assignee']}）" if a.get("assignee") else ""
            deadline = f" — {a['deadline']}" if a.get("deadline") else ""
            doc.add_paragraph(f"{status} {a['content']}{assignee}{deadline}", style="List Bullet")

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    filename = f"{meeting_id}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── PDF Translation ──────────────────────────────────────────────────────────

MAX_TRANSLATE_BYTES = 50 * 1024 * 1024  # 50 MB


@app.get("/translate/list")
def translate_list():
    return {"jobs": pdf_translator.list_jobs()}


@app.post("/translate/upload")
async def translate_upload(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支援 PDF 格式")
    content = await file.read()
    if len(content) > MAX_TRANSLATE_BYTES:
        raise HTTPException(status_code=413, detail="檔案過大，上限為 50 MB。")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    job_id = pdf_translator.start(tmp_path, original_filename=file.filename or "document.pdf")
    return {"job_id": job_id}


@app.get("/translate/status/{job_id}")
def translate_status(job_id: str):
    job = pdf_translator.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "status": job["status"],
        "progress": job["progress"],
        "total": job["total"],
        "done": job["done"],
        "source_lang": job["source_lang"],
        "error": job["error"],
    }


@app.get("/translate/download/{job_id}/{fmt}")
def translate_download(job_id: str, fmt: str):
    job = pdf_translator.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=202, detail="Not ready yet")
    if fmt == "pdf":
        path = job["pdf_out"]
        media_type = "application/pdf"
        filename = "translated.pdf"
    elif fmt == "docx":
        path = job["docx_out"]
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = "translated.docx"
    else:
        raise HTTPException(status_code=400, detail="格式不支援，請使用 pdf 或 docx")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Output file not found")

    def _iter():
        with open(path, "rb") as f:
            yield from f

    return StreamingResponse(
        _iter(),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.delete("/translate/{job_id}")
def translate_delete(job_id: str):
    found = pdf_translator.delete_job(job_id)
    if not found:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "deleted"}
