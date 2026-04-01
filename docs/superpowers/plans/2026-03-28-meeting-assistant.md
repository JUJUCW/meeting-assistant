# Meeting Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a meeting assistant that records or accepts uploaded audio, transcribes it via local Whisper, lets users tag segments as decisions/action items, and outputs a formatted summary.

**Architecture:** A Python FastAPI backend (`server.py`) handles audio ingestion and Whisper transcription in a background thread, exposing three REST endpoints at `localhost:8000`. A single-page frontend (`index.html`) walks the user through four steps: input → progress → tag → summary.

**Tech Stack:** Python 3.9+, FastAPI, uvicorn, openai-whisper, python-multipart, pytest, httpx; Vanilla HTML/CSS/JS (no frontend framework)

---

## File Structure

| File | Responsibility |
|---|---|
| `index.html` | Frontend wizard UI (4 steps) |
| `server.py` | FastAPI app: CORS, job store, Whisper transcription |
| `requirements.txt` | Python dependencies |
| `tests/test_server.py` | Backend unit + integration tests |

---

### Task 1: Python Dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.111.0
uvicorn==0.29.0
python-multipart==0.0.9
openai-whisper==20231117
pytest==8.2.0
httpx==0.27.0
```

- [ ] **Step 2: Install dependencies**

Run:
```bash
pip install -r requirements.txt
```
Expected: All packages install without error. If `openai-whisper` is already installed at a different version, that's fine — skip pinning it.

- [ ] **Step 3: Verify whisper is importable**

Run:
```bash
python -c "import whisper; print(whisper.available_models())"
```
Expected: prints a list like `['tiny', 'base', 'small', 'medium', 'large']`

- [ ] **Step 4: Commit**

```bash
git init
git add requirements.txt
git commit -m "chore: add Python dependencies"
```

---

### Task 2: FastAPI Backend Foundation

**Files:**
- Create: `server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write failing test for health check**

`tests/test_server.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from server import app

@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_server.py::test_health -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'server'`

- [ ] **Step 3: Implement backend foundation**

`server.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_server.py::test_health -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: add FastAPI foundation with health check"
```

---

### Task 3: /transcribe Endpoint

**Files:**
- Modify: `server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_server.py`:
```python
import io

@pytest.mark.anyio
async def test_transcribe_returns_job_id():
    # Create a minimal valid wav header (44 bytes) — Whisper will fail to process it,
    # but the endpoint should still accept it and return a job_id immediately.
    fake_audio = io.BytesIO(b"RIFF" + b"\x00" * 40)
    fake_audio.name = "test.wav"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/transcribe",
            files={"file": ("test.wav", fake_audio, "audio/wav")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data

@pytest.mark.anyio
async def test_transcribe_rejects_invalid_format():
    fake_file = io.BytesIO(b"not audio")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/transcribe",
            files={"file": ("test.txt", fake_file, "text/plain")},
        )
    assert response.status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_server.py -v -k "transcribe"
```
Expected: FAIL — `404 Not Found`

- [ ] **Step 3: Implement /transcribe**

Add to `server.py` (after the `jobs` dict, before end of file):
```python
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}


def _run_transcription(job_id: str, file_path: str):
    import whisper
    jobs[job_id]["status"] = "processing"
    try:
        model = whisper.load_model("base")
        result = model.transcribe(file_path)
        segments = [
            {"id": i, "text": seg["text"].strip(), "tag": None}
            for i, seg in enumerate(result["segments"])
        ]
        jobs[job_id]["segments"] = segments
        jobs[job_id]["status"] = "done"
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
    finally:
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
    jobs[job_id] = {"status": "pending", "segments": [], "error": None}
    thread = threading.Thread(target=_run_transcription, args=(job_id, tmp_path), daemon=True)
    thread.start()
    return {"job_id": job_id}
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/test_server.py -v -k "transcribe"
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: add /transcribe endpoint with Whisper background job"
```

---

### Task 4: /status and /result Endpoints

