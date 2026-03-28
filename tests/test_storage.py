# tests/test_storage.py
import json
import pytest
from pathlib import Path
import storage


@pytest.fixture(autouse=True)
def tmp_meetings(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEETINGS_DIR", tmp_path / "meetings")


def _sample_meeting(mid="2026-03-28_14-30"):
    return {
        "id": mid,
        "created_at": "2026-03-28T14:30:00",
        "transcript": "今天決定採用新系統。",
        "decisions": [
            {"id": "d-1", "content": "採用新系統", "rationale": "效率", "related_people": [], "status": "confirmed"}
        ],
        "action_items": [
            {"id": "a-1", "content": "更新文件", "assignee": "小明", "deadline": "2026-04-01", "priority": "high", "status": "pending"}
        ],
    }


def test_save_and_load_meeting():
    m = _sample_meeting()
    storage.save_meeting(m)
    loaded = storage.load_meeting(m["id"])
    assert loaded == m


def test_load_missing_returns_none():
    assert storage.load_meeting("nonexistent") is None


def test_list_meetings_returns_summary():
    storage.save_meeting(_sample_meeting("2026-03-28_09-00"))
    storage.save_meeting(_sample_meeting("2026-03-28_14-30"))
    result = storage.list_meetings()
    assert len(result) == 2
    assert result[0]["decision_count"] == 1
    assert result[0]["action_item_count"] == 1
    assert "transcript" not in result[0]


def test_get_pending_action_items():
    m = _sample_meeting()
    storage.save_meeting(m)
    items = storage.get_pending_action_items()
    assert len(items) == 1
    assert items[0]["id"] == "a-1"
    assert items[0]["meeting_id"] == "2026-03-28_14-30"


def test_get_pending_excludes_done():
    m = _sample_meeting()
    m["action_items"][0]["status"] = "done"
    storage.save_meeting(m)
    assert storage.get_pending_action_items() == []


def test_resolve_action_item():
    storage.save_meeting(_sample_meeting())
    ok = storage.resolve_action_item("2026-03-28_14-30", "a-1")
    assert ok is True
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert loaded["action_items"][0]["status"] == "done"


def test_resolve_missing_item_returns_false():
    storage.save_meeting(_sample_meeting())
    assert storage.resolve_action_item("2026-03-28_14-30", "a-99") is False


def test_resolve_missing_meeting_returns_false():
    assert storage.resolve_action_item("nonexistent", "a-1") is False


def test_corrupted_file_skipped_in_list(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEETINGS_DIR", tmp_path / "meetings")
    storage.save_meeting(_sample_meeting())
    (storage.MEETINGS_DIR / "bad.json").write_text("{{not json")
    result = storage.list_meetings()
    assert len(result) == 1
