# AI Decision & Action Item Analysis — Design Spec
**Date:** 2026-03-28

## Overview

Enhance the meeting assistant with AI-powered analysis using Llama 3.1 8B (via Ollama, local). After Whisper transcription completes, Llama automatically extracts structured decisions and action items from the transcript, cross-references historical pending action items, and auto-resolves completed ones. All data is persisted locally across meetings.

## Architecture

Three new components added to the existing project:

| File | Responsibility |
|---|---|
| `analyzer.py` | Calls Ollama (Llama 3.1 8B), builds prompt, parses JSON response, retries on failure |
| `storage.py` | Reads/writes meeting JSON files in `meetings/` directory |
| `meetings/` | Directory of per-meeting JSON files (`YYYY-MM-DD_HH-MM.json`) |

**Updated flow:**
1. Whisper transcription completes (existing)
2. `server.py` calls `analyzer.py` with transcript + pending historical action items
3. Llama returns structured JSON
4. `storage.py` saves the meeting record
5. Historical resolved items are updated in their source files
6. Frontend polls and receives full analysis result

Ollama runs separately (`ollama serve`) at `http://localhost:11434`. `server.py` communicates with it via HTTP.

## Data Structures

### Meeting file: `meetings/YYYY-MM-DD_HH-MM.json`

```json
{
  "id": "2026-03-28_14-30",
  "created_at": "2026-03-28T14:30:00",
  "transcript": "...",
  "decisions": [
    {
      "id": "d-1",
      "content": "採用新的報價系統",
      "rationale": "舊系統維護成本過高",
      "related_people": ["小明", "小華"],
      "status": "confirmed"
    }
  ],
  "action_items": [
    {
      "id": "a-1",
      "content": "更新合約範本",
      "assignee": "小明",
      "deadline": "2026-04-05",
      "priority": "high",
      "status": "pending"
    }
  ]
}
```

**Priority values:** `"high"` | `"medium"` | `"low"`
**Action item status:** `"pending"` | `"done"`
**Decision status:** `"confirmed"`

### Llama response schema

```json
{
  "decisions": [
    {
      "content": "string",
      "rationale": "string",
      "related_people": ["string"]
    }
  ],
  "action_items": [
    {
      "content": "string",
      "assignee": "string or null",
      "deadline": "YYYY-MM-DD or null",
      "priority": "high|medium|low"
    }
  ],
  "resolved_action_item_ids": ["a-1", "a-3"]
}
```

## Llama Prompt Design

The prompt sent to Llama contains three parts:

1. **System instruction:** Role as meeting analyst, output strict JSON only (no prose), respond in Traditional Chinese
2. **Transcript:** Full text of the current meeting
3. **Pending action items:** List of unresolved items from previous meetings (with IDs), asking Llama to identify which were completed in this meeting

On receiving the response:
- Parse JSON; if invalid, retry up to 2 times with the same prompt
- If still invalid after 2 retries, return empty structure (graceful degradation)
- `resolved_action_item_ids` triggers `storage.py` to update those items' `status` to `"done"` in their source files

## New API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /meetings` | GET | List all meetings (id, created_at, decision count, action item count) |
| `GET /meetings/{id}` | GET | Full meeting detail including decisions and action items |
| `GET /action-items/pending` | GET | All unresolved action items across all meetings |

The existing `/result/{job_id}` endpoint is extended to include `decisions`, `action_items`, and `resolved_items` alongside `segments`.

## Frontend Changes

### Step III — AI Analysis Results (replaces manual tagging)

- Transcript segments still shown, but AI-assigned tags pre-applied (user can still override)
- **Decision cards:** content, rationale, related people
- **Action item cards:** content, assignee, deadline, priority badge (high=gold / medium=cream / low=muted)
- If historical action items were auto-resolved, a banner shows at the top: "X 項待辦已在本次會議中完成"

### Step IV — Summary + History Panel

Existing summary output remains. Below it, a new **歷史待辦追蹤** panel:
- Lists all pending action items across all meetings
- Shows: source meeting date, assignee, deadline, priority
- Manual "標記完成" button per item

## Error Handling

| Scenario | Handling |
|---|---|
| Ollama not running | After transcription, show warning banner with "重新分析" button; allow proceeding to manual tagging |
| Llama returns invalid JSON | Retry up to 2 times; if still failing, use empty decisions/action_items, let user tag manually |
| Deadline format unparseable | Store raw string, do not force format |
| Corrupted meeting JSON file | Skip that file, log warning, do not affect current meeting |
| `meetings/` directory missing | Auto-create on first save |

## Dependencies

- **Ollama** — `brew install ollama` + `ollama pull llama3.1:8b`
- **httpx** — already in `requirements.txt`, used for async Ollama HTTP calls
- No new Python packages required

## Out of Scope (this version)

- Cloud sync or database
- Multi-user / multi-device
- Export to calendar (deadlines)
- Email notifications for action items
