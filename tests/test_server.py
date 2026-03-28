import pytest
import io
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
