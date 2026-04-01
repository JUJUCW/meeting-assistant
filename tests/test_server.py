import pytest
import io
import httpx
from httpx import AsyncClient, ASGITransport
from server import app
import storage

@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

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

@pytest.mark.anyio
async def test_status_pending():
    from server import jobs
    jobs["test-job-1"] = {"status": "pending", "segments": [], "error": None}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/status/test-job-1")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"

@pytest.mark.anyio
async def test_status_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/status/nonexistent-xyz-123")
    assert response.status_code == 404

@pytest.mark.anyio
async def test_result_done():
    from server import jobs
    jobs["test-job-2"] = {
        "status": "done",
        "segments": [{"id": 0, "text": "Hello", "tag": None}],
        "decisions": [],
        "action_items": [],
        "resolved_item_ids": [],
        "meeting_id": None,
        "ollama_available": None,
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


# ── Task 3 tests ──

from unittest.mock import patch, MagicMock

ANALYSIS_RESULT = {
    "decisions": [{"content": "採用新系統", "rationale": "效率", "related_people": []}],
    "action_items": [{"content": "更新文件", "assignee": "小明", "deadline": "2026-04-01", "priority": "high"}],
    "resolved_action_item_ids": [],
}


@pytest.mark.anyio
async def test_result_includes_decisions_when_ollama_available():
    import anyio
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
            content = b"\x1aE\xdf\xa3"
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

                for _ in range(30):
                    await anyio.sleep(0.1)
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
                assert body["ollama_available"] is True
                assert len(body["decisions"]) == 1


@pytest.mark.anyio
async def test_result_ollama_unavailable_returns_empty_lists():
    import anyio
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

                for _ in range(30):
                    await anyio.sleep(0.1)
                    s = await client.get(f"/status/{job_id}")
                    if s.json()["status"] in ("done", "error"):
                        break

                result_res = await client.get(f"/result/{job_id}")
                body = result_res.json()
                assert body["ollama_available"] is False
                assert body["decisions"] == []


# ── Task 4 tests: new endpoints ──

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


# ── Task 2 tests: delete and patch endpoints ──

@pytest.mark.anyio
async def test_delete_meeting_success(monkeypatch):
    monkeypatch.setattr(storage, "delete_meeting", lambda mid: True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete("/meetings/2026-03-28_14-30")
    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}


@pytest.mark.anyio
async def test_delete_meeting_not_found(monkeypatch):
    monkeypatch.setattr(storage, "delete_meeting", lambda mid: False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete("/meetings/nonexistent")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_patch_decision_success(monkeypatch):
    updated = {"id": "d-1", "content": "新決議", "rationale": "效率", "related_people": [], "status": "confirmed"}
    monkeypatch.setattr(storage, "update_decision", lambda mid, did, updates: updated)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            "/meetings/2026-03-28_14-30/decisions/d-1",
            json={"content": "新決議"},
        )
    assert response.status_code == 200
    assert response.json()["content"] == "新決議"


@pytest.mark.anyio
async def test_patch_decision_not_found(monkeypatch):
    monkeypatch.setattr(storage, "update_decision", lambda mid, did, updates: None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            "/meetings/nonexistent/decisions/d-1",
            json={"content": "x"},
        )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_patch_action_item_success(monkeypatch):
    updated = {"id": "a-1", "content": "更新文件", "assignee": "小明", "deadline": "2026-04-01", "priority": "high", "status": "done"}
    monkeypatch.setattr(storage, "update_action_item", lambda mid, iid, updates: updated)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            "/meetings/2026-03-28_14-30/action-items/a-1",
            json={"status": "done"},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "done"


@pytest.mark.anyio
async def test_patch_action_item_not_found(monkeypatch):
    monkeypatch.setattr(storage, "update_action_item", lambda mid, iid, updates: None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            "/meetings/nonexistent/action-items/a-1",
            json={"status": "done"},
        )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_decision_success(monkeypatch):
    new_d = {"id": "d-2", "content": "新決議", "rationale": "", "related_people": [], "status": "confirmed"}
    monkeypatch.setattr(storage, "add_decision", lambda mid, data: new_d)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/2026-03-28_14-30/decisions",
            json={"content": "新決議", "rationale": "", "related_people": []},
        )
    assert response.status_code == 200
    assert response.json()["id"] == "d-2"


