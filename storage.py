# storage.py
import json
import logging
import re
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

MEETINGS_DIR = Path(__file__).parent / "meetings"
CATEGORIES_PATH = Path(__file__).parent / "categories.json"
_MEETING_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$")

_DEFAULT_CATEGORIES = [
    {"id": "cat-1", "name": "週會"},
    {"id": "cat-2", "name": "產品"},
    {"id": "cat-3", "name": "一對一"},
    {"id": "cat-4", "name": "全員會議"},
]


def _validate_meeting_id(meeting_id: str) -> None:
    if not _MEETING_ID_RE.match(meeting_id):
        raise ValueError(f"Invalid meeting_id format: {meeting_id!r}")


def save_meeting(meeting: dict) -> None:
    if "id" not in meeting:
        raise ValueError("meeting must have an 'id' field")
    _validate_meeting_id(meeting["id"])
    MEETINGS_DIR.mkdir(exist_ok=True)
    path = MEETINGS_DIR / f"{meeting['id']}.json"
    path.write_text(json.dumps(meeting, ensure_ascii=False, indent=2))


def load_meeting(meeting_id: str) -> dict | None:
    _validate_meeting_id(meeting_id)
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def list_meetings() -> list[dict]:
    if not MEETINGS_DIR.exists():
        return []
    meetings = []
    for path in sorted(MEETINGS_DIR.glob("*.json"), reverse=True):
        try:
            m = json.loads(path.read_text())
            meetings.append({
                "id": m["id"],
                "created_at": m["created_at"],
                "decision_count": len(m.get("decisions", [])),
                "action_item_count": len(m.get("action_items", [])),
                "pending_action_item_count": sum(
                    1 for a in m.get("action_items", []) if a.get("status") == "pending"
                ),
            })
        except Exception as e:
            logger.warning("Skipping corrupted meeting file %s: %s", path, e)
            continue
    return meetings


def search_meetings(query: str) -> list[dict]:
    if not query:
        return []
    q = query.lower()
    if not MEETINGS_DIR.exists():
        return []
    results = []
    for path in sorted(MEETINGS_DIR.glob("*.json"), reverse=True):
        try:
            m = json.loads(path.read_text())
        except Exception as e:
            logger.warning("Skipping corrupted meeting file %s: %s", path, e)
            continue

        hits = []

        # 1. transcript
        transcript = m.get("transcript", "") or ""
        idx = transcript.lower().find(q)
        if idx >= 0:
            start = max(0, idx - 30)
            end = min(len(transcript), idx + len(query) + 30)
            snippet = transcript[start:end]
            if start > 0:
                snippet = "…" + snippet
            if end < len(transcript):
                snippet = snippet + "…"
            hits.append({"field": "transcript", "snippet": snippet})

        # 2. decisions（content 或 rationale，取第一筆命中）
        for d in m.get("decisions", []):
            matched = False
            for val in [d.get("content", "") or "", d.get("rationale", "") or ""]:
                idx = val.lower().find(q)
                if idx >= 0:
                    start = max(0, idx - 30)
                    end = min(len(val), idx + len(query) + 30)
                    snippet = val[start:end]
                    if start > 0:
                        snippet = "…" + snippet
                    if end < len(val):
                        snippet = snippet + "…"
                    hits.append({"field": "decisions", "snippet": snippet})
                    matched = True
                    break
            if matched:
                break

        # 3. action_items（content 或 assignee，取第一筆命中）
        for a in m.get("action_items", []):
            matched = False
            for val in [a.get("content", "") or "", a.get("assignee", "") or ""]:
                idx = val.lower().find(q)
                if idx >= 0:
                    start = max(0, idx - 30)
                    end = min(len(val), idx + len(query) + 30)
                    snippet = val[start:end]
                    if start > 0:
                        snippet = "…" + snippet
                    if end < len(val):
                        snippet = snippet + "…"
                    hits.append({"field": "action_items", "snippet": snippet})
                    matched = True
                    break
            if matched:
                break

        if hits:
            results.append({
                "id": m["id"],
                "created_at": m["created_at"],
                "decision_count": len(m.get("decisions", [])),
                "action_item_count": len(m.get("action_items", [])),
                "pending_action_item_count": sum(
                    1 for a in m.get("action_items", []) if a.get("status") == "pending"
                ),
                "hits": hits,
            })

    return results


def get_pending_action_items() -> list[dict]:
    if not MEETINGS_DIR.exists():
        return []
    items = []
    for path in sorted(MEETINGS_DIR.glob("*.json")):
        try:
            m = json.loads(path.read_text())
            for item in m.get("action_items", []):
                if item.get("status") == "pending":
                    items.append({
                        **item,
                        "meeting_id": m["id"],
                        "meeting_date": m["created_at"][:10],
                    })
        except Exception as e:
            logger.warning("Skipping corrupted meeting file %s: %s", path, e)
            continue
    return items


def resolve_action_item(meeting_id: str, item_id: str) -> bool:
    _validate_meeting_id(meeting_id)
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return False
    try:
        m = json.loads(path.read_text())
        for item in m.get("action_items", []):
            if item["id"] == item_id:
                item["status"] = "done"
                path.write_text(json.dumps(m, ensure_ascii=False, indent=2))
                return True
        return False
    except Exception as e:
        logger.warning("Error resolving action item %s in %s: %s", item_id, meeting_id, e)
        return False


