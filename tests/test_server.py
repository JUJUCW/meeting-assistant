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
