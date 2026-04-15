# tests/test_translation_api.py
"""Tests for translation REST API endpoints (tasks 2.1, 2.2, 2.3)."""
import pytest
from httpx import AsyncClient, ASGITransport
from dataclasses import asdict

import translation_storage
from translation_storage import Sentence, Translation


@pytest.fixture(autouse=True)
def tmp_dirs(tmp_path, monkeypatch):
    """Set up temporary directories for translations and audio."""
    monkeypatch.setattr(translation_storage, "TRANSLATIONS_DIR", tmp_path / "translations")
    monkeypatch.setattr(translation_storage, "AUDIO_DIR", tmp_path / "audio")


def _sample_sentence(seq: int = 1, tid: str = "T-001") -> Sentence:
    return Sentence(
        sentence_id=f"{tid}-S{seq:03d}",
        sequence=seq,
        offset_sec=seq * 3,
        original_text=f"Test sentence {seq}",
        translated_text=f"測試句子 {seq}",
        confidence=0.85,
    )


def _sample_translation(
    tid: str = "T-001",
    name: str = "Test Translation",
    status: str = "completed",
    source_lang: str = "en",
    target_lang: str = "zh-TW",
) -> Translation:
    return Translation(
        id=tid,
        name=name,
        started_at="2026-04-13T14:00:00",
        ended_at="2026-04-13T14:30:00" if status == "completed" else None,
        duration_sec=1800 if status == "completed" else 0,
        source_lang=source_lang,
        target_lang=target_lang,
        status=status,
        audio_path=f"audio/{tid}.wav" if status == "completed" else None,
        audio_size_bytes=3600000 if status == "completed" else None,
        sentences=[_sample_sentence(1, tid), _sample_sentence(2, tid)],
    )


# =====================================================
# Task 2.1: POST /api/translations/start
# =====================================================

class TestStartTranslation:
    """Tests for POST /api/translations/start endpoint."""

    @pytest.mark.anyio
    async def test_start_creates_new_session(self):
        """Start should create a new in_progress session and return ID."""
        from server import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/translations/start")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"].startswith("T-")

        # Verify session was created with in_progress status
        loaded = translation_storage.load(data["id"])
        assert loaded is not None
        assert loaded.status == "in_progress"

    @pytest.mark.anyio
    async def test_start_returns_409_if_in_progress_exists(self):
        """Start should return 409 if another in_progress session exists."""
        from server import app

        # Create existing in_progress session
        existing = _sample_translation("T-001", status="in_progress")
        translation_storage.save(existing)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/translations/start")

        assert response.status_code == 409
        data = response.json()
        assert "existing_id" in data
        assert data["existing_id"] == "T-001"

    @pytest.mark.anyio
    async def test_start_allowed_if_only_completed_exists(self):
        """Start should succeed if only completed sessions exist."""
        from server import app

        # Create completed session
        completed = _sample_translation("T-001", status="completed")
        translation_storage.save(completed)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/translations/start")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "T-002"

    @pytest.mark.anyio
    async def test_start_sets_correct_initial_values(self):
        """New session should have correct initial values."""
        from server import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/translations/start")

        assert response.status_code == 200
        tid = response.json()["id"]

        loaded = translation_storage.load(tid)
        assert loaded.status == "in_progress"
        assert loaded.ended_at is None
        assert loaded.duration_sec == 0
        assert loaded.sentences == []
        assert loaded.audio_path is None


# =====================================================
# Task 2.2: GET /api/translations, GET/PATCH /api/translations/{id}
# =====================================================

