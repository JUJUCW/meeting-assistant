# AI Decision & Action Item Analysis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local Llama 3.1 8B analysis after transcription to auto-extract decisions and action items, persist them across meetings, and surface them in the UI.

**Architecture:** `analyzer.py` calls Ollama synchronously (httpx.Client) from inside the existing background thread; `storage.py` reads/writes JSON files in `meetings/`; `server.py` wires them together and gains four new endpoints; `index.html` Step III becomes an AI results view and Step IV gains a history panel.

**Tech Stack:** Python 3.11, FastAPI, httpx (sync), Ollama + Llama 3.1 8B, vanilla JS, pytest + anyio[trio]

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `storage.py` | Save/load/list meetings, get pending items, resolve items |
| Create | `analyzer.py` | Build prompt, call Ollama, parse JSON, retry ×2 |
| Create | `meetings/` | Auto-created by storage.py on first save |
| Modify | `server.py` | Integrate analyzer in `_run_transcription`; add 4 endpoints |
| Modify | `index.html` | Step III AI results + Step IV history panel |
| Create | `tests/test_storage.py` | Unit tests for all storage functions |
| Create | `tests/test_analyzer.py` | Unit tests for prompt building and JSON parsing |
| Modify | `tests/test_server.py` | Tests for extended /result + 4 new endpoints |

---

### Task 1: storage.py — Meeting persistence

**Files:**
- Create: `storage.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_storage.py
import json
import pytest
from pathlib import Path
import storage


@pytest.fixture(autouse=True)
def tmp_meetings(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEETINGS_DIR", tmp_path / "meetings")


def _sample_meeting(mid="2026-03-28_14-30"):
    return {
        "id": mid,
        "created_at": "2026-03-28T14:30:00",
        "transcript": "今天決定採用新系統。",
        "decisions": [
            {"id": "d-1", "content": "採用新系統", "rationale": "效率", "related_people": [], "status": "confirmed"}
        ],
        "action_items": [
            {"id": "a-1", "content": "更新文件", "assignee": "小明", "deadline": "2026-04-01", "priority": "high", "status": "pending"}
        ],
    }


def test_save_and_load_meeting():
    m = _sample_meeting()
    storage.save_meeting(m)
    loaded = storage.load_meeting(m["id"])
    assert loaded == m


def test_load_missing_returns_none():
    assert storage.load_meeting("nonexistent") is None


def test_list_meetings_returns_summary():
    storage.save_meeting(_sample_meeting("2026-03-28_09-00"))
    storage.save_meeting(_sample_meeting("2026-03-28_14-30"))
    result = storage.list_meetings()
    assert len(result) == 2
    assert result[0]["decision_count"] == 1
    assert result[0]["action_item_count"] == 1
    assert "transcript" not in result[0]


def test_get_pending_action_items():
    m = _sample_meeting()
    storage.save_meeting(m)
    items = storage.get_pending_action_items()
    assert len(items) == 1
    assert items[0]["id"] == "a-1"
    assert items[0]["meeting_id"] == "2026-03-28_14-30"


def test_get_pending_excludes_done():
    m = _sample_meeting()
    m["action_items"][0]["status"] = "done"
    storage.save_meeting(m)
    assert storage.get_pending_action_items() == []


def test_resolve_action_item():
    storage.save_meeting(_sample_meeting())
    ok = storage.resolve_action_item("2026-03-28_14-30", "a-1")
    assert ok is True
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert loaded["action_items"][0]["status"] == "done"


def test_resolve_missing_item_returns_false():
    storage.save_meeting(_sample_meeting())
    assert storage.resolve_action_item("2026-03-28_14-30", "a-99") is False


def test_resolve_missing_meeting_returns_false():
    assert storage.resolve_action_item("nonexistent", "a-1") is False


def test_corrupted_file_skipped_in_list(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEETINGS_DIR", tmp_path / "meetings")
    storage.save_meeting(_sample_meeting())
    (storage.MEETINGS_DIR / "bad.json").write_text("{{not json")
    result = storage.list_meetings()
    assert len(result) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_storage.py -v
```

Expected: `ModuleNotFoundError: No module named 'storage'`

- [ ] **Step 3: Implement storage.py**

