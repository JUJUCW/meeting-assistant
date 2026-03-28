# History Maintenance Screen — Design Spec
**Date:** 2026-03-28

## Overview

Add a standalone `history.html` page for viewing and managing all past meeting records. Users can browse meetings, edit decisions and action items, change action item status, and delete meetings. The page shares the same Art Deco design language and connects to the same `localhost:8000` API.

Entry point: a "歷史紀錄" link added to the header area of `index.html`.

## Architecture

| Change | Responsibility |
|---|---|
| New `history.html` | Standalone history page — list view + detail view, single-column, master-detail pattern |
| Modify `storage.py` | Add `delete_meeting`, `update_decision`, `update_action_item` |
| Modify `server.py` | Add `DELETE /meetings/{id}`, `PATCH /meetings/{id}/decisions/{did}`, `PATCH /meetings/{id}/action-items/{aid}` |
| Modify `index.html` | Add "歷史紀錄" link in header |

No new data formats. `history.html` reads and writes the existing `meetings/*.json` files via the existing API.

## UI: history.html

### List View (default)

Art Deco header with title "歷史紀錄". Below: one card per meeting, newest first, showing:
- Date and time (`YYYY-MM-DD HH:MM`)
- Badge counts: decisions, total action items, pending action items
- "查看" button → switches to detail view
- "刪除" button → shows inline confirmation ("確認刪除此會議？" + confirm/cancel), then calls DELETE API and removes card on success

Empty state: "尚無會議紀錄"

### Detail View

Replaces list view in-place. Top: "← 返回列表" link + meeting date/time as heading.

**決議事項 section:** Each decision shows content, rationale, related people. "編輯" button expands an inline form with text fields for content, rationale, related_people (comma-separated). "儲存" calls PATCH, collapses form and updates display. "取消" discards changes.

**待辦事項 section:** Each action item shows content, assignee, deadline, priority badge, status. Two controls per item:
- "標記完成" / "重新開啟" quick-toggle (calls PATCH with `{"status": "done"}` or `{"status": "pending"}`)
- "編輯" expands inline form for content, assignee, deadline (date input), priority (select: high/medium/low)

Transcript is **not shown** (too granular for long recordings).

Only one item can be in edit mode at a time. Opening a second editor closes the first without saving.

## New API Endpoints

| Endpoint | Method | Request Body | Response |
|---|---|---|---|
| `DELETE /meetings/{meeting_id}` | DELETE | — | `{"status": "deleted"}` or 404 |
| `PATCH /meetings/{meeting_id}/decisions/{decision_id}` | PATCH | `{"content"?, "rationale"?, "related_people"?}` | updated decision dict or 404 |
| `PATCH /meetings/{meeting_id}/action-items/{item_id}` | PATCH | `{"content"?, "assignee"?, "deadline"?, "priority"?, "status"?}` | updated action item dict or 404 |

PATCH only updates fields present in the request body. Missing fields are left unchanged.

## New storage.py Functions

```python
def delete_meeting(meeting_id: str) -> bool
def update_decision(meeting_id: str, decision_id: str, updates: dict) -> dict | None
def update_action_item(meeting_id: str, item_id: str, updates: dict) -> dict | None
```

`update_decision` and `update_action_item` return the updated item dict on success, `None` if not found.

## Error Handling

| Scenario | Handling |
|---|---|
| Server not running | Warning banner at top of page |
| No meetings | Empty state message in list |
| Save fails (PATCH) | Keep edit form open, show error below form |
| Delete fails | Show error inline, do not remove card |
| Meeting not found (404) | Show error, return to list |

## Out of Scope

- Editing the meeting transcript
- Creating new meetings from history page (only via main flow)
- Search or filter meetings
- Pagination (all meetings shown, local file storage implies small volume)
