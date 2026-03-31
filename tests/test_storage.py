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
    assert storage.load_meeting("2099-01-01_00-00") is None


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
    assert storage.resolve_action_item("2099-01-01_00-00", "a-1") is False


def test_corrupted_file_skipped_in_list(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEETINGS_DIR", tmp_path / "meetings")
    storage.save_meeting(_sample_meeting())
    (storage.MEETINGS_DIR / "bad.json").write_text("{{not json")
    result = storage.list_meetings()
    assert len(result) == 1


def test_delete_meeting_returns_true():
    storage.save_meeting(_sample_meeting())
    assert storage.delete_meeting("2026-03-28_14-30") is True
    assert storage.load_meeting("2026-03-28_14-30") is None


def test_delete_meeting_missing_returns_false():
    assert storage.delete_meeting("2099-01-01_00-00") is False


def test_update_decision_returns_updated():
    storage.save_meeting(_sample_meeting())
    result = storage.update_decision("2026-03-28_14-30", "d-1", {"content": "新決議"})
    assert result is not None
    assert result["content"] == "新決議"
    assert result["rationale"] == "效率"  # unchanged


def test_update_decision_persists():
    storage.save_meeting(_sample_meeting())
    storage.update_decision("2026-03-28_14-30", "d-1", {"content": "新決議"})
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert loaded["decisions"][0]["content"] == "新決議"


def test_update_decision_missing_returns_none():
    storage.save_meeting(_sample_meeting())
    assert storage.update_decision("2026-03-28_14-30", "d-99", {"content": "x"}) is None


def test_update_decision_missing_meeting_returns_none():
    assert storage.update_decision("2099-01-01_00-00", "d-1", {"content": "x"}) is None


def test_update_action_item_returns_updated():
    storage.save_meeting(_sample_meeting())
    result = storage.update_action_item("2026-03-28_14-30", "a-1", {"status": "done"})
    assert result is not None
    assert result["status"] == "done"
    assert result["content"] == "更新文件"  # unchanged


def test_update_action_item_persists():
    storage.save_meeting(_sample_meeting())
    storage.update_action_item("2026-03-28_14-30", "a-1", {"assignee": "小花"})
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert loaded["action_items"][0]["assignee"] == "小花"


def test_update_action_item_missing_returns_none():
    storage.save_meeting(_sample_meeting())
    assert storage.update_action_item("2026-03-28_14-30", "a-99", {"status": "done"}) is None


def test_update_action_item_missing_meeting_returns_none():
    assert storage.update_action_item("2099-01-01_00-00", "a-1", {"status": "done"}) is None


def test_list_meetings_includes_pending_count():
    m = _sample_meeting()
    m["action_items"].append({
        "id": "a-2", "content": "審核報告", "assignee": "小花",
        "deadline": "2026-04-05", "priority": "medium", "status": "done"
    })
    storage.save_meeting(m)
    result = storage.list_meetings()
    assert result[0]["pending_action_item_count"] == 1
    assert result[0]["action_item_count"] == 2


def test_add_decision_returns_new_item():
    storage.save_meeting(_sample_meeting())
    result = storage.add_decision("2026-03-28_14-30", {
        "content": "新決議", "rationale": "效率", "related_people": ["小明"]
    })
    assert result is not None
    assert result["id"] == "d-2"  # existing d-1, next is d-2
    assert result["content"] == "新決議"
    assert result["status"] == "confirmed"


def test_add_decision_persists():
    storage.save_meeting(_sample_meeting())
    storage.add_decision("2026-03-28_14-30", {"content": "新決議", "rationale": "", "related_people": []})
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert len(loaded["decisions"]) == 2
    assert loaded["decisions"][1]["content"] == "新決議"


def test_add_decision_first_item_gets_id_d1():
    m = _sample_meeting()
    m["decisions"] = []
    storage.save_meeting(m)
    result = storage.add_decision("2026-03-28_14-30", {"content": "第一個決議", "rationale": "", "related_people": []})
    assert result["id"] == "d-1"


def test_add_decision_missing_meeting_returns_none():
    assert storage.add_decision("2099-01-01_00-00", {"content": "x", "rationale": "", "related_people": []}) is None


def test_add_action_item_returns_new_item():
    storage.save_meeting(_sample_meeting())
    result = storage.add_action_item("2026-03-28_14-30", {
        "content": "新任務", "assignee": "小花", "deadline": "2026-04-10", "priority": "high"
    })
    assert result is not None
    assert result["id"] == "a-2"  # existing a-1, next is a-2
    assert result["content"] == "新任務"
    assert result["status"] == "pending"
    assert result["priority"] == "high"


def test_add_action_item_persists():
    storage.save_meeting(_sample_meeting())
    storage.add_action_item("2026-03-28_14-30", {
        "content": "新任務", "assignee": "", "deadline": "", "priority": "medium"
    })
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert len(loaded["action_items"]) == 2
    assert loaded["action_items"][1]["content"] == "新任務"


def test_add_action_item_first_item_gets_id_a1():
    m = _sample_meeting()
    m["action_items"] = []
    storage.save_meeting(m)
    result = storage.add_action_item("2026-03-28_14-30", {
        "content": "第一個任務", "assignee": "", "deadline": "", "priority": "low"
    })
    assert result["id"] == "a-1"


def test_add_action_item_missing_meeting_returns_none():
    assert storage.add_action_item("2099-01-01_00-00", {
        "content": "x", "assignee": "", "deadline": "", "priority": "medium"
    }) is None


def test_add_decision_status_cannot_be_overridden():
    storage.save_meeting(_sample_meeting())
    result = storage.add_decision("2026-03-28_14-30", {
        "content": "決議", "rationale": "", "related_people": [], "status": "overridden"
    })
    assert result["status"] == "confirmed"


def test_add_action_item_status_cannot_be_overridden():
    storage.save_meeting(_sample_meeting())
    result = storage.add_action_item("2026-03-28_14-30", {
        "content": "任務", "assignee": "", "deadline": "", "priority": "medium", "status": "overridden"
    })
    assert result["status"] == "pending"


def test_add_decision_raises_on_missing_content():
    storage.save_meeting(_sample_meeting())
    with pytest.raises(ValueError, match="content is required"):
        storage.add_decision("2026-03-28_14-30", {"rationale": ""})


def test_add_action_item_raises_on_missing_content():
    storage.save_meeting(_sample_meeting())
    with pytest.raises(ValueError, match="content is required"):
        storage.add_action_item("2026-03-28_14-30", {"priority": "medium"})


def test_add_action_item_raises_on_missing_priority():
    storage.save_meeting(_sample_meeting())
    with pytest.raises(ValueError, match="priority is required"):
        storage.add_action_item("2026-03-28_14-30", {"content": "任務"})


def test_search_finds_in_transcript():
    m = _sample_meeting()
    storage.save_meeting(m)
    results = storage.search_meetings("新系統")
    assert len(results) == 1
    assert any(h["field"] == "transcript" for h in results[0]["hits"])


def test_search_finds_in_decisions_content():
    m = _sample_meeting()
    storage.save_meeting(m)
    results = storage.search_meetings("採用新系統")
    assert len(results) == 1
    assert any(h["field"] == "decisions" for h in results[0]["hits"])


def test_search_finds_in_decisions_rationale():
    m = _sample_meeting()
    storage.save_meeting(m)
    results = storage.search_meetings("效率")
    assert len(results) == 1
    assert any(h["field"] == "decisions" for h in results[0]["hits"])


def test_search_finds_in_action_items_content():
    m = _sample_meeting()
    storage.save_meeting(m)
    results = storage.search_meetings("更新文件")
    assert len(results) == 1
    assert any(h["field"] == "action_items" for h in results[0]["hits"])


def test_search_finds_in_action_items_assignee():
    m = _sample_meeting()
    storage.save_meeting(m)
    results = storage.search_meetings("小明")
    assert len(results) == 1
    assert any(h["field"] == "action_items" for h in results[0]["hits"])


def test_search_case_insensitive():
    m = _sample_meeting()
    m["transcript"] = "今天的Meeting討論了新系統。"
    storage.save_meeting(m)
    results = storage.search_meetings("MEETING")
    assert len(results) == 1


def test_search_no_match_returns_empty():
    storage.save_meeting(_sample_meeting())
    results = storage.search_meetings("不存在的關鍵字xyz")
    assert results == []


def test_search_empty_query_returns_empty():
    storage.save_meeting(_sample_meeting())
    results = storage.search_meetings("")
    assert results == []


def test_search_returns_summary_fields():
    storage.save_meeting(_sample_meeting())
    results = storage.search_meetings("新系統")
    r = results[0]
    assert r["id"] == "2026-03-28_14-30"
    assert "created_at" in r
    assert "decision_count" in r
    assert "action_item_count" in r
    assert "pending_action_item_count" in r
    assert "hits" in r


def test_search_snippet_contains_keyword():
    storage.save_meeting(_sample_meeting())
    results = storage.search_meetings("新系統")
    hit = next(h for h in results[0]["hits"] if h["field"] == "transcript")
    assert "新系統" in hit["snippet"]


def test_search_snippet_has_context_ellipsis():
    m = _sample_meeting()
    m["transcript"] = "A" * 50 + "新系統" + "B" * 50
    storage.save_meeting(m)
    results = storage.search_meetings("新系統")
    hit = next(h for h in results[0]["hits"] if h["field"] == "transcript")
    assert hit["snippet"].startswith("…")
    assert hit["snippet"].endswith("…")
    assert "新系統" in hit["snippet"]


def test_search_corrupted_file_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "MEETINGS_DIR", tmp_path / "meetings")
    storage.save_meeting(_sample_meeting())
    (storage.MEETINGS_DIR / "bad.json").write_text("{{not json")
    results = storage.search_meetings("新系統")
    assert len(results) == 1


