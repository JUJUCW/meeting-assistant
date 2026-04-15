# translation_storage.py
"""Storage module for translation sessions."""
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

TranslationStatus = Literal["in_progress", "completed", "interrupted"]

TRANSLATIONS_DIR = Path(__file__).parent / "translations"
AUDIO_DIR = Path(__file__).parent / "audio"

_TRANSLATION_ID_RE = re.compile(r"^T-\d{3,}$")


@dataclass
class Sentence:
    """A single transcribed and translated sentence."""

    sentence_id: str
    sequence: int
    offset_sec: int
    original_text: str
    translated_text: str
    confidence: float


@dataclass
class Translation:
    """A translation session containing metadata and sentences."""

    id: str
    name: str
    started_at: str
    ended_at: str | None
    duration_sec: int
    source_lang: str
    target_lang: str
    status: TranslationStatus
    audio_path: str | None
    audio_size_bytes: int | None
    sentences: list[Sentence]


def _validate_translation_id(translation_id: str) -> None:
    """Validate translation ID format (T-001, T-002, etc.)."""
    if not _TRANSLATION_ID_RE.match(translation_id):
        raise ValueError(f"Invalid translation_id format: {translation_id!r}")


def generate_id() -> str:
    """Generate next translation ID (T-001, T-002, etc.)."""
    TRANSLATIONS_DIR.mkdir(exist_ok=True)

    max_num = 0
    for path in TRANSLATIONS_DIR.glob("T-*.json"):
        match = re.match(r"T-(\d+)\.json$", path.name)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)

    return f"T-{max_num + 1:03d}"


def save(translation: Translation) -> None:
    """Save a translation session to JSON file."""
    _validate_translation_id(translation.id)
    TRANSLATIONS_DIR.mkdir(exist_ok=True)
    AUDIO_DIR.mkdir(exist_ok=True)

    path = TRANSLATIONS_DIR / f"{translation.id}.json"
    data = asdict(translation)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load(translation_id: str) -> Translation | None:
    """Load a translation session from JSON file."""
    _validate_translation_id(translation_id)
    path = TRANSLATIONS_DIR / f"{translation_id}.json"

    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text())
        sentences = [Sentence(**s) for s in data.pop("sentences", [])]
        return Translation(**data, sentences=sentences)
    except Exception:
        return None


def list_translations(
    page: int = 1,
    limit: int = 8,
    status: str | None = None,
    source_lang: str | None = None,
    target_lang: str | None = None,
    q: str | None = None,
) -> tuple[list[Translation], int]:
    """List translation sessions with filtering and pagination.

    Args:
        page: Page number (1-based)
        limit: Items per page (default 8)
        status: Filter by status (in_progress, completed, interrupted)
        source_lang: Filter by source language
        target_lang: Filter by target language
        q: Search keyword in name (case-insensitive)

    Returns:
        Tuple of (list of Translation objects, total count)
    """
    if not TRANSLATIONS_DIR.exists():
        return [], 0

    results: list[Translation] = []
    for path in sorted(TRANSLATIONS_DIR.glob("T-*.json"), reverse=True):
        try:
            data = json.loads(path.read_text())
            sentences = [Sentence(**s) for s in data.pop("sentences", [])]
            translation = Translation(**data, sentences=sentences)

            # Apply filters
            if status and translation.status != status:
                continue
            if source_lang and translation.source_lang != source_lang:
                continue
            if target_lang and translation.target_lang != target_lang:
                continue
            if q and q.lower() not in translation.name.lower():
                continue

            results.append(translation)
        except Exception:
            continue

    total = len(results)
    start = (page - 1) * limit
    return results[start : start + limit], total


def update_name(translation_id: str, name: str) -> Translation | None:
    """Update translation name.

    Args:
        translation_id: ID of translation to update
        name: New name

    Returns:
        Updated Translation or None if not found
    """
    translation = load(translation_id)
    if translation is None:
        return None

    translation.name = name
    save(translation)
    return translation


def delete(translation_id: str) -> bool:
    """Delete translation and associated audio file.

    Args:
        translation_id: ID of translation to delete

    Returns:
        True if deleted, False if not found
    """
    _validate_translation_id(translation_id)
    path = TRANSLATIONS_DIR / f"{translation_id}.json"

    if not path.exists():
        return False

    # Load to get audio path before deleting
    translation = load(translation_id)
    if translation and translation.audio_path:
        audio_file = Path(translation.audio_path)
        # Handle both relative and absolute paths
        if not audio_file.is_absolute():
            audio_file = AUDIO_DIR.parent / translation.audio_path
        if audio_file.exists():
            audio_file.unlink()

    path.unlink()
    return True


def append_sentence(translation_id: str, sentence: Sentence) -> None:
    """Append a sentence to a translation session.

    Args:
        translation_id: ID of translation
        sentence: Sentence to append

    Raises:
        ValueError: If translation not found
    """
    translation = load(translation_id)
    if translation is None:
        raise ValueError(f"Translation not found: {translation_id}")

    translation.sentences.append(sentence)
    save(translation)


def update_sentence_translation(
    translation_id: str, sentence_id: str, translated_text: str
) -> None:
    """Update the translated text of a specific sentence.

    Args:
        translation_id: ID of translation
        sentence_id: ID of sentence to update
        translated_text: New translated text

    Raises:
        ValueError: If translation or sentence not found
    """
    translation = load(translation_id)
    if translation is None:
        raise ValueError(f"Translation not found: {translation_id}")

    for sentence in translation.sentences:
        if sentence.sentence_id == sentence_id:
            sentence.translated_text = translated_text
            save(translation)
            return

    raise ValueError(f"Sentence not found: {sentence_id}")
