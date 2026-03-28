# analyzer.py
import json
import logging
import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
EMPTY_RESULT: dict = {"decisions": [], "action_items": [], "resolved_action_item_ids": []}


def analyze(transcript: str, pending_items: list[dict]) -> tuple[dict, bool]:
    """Returns (result_dict, ollama_available). Never raises."""
    prompt = _build_prompt(transcript, pending_items)
    for attempt in range(3):
        try:
            raw = _call_ollama(prompt)
            result = _parse_response(raw)
            return result, True
        except Exception as e:
            logger.warning("Ollama attempt %d failed: %s", attempt + 1, e)
    return dict(EMPTY_RESULT), False


def _build_prompt(transcript: str, pending_items: list[dict]) -> str:
    pending_section = ""
    if pending_items:
        lines = [
            f"- [{item['id']}] {item['content']}"
            f" (負責人: {item.get('assignee') or '未指定'},"
            f" 來自會議: {item.get('meeting_date', '未知')})"
            for item in pending_items
        ]
        pending_section = (
            "\n\n歷史待辦事項（請判斷哪些已在本次會議中完成，輸出其 ID 於 resolved_action_item_ids）：\n"
            + "\n".join(lines)
        )

    return (
        "你是一位會議分析師。請從以下會議逐字稿中提取決議事項和待辦事項，"
        "以嚴格的 JSON 格式輸出，不得輸出任何其他文字。使用繁體中文。\n\n"
        "輸出格式：\n"
        '{"decisions": [{"content": "string", "rationale": "string", "related_people": ["string"]}],'
        ' "action_items": [{"content": "string", "assignee": "string or null",'
        ' "deadline": "YYYY-MM-DD or null", "priority": "high|medium|low"}],'
        ' "resolved_action_item_ids": ["id1"]}\n\n'
        f"會議逐字稿：\n{transcript}"
        f"{pending_section}"
    )


def _call_ollama(prompt: str) -> str:
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        return response.json()["response"]


def _parse_response(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])
    data = json.loads(text)
    return {
        "decisions": data.get("decisions", []),
        "action_items": data.get("action_items", []),
        "resolved_action_item_ids": data.get("resolved_action_item_ids", []),
    }