```python
# storage.py
import json
from pathlib import Path

MEETINGS_DIR = Path(__file__).parent / "meetings"


def save_meeting(meeting: dict) -> None:
    MEETINGS_DIR.mkdir(exist_ok=True)
    path = MEETINGS_DIR / f"{meeting['id']}.json"
    path.write_text(json.dumps(meeting, ensure_ascii=False, indent=2))


def load_meeting(meeting_id: str) -> dict | None:
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def list_meetings() -> list[dict]:
    if not MEETINGS_DIR.exists():
        return []
    meetings = []
    for path in sorted(MEETINGS_DIR.glob("*.json"), reverse=True):
        try:
            m = json.loads(path.read_text())
            meetings.append({
                "id": m["id"],
                "created_at": m["created_at"],
                "decision_count": len(m.get("decisions", [])),
                "action_item_count": len(m.get("action_items", [])),
            })
        except Exception:
            continue
    return meetings


def get_pending_action_items() -> list[dict]:
    if not MEETINGS_DIR.exists():
        return []
    items = []
    for path in sorted(MEETINGS_DIR.glob("*.json")):
        try:
            m = json.loads(path.read_text())
            for item in m.get("action_items", []):
                if item.get("status") == "pending":
                    items.append({
                        **item,
                        "meeting_id": m["id"],
                        "meeting_date": m["created_at"][:10],
                    })
        except Exception:
            continue
    return items


def resolve_action_item(meeting_id: str, item_id: str) -> bool:
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return False
    try:
        m = json.loads(path.read_text())
        for item in m.get("action_items", []):
            if item["id"] == item_id:
                item["status"] = "done"
                path.write_text(json.dumps(m, ensure_ascii=False, indent=2))
                return True
        return False
    except Exception:
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_storage.py -v
```

Expected: 10 PASSED

- [ ] **Step 5: Commit**

```bash
git add storage.py tests/test_storage.py
git commit -m "feat: add storage.py for meeting JSON persistence"
```

---

### Task 2: analyzer.py — Llama prompt, call, parse

**Files:**
- Create: `analyzer.py`
- Create: `tests/test_analyzer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_analyzer.py
import json
import pytest
from unittest.mock import patch, MagicMock
import analyzer


VALID_RESPONSE = json.dumps({
    "decisions": [{"content": "採用新系統", "rationale": "效率", "related_people": ["小明"]}],
    "action_items": [{"content": "更新文件", "assignee": "小明", "deadline": "2026-04-01", "priority": "high"}],
    "resolved_action_item_ids": ["a-1"],
})

FENCED_RESPONSE = f"```json\n{VALID_RESPONSE}\n```"


def _mock_post(response_text):
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.post.return_value.raise_for_status = MagicMock()
    mock.post.return_value.json.return_value = {"response": response_text}
    return mock


def test_build_prompt_contains_transcript():
    prompt = analyzer._build_prompt("今天討論了A和B", [])
    assert "今天討論了A和B" in prompt


def test_build_prompt_contains_pending_items():
    items = [{"id": "a-1", "content": "更新文件", "assignee": "小明", "meeting_date": "2026-03-01"}]
    prompt = analyzer._build_prompt("逐字稿", items)
    assert "a-1" in prompt
    assert "更新文件" in prompt


def test_parse_response_valid_json():
    result = analyzer._parse_response(VALID_RESPONSE)
    assert len(result["decisions"]) == 1
    assert result["decisions"][0]["content"] == "採用新系統"
    assert result["resolved_action_item_ids"] == ["a-1"]


def test_parse_response_strips_code_fences():
    result = analyzer._parse_response(FENCED_RESPONSE)
    assert len(result["action_items"]) == 1


def test_parse_response_invalid_json_raises():
    with pytest.raises(Exception):
        analyzer._parse_response("not json at all")


def test_analyze_success():
    with patch("analyzer.httpx.Client", return_value=_mock_post(VALID_RESPONSE)):
        result, available = analyzer.analyze("逐字稿", [])
    assert available is True
    assert len(result["decisions"]) == 1


def test_analyze_retries_on_failure():
    bad_mock = MagicMock()
    bad_mock.__enter__ = lambda s: s
    bad_mock.__exit__ = MagicMock(return_value=False)
    bad_mock.post.side_effect = Exception("connection refused")

    with patch("analyzer.httpx.Client", return_value=bad_mock):
        result, available = analyzer.analyze("逐字稿", [])

    assert available is False
    assert result["decisions"] == []
    assert result["action_items"] == []
    assert result["resolved_action_item_ids"] == []
    # Should have attempted 3 times
    assert bad_mock.post.call_count == 3


def test_analyze_returns_empty_on_persistent_invalid_json():
    bad_response_mock = MagicMock()
    bad_response_mock.__enter__ = lambda s: s
    bad_response_mock.__exit__ = MagicMock(return_value=False)
    bad_response_mock.post.return_value.raise_for_status = MagicMock()
    bad_response_mock.post.return_value.json.return_value = {"response": "{{broken"}

    with patch("analyzer.httpx.Client", return_value=bad_response_mock):
        result, available = analyzer.analyze("逐字稿", [])

    assert available is False
    assert result == {"decisions": [], "action_items": [], "resolved_action_item_ids": []}
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_analyzer.py -v
```

