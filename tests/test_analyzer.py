# tests/test_analyzer.py
import json
import pytest
from unittest.mock import patch, MagicMock
import analyzer


VALID_RESPONSE = json.dumps({
    "decisions": [{"content": "採用新系統", "rationale": "效率", "related_people": ["小明"]}],
    "action_items": [{"content": "更新文件", "assignee": "小明", "deadline": "2026-04-01", "priority": "high"}],
    "resolved_action_item_ids": ["a-1"],
})

FENCED_RESPONSE = f"```json\n{VALID_RESPONSE}\n```"


def _mock_client(response_text):
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.post.return_value.raise_for_status = MagicMock()
    mock.post.return_value.json.return_value = {"response": response_text}
    return mock


def test_build_prompt_contains_transcript():
    prompt = analyzer._build_prompt("今天討論了A和B", [])
    assert "今天討論了A和B" in prompt


def test_build_prompt_contains_pending_items():
    items = [{"id": "a-1", "content": "更新文件", "assignee": "小明", "meeting_date": "2026-03-01"}]
    prompt = analyzer._build_prompt("逐字稿", items)
    assert "a-1" in prompt
    assert "更新文件" in prompt


def test_parse_response_valid_json():
    result = analyzer._parse_response(VALID_RESPONSE)
    assert len(result["decisions"]) == 1
    assert result["decisions"][0]["content"] == "採用新系統"
    assert result["resolved_action_item_ids"] == ["a-1"]


def test_parse_response_strips_code_fences():
    result = analyzer._parse_response(FENCED_RESPONSE)
    assert len(result["action_items"]) == 1


def test_parse_response_invalid_json_raises():
    with pytest.raises(Exception):
        analyzer._parse_response("not json at all")


def test_analyze_success():
    with patch("analyzer.httpx.Client", return_value=_mock_client(VALID_RESPONSE)):
        result, available = analyzer.analyze("逐字稿", [])
    assert available is True
    assert len(result["decisions"]) == 1


def test_analyze_retries_on_failure():
    bad_mock = MagicMock()
    bad_mock.__enter__ = lambda s: s
    bad_mock.__exit__ = MagicMock(return_value=False)
    bad_mock.post.side_effect = Exception("connection refused")

    with patch("analyzer.httpx.Client", return_value=bad_mock):
        result, available = analyzer.analyze("逐字稿", [])

    assert available is False
    assert result["decisions"] == []
    assert result["action_items"] == []
    assert result["resolved_action_item_ids"] == []
    assert bad_mock.post.call_count == 3


def test_analyze_returns_empty_on_persistent_invalid_json():
    bad_response_mock = MagicMock()
    bad_response_mock.__enter__ = lambda s: s
    bad_response_mock.__exit__ = MagicMock(return_value=False)
    bad_response_mock.post.return_value.raise_for_status = MagicMock()
    bad_response_mock.post.return_value.json.return_value = {"response": "{{broken"}

    with patch("analyzer.httpx.Client", return_value=bad_response_mock):
        result, available = analyzer.analyze("逐字稿", [])

    assert available is False
    assert result == {"decisions": [], "action_items": [], "resolved_action_item_ids": []}