**Files:**
- Modify: `server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_server.py`:
```python
@pytest.mark.anyio
async def test_status_pending():
    # Manually insert a job
    from server import jobs
    jobs["test-job-1"] = {"status": "pending", "segments": [], "error": None}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/status/test-job-1")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

@pytest.mark.anyio
async def test_status_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/status/nonexistent")
    assert response.status_code == 404

@pytest.mark.anyio
async def test_result_done():
    from server import jobs
    jobs["test-job-2"] = {
        "status": "done",
        "segments": [{"id": 0, "text": "Hello", "tag": None}],
        "error": None,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/result/test-job-2")
    assert response.status_code == 200
    assert response.json()["segments"][0]["text"] == "Hello"

@pytest.mark.anyio
async def test_result_not_ready():
    from server import jobs
    jobs["test-job-3"] = {"status": "processing", "segments": [], "error": None}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/result/test-job-3")
    assert response.status_code == 202
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_server.py -v -k "status or result"
```
Expected: FAIL — `404 Not Found`

- [ ] **Step 3: Implement /status and /result**

Append to `server.py`:
```python
@app.get("/status/{job_id}")
def status(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job["status"], "error": job.get("error")}


@app.get("/result/{job_id}")
def result(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(status_code=202, detail="Not ready yet")
    return {"segments": job["segments"]}
```

- [ ] **Step 4: Add anyio pytest config**

Create `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
```

Install anyio pytest plugin:
```bash
pip install anyio[trio] pytest-anyio
```

- [ ] **Step 5: Run all tests**