class TestListTranslations:
    """Tests for GET /api/translations endpoint."""

    @pytest.mark.anyio
    async def test_list_returns_empty_when_no_data(self):
        """List should return empty array when no translations exist."""
        from server import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations")

        assert response.status_code == 200
        data = response.json()
        assert data["translations"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 8

    @pytest.mark.anyio
    async def test_list_returns_translations(self):
        """List should return all translations."""
        from server import app

        translation_storage.save(_sample_translation("T-001"))
        translation_storage.save(_sample_translation("T-002"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations")

        assert response.status_code == 200
        data = response.json()
        assert len(data["translations"]) == 2
        assert data["total"] == 2

    @pytest.mark.anyio
    async def test_list_pagination(self):
        """List should support pagination."""
        from server import app

        for i in range(1, 11):
            translation_storage.save(_sample_translation(f"T-{i:03d}"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations?page=2&limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data["translations"]) == 3
        assert data["total"] == 10
        assert data["page"] == 2
        assert data["limit"] == 3

    @pytest.mark.anyio
    async def test_list_filter_by_status(self):
        """List should filter by status."""
        from server import app

        translation_storage.save(_sample_translation("T-001", status="completed"))
        translation_storage.save(_sample_translation("T-002", status="in_progress"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations?status=completed")

        assert response.status_code == 200
        data = response.json()
        assert len(data["translations"]) == 1
        assert data["translations"][0]["status"] == "completed"

    @pytest.mark.anyio
    async def test_list_filter_by_language(self):
        """List should filter by source and target language."""
        from server import app

        translation_storage.save(_sample_translation("T-001", source_lang="en", target_lang="zh-TW"))
        translation_storage.save(_sample_translation("T-002", source_lang="ja", target_lang="zh-TW"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations?source_lang=en")

        assert response.status_code == 200
        data = response.json()
        assert len(data["translations"]) == 1
        assert data["translations"][0]["source_lang"] == "en"

    @pytest.mark.anyio
    async def test_list_search_by_keyword(self):
        """List should search by name keyword."""
        from server import app

        translation_storage.save(_sample_translation("T-001", name="Meeting Notes"))
        translation_storage.save(_sample_translation("T-002", name="Interview"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations?q=meeting")

        assert response.status_code == 200
        data = response.json()
        assert len(data["translations"]) == 1
        assert "Meeting" in data["translations"][0]["name"]

    @pytest.mark.anyio
    async def test_list_returns_sentence_count(self):
        """List items should include sentence_count."""
        from server import app

        translation_storage.save(_sample_translation("T-001"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations")

        assert response.status_code == 200
        data = response.json()
        assert data["translations"][0]["sentence_count"] == 2


class TestGetTranslation:
    """Tests for GET /api/translations/{id} endpoint."""

    @pytest.mark.anyio
    async def test_get_returns_translation_detail(self):
        """Get should return full translation with sentences."""
        from server import app

        translation_storage.save(_sample_translation("T-001"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations/T-001")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "T-001"
        assert data["name"] == "Test Translation"
        assert "sentences" in data
        assert len(data["sentences"]) == 2

    @pytest.mark.anyio
    async def test_get_not_found(self):
        """Get should return 404 for non-existent translation."""
        from server import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations/T-999")

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_get_invalid_id_format(self):
        """Get should return 400 for invalid ID format."""
        from server import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/translations/invalid-id")

        assert response.status_code == 400


class TestUpdateTranslation:
    """Tests for PATCH /api/translations/{id} endpoint."""

    @pytest.mark.anyio
    async def test_patch_updates_name(self):
        """Patch should update translation name."""
        from server import app

        translation_storage.save(_sample_translation("T-001", name="Original Name"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                "/api/translations/T-001",
                json={"name": "New Name"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

        # Verify persisted
        loaded = translation_storage.load("T-001")
        assert loaded.name == "New Name"

    @pytest.mark.anyio
    async def test_patch_not_found(self):
        """Patch should return 404 for non-existent translation."""
        from server import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                "/api/translations/T-999",
                json={"name": "New Name"}
            )

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_patch_invalid_body(self):
        """Patch should return 422 for invalid body."""
        from server import app

        translation_storage.save(_sample_translation("T-001"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                "/api/translations/T-001",
                json={}  # Missing name
            )

        assert response.status_code == 422


# =====================================================
# Task 2.3: DELETE /api/translations/{id}
# =====================================================

class TestDeleteTranslation:
    """Tests for DELETE /api/translations/{id} endpoint."""

    @pytest.mark.anyio
    async def test_delete_removes_translation(self):
        """Delete should remove translation and return success."""
        from server import app

        translation_storage.save(_sample_translation("T-001"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/translations/T-001")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify deleted
        assert translation_storage.load("T-001") is None

    @pytest.mark.anyio
    async def test_delete_removes_audio_file(self):
        """Delete should also remove associated audio file."""
        from server import app

        t = _sample_translation("T-001", status="completed")
        translation_storage.save(t)

        # Create audio file
        audio_path = translation_storage.AUDIO_DIR / "T-001.wav"
        audio_path.parent.mkdir(exist_ok=True)
        audio_path.write_bytes(b"fake audio data")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/translations/T-001")

        assert response.status_code == 200
        assert not audio_path.exists()

    @pytest.mark.anyio
    async def test_delete_not_found(self):
        """Delete should return 404 for non-existent translation."""
        from server import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/translations/T-999")

        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_delete_invalid_id_format(self):
        """Delete should return 400 for invalid ID format."""
        from server import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/translations/invalid-id")

        assert response.status_code == 400