@pytest.mark.anyio
async def test_create_decision_not_found(monkeypatch):
    monkeypatch.setattr(storage, "add_decision", lambda mid, data: None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/nonexistent/decisions",
            json={"content": "x", "rationale": "", "related_people": []},
        )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_action_item_success(monkeypatch):
    new_a = {"id": "a-2", "content": "新任務", "assignee": "", "deadline": "", "priority": "medium", "status": "pending"}
    monkeypatch.setattr(storage, "add_action_item", lambda mid, data: new_a)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/2026-03-28_14-30/action-items",
            json={"content": "新任務", "assignee": "", "deadline": "", "priority": "medium"},
        )
    assert response.status_code == 200
    assert response.json()["id"] == "a-2"


@pytest.mark.anyio
async def test_create_action_item_not_found(monkeypatch):
    monkeypatch.setattr(storage, "add_action_item", lambda mid, data: None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/nonexistent/action-items",
            json={"content": "x", "assignee": "", "deadline": "", "priority": "medium"},
        )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_decision_missing_content_returns_422(monkeypatch):
    def _raise_value_error(mid, data):
        raise ValueError("content is required")
    monkeypatch.setattr(storage, "add_decision", _raise_value_error)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/2026-03-28_14-30/decisions",
            json={"rationale": ""},
        )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_action_item_missing_content_returns_422(monkeypatch):
    def _raise_value_error(mid, data):
        raise ValueError("content is required")
    monkeypatch.setattr(storage, "add_action_item", _raise_value_error)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/2026-03-28_14-30/action-items",
            json={"priority": "medium"},
        )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_action_item_missing_priority_returns_422(monkeypatch):
    def _raise_value_error(mid, data):
        raise ValueError("priority is required")
    monkeypatch.setattr(storage, "add_action_item", _raise_value_error)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/2026-03-28_14-30/action-items",
            json={"content": "任務"},
        )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_transcribe_file_too_large_returns_413():
    oversized = io.BytesIO(b"x" * (200 * 1024 * 1024 + 1))
    oversized.name = "big.mp3"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/transcribe",
            files={"file": ("big.mp3", oversized, "audio/mpeg")},
        )
    assert response.status_code == 413
    assert "200 MB" in response.json()["detail"]


# ── Search endpoint tests ──

@pytest.mark.anyio
async def test_search_endpoint_returns_matching_meetings(monkeypatch):
    results = [
        {
            "id": "2026-03-28_14-30",
            "created_at": "2026-03-28T14:30:00",
            "decision_count": 1,
            "action_item_count": 1,
            "pending_action_item_count": 1,
            "hits": [{"field": "transcript", "snippet": "…採用新系統…"}],
        }
    ]
    monkeypatch.setattr(storage, "search_meetings", lambda q: results)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/meetings/search?q=新系統")
    assert res.status_code == 200
    data = res.json()
    assert len(data["meetings"]) == 1
    assert data["meetings"][0]["id"] == "2026-03-28_14-30"
    assert data["meetings"][0]["hits"][0]["field"] == "transcript"


@pytest.mark.anyio
async def test_search_endpoint_empty_query_returns_empty(monkeypatch):
    monkeypatch.setattr(storage, "search_meetings", lambda q: [])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/meetings/search?q=")
    assert res.status_code == 200
    assert res.json()["meetings"] == []


@pytest.mark.anyio
async def test_search_endpoint_no_match_returns_empty(monkeypatch):
    monkeypatch.setattr(storage, "search_meetings", lambda q: [])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/meetings/search?q=notfound")
    assert res.status_code == 200
    assert res.json()["meetings"] == []


# ── Categories ──────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_categories_returns_list(monkeypatch):
    monkeypatch.setattr(storage, "load_categories", lambda: [{"id": "cat-1", "name": "週會"}])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/categories")
    assert r.status_code == 200
    assert r.json() == {"categories": [{"id": "cat-1", "name": "週會"}]}


@pytest.mark.anyio
async def test_post_category_adds_item(monkeypatch):
    new_cat = {"id": "cat-abc12345", "name": "新分類"}
    monkeypatch.setattr(storage, "add_category", lambda name: new_cat)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/categories", json={"name": "新分類"})
    assert r.status_code == 200
    assert r.json() == new_cat


