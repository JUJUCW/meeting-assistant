# tests/test_translation_integration.py
"""Integration tests for full translation workflow (Task 8.2)."""

import pytest
from httpx import AsyncClient, ASGITransport
from starlette.testclient import TestClient

import translation_storage
from translation_storage import Sentence, Translation


@pytest.fixture(autouse=True)
def tmp_dirs(tmp_path, monkeypatch):
    """Set up temporary directories for translations and audio."""
    monkeypatch.setattr(translation_storage, "TRANSLATIONS_DIR", tmp_path / "translations")
    monkeypatch.setattr(translation_storage, "AUDIO_DIR", tmp_path / "audio")


class TestFullTranslationWorkflow:
    """Integration tests for complete translation workflow."""

    @pytest.mark.anyio
    async def test_complete_workflow_start_to_query(self):
        """Test full workflow: start → query → delete."""
        import server

        async with AsyncClient(
            transport=ASGITransport(app=server.app), base_url="http://test"
        ) as client:
            # Step 1: Start a new translation session
            start_response = await client.post("/api/translations/start")
            assert start_response.status_code == 200
            session_id = start_response.json()["id"]

            # Step 2: Verify session appears in list
            list_response = await client.get("/api/translations")
            assert list_response.status_code == 200
            data = list_response.json()
            assert data["total"] >= 1
            session_ids = [t["id"] for t in data["translations"]]
            assert session_id in session_ids

            # Step 3: Get session details
            detail_response = await client.get(f"/api/translations/{session_id}")
            assert detail_response.status_code == 200
            detail = detail_response.json()
            assert detail["id"] == session_id
            assert detail["status"] == "in_progress"

            # Step 4: Update session name
            patch_response = await client.patch(
                f"/api/translations/{session_id}",
                json={"name": "Integration Test Session"}
            )
            assert patch_response.status_code == 200
            assert patch_response.json()["name"] == "Integration Test Session"

            # Step 5: Delete session
            delete_response = await client.delete(f"/api/translations/{session_id}")
            assert delete_response.status_code == 200

            # Step 6: Verify session is gone
            verify_response = await client.get(f"/api/translations/{session_id}")
            assert verify_response.status_code == 404

    @pytest.mark.anyio
    async def test_pagination_workflow(self):
        """Test list pagination with multiple sessions."""
        import server

        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = Translation(
                id=f"T-{i+1:03d}",
                name=f"Test Session {i+1}",
                started_at="2026-04-14T10:00:00",
                ended_at="2026-04-14T10:30:00",
                duration_sec=1800,
                source_lang="en",
                target_lang="zh-TW",
                status="completed",
                audio_path=None,
                audio_size_bytes=None,
                sentences=[],
            )
            translation_storage.save(session)
            sessions.append(session)

        async with AsyncClient(
            transport=ASGITransport(app=server.app), base_url="http://test"
        ) as client:
            # Get first page with limit 2
            response = await client.get("/api/translations?page=1&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 5
            assert len(data["translations"]) == 2
            assert data["page"] == 1
            assert data["limit"] == 2

            # Get second page
            response = await client.get("/api/translations?page=2&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data["translations"]) == 2
            assert data["page"] == 2

            # Get third page (should have 1 item)
            response = await client.get("/api/translations?page=3&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data["translations"]) == 1

    @pytest.mark.anyio
    async def test_filter_by_status(self):
        """Test filtering sessions by status."""
        import server

        # Create sessions with different statuses
        for i, status in enumerate(["in_progress", "completed", "completed", "interrupted"]):
            session = Translation(
                id=f"T-{i+1:03d}",
                name=f"Test Session {i+1}",
                started_at="2026-04-14T10:00:00",
                ended_at="2026-04-14T10:30:00" if status != "in_progress" else None,
                duration_sec=1800 if status != "in_progress" else 0,
                source_lang="en",
                target_lang="zh-TW",
                status=status,
                audio_path=None,
                audio_size_bytes=None,
                sentences=[],
            )
            translation_storage.save(session)

        async with AsyncClient(
            transport=ASGITransport(app=server.app), base_url="http://test"
        ) as client:
            # Filter by completed
            response = await client.get("/api/translations?status=completed")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            for t in data["translations"]:
                assert t["status"] == "completed"

            # Filter by in_progress
            response = await client.get("/api/translations?status=in_progress")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["translations"][0]["status"] == "in_progress"


class TestWebSocketIntegration:
    """Integration tests for WebSocket streaming."""

    def test_websocket_connection_and_stop(self):
        """Test WebSocket connection lifecycle."""
        import server

        # Create an in_progress session
        session = Translation(
            id="T-001",
            name="WebSocket Test",
            started_at="2026-04-14T10:00:00",
            ended_at=None,
            duration_sec=0,
            source_lang="",
            target_lang="zh-TW",
            status="in_progress",
            audio_path=None,
            audio_size_bytes=None,
            sentences=[],
        )
        translation_storage.save(session)

        with TestClient(server.app) as client:
            # Connect to WebSocket
            with client.websocket_connect("/api/translations/T-001/stream") as ws:
                # Send stop command
                ws.send_json({"type": "stop"})

                # Should receive status completed
                response = ws.receive_json()
                assert response["type"] == "status"
                assert response["status"] == "completed"

        # Verify session was marked as completed
        loaded = translation_storage.load("T-001")
        assert loaded is not None
        assert loaded.status == "completed"

    def test_websocket_reject_completed_session(self):
        """Test that WebSocket rejects completed sessions."""
        import server

        # Create a completed session
        session = Translation(
            id="T-002",
            name="Completed Session",
            started_at="2026-04-14T10:00:00",
            ended_at="2026-04-14T10:30:00",
            duration_sec=1800,
            source_lang="en",
            target_lang="zh-TW",
            status="completed",
            audio_path=None,
            audio_size_bytes=None,
            sentences=[],
        )
        translation_storage.save(session)

        with TestClient(server.app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/api/translations/T-002/stream"):
                    pass


class TestExportIntegration:
    """Integration tests for export functionality."""

    @pytest.mark.anyio
    async def test_docx_export_contains_all_sentences(self):
        """Test DOCX export includes all sentence data."""
        import io
        from docx import Document
        import server

        # Create session with multiple sentences
        sentences = [
            Sentence(
                sentence_id=f"T-001-S{i:03d}",
                sequence=i,
                offset_sec=i * 5,
                original_text=f"Original text {i}",
                translated_text=f"譯文 {i}",
                confidence=0.8 + (i * 0.02),
            )
            for i in range(1, 6)
        ]
        session = Translation(
            id="T-001",
            name="Export Test",
            started_at="2026-04-14T10:00:00",
            ended_at="2026-04-14T10:30:00",
            duration_sec=1800,
            source_lang="en",
            target_lang="zh-TW",
            status="completed",
            audio_path=None,
            audio_size_bytes=None,
            sentences=sentences,
        )
        translation_storage.save(session)

        async with AsyncClient(
            transport=ASGITransport(app=server.app), base_url="http://test"
        ) as client:
            response = await client.get("/api/translations/T-001/export/docx")

        assert response.status_code == 200
        assert "application/vnd.openxmlformats" in response.headers["content-type"]

        # Parse DOCX and verify content
        doc = Document(io.BytesIO(response.content))
        full_text = "\n".join(p.text for p in doc.paragraphs)

        # All sentences should be present
        for i in range(1, 6):
            assert f"Original text {i}" in full_text