Run:
```bash
pytest tests/test_server.py -v
```
Expected: All tests PASS (transcription tests pass immediately; Whisper won't actually run since test audio is invalid, but job creation succeeds)

- [ ] **Step 6: Manual smoke test**

Run the server:
```bash
uvicorn server:app --reload
```
Open browser: `http://localhost:8000/health` — should return `{"status":"ok"}`

- [ ] **Step 7: Commit**

```bash
git add server.py tests/test_server.py pytest.ini
git commit -m "feat: add /status and /result endpoints"
```

---

### Task 5: Frontend — HTML Structure & Step Navigation

**Files:**
- Modify: `index.html` (full rewrite)

- [ ] **Step 1: Rewrite index.html with 4-step wizard shell**

`index.html`:
```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>會議助理</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f0f2f5;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      padding: 48px 16px;
    }
    .container { width: 100%; max-width: 600px; }
    h1 { font-size: 26px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }
    .subtitle { font-size: 14px; color: #888; margin-bottom: 32px; }

    /* Step indicator */
    .steps {
      display: flex;
      align-items: center;
      margin-bottom: 32px;
      gap: 0;
    }
    .step-dot {
      width: 32px; height: 32px;
      border-radius: 50%;
      background: #e0e0e0;
      color: #aaa;
      font-size: 13px; font-weight: 700;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .step-dot.active { background: #6c63ff; color: #fff; }
    .step-dot.done { background: #4caf50; color: #fff; }
    .step-line { flex: 1; height: 2px; background: #e0e0e0; }
    .step-line.done { background: #4caf50; }

    /* Card */
    .card {
      background: #fff;
      border-radius: 16px;
      padding: 28px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    }
    .card h2 { font-size: 18px; color: #1a1a2e; margin-bottom: 6px; }
    .card p { font-size: 14px; color: #666; margin-bottom: 20px; }

    /* Buttons */
    .btn {
      padding: 12px 24px;
      border: none; border-radius: 10px;
      font-size: 15px; cursor: pointer;
      transition: background 0.2s;
    }
    .btn-primary { background: #6c63ff; color: #fff; }
    .btn-primary:hover { background: #574fd6; }
    .btn-primary:disabled { background: #c5c2f5; cursor: not-allowed; }
    .btn-secondary { background: #f0f2f5; color: #555; }
    .btn-secondary:hover { background: #e0e2e8; }

    .error-msg { color: #e74c3c; font-size: 13px; margin-top: 8px; }

    /* Steps panels */
    .step-panel { display: none; }
    .step-panel.active { display: block; }
  </style>
</head>
<body>
  <div class="container">
    <h1>會議助理</h1>
    <p class="subtitle">語音轉文字 · 標記決議與待辦 · 一鍵輸出摘要</p>

    <!-- Step indicator -->
    <div class="steps">
      <div class="step-dot active" id="dot-1">1</div>
      <div class="step-line" id="line-1"></div>
      <div class="step-dot" id="dot-2">2</div>
      <div class="step-line" id="line-2"></div>
      <div class="step-dot" id="dot-3">3</div>
      <div class="step-line" id="line-3"></div>
      <div class="step-dot" id="dot-4">4</div>
    </div>

    <!-- Step 1: Input -->
    <div class="step-panel active" id="panel-1">
      <div class="card">
        <h2>上傳或錄製音訊</h2>
        <p>選擇音檔（mp3、wav、m4a）或直接錄音</p>
        <!-- Step 1 content injected in Task 6 -->
      </div>
    </div>

    <!-- Step 2: Transcribing -->
    <div class="step-panel" id="panel-2">
      <div class="card">
        <h2>轉錄中...</h2>
        <p>正在使用本地 Whisper 模型處理音訊，請稍候</p>
        <!-- Step 2 content injected in Task 7 -->
      </div>
    </div>

    <!-- Step 3: Review & Tag -->
    <div class="step-panel" id="panel-3">
      <div class="card">
        <h2>標記逐字稿</h2>
        <p>點擊每段文字旁的按鈕，標記為「決議」或「待辦」</p>
        <!-- Step 3 content injected in Task 8 -->
      </div>
    </div>

    <!-- Step 4: Summary -->
    <div class="step-panel" id="panel-4">
      <div class="card">
        <h2>會議摘要</h2>
        <p>整理完成，可一鍵複製</p>
        <!-- Step 4 content injected in Task 9 -->
      </div>
    </div>
  </div>

  <script>
    // --- State ---
    let currentStep = 1;
    let jobId = null;
    let segments = []; // [{ id, text, tag }]

    const API = 'http://localhost:8000';

    // --- Step navigation ---
    function goToStep(n) {
      document.getElementById(`panel-${currentStep}`).classList.remove('active');
      document.getElementById(`dot-${currentStep}`).classList.remove('active');
      document.getElementById(`dot-${currentStep}`).classList.add('done');
      if (currentStep < 4) {
        document.getElementById(`line-${currentStep}`).classList.add('done');
      }
      currentStep = n;
      document.getElementById(`panel-${n}`).classList.add('active');
      document.getElementById(`dot-${n}`).classList.add('active');
      document.getElementById(`dot-${n}`).classList.remove('done');
    }

    // Placeholder for step implementations (filled in Tasks 6-9)
  </script>
</body>
</html>
```

- [ ] **Step 2: Verify steps render correctly**

Open `index.html` in browser. Expected: Title + subtitle + 4 step dots (dot 1 is purple). Only "上傳或錄製音訊" panel is visible.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add frontend wizard shell with step navigation"
```

---

### Task 6: Frontend Step 1 — Audio Input

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add Step 1 content inside `#panel-1 .card`**

Replace the `<!-- Step 1 content injected in Task 6 -->` comment with:
```html
        <div id="server-error" class="error-msg" style="display:none">
          ⚠️ 無法連線到本地伺服器，請先執行：<code>uvicorn server:app --reload</code>
        </div>

        <!-- File upload -->
        <div style="margin-bottom:16px">
          <label style="font-size:14px;font-weight:600;display:block;margin-bottom:8px">上傳音檔</label>
          <input type="file" id="fileInput" accept=".mp3,.wav,.m4a,.ogg,.flac,.webm"
            style="font-size:14px;width:100%">
          <div id="file-error" class="error-msg" style="display:none"></div>
        </div>

        <div style="text-align:center;color:#bbb;margin:16px 0;font-size:13px">— 或 —</div>

        <!-- Record -->
        <div style="margin-bottom:24px">
          <label style="font-size:14px;font-weight:600;display:block;margin-bottom:8px">即時錄音</label>
          <div style="display:flex;gap:8px;align-items:center">
            <button class="btn btn-secondary" id="recordBtn" onclick="toggleRecord()">● 開始錄音</button>
            <span id="recordStatus" style="font-size:13px;color:#888"></span>
          </div>
          <div id="record-error" class="error-msg" style="display:none"></div>
        </div>

        <button class="btn btn-primary" id="submitBtn" onclick="submitAudio()" disabled>送出轉錄</button>
```

- [ ] **Step 2: Add recording JS below the `goToStep` function in the `<script>` tag**

```javascript
    // --- Step 1: Audio input ---
    let mediaRecorder = null;
    let recordedChunks = [];
    let recordedBlob = null;
    let selectedFile = null;

    document.addEventListener('DOMContentLoaded', () => {
      checkServer();
      document.getElementById('fileInput').addEventListener('change', (e) => {
        selectedFile = e.target.files[0] || null;
        recordedBlob = null;
        updateSubmitBtn();
      });
    });

    async function checkServer() {
      try {
        const res = await fetch(`${API}/health`);
        if (!res.ok) throw new Error();
      } catch {
        document.getElementById('server-error').style.display = 'block';
      }
    }

    function updateSubmitBtn() {
      const hasAudio = selectedFile || recordedBlob;
      document.getElementById('submitBtn').disabled = !hasAudio;
    }

    async function toggleRecord() {
      const btn = document.getElementById('recordBtn');
      const status = document.getElementById('recordStatus');
      const errEl = document.getElementById('record-error');
      errEl.style.display = 'none';

      if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        btn.textContent = '● 開始錄音';
        status.textContent = '';
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        recordedChunks = [];
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) recordedChunks.push(e.data); };
        mediaRecorder.onstop = () => {
          recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' });
          selectedFile = null;
          document.getElementById('fileInput').value = '';
          status.textContent = '錄音完成 ✓';
          stream.getTracks().forEach(t => t.stop());
          updateSubmitBtn();
        };
        mediaRecorder.start();
        btn.textContent = '■ 停止錄音';
        status.textContent = '錄音中...';
      } catch {
        errEl.textContent = '無法存取麥克風，請確認瀏覽器已授予麥克風權限。';
        errEl.style.display = 'block';
      }
    }

    async function submitAudio() {
      const audio = selectedFile || recordedBlob;
      if (!audio) return;

      const formData = new FormData();
      const filename = selectedFile ? selectedFile.name : 'recording.webm';
      formData.append('file', audio, filename);

      try {
        const res = await fetch(`${API}/transcribe`, { method: 'POST', body: formData });
        if (!res.ok) {
          const err = await res.json();
          document.getElementById('file-error').textContent = err.detail;
          document.getElementById('file-error').style.display = 'block';
          return;
        }
        const data = await res.json();
        jobId = data.job_id;
        goToStep(2);
        startPolling();
      } catch {
        document.getElementById('server-error').style.display = 'block';
      }
    }
```

- [ ] **Step 3: Verify in browser**

Open `index.html`. Expected:
- Server error banner appears if backend is not running
- File upload input visible
- Record button toggles start/stop
- Submit button is disabled until file selected or recording done

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: step 1 — audio upload and recording"
```

---

### Task 7: Frontend Step 2 — Transcription Progress

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add Step 2 content inside `#panel-2 .card`**

Replace `<!-- Step 2 content injected in Task 7 -->` with:
```html
        <div style="text-align:center;padding:24px 0">
          <div id="spinner" style="font-size:32px;margin-bottom:16px">⏳</div>
          <div id="progress-status" style="font-size:15px;color:#555">初始化中...</div>
          <div id="progress-error" class="error-msg" style="margin-top:12px;display:none"></div>
          <button class="btn btn-secondary" id="retryBtn" style="margin-top:16px;display:none"
            onclick="retryTranscription()">重試</button>
        </div>
```

- [ ] **Step 2: Add polling JS inside `<script>`**

```javascript
    // --- Step 2: Polling ---
    let pollTimer = null;

    function startPolling() {
      document.getElementById('progress-status').textContent = '轉錄中，請稍候...';
      pollTimer = setInterval(poll, 2000);
    }

    async function poll() {
      try {
        const res = await fetch(`${API}/status/${jobId}`);
        if (!res.ok) throw new Error('status error');
        const data = await res.json();

        if (data.status === 'done') {
          clearInterval(pollTimer);
          await loadResult();
        } else if (data.status === 'error') {
          clearInterval(pollTimer);
          showTranscribeError(data.error || '轉錄失敗');
        } else {
          const labels = { pending: '等待處理...', processing: '轉錄中，請稍候...' };
          document.getElementById('progress-status').textContent = labels[data.status] || '處理中...';
        }
      } catch {
        clearInterval(pollTimer);
        showTranscribeError('無法連線到伺服器');
      }
    }

    function showTranscribeError(msg) {
      document.getElementById('spinner').textContent = '❌';
      document.getElementById('progress-status').textContent = '發生錯誤';
      const errEl = document.getElementById('progress-error');
      errEl.textContent = msg;
      errEl.style.display = 'block';
      document.getElementById('retryBtn').style.display = 'inline-block';
    }

    function retryTranscription() {
      goToStep(1);
      document.getElementById('progress-error').style.display = 'none';
      document.getElementById('retryBtn').style.display = 'none';
      document.getElementById('spinner').textContent = '⏳';
    }

    async function loadResult() {
      const res = await fetch(`${API}/result/${jobId}`);
      const data = await res.json();
      segments = data.segments;
      goToStep(3);
      renderSegments();
    }
```

- [ ] **Step 3: Verify manually**

Start backend (`uvicorn server:app --reload`), upload a real audio file, click submit. Expected: Step 2 shows spinner + status text; after Whisper finishes, auto-advances to Step 3.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: step 2 — transcription progress with polling"
```

---

### Task 8: Frontend Step 3 — Review & Tag

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add Step 3 content inside `#panel-3 .card`**

Replace `<!-- Step 3 content injected in Task 8 -->` with:
```html
        <div id="segments-list" style="display:flex;flex-direction:column;gap:10px;margin-bottom:24px"></div>
        <button class="btn btn-primary" onclick="goToStep(4); renderSummary()">產生摘要</button>
```

- [ ] **Step 2: Add segment rendering JS inside `<script>`**

```javascript
    // --- Step 3: Tag segments ---
    const TAG_LABELS = { decision: '決議', action: '待辦', null: '' };
    const TAG_COLORS = { decision: '#6c63ff', action: '#ff6584', null: '' };

    function renderSegments() {
      const list = document.getElementById('segments-list');
      list.innerHTML = '';
      segments.forEach(seg => {
        const div = document.createElement('div');
        div.style.cssText = 'display:flex;gap:10px;align-items:flex-start;background:#f8f8fb;border-radius:10px;padding:12px';
        div.innerHTML = `
          <span style="flex:1;font-size:14px;color:#333;line-height:1.6">${escapeHtml(seg.text)}</span>
          <div style="display:flex;flex-direction:column;gap:4px;flex-shrink:0">
            <button onclick="setTag(${seg.id},'decision')" style="
              padding:3px 10px;border-radius:6px;border:1.5px solid #6c63ff;
              background:${seg.tag==='decision'?'#6c63ff':'#fff'};
              color:${seg.tag==='decision'?'#fff':'#6c63ff'};
              font-size:12px;cursor:pointer">決議</button>
            <button onclick="setTag(${seg.id},'action')" style="
              padding:3px 10px;border-radius:6px;border:1.5px solid #ff6584;
              background:${seg.tag==='action'?'#ff6584':'#fff'};
              color:${seg.tag==='action'?'#fff':'#ff6584'};
              font-size:12px;cursor:pointer">待辦</button>
          </div>
        `;
        list.appendChild(div);
      });
    }

    function setTag(id, tag) {
      const seg = segments.find(s => s.id === id);
      if (!seg) return;
      seg.tag = seg.tag === tag ? null : tag;
      renderSegments();
    }

    function escapeHtml(str) {
      return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }
```

- [ ] **Step 3: Verify manually**

After transcription completes, Step 3 shows each segment. Clicking 「決議」 highlights it purple; clicking again deselects. 「待辦」 highlights pink.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: step 3 — segment review and tagging"
```

---

### Task 9: Frontend Step 4 — Summary & Copy

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add Step 4 content inside `#panel-4 .card`**

Replace `<!-- Step 4 content injected in Task 9 -->` with:
```html
        <div id="summary-output" style="white-space:pre-wrap;font-size:14px;color:#333;
          background:#f8f8fb;border-radius:10px;padding:16px;line-height:1.8;
          margin-bottom:16px;min-height:100px"></div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-primary" id="copyBtn" onclick="copySummary()">複製摘要</button>
          <button class="btn btn-secondary" onclick="startOver()">重新開始</button>
        </div>
```

- [ ] **Step 2: Add summary JS inside `<script>`**

```javascript
    // --- Step 4: Summary ---
    function renderSummary() {
      const decisions = segments.filter(s => s.tag === 'decision');
      const actions = segments.filter(s => s.tag === 'action');
      const allText = segments.map(s => s.text).join('\n');

      let output = '【會議記錄】\n';
      output += allText + '\n';

      if (decisions.length > 0) {
        output += '\n【決議事項】\n';
        decisions.forEach((s, i) => { output += `${i+1}. ${s.text}\n`; });
      }

      if (actions.length > 0) {
        output += '\n【待辦事項】\n';
        actions.forEach((s, i) => { output += `${i+1}. ${s.text}\n`; });
      }

      document.getElementById('summary-output').textContent = output;
    }

    async function copySummary() {
      const text = document.getElementById('summary-output').textContent;
      await navigator.clipboard.writeText(text);
      const btn = document.getElementById('copyBtn');
      btn.textContent = '已複製 ✓';
      setTimeout(() => { btn.textContent = '複製摘要'; }, 2000);
    }

    function startOver() {
      jobId = null;
      segments = [];
      selectedFile = null;
      recordedBlob = null;
      document.getElementById('fileInput').value = '';
      document.getElementById('recordStatus').textContent = '';
      document.getElementById('submitBtn').disabled = true;

      // Reset step indicators
      for (let i = 1; i <= 4; i++) {
        document.getElementById(`dot-${i}`).classList.remove('active', 'done');
        if (i < 4) document.getElementById(`line-${i}`).classList.remove('done');
        document.getElementById(`panel-${i}`).classList.remove('active');
      }
      document.getElementById(`dot-1`).classList.add('active');
      document.getElementById(`panel-1`).classList.add('active');
      currentStep = 1;
    }
```

- [ ] **Step 3: Verify end-to-end**

Full flow test:
1. Start backend: `uvicorn server:app --reload`
2. Open `index.html` in browser
3. Upload an audio file → click 送出轉錄
4. Wait for Step 3 to appear with transcript segments
5. Tag some segments as 決議/待辦
6. Click 產生摘要
7. Verify Step 4 shows formatted summary with tagged sections
8. Click 複製摘要 → paste into text editor → confirm content matches
9. Click 重新開始 → back to Step 1

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: step 4 — meeting summary and copy"
```

---

## Running the App

```bash
# Terminal 1: start backend
uvicorn server:app --reload

# Browser: open index.html directly (file://) or serve with:
python -m http.server 3000
# then visit http://localhost:3000
```

> **Note:** Whisper model size in `server.py` is set to `"base"`. For better accuracy, change to `"small"` or `"medium"` in `_run_transcription()`. Larger models take longer to load and transcribe.
