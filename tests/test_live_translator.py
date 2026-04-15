# tests/test_live_translator.py
"""Tests for live_translator module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

import translation_storage
from translation_storage import Sentence, Translation


@pytest.fixture(autouse=True)
def tmp_dirs(tmp_path, monkeypatch):
    """Set up temporary directories for translations and audio."""
    monkeypatch.setattr(translation_storage, "TRANSLATIONS_DIR", tmp_path / "translations")
    monkeypatch.setattr(translation_storage, "AUDIO_DIR", tmp_path / "audio")


def _sample_translation(tid: str = "T-001", status: str = "in_progress") -> Translation:
    return Translation(
        id=tid,
        name="Test Translation",
        started_at="2026-04-14T10:00:00",
        ended_at=None,
        duration_sec=0,
        source_lang="",
        target_lang="zh-TW",
        status=status,
        audio_path=None,
        audio_size_bytes=None,
        sentences=[],
    )


class TestLiveTranslatorFramework:
    """Tests for LiveTranslator class framework (Task 3.1)."""

    def test_live_translator_initialization(self):
        """LiveTranslator should initialize with session ID."""
        from live_translator import LiveTranslator

        translator = LiveTranslator(session_id="T-001")
        assert translator.session_id == "T-001"
        assert translator._started is False

    def test_live_translator_callbacks(self):
        """LiveTranslator should accept callbacks."""
        from live_translator import LiveTranslator

        on_sentence = Mock()
        on_translation = Mock()
        on_error = Mock()

        translator = LiveTranslator(
            session_id="T-001",
            on_sentence=on_sentence,
            on_translation=on_translation,
            on_error=on_error,
        )
        assert translator.on_sentence is on_sentence
        assert translator.on_translation is on_translation
        assert translator.on_error is on_error

    def test_start_initializes_state(self):
        """start() should initialize session state."""
        from live_translator import LiveTranslator

        session = _sample_translation("T-001")
        translation_storage.save(session)

        translator = LiveTranslator(session_id="T-001")
        translator.start()

        assert translator._started is True
        assert translator._audio_buffer is not None
        assert translator._audio_chunks == []
        assert translator._sentence_counter == 0

    def test_stop_finalizes_session(self):
        """stop() should finalize session and mark as completed."""
        from live_translator import LiveTranslator

        session = _sample_translation("T-001", status="in_progress")
        translation_storage.save(session)

        translator = LiveTranslator(session_id="T-001")
        translator.start()
        translator.stop()

        assert translator._started is False

        # Verify session status updated
        loaded = translation_storage.load("T-001")
        assert loaded.status == "completed"


class TestLogprobToConfidence:
    """Tests for logprob_to_confidence function (Task 3.3)."""

    def test_logprob_zero_returns_one(self):
        """avg_logprob of 0 should give confidence ~1.0."""
        from live_translator import logprob_to_confidence

        confidence = logprob_to_confidence(0.0)
        assert 0.99 <= confidence <= 1.0

    def test_logprob_minus_one_returns_lower(self):
        """avg_logprob of -1 should give confidence ~0.37."""
        from live_translator import logprob_to_confidence

        confidence = logprob_to_confidence(-1.0)
        assert 0.35 <= confidence <= 0.40

    def test_logprob_clamped_lower(self):
        """Very low logprob should be clamped."""
        from live_translator import logprob_to_confidence

        confidence = logprob_to_confidence(-10.0)
        # exp(-2) ≈ 0.135
        assert 0.10 <= confidence <= 0.20


class TestAudioBufferAccumulation:
    """Tests for audio buffer logic (Task 3.2)."""

    def test_add_audio_chunk_before_start(self):
        """add_audio_chunk should do nothing before start()."""
        from live_translator import LiveTranslator

        translator = LiveTranslator(session_id="T-001")
        translator.add_audio_chunk(b"test audio")
        assert translator._audio_chunks == []

    def test_add_audio_chunk_accumulates(self):
        """add_audio_chunk should accumulate audio data."""
        from live_translator import LiveTranslator

        session = _sample_translation("T-001")
        translation_storage.save(session)

        translator = LiveTranslator(session_id="T-001")
        translator.start()
        translator.add_audio_chunk(b"chunk1")
        translator.add_audio_chunk(b"chunk2")

        assert len(translator._audio_chunks) == 2
        assert len(translator._full_audio) == 2


class TestTranslateText:
    """Tests for translate_text function (Task 3.4)."""

    @pytest.mark.anyio
    async def test_translate_returns_original_on_timeout(self):
        """translate_text should return original text on timeout."""
        from live_translator import LiveTranslator

        translator = LiveTranslator(session_id="T-001")

        with patch("httpx.AsyncClient.post") as mock_post:
            import httpx
            mock_post.side_effect = httpx.TimeoutException("timeout")

            result = await translator.translate_text("Hello world")
            assert result == "Hello world"

    @pytest.mark.anyio
    async def test_translate_returns_original_on_error(self):
        """translate_text should return original text on error."""
        from live_translator import LiveTranslator

        translator = LiveTranslator(session_id="T-001")

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = Exception("network error")

            result = await translator.translate_text("Hello world")
            assert result == "Hello world"
