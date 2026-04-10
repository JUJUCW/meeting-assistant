# analyzer.py
import json
import logging
import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:e4b"
EMPTY_RESULT: dict = {"decisions": [], "action_items": [], "resolved_action_item_ids": []}
EMPTY_PARAGRAPHS: list[list[int]] = []


def segment_paragraphs(segments: list[dict]) -> tuple[list[list[int]], bool]:
    """
    Group transcript segments into semantic paragraphs.
    Returns (paragraph_groups, ollama_available).
    Each group is a list of segment IDs that belong together.
    """
    if not segments:
        return [], True

    # Build numbered transcript for LLM
    numbered_lines = [f"[{s['id']}] {s['text']}" for s in segments]
    transcript_text = "\n".join(numbered_lines)

    prompt = (
        "你是一位文字編輯。以下是逐字稿，每行前面有編號 [N]。\n"
        "請根據語義將這些句子分組成段落，輸出格式為 JSON 陣列的陣列。\n"
        "例如：[[0,1,2],[3,4,5],[6,7]] 表示三個段落。\n"
        "規則：\n"
        "- 同一主題或連續論述的句子放在同一段落\n"
        "- 主題轉換時開始新段落\n"
        "- 每段落建議 3-8 句，但可依內容調整\n"
        "- 只輸出 JSON，不要其他文字\n\n"
        f"逐字稿：\n{transcript_text}"
    )

    for attempt in range(3):
        try:
            raw = _call_ollama(prompt)
            groups = _parse_paragraph_groups(raw, len(segments))
            return groups, True
        except Exception as e:
            logger.warning("Ollama paragraph segmentation attempt %d failed: %s", attempt + 1, e)

    # Fallback: group every 5 segments
    fallback = [
        list(range(i, min(i + 5, len(segments))))
        for i in range(0, len(segments), 5)
    ]
    return fallback, False


def _parse_paragraph_groups(raw: str, total_segments: int) -> list[list[int]]:
    """Parse LLM response into paragraph groups."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])

    groups = json.loads(text)

    # Validate: must be list of lists of ints
    if not isinstance(groups, list):
        raise ValueError("Expected list of lists")

    validated = []
    seen = set()
    for group in groups:
        if not isinstance(group, list):
            raise ValueError("Each group must be a list")
        valid_ids = [int(x) for x in group if 0 <= int(x) < total_segments]
        # Remove duplicates while preserving order
        unique_ids = [x for x in valid_ids if x not in seen]
        seen.update(unique_ids)
        if unique_ids:
            validated.append(unique_ids)

    # Add any missing segment IDs at the end
    missing = [i for i in range(total_segments) if i not in seen]
    if missing:
        validated.append(missing)

    return validated


def generate_summary(transcript: str) -> tuple[str, bool]:
    """Returns (summary_text, ollama_available). Never raises."""
    prompt = (
        "你是一位會議記錄員。請根據以下會議逐字稿，用繁體中文撰寫一份簡潔的會議摘要（3至5句話）。"
        "只輸出摘要文字，不要加任何前言或標題。\n\n"
        f"逐字稿：\n{transcript}"
    )
    for attempt in range(3):
        try:
            raw = _call_ollama(prompt)
            return raw.strip(), True
        except Exception as e:
            logger.warning("Ollama summary attempt %d failed: %s", attempt + 1, e)
    return "", False


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
