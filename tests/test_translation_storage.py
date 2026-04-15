# tests/test_translation_storage.py
"""Tests for translation_storage module."""
import json
import pytest
from pathlib import Path
from datetime import datetime

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


def _sample_translation(tid: str = "T-001") -> Translation:
    return Translation(
        id=tid,
        name="Test Translation",
        started_at="2026-04-13T14:00:00",
        ended_at="2026-04-13T14:30:00",
        duration_sec=1800,
        source_lang="en",
        target_lang="zh-TW",
        status="completed",
        audio_path="audio/T-001.wav",
        audio_size_bytes=3600000,
        sentences=[_sample_sentence(1), _sample_sentence(2)],
    )


class TestSentenceDataclass:
    def test_sentence_creation(self):
        s = _sample_sentence()
        assert s.sentence_id == "T-001-S001"
        assert s.sequence == 1
        assert s.offset_sec == 3
        assert s.original_text == "Test sentence 1"
        assert s.translated_text == "測試句子 1"
        assert s.confidence == 0.85


class TestTranslationDataclass:
    def test_translation_creation(self):
        t = _sample_translation()
        assert t.id == "T-001"
        assert t.name == "Test Translation"
        assert t.status == "completed"
        assert len(t.sentences) == 2

    def test_translation_with_no_audio(self):
        t = Translation(
            id="T-002",
            name="In Progress",
            started_at="2026-04-13T15:00:00",
            ended_at=None,
            duration_sec=0,
            source_lang="en",
            target_lang="zh-TW",
            status="in_progress",
            audio_path=None,
            audio_size_bytes=None,
            sentences=[],
        )
        assert t.audio_path is None
        assert t.audio_size_bytes is None


class TestGenerateId:
    def test_generate_id_format(self):
        """ID should follow T-001 format."""
        tid = translation_storage.generate_id()
        assert tid.startswith("T-")
        assert len(tid) == 5  # T-001
        int(tid[2:])  # Should be a valid number

    def test_generate_id_increments(self):
        """Each new ID should increment."""
        t1 = _sample_translation("T-001")
        translation_storage.save(t1)

        new_id = translation_storage.generate_id()
        assert new_id == "T-002"

    def test_generate_id_finds_max(self):
        """Should find max ID and increment."""
        translation_storage.save(_sample_translation("T-001"))
        translation_storage.save(_sample_translation("T-005"))
        translation_storage.save(_sample_translation("T-003"))

        new_id = translation_storage.generate_id()
        assert new_id == "T-006"

    def test_generate_id_empty_dir(self):
        """Returns T-001 for empty directory."""
        tid = translation_storage.generate_id()
        assert tid == "T-001"


class TestSaveAndLoad:
    def test_save_creates_directories(self):
        t = _sample_translation()
        translation_storage.save(t)

        assert translation_storage.TRANSLATIONS_DIR.exists()
        assert (translation_storage.TRANSLATIONS_DIR / "T-001.json").exists()

    def test_save_and_load_roundtrip(self):
        t = _sample_translation()
        translation_storage.save(t)

        loaded = translation_storage.load("T-001")
        assert loaded is not None
        assert loaded.id == t.id
        assert loaded.name == t.name
        assert loaded.status == t.status
        assert len(loaded.sentences) == 2
        assert loaded.sentences[0].original_text == "Test sentence 1"

    def test_load_missing_returns_none(self):
        result = translation_storage.load("T-999")
        assert result is None

    def test_save_overwrites_existing(self):
        t = _sample_translation()
        translation_storage.save(t)

        t.name = "Updated Name"
        translation_storage.save(t)

        loaded = translation_storage.load("T-001")
        assert loaded.name == "Updated Name"

    def test_json_format_is_readable(self):
        t = _sample_translation()
        translation_storage.save(t)

        path = translation_storage.TRANSLATIONS_DIR / "T-001.json"
        data = json.loads(path.read_text())

        assert data["id"] == "T-001"
        assert data["name"] == "Test Translation"
        assert len(data["sentences"]) == 2