def test_search_no_meetings_dir_returns_empty():
    results = storage.search_meetings("新系統")
    assert results == []


# ── Categories ─────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_categories(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "CATEGORIES_PATH", tmp_path / "categories.json")


def test_load_categories_returns_defaults(tmp_categories):
    cats = storage.load_categories()
    assert len(cats) == 4
    assert all("id" in c and "name" in c for c in cats)


def test_load_categories_returns_saved(tmp_categories):
    storage.save_categories([{"id": "cat-x", "name": "測試"}])
    cats = storage.load_categories()
    assert cats == [{"id": "cat-x", "name": "測試"}]


def test_add_category_returns_new_item(tmp_categories):
    result = storage.add_category("新分類")
    assert result["name"] == "新分類"
    assert result["id"].startswith("cat-")


def test_add_category_persists(tmp_categories):
    storage.add_category("新分類")
    cats = storage.load_categories()
    assert any(c["name"] == "新分類" for c in cats)


def test_delete_category_returns_true(tmp_categories):
    storage.save_categories([{"id": "cat-1", "name": "週會"}])
    assert storage.delete_category("cat-1") is True
    assert storage.load_categories() == []


def test_delete_category_missing_returns_false(tmp_categories):
    assert storage.delete_category("cat-999") is False


def test_update_meeting_tags_persists():
    storage.save_meeting(_sample_meeting())
    result = storage.update_meeting_tags("2026-03-28_14-30", {"category_id": "cat-2", "tags": ["Q2"]})
    assert result is not None
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert loaded["category_id"] == "cat-2"
    assert loaded["tags"] == ["Q2"]


def test_update_meeting_tags_partial_category_only():
    m = _sample_meeting()
    m["tags"] = ["existing"]
    storage.save_meeting(m)
    storage.update_meeting_tags("2026-03-28_14-30", {"category_id": "cat-3"})
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert loaded["category_id"] == "cat-3"
    assert loaded["tags"] == ["existing"]


def test_update_meeting_tags_partial_tags_only():
    m = _sample_meeting()
    m["category_id"] = "cat-1"
    storage.save_meeting(m)
    storage.update_meeting_tags("2026-03-28_14-30", {"tags": ["new"]})
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert loaded["category_id"] == "cat-1"
    assert loaded["tags"] == ["new"]


def test_update_meeting_tags_missing_meeting_returns_none():
    assert storage.update_meeting_tags("2099-01-01_00-00", {"tags": []}) is None
