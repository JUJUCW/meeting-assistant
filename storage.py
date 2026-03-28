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
