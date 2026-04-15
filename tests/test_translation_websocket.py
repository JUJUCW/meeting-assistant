# tests/test_translation_websocket.py
"""Tests for translation WebSocket and new endpoints (Tasks 2.4, 2.5, 4.x)."""

import os
import io
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

import translation_storage
from translation_storage import Sentence, Translation


@pytest.fixture(autouse=True)
def tmp_dirs(tmp_path, monkeypatch):
    """Set up temporary directories for translations and audio."""
    monkeypatch.setattr(translation_storage, "TRANSLATIONS_DIR", tmp_path / "translations")
    monkeypatch.setattr(translation_storage, "AUDIO_DIR", tmp_path / "audio")


def _sample_sentence(seq: int = 1) -> Sentence:
    return Sentence(
        sentence_id=f"T-001-S{seq:03d}",
        sequence=seq,
        offset_sec=seq * 3,
        original_text=f"Test sentence {seq}",
        translated_text=f"測試句子 {seq}",
        confidence=0.85,
    )


def _sample_translation(
    tid: str = "T-001",
    status: str = "completed",
    with_audio: bool = False,
    sentences: list[Sentence] | None = None,
) -> Translation:
    return Translation(
        id=tid,
        name="Test Translation",
        started_at="2026-04-14T10:00:00",
        ended_at="2026-04-14T10:30:00",
        duration_sec=1800,
        source_lang="en",
        target_lang="zh-TW",
        status=status,
        audio_path=f"audio/{tid}.wav" if with_audio else None,
        audio_size_bytes=3600000 if with_audio else None,
        sentences=sentences or [_sample_sentence(1), _sample_sentence(2)],
    )


class TestAudioDownloadEndpoint:
    """Tests for GET /api/translations/{id}/audio endpoint (Task 2.4)."""

    @pytest.mark.anyio
    async def test_download_audio_success(self, tmp_path):
        """Should return audio file for completed session."""
        from httpx import AsyncClient, ASGITransport
        import server

        # Create session with audio
        session = _sample_translation("T-001", status="completed", with_audio=True)
        translation_storage.save(session)

        # Create audio file
        audio_path = translation_storage.AUDIO_DIR / "T-001.wav"
        audio_path.parent.mkdir(exist_ok=True)
        audio_path.write_bytes(b"RIFF" + b"\x00" * 100)  # Fake WAV

        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as client:
            response = await client.get("/api/translations/T-001/audio")

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    @pytest.mark.anyio
    async def test_download_audio_in_progress_returns_404(self):
        """Should return 404 for in_progress session."""
        from httpx import AsyncClient, ASGITransport
        import server

        session = _sample_translation("T-001", status="in_progress")
        translation_storage.save(session)

        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as client:
            response = await client.get("/api/translations/T-001/audio")

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_download_audio_no_file_returns_404(self):
        """Should return 404 if no audio file."""
        from httpx import AsyncClient, ASGITransport
        import server

        session = _sample_translation("T-001", status="completed", with_audio=False)
        translation_storage.save(session)

        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as client:
            response = await client.get("/api/translations/T-001/audio")

        assert response.status_code == 404


class TestDocxExportEndpoint:
    """Tests for GET /api/translations/{id}/export/docx endpoint (Task 2.5)."""

    @pytest.mark.anyio
    async def test_export_docx_success(self):
        """Should return DOCX file."""
        from httpx import AsyncClient, ASGITransport
        import server

        session = _sample_translation("T-001")
        translation_storage.save(session)

        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as client:
            response = await client.get("/api/translations/T-001/export/docx")

        assert response.status_code == 200
        assert "application/vnd.openxmlformats" in response.headers["content-type"]

    @pytest.mark.anyio
    async def test_export_docx_not_found(self):
        """Should return 404 for non-existent session."""
        from httpx import AsyncClient, ASGITransport
        import server

        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as client:
            response = await client.get("/api/translations/T-999/export/docx")

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_export_docx_contains_sentences(self):
        """DOCX should contain sentence data."""
        from httpx import AsyncClient, ASGITransport
        from docx import Document
        import server

        low_conf_sentence = Sentence(
            sentence_id="T-001-S003",
            sequence=3,
            offset_sec=9,
            original_text="Low confidence text",
            translated_text="低信心文字",
            confidence=0.50,  # Below 0.65 threshold
        )
        session = _sample_translation("T-001", sentences=[_sample_sentence(1), low_conf_sentence])
        translation_storage.save(session)

        async with AsyncClient(transport=ASGITransport(app=server.app), base_url="http://test") as client:
            response = await client.get("/api/translations/T-001/export/docx")

        # Parse DOCX
        doc = Document(io.BytesIO(response.content))
        full_text = "\n".join(p.text for p in doc.paragraphs)

        assert "Test sentence 1" in full_text
        assert "Low confidence text" in full_text


class TestWebSocketValidation:
    """Tests for WebSocket connection validation (Task 4.1)."""

    def test_websocket_reject_nonexistent_session(self):
        """Should reject connection for non-existent session."""
        from starlette.testclient import TestClient
        import server

        with TestClient(server.app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/api/translations/T-999/stream"):
                    pass

    def test_websocket_reject_completed_session(self):
        """Should reject connection for completed session."""
        from starlette.testclient import TestClient
        import server

        session = _sample_translation("T-001", status="completed")
        translation_storage.save(session)

        with TestClient(server.app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/api/translations/T-001/stream"):
                    pass

    def test_websocket_accept_in_progress_session(self):
        """Should accept connection for in_progress session."""
        from starlette.testclient import TestClient
        import server

        session = _sample_translation("T-001", status="in_progress")
        translation_storage.save(session)

        with TestClient(server.app) as client:
            with client.websocket_connect("/api/translations/T-001/stream") as ws:
                # Connection accepted - send stop to close cleanly
                ws.send_json({"type": "stop"})
                response = ws.receive_json()
                assert response["type"] == "status"
                assert response["status"] == "completed"
