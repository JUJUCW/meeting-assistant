# Add Decisions and Action Items — Design Spec
**Date:** 2026-03-29

## Overview

Allow users to manually add new decisions and action items from the history detail view (`history.html`). Currently items are only created by the AI analyzer post-transcription; this adds a manual creation path.

## Architecture

| Change | Responsibility |
|---|---|
| Modify `storage.py` | Add `add_decision`, `add_action_item` |
| Modify `server.py` | Add `POST /meetings/{id}/decisions`, `POST /meetings/{id}/action-items` |
| Modify `history.html` | Add "＋ 新增" button + inline form at bottom of each section |

No changes to `index.html`, `analyzer.py`, or data formats.

## New API Endpoints

| Endpoint | Method | Request Body | Response |
|---|---|---|---|
| `POST /meetings/{meeting_id}/decisions` | POST | `{"content", "rationale"?, "related_people"?}` | new decision dict or 404 |
| `POST /meetings/{meeting_id}/action-items` | POST | `{"content", "assignee"?, "deadline"?, "priority"}` | new action item dict or 404 |

`content` is required for both. `priority` is required for action items (no server-side default — client sends `"medium"` if user leaves it unset).

## New storage.py Functions

```python
def add_decision(meeting_id: str, data: dict) -> dict | None
def add_action_item(meeting_id: str, data: dict) -> dict | None
```

**ID generation:** Look at existing items in the meeting, extract the numeric suffix from each ID, take the max, add 1. If no items exist, start at 1. Examples: existing `["d-1", "d-2"]` → new ID is `"d-3"`. Existing `[]` → `"d-1"`.

**Default fields added by storage (not by caller):**
- Decision: `status: "confirmed"`
- Action item: `status: "pending"`

Both functions return the complete new item dict on success, `None` if meeting not found.

## history.html Changes

### UI

Each section (決議事項, 待辦事項) gets a "＋ 新增" button at the bottom. Clicking it:
1. Closes any currently open editor (same single-editor rule as existing edit forms)
2. Expands an inline add form at the bottom of the section

The add form uses the same CSS as the existing edit forms.

### Decision add form fields
- 內容 — `<textarea name="content">` (required)
- 依據 — `<input type="text" name="rationale">` (optional)
- 相關人員（逗號分隔） — `<input type="text" name="related_people">` (optional)
- 儲存 button (submit) + 取消 button

### Action item add form fields
- 內容 — `<textarea name="content">` (required)
- 負責人 — `<input type="text" name="assignee">` (optional)
- 期限 — `<input type="date" name="deadline">` (optional)
- 優先順序 — `<select name="priority">` high/medium/low, default medium (required)
- 儲存 button (submit) + 取消 button

### Submit behaviour
- Client validates `content` is not empty; shows inline error if blank
- Calls POST endpoint
- On success: close form, re-fetch meeting from API, re-render the full section (decisions or action items)
- On failure: keep form open, show error below form ("新增失敗，請再試一次。")

### Single-editor rule
The new add form counts as an editor. Opening it closes any open edit form, and opening any edit form closes an open add form. The existing `activeEditType` / `activeEditId` tracking is extended with a new type `'add-decision'` and `'add-action'`.

## Error Handling

| Scenario | Handling |
|---|---|
| `content` empty on submit | Inline validation error, do not call API |
| POST fails | Keep form open, show "新增失敗，請再試一次。" below form |
| Meeting not found (404) | Show error, return to list |

## Out of Scope

- Adding decisions/action items from `index.html` Step III
- Deleting individual decisions or action items
- Reordering items