class TestIdValidation:
    def test_valid_id_format(self):
        """Valid IDs should not raise."""
        translation_storage._validate_translation_id("T-001")
        translation_storage._validate_translation_id("T-999")
        translation_storage._validate_translation_id("T-1234")  # More than 3 digits OK

    def test_invalid_id_raises(self):
        """Invalid IDs should raise ValueError."""
        with pytest.raises(ValueError):
            translation_storage._validate_translation_id("invalid")
        with pytest.raises(ValueError):
            translation_storage._validate_translation_id("T-")
        with pytest.raises(ValueError):
            translation_storage._validate_translation_id("T-abc")
        with pytest.raises(ValueError):
            translation_storage._validate_translation_id("M-001")  # Wrong prefix


def _make_translation(
    tid: str,
    name: str = "Test",
    status: str = "completed",
    source_lang: str = "en",
    target_lang: str = "zh-TW",
) -> Translation:
    """Helper to create translations with custom attributes."""
    return Translation(
        id=tid,
        name=name,
        started_at="2026-04-13T14:00:00",
        ended_at="2026-04-13T14:30:00",
        duration_sec=1800,
        source_lang=source_lang,
        target_lang=target_lang,
        status=status,
        audio_path=None,
        audio_size_bytes=None,
        sentences=[_sample_sentence(1)],
    )


class TestListTranslations:
    def test_list_empty_returns_empty(self):
        """Empty directory returns empty list."""
        result, total = translation_storage.list_translations()
        assert result == []
        assert total == 0

    def test_list_returns_all(self):
        """Returns all translations without filters."""
        translation_storage.save(_make_translation("T-001"))
        translation_storage.save(_make_translation("T-002"))
        translation_storage.save(_make_translation("T-003"))

        result, total = translation_storage.list_translations()
        assert len(result) == 3
        assert total == 3

    def test_list_pagination_default_limit(self):
        """Default limit is 8."""
        for i in range(1, 11):
            translation_storage.save(_make_translation(f"T-{i:03d}"))

        result, total = translation_storage.list_translations()
        assert len(result) == 8
        assert total == 10

    def test_list_pagination_page_2(self):
        """Page 2 returns correct items."""
        for i in range(1, 11):
            translation_storage.save(_make_translation(f"T-{i:03d}"))

        result, total = translation_storage.list_translations(page=2, limit=8)
        assert len(result) == 2
        assert total == 10

    def test_list_filter_by_status(self):
        """Filter by status."""
        translation_storage.save(_make_translation("T-001", status="completed"))
        translation_storage.save(_make_translation("T-002", status="in_progress"))
        translation_storage.save(_make_translation("T-003", status="completed"))

        result, total = translation_storage.list_translations(status="completed")
        assert len(result) == 2
        assert total == 2
        assert all(t.status == "completed" for t in result)

    def test_list_filter_by_source_lang(self):
        """Filter by source language."""
        translation_storage.save(_make_translation("T-001", source_lang="en"))
        translation_storage.save(_make_translation("T-002", source_lang="ja"))
        translation_storage.save(_make_translation("T-003", source_lang="en"))

        result, total = translation_storage.list_translations(source_lang="en")
        assert len(result) == 2
        assert total == 2

    def test_list_filter_by_target_lang(self):
        """Filter by target language."""
        translation_storage.save(_make_translation("T-001", target_lang="zh-TW"))
        translation_storage.save(_make_translation("T-002", target_lang="ja"))

        result, total = translation_storage.list_translations(target_lang="ja")
        assert len(result) == 1
        assert result[0].target_lang == "ja"

    def test_list_search_by_name(self):
        """Search by name keyword."""
        translation_storage.save(_make_translation("T-001", name="Meeting Notes"))
        translation_storage.save(_make_translation("T-002", name="Interview"))
        translation_storage.save(_make_translation("T-003", name="Team Meeting"))

        result, total = translation_storage.list_translations(q="meeting")
        assert len(result) == 2
        assert total == 2

    def test_list_search_case_insensitive(self):
        """Search is case insensitive."""
        translation_storage.save(_make_translation("T-001", name="IMPORTANT Meeting"))

        result, total = translation_storage.list_translations(q="important")
        assert len(result) == 1

    def test_list_combined_filters(self):
        """Multiple filters combined."""
        translation_storage.save(_make_translation("T-001", name="Meeting", status="completed", source_lang="en"))
        translation_storage.save(_make_translation("T-002", name="Meeting", status="in_progress", source_lang="en"))
        translation_storage.save(_make_translation("T-003", name="Interview", status="completed", source_lang="en"))

        result, total = translation_storage.list_translations(
            status="completed", source_lang="en", q="meeting"
        )
        assert len(result) == 1
        assert result[0].id == "T-001"

    def test_list_sorted_by_id_descending(self):
        """Results sorted by ID descending (newest first)."""
        translation_storage.save(_make_translation("T-001"))
        translation_storage.save(_make_translation("T-003"))
        translation_storage.save(_make_translation("T-002"))

        result, total = translation_storage.list_translations()
        assert [t.id for t in result] == ["T-003", "T-002", "T-001"]