def delete_meeting(meeting_id: str) -> bool:
    _validate_meeting_id(meeting_id)
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return False
    path.unlink()
    return True


def load_categories() -> list[dict]:
    if not CATEGORIES_PATH.exists():
        save_categories(_DEFAULT_CATEGORIES)
        return list(_DEFAULT_CATEGORIES)
    try:
        return json.loads(CATEGORIES_PATH.read_text())
    except Exception:
        return list(_DEFAULT_CATEGORIES)


def save_categories(categories: list[dict]) -> None:
    CATEGORIES_PATH.write_text(json.dumps(categories, ensure_ascii=False, indent=2))


def add_category(name: str) -> dict:
    cats = load_categories()
    new_cat = {"id": f"cat-{uuid.uuid4().hex[:8]}", "name": name}
    cats.append(new_cat)
    save_categories(cats)
    return new_cat


def delete_category(cat_id: str) -> bool:
    cats = load_categories()
    new_cats = [c for c in cats if c["id"] != cat_id]
    if len(new_cats) == len(cats):
        return False
    save_categories(new_cats)
    return True


_MEETING_TAGS_UPDATABLE = {"category_id", "tags"}


def update_meeting_tags(meeting_id: str, updates: dict) -> dict | None:
    _validate_meeting_id(meeting_id)
    updates = {k: v for k, v in updates.items() if k in _MEETING_TAGS_UPDATABLE}
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
    try:
        m = json.loads(path.read_text())
        for k, v in updates.items():
            m[k] = v
        path.write_text(json.dumps(m, ensure_ascii=False, indent=2))
        return m
    except Exception as e:
        logger.warning("Error updating tags for %s: %s", meeting_id, e)
        return None


_DECISION_UPDATABLE = {"content", "rationale", "related_people", "status"}
_ACTION_ITEM_UPDATABLE = {"content", "assignee", "deadline", "priority", "status"}


def update_decision(meeting_id: str, decision_id: str, updates: dict) -> dict | None:
    _validate_meeting_id(meeting_id)
    updates = {k: v for k, v in updates.items() if k in _DECISION_UPDATABLE}
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
    try:
        m = json.loads(path.read_text())
        for decision in m.get("decisions", []):
            if decision["id"] == decision_id:
                for k, v in updates.items():
                    decision[k] = v
                path.write_text(json.dumps(m, ensure_ascii=False, indent=2))
                return decision
        return None
    except Exception as e:
        logger.warning("Error updating decision %s in %s: %s", decision_id, meeting_id, e)
        return None


def update_action_item(meeting_id: str, item_id: str, updates: dict) -> dict | None:
    _validate_meeting_id(meeting_id)
    updates = {k: v for k, v in updates.items() if k in _ACTION_ITEM_UPDATABLE}
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
    try:
        m = json.loads(path.read_text())
        for item in m.get("action_items", []):
            if item["id"] == item_id:
                for k, v in updates.items():
                    item[k] = v
                path.write_text(json.dumps(m, ensure_ascii=False, indent=2))
                return item
        return None
    except Exception as e:
        logger.warning("Error updating action item %s in %s: %s", item_id, meeting_id, e)
        return None


def add_decision(meeting_id: str, data: dict) -> dict | None:
    _validate_meeting_id(meeting_id)
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
    if "content" not in data:
        raise ValueError("content is required")
    try:
        m = json.loads(path.read_text())
        decisions = m.get("decisions", [])
        nums = [int(d["id"].split("-")[1]) for d in decisions if d.get("id", "").startswith("d-")]
        next_num = max(nums) + 1 if nums else 1
        new_decision = {
            "id": f"d-{next_num}",
            "status": "confirmed",
            "content": data["content"],
            "rationale": data.get("rationale", ""),
            "related_people": data.get("related_people", []),
        }
        decisions.append(new_decision)
        m["decisions"] = decisions
        path.write_text(json.dumps(m, ensure_ascii=False, indent=2))
        return new_decision
    except Exception as e:
        logger.warning("Error adding decision to %s: %s", meeting_id, e)
        return None


def add_action_item(meeting_id: str, data: dict) -> dict | None:
    _validate_meeting_id(meeting_id)
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
    if "content" not in data:
        raise ValueError("content is required")
    if "priority" not in data:
        raise ValueError("priority is required")
    try:
        m = json.loads(path.read_text())
        items = m.get("action_items", [])
        nums = [int(a["id"].split("-")[1]) for a in items if a.get("id", "").startswith("a-")]
        next_num = max(nums) + 1 if nums else 1
        new_item = {
            "id": f"a-{next_num}",
            "status": "pending",
            "content": data["content"],
            "assignee": data.get("assignee", ""),
            "deadline": data.get("deadline", ""),
            "priority": data["priority"],
        }
        items.append(new_item)
        m["action_items"] = items
        path.write_text(json.dumps(m, ensure_ascii=False, indent=2))
        return new_item
    except Exception as e:
        logger.warning("Error adding action item to %s: %s", meeting_id, e)
        return None
