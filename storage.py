# storage.py
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MEETINGS_DIR = Path(__file__).parent / "meetings"


def save_meeting(meeting: dict) -> None:
    if "id" not in meeting:
        raise ValueError("meeting must have an 'id' field")
    MEETINGS_DIR.mkdir(exist_ok=True)
    path = MEETINGS_DIR / f"{meeting['id']}.json"
    path.write_text(json.dumps(meeting, ensure_ascii=False, indent=2))


def load_meeting(meeting_id: str) -> dict | None:
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
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return False
    path.unlink()
    return True


def update_decision(meeting_id: str, decision_id: str, updates: dict) -> dict | None:
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
