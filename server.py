# server.py
import uuid
import threading
import tempfile
import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import whisper
import analyzer
import storage

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


def _run_transcription(job_id: str, file_path: str):
    with jobs_lock:
        jobs[job_id]["status"] = "processing"
    try:
        model = whisper.load_model("base")
        result = model.transcribe(file_path, language="zh")
        segments = [
            {"id": i, "text": seg["text"].strip(), "tag": None}
            for i, seg in enumerate(result["segments"])
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
def list_meetings():
    return {"meetings": storage.list_meetings()}


@app.get("/meetings/search")
def search_meetings_endpoint(q: str = ""):
    return {"meetings": storage.search_meetings(q)}


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
