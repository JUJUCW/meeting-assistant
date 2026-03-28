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


@app.get("/health")
def health():
    return {"status": "ok"}