Expected: `ModuleNotFoundError: No module named 'analyzer'`

- [ ] **Step 3: Implement analyzer.py**

```python
# analyzer.py
import json
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
EMPTY_RESULT = {"decisions": [], "action_items": [], "resolved_action_item_ids": []}


def analyze(transcript: str, pending_items: list[dict]) -> tuple[dict, bool]:
    """Returns (result_dict, ollama_available). Never raises."""
    prompt = _build_prompt(transcript, pending_items)
    for attempt in range(3):
        try:
            raw = _call_ollama(prompt)
            result = _parse_response(raw)
            return result, True
        except Exception:
            if attempt == 2:
                break
    return dict(EMPTY_RESULT), False


def _build_prompt(transcript: str, pending_items: list[dict]) -> str:
    pending_section = ""
    if pending_items:
        lines = [
            f"- [{item['id']}] {item['content']}"
            f" (負責人: {item.get('assignee') or '未指定'},"
            f" 來自會議: {item.get('meeting_date', '未知')})"
            for item in pending_items
        ]
        pending_section = (
            "\n\n歷史待辦事項（請判斷哪些已在本次會議中完成，輸出其 ID 於 resolved_action_item_ids）：\n"
            + "\n".join(lines)
        )

    return (
        "你是一位會議分析師。請從以下會議逐字稿中提取決議事項和待辦事項，"
        "以嚴格的 JSON 格式輸出，不得輸出任何其他文字。使用繁體中文。\n\n"
        "輸出格式：\n"
        '{"decisions": [{"content": "string", "rationale": "string", "related_people": ["string"]}],'
        ' "action_items": [{"content": "string", "assignee": "string or null",'
        ' "deadline": "YYYY-MM-DD or null", "priority": "high|medium|low"}],'
        ' "resolved_action_item_ids": ["id1"]}\n\n'
        f"會議逐字稿：\n{transcript}"
        f"{pending_section}"
    )


def _call_ollama(prompt: str) -> str:
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        return response.json()["response"]


def _parse_response(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])
    data = json.loads(text)
    return {
        "decisions": data.get("decisions", []),
        "action_items": data.get("action_items", []),
        "resolved_action_item_ids": data.get("resolved_action_item_ids", []),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_analyzer.py -v
```

Expected: 9 PASSED

- [ ] **Step 5: Commit**

```bash
git add analyzer.py tests/test_analyzer.py
git commit -m "feat: add analyzer.py for Llama-powered meeting analysis"
```

---

### Task 3: server.py — wire in analyzer + extend /result

**Files:**
- Modify: `server.py`
- Modify: `tests/test_server.py`

The goal: after Whisper finishes, `_run_transcription` calls `analyzer.analyze()`, calls `storage.save_meeting()`, resolves historical items, and stores decisions/action_items/resolved_item_ids/meeting_id/ollama_available in the jobs dict. The `/result` endpoint returns all of this.

- [ ] **Step 1: Write failing tests**

Add these tests to `tests/test_server.py` (append after existing tests):