class TestUpdateName:
    def test_update_name_success(self):
        """Update name returns updated translation."""
        translation_storage.save(_make_translation("T-001", name="Original"))

        result = translation_storage.update_name("T-001", "New Name")
        assert result is not None
        assert result.name == "New Name"

        # Verify persisted
        loaded = translation_storage.load("T-001")
        assert loaded.name == "New Name"

    def test_update_name_missing_returns_none(self):
        """Update non-existent returns None."""
        result = translation_storage.update_name("T-999", "Name")
        assert result is None


class TestDelete:
    def test_delete_success(self):
        """Delete removes translation file."""
        translation_storage.save(_make_translation("T-001"))
        assert translation_storage.load("T-001") is not None

        result = translation_storage.delete("T-001")
        assert result is True
        assert translation_storage.load("T-001") is None

    def test_delete_missing_returns_false(self):
        """Delete non-existent returns False."""
        result = translation_storage.delete("T-999")
        assert result is False

    def test_delete_removes_audio_file(self):
        """Delete also removes associated audio file."""
        t = _make_translation("T-001")
        t.audio_path = "audio/T-001.wav"
        translation_storage.save(t)

        # Create audio file
        audio_path = translation_storage.AUDIO_DIR / "T-001.wav"
        audio_path.parent.mkdir(exist_ok=True)
        audio_path.write_bytes(b"fake audio data")
        assert audio_path.exists()

        translation_storage.delete("T-001")
        assert not audio_path.exists()

    def test_delete_no_audio_still_succeeds(self):
        """Delete works even if no audio file exists."""
        t = _make_translation("T-001")
        t.audio_path = None
        translation_storage.save(t)

        result = translation_storage.delete("T-001")
        assert result is True


class TestAppendSentence:
    def test_append_sentence_success(self):
        """Append adds sentence to translation."""
        translation_storage.save(_make_translation("T-001"))

        new_sentence = Sentence(
            sentence_id="T-001-S003",
            sequence=3,
            offset_sec=9,
            original_text="New sentence",
            translated_text="新句子",
            confidence=0.9,
        )
        translation_storage.append_sentence("T-001", new_sentence)

        loaded = translation_storage.load("T-001")
        assert len(loaded.sentences) == 2  # Original had 1 sentence
        assert loaded.sentences[-1].sentence_id == "T-001-S003"

    def test_append_sentence_missing_translation(self):
        """Append to non-existent translation raises."""
        new_sentence = _sample_sentence(1)
        with pytest.raises(ValueError):
            translation_storage.append_sentence("T-999", new_sentence)


class TestUpdateSentenceTranslation:
    def test_update_sentence_translation_success(self):
        """Update translated text of specific sentence."""
        translation_storage.save(_make_translation("T-001"))
        loaded = translation_storage.load("T-001")
        sentence_id = loaded.sentences[0].sentence_id

        translation_storage.update_sentence_translation(
            "T-001", sentence_id, "更新的翻譯"
        )

        loaded = translation_storage.load("T-001")
        assert loaded.sentences[0].translated_text == "更新的翻譯"

    def test_update_sentence_missing_translation(self):
        """Update on non-existent translation raises."""
        with pytest.raises(ValueError):
            translation_storage.update_sentence_translation(
                "T-999", "T-999-S001", "text"
            )

    def test_update_sentence_missing_sentence(self):
        """Update non-existent sentence raises."""
        translation_storage.save(_make_translation("T-001"))

        with pytest.raises(ValueError):
            translation_storage.update_sentence_translation(
                "T-001", "T-001-S999", "text"
            )