@pytest.mark.anyio
async def test_delete_category_success(monkeypatch):
    monkeypatch.setattr(storage, "delete_category", lambda cat_id: True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.delete("/categories/cat-1")
    assert r.status_code == 200
    assert r.json() == {"status": "deleted"}


@pytest.mark.anyio
async def test_delete_category_not_found(monkeypatch):
    monkeypatch.setattr(storage, "delete_category", lambda cat_id: False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.delete("/categories/cat-999")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_patch_meeting_tags_success(monkeypatch):
    updated = {"id": "2026-03-28_14-30", "category_id": "cat-2", "tags": ["Q2"],
               "decisions": [], "action_items": [], "transcript": "", "created_at": "2026-03-28T14:30:00"}
    monkeypatch.setattr(storage, "update_meeting_tags", lambda mid, updates: updated)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.patch("/meetings/2026-03-28_14-30/tags", json={"category_id": "cat-2", "tags": ["Q2"]})
    assert r.status_code == 200
    assert r.json()["category_id"] == "cat-2"


@pytest.mark.anyio
async def test_patch_meeting_tags_not_found(monkeypatch):
    monkeypatch.setattr(storage, "update_meeting_tags", lambda mid, updates: None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.patch("/meetings/2099-01-01_00-00/tags", json={"tags": []})
    assert r.status_code == 404


# ── UAT-style flow tests (real storage, no mocks) ──────────────────────────

@pytest.fixture
def tmp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEETINGS_DIR", tmp_path / "meetings")
    monkeypatch.setattr(storage, "CATEGORIES_PATH", tmp_path / "categories.json")


def _make_meeting(mid="2026-03-28_14-30"):
    return {
        "id": mid,
        "created_at": "2026-03-28T14:30:00",
        "transcript": "今天決定採用新系統",
        "decisions": [],
        "action_items": [],
    }


@pytest.mark.anyio
async def test_patch_tags_then_list_includes_tags(tmp_storage):
    """PATCH tags → GET /meetings 回傳的摘要帶 tags 欄位。"""
    mid = "2026-03-28_14-30"
    storage.save_meeting(_make_meeting(mid))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.patch(f"/meetings/{mid}/tags", json={"tags": ["Q2", "重要"]})
        assert r.status_code == 200

        r = await client.get("/meetings")
        meeting = r.json()["meetings"][0]
        assert meeting["tags"] == ["Q2", "重要"]
        assert meeting["category_id"] is None


@pytest.mark.anyio
async def test_patch_tags_then_get_meeting_persists(tmp_storage):
    """PATCH tags → GET /meetings/{id} 能讀回完整 tags。"""
    mid = "2026-03-28_14-30"
    storage.save_meeting(_make_meeting(mid))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.patch(f"/meetings/{mid}/tags", json={"tags": ["test-tag"]})
        r = await client.get(f"/meetings/{mid}")
        assert r.json()["tags"] == ["test-tag"]


@pytest.mark.anyio
async def test_patch_tags_then_search_includes_tags(tmp_storage):
    """PATCH tags → GET /meetings/search 回傳的結果帶 tags 欄位。"""
    mid = "2026-03-28_14-30"
    storage.save_meeting(_make_meeting(mid))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.patch(f"/meetings/{mid}/tags", json={"tags": ["Q2"]})
        r = await client.get("/meetings/search?q=新系統")
        result = r.json()["meetings"][0]
        assert result["tags"] == ["Q2"]


@pytest.mark.anyio
async def test_category_create_assign_list(tmp_storage):
    """POST /categories → PATCH tags → GET /meetings 帶 category_id。"""
    mid = "2026-03-28_14-30"
    storage.save_meeting(_make_meeting(mid))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/categories", json={"name": "週會"})
        assert r.status_code == 200
        cat_id = r.json()["id"]

        await client.patch(f"/meetings/{mid}/tags", json={"category_id": cat_id})

        r = await client.get("/meetings")
        assert r.json()["meetings"][0]["category_id"] == cat_id


@pytest.mark.anyio
async def test_patch_tags_clears_existing_tags(tmp_storage):
    """送空 tags 陣列會清除舊標籤。"""
    mid = "2026-03-28_14-30"
    m = _make_meeting(mid)
    m["tags"] = ["old-tag"]
    storage.save_meeting(m)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.patch(f"/meetings/{mid}/tags", json={"tags": []})
        r = await client.get(f"/meetings/{mid}")
        assert r.json()["tags"] == []


@pytest.mark.anyio
async def test_post_category_empty_name_returns_422(tmp_storage):
    """空白分類名稱應回傳 422。"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/categories", json={"name": "  "})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_patch_tags_missing_meeting_returns_404(tmp_storage):
    """對不存在的會議 PATCH tags 應回傳 404（真實 storage 驗證）。"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.patch("/meetings/2099-01-01_00-00/tags", json={"tags": ["x"]})
    assert r.status_code == 404