```python
# Add to tests/test_server.py

import json as json_module
from unittest.mock import patch, MagicMock

ANALYSIS_RESULT = {
    "decisions": [{"content": "採用新系統", "rationale": "效率", "related_people": []}],
    "action_items": [{"content": "更新文件", "assignee": "小明", "deadline": "2026-04-01", "priority": "high"}],
    "resolved_action_item_ids": [],
}


def _make_analyze_mock(result=None, available=True):
    if result is None:
        result = dict(ANALYSIS_RESULT)
    return MagicMock(return_value=(result, available))


@pytest.mark.anyio
async def test_result_includes_decisions_when_ollama_available(tmp_path):
    from server import app
    import storage as st
    with (
        patch("server.analyzer") as mock_analyzer,
        patch("server.storage") as mock_storage,
    ):
        mock_analyzer.analyze.return_value = (dict(ANALYSIS_RESULT), True)
        mock_storage.get_pending_action_items.return_value = []
        mock_storage.save_meeting = MagicMock()
        mock_storage.resolve_action_item = MagicMock()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Upload a tiny valid webm-named file
            content = b"\x1aE\xdf\xa3"  # webm magic bytes stub
            files = {"file": ("audio.webm", content, "audio/webm")}

            with patch("server.whisper") as mock_whisper:
                mock_model = MagicMock()
                mock_model.transcribe.return_value = {
                    "segments": [{"text": "  今天決定採用新系統  "}]
                }
                mock_whisper.load_model.return_value = mock_model

                post_res = await client.post("/transcribe", files=files)
                assert post_res.status_code == 200
                job_id = post_res.json()["job_id"]

                # Poll until done
                import asyncio
                for _ in range(20):
                    await asyncio.sleep(0.1)
                    s = await client.get(f"/status/{job_id}")
                    if s.json()["status"] in ("done", "error"):
                        break

                result_res = await client.get(f"/result/{job_id}")
                assert result_res.status_code == 200
                body = result_res.json()
                assert "decisions" in body
                assert "action_items" in body
                assert "ollama_available" in body
                assert "meeting_id" in body


@pytest.mark.anyio
async def test_result_ollama_unavailable_returns_empty_lists():
    from server import app
    with (
        patch("server.analyzer") as mock_analyzer,
        patch("server.storage") as mock_storage,
    ):
        mock_analyzer.analyze.return_value = (
            {"decisions": [], "action_items": [], "resolved_action_item_ids": []},
            False,
        )
        mock_storage.get_pending_action_items.return_value = []
        mock_storage.save_meeting = MagicMock()
        mock_storage.resolve_action_item = MagicMock()

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            content = b"\x1aE\xdf\xa3"
            files = {"file": ("audio.webm", content, "audio/webm")}

            with patch("server.whisper") as mock_whisper:
                mock_model = MagicMock()
                mock_model.transcribe.return_value = {"segments": [{"text": "test"}]}
                mock_whisper.load_model.return_value = mock_model

                post_res = await client.post("/transcribe", files=files)
                job_id = post_res.json()["job_id"]

                import asyncio
                for _ in range(20):
                    await asyncio.sleep(0.1)
                    s = await client.get(f"/status/{job_id}")
                    if s.json()["status"] in ("done", "error"):
                        break

                result_res = await client.get(f"/result/{job_id}")
                body = result_res.json()
                assert body["ollama_available"] is False
                assert body["decisions"] == []
```

- [ ] **Step 2: Run new tests to verify they fail**

```
pytest tests/test_server.py::test_result_includes_decisions_when_ollama_available tests/test_server.py::test_result_ollama_unavailable_returns_empty_lists -v
```

