import uuid
import threading
import tempfile
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store: { job_id: { "status": "pending"|"processing"|"done"|"error", "segments": [...], "error": str } }
jobs: dict = {}
jobs_lock = threading.Lock()

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}


def _run_transcription(job_id: str, file_path: str):
    import whisper
    with jobs_lock:
        jobs[job_id]["status"] = "processing"
    try:
        model = whisper.load_model("base")
        result = model.transcribe(file_path)
        segments = [
            {"id": i, "text": seg["text"].strip(), "tag": None}
            for i, seg in enumerate(result["segments"])
        ]
        with jobs_lock:
            jobs[job_id]["segments"] = segments
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
    # Save to temp file
    suffix = ext
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "pending", "segments": [], "error": None}
    thread = threading.Thread(target=_run_transcription, args=(job_id, tmp_path), daemon=True)
    thread.start()
    return {"job_id": job_id}


@app.get("/health")
def health():
    return {"status": "ok"}
