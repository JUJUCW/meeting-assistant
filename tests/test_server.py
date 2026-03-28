import pytest
import io
import httpx
from httpx import AsyncClient, ASGITransport
from server import app

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
