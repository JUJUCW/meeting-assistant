# live_translator.py
"""Live translation module for real-time speech recognition and translation."""

import io
import logging
import math
import os
import tempfile
import uuid
from typing import Callable

import httpx

import translation_storage
from translation_storage import Sentence

logger = logging.getLogger(__name__)

# Ollama configuration (same as analyzer.py)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:4b"

# Audio processing constants
MIN_BUFFER_SECONDS = 3.0
SAMPLE_RATE = 16000


def logprob_to_confidence(avg_logprob: float) -> float:
    """Convert avg_logprob to confidence score (0-1).

    avg_logprob typically ranges from -1.0 (low) to 0 (high).
    We use exp() to convert: exp(0) = 1.0, exp(-1) ~= 0.37
    """
    # Clamp to reasonable range
    clamped = max(-2.0, min(0.0, avg_logprob))
    return math.exp(clamped)


class LiveTranslator:
    """Real-time audio translator with ASR and translation."""

    def __init__(
        self,
        session_id: str,
        whisper_model=None,
        on_sentence: Callable[[Sentence], None] | None = None,
        on_translation: Callable[[str, str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ):
        """Initialize LiveTranslator.

        Args:
            session_id: The translation session ID
            whisper_model: Optional whisper model (for testing/injection)
            on_sentence: Callback when a sentence is recognized
            on_translation: Callback when translation is complete (sentence_id, text)
            on_error: Callback when an error occurs
        """
        self.session_id = session_id
        self._whisper_model = whisper_model
        self.on_sentence = on_sentence
        self.on_translation = on_translation
        self.on_error = on_error

        self._started = False
        self._audio_buffer: io.BytesIO | None = None
        self._audio_chunks: list[bytes] = []
        self._full_audio: list[bytes] = []
        self._sentence_counter = 0
        self._detected_language: str | None = None
        self._start_time: float = 0.0

    def start(self) -> None:
        """Initialize session state for recording."""
        self._started = True
        self._audio_buffer = io.BytesIO()
        self._audio_chunks = []
        self._full_audio = []
        self._sentence_counter = 0
        self._start_time = 0.0
        logger.info("LiveTranslator started for session %s", self.session_id)

    def stop(self) -> None:
        """Finalize session and save audio."""
        if not self._started:
            return

        self._started = False

        # Save full audio if we have any
        if self._full_audio:
            try:
                self._save_full_audio()
            except Exception as e:
                logger.error("Failed to save audio: %s", e)
                if self.on_error:
                    self.on_error(f"Failed to save audio: {e}")

        # Update session status
        session = translation_storage.load(self.session_id)
        if session:
            session.status = "completed"
            translation_storage.save(session)
        logger.info("LiveTranslator stopped for session %s", self.session_id)

    def add_audio_chunk(self, chunk: bytes) -> None:
        """Add an audio chunk to the buffer.

        When buffer reaches MIN_BUFFER_SECONDS, triggers ASR processing.
        """
        if not self._started:
            return

        self._audio_chunks.append(chunk)
        self._full_audio.append(chunk)

        # Check if we have enough audio to process
        # Estimate: WebM/Opus at ~128kbps = ~16KB/s
        # 3 seconds = ~48KB
        total_size = sum(len(c) for c in self._audio_chunks)
        if total_size >= 48000:  # ~3 seconds of audio
            self._process_buffer()

    def _process_buffer(self) -> None:
        """Process accumulated audio buffer."""
        if not self._audio_chunks:
            return

        # Combine chunks
        combined = b"".join(self._audio_chunks)
        self._audio_chunks = []

        try:
            result = self._process_audio(combined)
            if result:
                sentence, text = result
                if self.on_sentence:
                    self.on_sentence(sentence)

                # Store sentence
                translation_storage.append_sentence(self.session_id, sentence)
        except Exception as e:
            logger.error("Audio processing error: %s", e)
            if self.on_error:
                self.on_error(f"Audio processing error: {e}")

    def _process_audio(self, audio_data: bytes) -> tuple[Sentence, str] | None:
        """Process audio data with ASR.

        Returns:
            Tuple of (Sentence, original_text) or None if no speech detected
        """
        if self._whisper_model is None:
            logger.warning("No whisper model available")
            return None

        # Convert to WAV
        wav_data = self._convert_to_wav(audio_data)

        # Write to temp file for whisper
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_data)
            tmp_path = tmp.name

        try:
            # Transcribe
            segments, info = self._whisper_model.transcribe(
                tmp_path,
                language=None,  # Auto-detect
            )

            # Collect segments
            text_parts = []
            total_confidence = 0.0
            segment_count = 0

            for segment in segments:
                text_parts.append(segment.text.strip())
                total_confidence += logprob_to_confidence(segment.avg_logprob)
                segment_count += 1

            if not text_parts:
                return None

            # Detect language from first transcription
            if self._detected_language is None and hasattr(info, "language"):
                self._detected_language = info.language
                session = translation_storage.load(self.session_id)
                if session:
                    session.source_lang = self._detected_language
                    translation_storage.save(session)

            # Create sentence
            self._sentence_counter += 1
            sentence = Sentence(
                sentence_id=f"{self.session_id}-S{self._sentence_counter:03d}",
                sequence=self._sentence_counter,
                offset_sec=int(self._start_time),
                original_text=" ".join(text_parts),
                translated_text="",
                confidence=total_confidence / segment_count if segment_count else 0.0,
            )

            return sentence, sentence.original_text

        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _convert_to_wav(self, audio_data: bytes) -> bytes:
        """Convert WebM/Opus audio to WAV format.

        Uses pydub for conversion.
        """
        try:
            from pydub import AudioSegment

            # Create temp file for input
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                # Load and convert
                segment = AudioSegment.from_file(tmp_path, format="webm")
                segment = segment.set_frame_rate(SAMPLE_RATE)
                segment = segment.set_channels(1)

                # Export to WAV
                output = io.BytesIO()
                segment.export(output, format="wav")
                return output.getvalue()
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        except ImportError:
            logger.error("pydub not installed, returning raw audio")
            return audio_data
        except Exception as e:
            logger.error("Audio conversion failed: %s", e)
            return audio_data

    def _save_full_audio(self) -> None:
        """Save the full recording to a WAV file."""
        if not self._full_audio:
            return

        combined = b"".join(self._full_audio)
        wav_data = self._convert_to_wav(combined)

        # Save to audio directory
        audio_path = translation_storage.AUDIO_DIR / f"{self.session_id}.wav"
        audio_path.parent.mkdir(exist_ok=True)
        audio_path.write_bytes(wav_data)

        # Update session with audio path
        session = translation_storage.load(self.session_id)
        if session:
            session.audio_path = f"audio/{self.session_id}.wav"
            session.audio_size_bytes = len(wav_data)
            translation_storage.save(session)

    async def translate_text(self, text: str) -> str:
        """Translate text using Ollama.

        Returns translated text, or original text on error.
        """
        prompt = (
            f"Translate the following text to Traditional Chinese (zh-TW). "
            f"Output ONLY the translation, nothing else.\n\n"
            f"Text: {text}"
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    OLLAMA_URL,
                    json={"model": MODEL, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                result = response.json()["response"].strip()
                return result if result else text
        except Exception as e:
            logger.warning("Translation failed: %s", e)
            return text

    async def process_and_translate(self, audio_data: bytes) -> None:
        """Process audio and translate result.

        This is the main entry point for WebSocket audio processing.
        """
        # Add to buffer
        self.add_audio_chunk(audio_data)

        # Check if we have a new sentence from buffer processing
        # (handled in add_audio_chunk -> _process_buffer)