Expected: FAILED (AttributeError or similar — server doesn't have analyzer/storage yet)

- [ ] **Step 3: Update server.py**

Replace the imports block and `_run_transcription` function, and update the `/result` endpoint:

```python
# server.py
import uuid
import threading
import tempfile
import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import analyzer
import storage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    suffix = ext
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
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
```

- [ ] **Step 4: Run all tests to verify they pass**

```
pytest tests/ -v
```

Expected: All previous tests + 2 new = all PASSED

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: integrate AI analysis into transcription pipeline"
```

---

### Task 4: server.py — four new API endpoints

**Files:**
- Modify: `server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_server.py`:

```python
# Add to tests/test_server.py — new endpoint tests

@pytest.mark.anyio
async def test_list_meetings_empty():
    with patch("server.storage") as mock_storage:
        mock_storage.list_meetings.return_value = []
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.get("/meetings")
        assert res.status_code == 200
        assert res.json() == {"meetings": []}


@pytest.mark.anyio
async def test_list_meetings_returns_data():
    meetings_data = [
        {"id": "2026-03-28_14-30", "created_at": "2026-03-28T14:30:00",
         "decision_count": 2, "action_item_count": 3}
    ]
    with patch("server.storage") as mock_storage:
        mock_storage.list_meetings.return_value = meetings_data
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.get("/meetings")
        assert res.json()["meetings"][0]["decision_count"] == 2


@pytest.mark.anyio
async def test_get_meeting_found():
    meeting = {
        "id": "2026-03-28_14-30", "created_at": "2026-03-28T14:30:00",
        "transcript": "text", "decisions": [], "action_items": []
    }
    with patch("server.storage") as mock_storage:
        mock_storage.load_meeting.return_value = meeting
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.get("/meetings/2026-03-28_14-30")
        assert res.status_code == 200
        assert res.json()["id"] == "2026-03-28_14-30"


@pytest.mark.anyio
async def test_get_meeting_not_found():
    with patch("server.storage") as mock_storage:
        mock_storage.load_meeting.return_value = None
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.get("/meetings/nonexistent")
        assert res.status_code == 404


@pytest.mark.anyio
async def test_get_pending_action_items():
    items = [
        {"id": "a-1", "content": "更新文件", "assignee": "小明",
         "deadline": "2026-04-01", "priority": "high", "status": "pending",
         "meeting_id": "2026-03-28_14-30", "meeting_date": "2026-03-28"}
    ]
    with patch("server.storage") as mock_storage:
        mock_storage.get_pending_action_items.return_value = items
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.get("/action-items/pending")
        assert res.status_code == 200
        assert res.json()["items"][0]["id"] == "a-1"


@pytest.mark.anyio
async def test_resolve_action_item_success():
    with patch("server.storage") as mock_storage:
        mock_storage.resolve_action_item.return_value = True
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.post("/action-items/2026-03-28_14-30/a-1/resolve")
        assert res.status_code == 200
        assert res.json() == {"status": "done"}


@pytest.mark.anyio
async def test_resolve_action_item_not_found():
    with patch("server.storage") as mock_storage:
        mock_storage.resolve_action_item.return_value = False
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.post("/action-items/bad-meeting/a-99/resolve")
        assert res.status_code == 404
```

- [ ] **Step 2: Run new tests to verify they fail**

```
pytest tests/test_server.py -k "meetings or pending or resolve" -v
```

Expected: FAILED with 404 / connection errors (routes don't exist)

- [ ] **Step 3: Add four endpoints to server.py**

Add after the `/result` endpoint in `server.py`:

```python
@app.get("/meetings")
def list_meetings():
    return {"meetings": storage.list_meetings()}


@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: str):
    meeting = storage.load_meeting(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@app.get("/action-items/pending")
def get_pending_action_items():
    return {"items": storage.get_pending_action_items()}


@app.post("/action-items/{meeting_id}/{item_id}/resolve")
def resolve_action_item(meeting_id: str, item_id: str):
    ok = storage.resolve_action_item(meeting_id, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "done"}
```

- [ ] **Step 4: Run all tests to verify they pass**

```
pytest tests/ -v
```

Expected: All PASSED

- [ ] **Step 5: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: add /meetings, /meetings/{id}, /action-items/pending, /action-items/{id}/{id}/resolve endpoints"
```

---

### Task 5: Frontend Step III — AI analysis results view

**Files:**
- Modify: `index.html`

Step III currently shows segments for manual tagging. After this task it shows:
1. (if `!ollama_available`) Warning banner with "重新分析" button
2. (if `resolved_item_ids.length > 0`) Resolved banner "X 項待辦已在本次會議中完成"
3. Decision cards
4. Action item cards
5. Segments (with AI pre-applied tags, still manually overridable)
6. "產生摘要" button

- [ ] **Step 1: Add CSS for AI result components**

Inside the `<style>` block, after the `.tag-btn-action` rules and before `#summary-output`, add:

```css
/* ── AI Analysis Banners ── */
.banner {
  padding: 14px 18px;
  margin-bottom: 20px;
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.banner-warn {
  border: 1px solid rgba(192,57,43,0.4);
  background: rgba(192,57,43,0.06);
  color: #e67e6e;
}
.banner-success {
  border: 1px solid rgba(212,175,55,0.4);
  background: rgba(212,175,55,0.06);
  color: var(--gold);
}

/* ── Analysis Cards ── */
.analysis-section-title {
  font-family: var(--font-display);
  font-size: 11px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--gold);
  opacity: 0.7;
  margin: 24px 0 12px;
}
.analysis-card {
  background: rgba(212,175,55,0.03);
  border: 1px solid rgba(212,175,55,0.12);
  padding: 16px;
  margin-bottom: 10px;
}
.analysis-card-content {
  font-size: 13px;
  color: var(--cream);
  letter-spacing: 0.03em;
  line-height: 1.65;
  margin-bottom: 8px;
}
.analysis-card-meta {
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.priority-badge {
  padding: 2px 8px;
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  border: 1px solid;
}
.priority-high   { color: var(--gold);  border-color: rgba(212,175,55,0.5); }
.priority-medium { color: var(--cream); border-color: rgba(242,240,228,0.3); }
.priority-low    { color: var(--muted); border-color: rgba(136,136,136,0.3); }

.segments-title {
  font-family: var(--font-display);
  font-size: 11px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--muted);
  opacity: 0.6;
  margin: 24px 0 12px;
}
```

- [ ] **Step 2: Update Step III HTML panel**

Replace the existing Step III panel in `index.html`:

```html
<!-- Step III: AI Analysis + Review -->
<div class="step-panel" id="panel-3">
  <div class="card">
    <div class="card-title-row">
      <span class="card-step-num" aria-hidden="true">III</span>
      <h2>分析結果</h2>
    </div>
    <div class="card-divider" aria-hidden="true"></div>
    <p>AI 自動提取決議與待辦，可手動調整標記</p>

    <div id="ollama-warn" class="banner banner-warn" style="display:none">
      <span>⚠ Ollama 未運行，請先執行 <code>ollama serve</code></span>
      <button class="btn btn-secondary" style="font-size:11px;padding:8px 14px" onclick="reanalyze()">重新分析</button>
    </div>
    <div id="resolved-banner" class="banner banner-success" style="display:none"></div>

    <div id="decisions-section" style="display:none">
      <div class="analysis-section-title">決議事項</div>
      <div id="decisions-list"></div>
    </div>

    <div id="action-items-section" style="display:none">
      <div class="analysis-section-title">待辦事項</div>
      <div id="action-items-list"></div>
    </div>

    <div class="segments-title">逐字稿</div>
    <div id="segments-list" style="margin-bottom:28px"></div>
    <button class="btn btn-primary" onclick="goToStep(4); renderSummary()">產生摘要</button>
  </div>
</div>
```

- [ ] **Step 3: Add JS state variables and renderAnalysis function**

In the `<script>` block, after `let segments = [];`, add:

```javascript
let decisions = [];
let actionItems = [];
let resolvedItemIds = [];
let ollamaAvailable = true;
let currentMeetingId = null;
```

After the `escapeHtml` function, add:

```javascript
function renderAnalysis() {
  // Ollama warning
  document.getElementById('ollama-warn').style.display =
    ollamaAvailable ? 'none' : 'flex';

  // Resolved banner
  const resolvedBanner = document.getElementById('resolved-banner');
  if (resolvedItemIds.length > 0) {
    resolvedBanner.textContent = `✓ ${resolvedItemIds.length} 項待辦已在本次會議中完成`;
    resolvedBanner.style.display = 'flex';
  } else {
    resolvedBanner.style.display = 'none';
  }

  // Decision cards
  const decisionsSection = document.getElementById('decisions-section');
  const decisionsList = document.getElementById('decisions-list');
  if (decisions.length > 0) {
    decisionsSection.style.display = 'block';
    decisionsList.innerHTML = decisions.map(d => `
      <div class="analysis-card">
        <div class="analysis-card-content">${escapeHtml(d.content)}</div>
        <div class="analysis-card-meta">
          ${d.rationale ? `<span>理由：${escapeHtml(d.rationale)}</span>` : ''}
          ${d.related_people && d.related_people.length > 0
            ? `<span>相關人員：${d.related_people.map(escapeHtml).join('、')}</span>`
            : ''}
        </div>
      </div>
    `).join('');
  } else {
    decisionsSection.style.display = 'none';
  }

  // Action item cards
  const actionItemsSection = document.getElementById('action-items-section');
  const actionItemsList = document.getElementById('action-items-list');
  if (actionItems.length > 0) {
    actionItemsSection.style.display = 'block';
    actionItemsList.innerHTML = actionItems.map(a => `
      <div class="analysis-card">
        <div class="analysis-card-content">${escapeHtml(a.content)}</div>
        <div class="analysis-card-meta">
          <span class="priority-badge priority-${a.priority}">${
            {'high':'高','medium':'中','low':'低'}[a.priority] || a.priority
          }</span>
          ${a.assignee ? `<span>負責人：${escapeHtml(a.assignee)}</span>` : ''}
          ${a.deadline ? `<span>截止：${escapeHtml(a.deadline)}</span>` : ''}
        </div>
      </div>
    `).join('');
  } else {
    actionItemsSection.style.display = 'none';
  }
}

async function reanalyze() {
  if (!currentMeetingId) return;
  // Re-fetch result (Ollama might now be available)
  const res = await fetch(`${API}/result/${jobId}`);
  if (!res.ok) return;
  const data = await res.json();
  decisions = data.decisions || [];
  actionItems = data.action_items || [];
  resolvedItemIds = data.resolved_item_ids || [];
  ollamaAvailable = data.ollama_available !== false;
  renderAnalysis();
  renderSegments();
}
```

- [ ] **Step 4: Update loadResult() to populate new state**

Replace the existing `loadResult` function:

```javascript
async function loadResult() {
  const res = await fetch(`${API}/result/${jobId}`);
  if (!res.ok) {
    showTranscribeError('無法取得轉錄結果');
    return;
  }
  const data = await res.json();
  segments = data.segments;
  decisions = data.decisions || [];
  actionItems = data.action_items || [];
  resolvedItemIds = data.resolved_item_ids || [];
  ollamaAvailable = data.ollama_available !== false;
  currentMeetingId = data.meeting_id || null;

  // Pre-apply AI tags to segments based on action_items content matching
  // (segments keep tag=null; AI results are shown separately in cards)
  goToStep(3);
  renderAnalysis();
  renderSegments();
}
```

- [ ] **Step 5: Update startOver() to reset new state**

Add these lines inside `startOver()`, after `segments = [];`:

```javascript
decisions = [];
actionItems = [];
resolvedItemIds = [];
ollamaAvailable = true;
currentMeetingId = null;
document.getElementById('ollama-warn').style.display = 'none';
document.getElementById('resolved-banner').style.display = 'none';
document.getElementById('decisions-section').style.display = 'none';
document.getElementById('action-items-section').style.display = 'none';
```

- [ ] **Step 6: Manual verification**

Start the server (`uvicorn server:app --reload`), ensure Ollama is running (`ollama serve`), open `index.html` in a browser, upload an audio file. After transcription completes:

- Step III should show decision cards and action item cards (or Ollama warning banner if Ollama is down)
- Segments should still be shown below and manually taggable
- "產生摘要" button should still work

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "feat: Step III — AI analysis results view with decision/action item cards"
```

---

### Task 6: Frontend Step IV — history panel + updated renderSummary

**Files:**
- Modify: `index.html`

Step IV currently shows a text summary. After this task it also shows a **歷史待辦追蹤** panel listing all pending action items from previous meetings with a "標記完成" button per item.

- [ ] **Step 1: Add CSS for history panel**

Inside `<style>`, after `.priority-low` rule, add:

```css
/* ── History Panel ── */
.history-panel {
  margin-top: 36px;
  border-top: 1px solid var(--gold-dim);
  padding-top: 28px;
}
.history-panel-title {
  font-family: var(--font-display);
  font-size: 14px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.history-panel-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--gold-dim);
}
.history-item {
  background: rgba(212,175,55,0.02);
  border: 1px solid rgba(212,175,55,0.1);
  padding: 14px 16px;
  margin-bottom: 8px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
}
.history-item-body { flex: 1; }
.history-item-content {
  font-size: 13px;
  color: var(--cream);
  letter-spacing: 0.02em;
  line-height: 1.6;
  margin-bottom: 6px;
}
.history-item-meta {
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.btn-resolve {
  padding: 6px 12px;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
  border: 1px solid rgba(136,136,136,0.3);
  background: transparent;
  color: var(--muted);
  font-family: var(--font-body);
  flex-shrink: 0;
  transition: all 0.2s;
}
.btn-resolve:hover {
  border-color: var(--gold);
  color: var(--gold);
}
.history-empty {
  font-size: 12px;
  color: var(--muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-align: center;
  padding: 20px 0;
}
```

- [ ] **Step 2: Update Step IV HTML panel**

Replace the existing Step IV panel:

```html
<!-- Step IV: Summary -->
<div class="step-panel" id="panel-4">
  <div class="card">
    <div class="card-title-row">
      <span class="card-step-num" aria-hidden="true">IV</span>
      <h2>會議摘要</h2>
    </div>
    <div class="card-divider" aria-hidden="true"></div>
    <p>整理完成，可一鍵複製全文</p>
    <div id="summary-output" aria-label="會議摘要內容"></div>
    <div class="btn-row">
      <button class="btn btn-primary" id="copyBtn" onclick="copySummary()">複製摘要</button>
      <button class="btn btn-secondary" onclick="startOver()">重新開始</button>
    </div>

    <div class="history-panel">
      <div class="history-panel-title">歷史待辦追蹤</div>
      <div id="history-list"></div>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Update renderSummary() to include AI-extracted items**

Replace the existing `renderSummary` function:

```javascript
function renderSummary() {
  const manualDecisions = segments.filter(s => s.tag === 'decision');
  const manualActions   = segments.filter(s => s.tag === 'action');
  const allText = segments.map(s => s.text).join('\n');

  let output = '【會議記錄】\n' + allText + '\n';

  if (decisions.length > 0) {
    output += '\n【決議事項】\n';
    decisions.forEach((d, i) => {
      output += `${i + 1}. ${d.content}`;
      if (d.rationale) output += `（${d.rationale}）`;
      output += '\n';
    });
  } else if (manualDecisions.length > 0) {
    output += '\n【決議事項】\n';
    manualDecisions.forEach((s, i) => { output += `${i + 1}. ${s.text}\n`; });
  }

  if (actionItems.length > 0) {
    output += '\n【待辦事項】\n';
    actionItems.forEach((a, i) => {
      output += `${i + 1}. ${a.content}`;
      if (a.assignee) output += `（負責人：${a.assignee}）`;
      if (a.deadline) output += `（截止：${a.deadline}）`;
      output += '\n';
    });
  } else if (manualActions.length > 0) {
    output += '\n【待辦事項】\n';
    manualActions.forEach((s, i) => { output += `${i + 1}. ${s.text}\n`; });
  }

  document.getElementById('summary-output').textContent = output;
  loadHistoryPanel();
}
```

- [ ] **Step 4: Add loadHistoryPanel() and resolveHistoryItem() functions**

After `renderSummary`, add:

```javascript
async function loadHistoryPanel() {
  const list = document.getElementById('history-list');
  list.innerHTML = '<div class="history-empty">載入中...</div>';
  try {
    const res = await fetch(`${API}/action-items/pending`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    const items = data.items || [];
    if (items.length === 0) {
      list.innerHTML = '<div class="history-empty">目前無待處理事項</div>';
      return;
    }
    list.innerHTML = items.map(item => `
      <div class="history-item" id="history-item-${item.meeting_id}-${item.id}">
        <div class="history-item-body">
          <div class="history-item-content">${escapeHtml(item.content)}</div>
          <div class="history-item-meta">
            <span class="priority-badge priority-${item.priority}">${
              {'high':'高','medium':'中','low':'低'}[item.priority] || item.priority
            }</span>
            ${item.assignee ? `<span>負責人：${escapeHtml(item.assignee)}</span>` : ''}
            ${item.deadline ? `<span>截止：${escapeHtml(item.deadline)}</span>` : ''}
            <span>來源：${escapeHtml(item.meeting_date || item.meeting_id)}</span>
          </div>
        </div>
        <button class="btn-resolve"
          onclick="resolveHistoryItem('${escapeHtml(item.meeting_id)}','${escapeHtml(item.id)}', this)">
          標記完成
        </button>
      </div>
    `).join('');
  } catch {
    list.innerHTML = '<div class="history-empty">無法載入歷史待辦</div>';
  }
}

async function resolveHistoryItem(meetingId, itemId, btn) {
  btn.disabled = true;
  btn.textContent = '處理中...';
  try {
    const res = await fetch(`${API}/action-items/${meetingId}/${itemId}/resolve`, {
      method: 'POST',
    });
    if (res.ok) {
      const row = document.getElementById(`history-item-${meetingId}-${itemId}`);
      if (row) {
        row.style.opacity = '0.4';
        btn.textContent = '已完成 ✓';
        setTimeout(() => row.remove(), 1200);
      }
    } else {
      btn.textContent = '失敗';
      setTimeout(() => { btn.textContent = '標記完成'; btn.disabled = false; }, 2000);
    }
  } catch {
    btn.textContent = '失敗';
    setTimeout(() => { btn.textContent = '標記完成'; btn.disabled = false; }, 2000);
  }
}
```

- [ ] **Step 5: Manual verification**

Open `index.html`, complete a full transcription + analysis flow. On Step IV:
- Summary shows AI-extracted decisions and action items (or manual tags if AI unavailable)
- History panel shows pending items from previous meetings
- "標記完成" button marks an item done and removes it from the list with fade

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat: Step IV — history panel with pending action items and manual resolve"
```

---

## Self-Review

### Spec coverage check

| Spec requirement | Task |
|---|---|
| `analyzer.py` — calls Ollama, builds prompt, parses JSON, retries | Task 2 |
| `storage.py` — reads/writes meetings/ | Task 1 |
| `meetings/YYYY-MM-DD_HH-MM.json` schema with decisions + action_items | Tasks 1+3 |
| Llama response parsed, IDs assigned (`d-1`, `a-1`) | Task 3 |
| `resolved_action_item_ids` → update source files | Task 3 |
| `GET /meetings`, `GET /meetings/{id}`, `GET /action-items/pending` | Task 4 |
| `/result/{job_id}` extended with decisions, action_items, resolved_items | Task 3 |
| Retry 2 times on invalid JSON, then return empty | Task 2 |
| Decision cards (content, rationale, related people) | Task 5 |
| Action item cards (content, assignee, deadline, priority badge) | Task 5 |
| Resolved banner "X 項待辦已在本次會議中完成" | Task 5 |
| Ollama warning banner + "重新分析" button | Task 5 |
| 歷史待辦追蹤 panel with manual "標記完成" | Task 6 |
| `meetings/` auto-created on first save | Task 1 (`mkdir exist_ok`) |
| Corrupted file skipped | Task 1 |
| Priority badges: high=gold / medium=cream / low=muted | Task 5 (CSS `.priority-high/medium/low`) |

All spec requirements covered. No gaps.

### Type consistency check
- `decisions` items always have: `id`, `content`, `rationale`, `related_people`, `status` — assigned in Task 3, consumed in Task 5 ✓
- `action_items` items always have: `id`, `content`, `assignee`, `deadline`, `priority`, `status` — assigned in Task 3, consumed in Tasks 5 & 6 ✓
- `meeting_id` format `YYYY-MM-DD_HH-MM` used consistently in storage filename and jobs dict ✓
- `pending_items` from `get_pending_action_items()` include `meeting_id` and `meeting_date` — used in Task 3 for resolve mapping and Task 6 for display ✓
