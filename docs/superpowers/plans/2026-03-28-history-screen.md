# History Screen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone `history.html` page for viewing and managing all past meeting records, with full CRUD for meetings, decisions, and action items.

**Architecture:** New `history.html` page with list-view/detail-view master-detail pattern. Three new `storage.py` functions (`delete_meeting`, `update_decision`, `update_action_item`) exposed via three new FastAPI endpoints. `index.html` gains a "歷史紀錄" header link. All data lives in existing `meetings/*.json` files.

**Tech Stack:** Python/FastAPI backend, vanilla JS frontend, Art Deco CSS (same design tokens as `index.html`), pytest for backend tests.

---

### Task 1: Extend storage.py

**Files:**
- Modify: `storage.py`
- Modify: `tests/test_storage.py`

- [ ] **Step 1: Write failing tests for `delete_meeting`**

Append to `tests/test_storage.py`:

```python
def test_delete_meeting_returns_true():
    storage.save_meeting(_sample_meeting())
    assert storage.delete_meeting("2026-03-28_14-30") is True
    assert storage.load_meeting("2026-03-28_14-30") is None


def test_delete_meeting_missing_returns_false():
    assert storage.delete_meeting("nonexistent") is False
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_storage.py::test_delete_meeting_returns_true tests/test_storage.py::test_delete_meeting_missing_returns_false -v
```

Expected: FAIL with `AttributeError: module 'storage' has no attribute 'delete_meeting'`

- [ ] **Step 3: Implement `delete_meeting`**

Add to `storage.py` after `resolve_action_item`:

```python
def delete_meeting(meeting_id: str) -> bool:
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return False
    path.unlink()
    return True
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_storage.py::test_delete_meeting_returns_true tests/test_storage.py::test_delete_meeting_missing_returns_false -v
```

Expected: PASS

- [ ] **Step 5: Write failing tests for `update_decision`**

Append to `tests/test_storage.py`:

```python
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
    assert storage.update_decision("nonexistent", "d-1", {"content": "x"}) is None
```

- [ ] **Step 6: Run tests to verify they fail**

```
pytest tests/test_storage.py::test_update_decision_returns_updated tests/test_storage.py::test_update_decision_persists tests/test_storage.py::test_update_decision_missing_returns_none tests/test_storage.py::test_update_decision_missing_meeting_returns_none -v
```

Expected: FAIL with `AttributeError`

- [ ] **Step 7: Implement `update_decision`**

Add to `storage.py` after `delete_meeting`:

```python
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
```

- [ ] **Step 8: Run tests to verify they pass**

```
pytest tests/test_storage.py::test_update_decision_returns_updated tests/test_storage.py::test_update_decision_persists tests/test_storage.py::test_update_decision_missing_returns_none tests/test_storage.py::test_update_decision_missing_meeting_returns_none -v
```

Expected: PASS

- [ ] **Step 9: Write failing tests for `update_action_item`**

Append to `tests/test_storage.py`:

```python
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
    assert storage.update_action_item("nonexistent", "a-1", {"status": "done"}) is None
```

- [ ] **Step 10: Run tests to verify they fail**

```
pytest tests/test_storage.py::test_update_action_item_returns_updated tests/test_storage.py::test_update_action_item_persists tests/test_storage.py::test_update_action_item_missing_returns_none tests/test_storage.py::test_update_action_item_missing_meeting_returns_none -v
```

Expected: FAIL with `AttributeError`

- [ ] **Step 11: Implement `update_action_item`**

Add to `storage.py` after `update_decision`:

```python
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
```

- [ ] **Step 12: Add `pending_action_item_count` to `list_meetings`**

The history list view shows a "pending" badge. Update `list_meetings()` in `storage.py` — replace the meetings.append block:

```python
            meetings.append({
                "id": m["id"],
                "created_at": m["created_at"],
                "decision_count": len(m.get("decisions", [])),
                "action_item_count": len(m.get("action_items", [])),
                "pending_action_item_count": sum(
                    1 for a in m.get("action_items", []) if a.get("status") == "pending"
                ),
            })
```

- [ ] **Step 13: Write test for `pending_action_item_count`**

Append to `tests/test_storage.py`:

```python
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
```

- [ ] **Step 14: Run all storage tests**

```
pytest tests/test_storage.py -v
```

Expected: All pass (9 original + 10 new = 19 tests)

- [ ] **Step 15: Commit**

```bash
git add storage.py tests/test_storage.py
git commit -m "feat: add delete_meeting, update_decision, update_action_item to storage"
```

---

### Task 2: Add API Endpoints

**Files:**
- Modify: `server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Write failing tests for `DELETE /meetings/{id}`**

Append to `tests/test_server.py`:

```python
@pytest.mark.anyio
async def test_delete_meeting_success(monkeypatch):
    monkeypatch.setattr(storage, "delete_meeting", lambda mid: True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete("/meetings/2026-03-28_14-30")
    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}


@pytest.mark.anyio
async def test_delete_meeting_not_found(monkeypatch):
    monkeypatch.setattr(storage, "delete_meeting", lambda mid: False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete("/meetings/nonexistent")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_server.py::test_delete_meeting_success tests/test_server.py::test_delete_meeting_not_found -v
```

Expected: FAIL with `405 Method Not Allowed`

- [ ] **Step 3: Add `DELETE /meetings/{meeting_id}` to `server.py`**

Add to `server.py` after the `get_meeting` endpoint. Also add `Body` to the fastapi import line:

Change:
```python
from fastapi import FastAPI, UploadFile, File, HTTPException
```
To:
```python
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
```

Then add:
```python
@app.delete("/meetings/{meeting_id}")
def delete_meeting_endpoint(meeting_id: str):
    ok = storage.delete_meeting(meeting_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"status": "deleted"}
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_server.py::test_delete_meeting_success tests/test_server.py::test_delete_meeting_not_found -v
```

Expected: PASS

- [ ] **Step 5: Write failing tests for `PATCH /meetings/{id}/decisions/{did}`**

Append to `tests/test_server.py`:

```python
@pytest.mark.anyio
async def test_patch_decision_success(monkeypatch):
    updated = {"id": "d-1", "content": "新決議", "rationale": "效率", "related_people": [], "status": "confirmed"}
    monkeypatch.setattr(storage, "update_decision", lambda mid, did, updates: updated)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            "/meetings/2026-03-28_14-30/decisions/d-1",
            json={"content": "新決議"},
        )
    assert response.status_code == 200
    assert response.json()["content"] == "新決議"


@pytest.mark.anyio
async def test_patch_decision_not_found(monkeypatch):
    monkeypatch.setattr(storage, "update_decision", lambda mid, did, updates: None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            "/meetings/nonexistent/decisions/d-1",
            json={"content": "x"},
        )
    assert response.status_code == 404
```

- [ ] **Step 6: Run tests to verify they fail**

```
pytest tests/test_server.py::test_patch_decision_success tests/test_server.py::test_patch_decision_not_found -v
```

Expected: FAIL with `405 Method Not Allowed`

- [ ] **Step 7: Add `PATCH /meetings/{id}/decisions/{did}` to `server.py`**

Add after `delete_meeting_endpoint`:

```python
@app.patch("/meetings/{meeting_id}/decisions/{decision_id}")
def patch_decision(meeting_id: str, decision_id: str, body: dict = Body(...)):
    result = storage.update_decision(meeting_id, decision_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return result
```

- [ ] **Step 8: Run tests to verify they pass**

```
pytest tests/test_server.py::test_patch_decision_success tests/test_server.py::test_patch_decision_not_found -v
```

Expected: PASS

- [ ] **Step 9: Write failing tests for `PATCH /meetings/{id}/action-items/{aid}`**

Append to `tests/test_server.py`:

```python
@pytest.mark.anyio
async def test_patch_action_item_success(monkeypatch):
    updated = {"id": "a-1", "content": "更新文件", "assignee": "小明", "deadline": "2026-04-01", "priority": "high", "status": "done"}
    monkeypatch.setattr(storage, "update_action_item", lambda mid, iid, updates: updated)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            "/meetings/2026-03-28_14-30/action-items/a-1",
            json={"status": "done"},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "done"


@pytest.mark.anyio
async def test_patch_action_item_not_found(monkeypatch):
    monkeypatch.setattr(storage, "update_action_item", lambda mid, iid, updates: None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            "/meetings/nonexistent/action-items/a-1",
            json={"status": "done"},
        )
    assert response.status_code == 404
```

- [ ] **Step 10: Run tests to verify they fail**

```
pytest tests/test_server.py::test_patch_action_item_success tests/test_server.py::test_patch_action_item_not_found -v
```

Expected: FAIL with `405 Method Not Allowed`

- [ ] **Step 11: Add `PATCH /meetings/{id}/action-items/{aid}` to `server.py`**

Add after `patch_decision`:

```python
@app.patch("/meetings/{meeting_id}/action-items/{item_id}")
def patch_action_item(meeting_id: str, item_id: str, body: dict = Body(...)):
    result = storage.update_action_item(meeting_id, item_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Action item not found")
    return result
```

- [ ] **Step 12: Run all server tests**

```
pytest tests/test_server.py -v
```

Expected: All pass (existing tests + 6 new = 55 tests)

- [ ] **Step 13: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: add DELETE /meetings, PATCH decisions and action-items endpoints"
```

---

### Task 3: Create history.html

**Files:**
- Create: `history.html`

No automated tests for a standalone HTML file. Verification is manual (listed at end of task).

- [ ] **Step 1: Create `history.html`**

Create `/Users/ju/Desktop/my-project/history.html` with the following content:

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>歷史紀錄 — 會議助理</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Josefin+Sans:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg:        #0A0A0A;
      --card-bg:   #141414;
      --gold:      #D4AF37;
      --gold-dim:  rgba(212,175,55,0.3);
      --gold-glow: 0 0 15px rgba(212,175,55,0.2);
      --cream:     #F2F0E4;
      --muted:     #888888;
      --font-display: 'Marcellus', serif;
      --font-body:    'Josefin Sans', sans-serif;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--font-body);
      background-color: var(--bg);
      background-image:
        repeating-linear-gradient( 45deg, rgba(212,175,55,0.03) 0, rgba(212,175,55,0.03) 1px, transparent 1px, transparent 10px),
        repeating-linear-gradient(-45deg, rgba(212,175,55,0.03) 0, rgba(212,175,55,0.03) 1px, transparent 1px, transparent 10px);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      padding: 60px 16px;
      color: var(--cream);
    }

    .container { width: 100%; max-width: 680px; }

    /* Header */
    .header { text-align: center; margin-bottom: 48px; }
    .header-eyebrow {
      font-family: var(--font-body);
      font-size: 12px;
      letter-spacing: 0.3em;
      text-transform: uppercase;
      color: var(--gold);
      margin-bottom: 14px;
    }
    .header h1 {
      font-family: var(--font-display);
      font-size: clamp(28px, 6vw, 42px);
      color: var(--cream);
      letter-spacing: 0.05em;
      margin-bottom: 16px;
    }
    .header-divider {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 0 auto 20px;
      max-width: 240px;
    }
    .header-divider-line { flex: 1; height: 1px; background: var(--gold-dim); }
    .header-divider-diamond {
      width: 8px; height: 8px;
      background: var(--gold);
      transform: rotate(45deg);
      flex-shrink: 0;
    }
    .back-home {
      display: inline-block;
      color: var(--gold);
      text-decoration: none;
      font-size: 13px;
      letter-spacing: 0.08em;
      opacity: 0.8;
      transition: opacity 0.2s;
    }
    .back-home:hover { opacity: 1; }

    /* Warning banner */
    .warning-banner {
      display: none;
      background: rgba(180,50,50,0.15);
      border: 1px solid rgba(180,50,50,0.4);
      color: #e88;
      padding: 12px 16px;
      border-radius: 4px;
      font-size: 13px;
      margin-bottom: 24px;
      letter-spacing: 0.04em;
    }

    /* Meeting cards (list view) */
    .meeting-card {
      background: var(--card-bg);
      border: 1px solid var(--gold-dim);
      border-radius: 4px;
      padding: 20px 24px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .meeting-card-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .meeting-date {
      font-family: var(--font-display);
      font-size: 15px;
      color: var(--cream);
      letter-spacing: 0.03em;
      margin-right: 4px;
    }
    .badge {
      font-size: 11px;
      letter-spacing: 0.06em;
      padding: 3px 8px;
      border-radius: 2px;
      background: rgba(212,175,55,0.1);
      color: var(--gold);
      border: 1px solid var(--gold-dim);
    }
    .badge-pending {
      background: rgba(212,175,55,0.05);
      color: var(--muted);
      border-color: rgba(136,136,136,0.3);
    }
    .meeting-card-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }
    .confirm-msg {
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.04em;
    }

    /* Empty state */
    .empty-state {
      text-align: center;
      color: var(--muted);
      font-size: 14px;
      letter-spacing: 0.1em;
      padding: 60px 0;
    }

    /* Detail view */
    .detail-back {
      display: inline-block;
      color: var(--gold);
      text-decoration: none;
      font-size: 13px;
      letter-spacing: 0.08em;
      margin-bottom: 24px;
      cursor: pointer;
      opacity: 0.8;
      transition: opacity 0.2s;
      background: none;
      border: none;
      padding: 0;
    }
    .detail-back:hover { opacity: 1; }
    .detail-date {
      font-family: var(--font-display);
      font-size: 22px;
      color: var(--cream);
      margin-bottom: 32px;
      letter-spacing: 0.04em;
    }
    .section-title {
      font-family: var(--font-display);
      font-size: 16px;
      color: var(--gold);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--gold-dim);
    }
    .detail-section { margin-bottom: 40px; }

    /* Item cards */
    .item-card {
      background: var(--card-bg);
      border: 1px solid var(--gold-dim);
      border-radius: 4px;
      padding: 18px 20px;
      margin-bottom: 12px;
    }
    .item-header {
      display: flex;
      gap: 8px;
      margin-bottom: 8px;
      align-items: center;
    }
    .item-text {
      font-size: 14px;
      line-height: 1.6;
      color: var(--cream);
      margin-bottom: 6px;
    }
    .item-meta {
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.04em;
      margin-bottom: 4px;
    }
    .item-actions {
      display: flex;
      gap: 8px;
      margin-top: 12px;
    }
    .empty-section {
      color: var(--muted);
      font-size: 13px;
      padding: 12px 0;
    }

    /* Priority badges */
    .priority-badge {
      font-size: 10px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 2px 7px;
      border-radius: 2px;
    }
    .priority-high   { background: rgba(200,60,60,0.2);  color: #e88; border: 1px solid rgba(200,60,60,0.4); }
    .priority-medium { background: rgba(212,175,55,0.15); color: var(--gold); border: 1px solid var(--gold-dim); }
    .priority-low    { background: rgba(100,180,100,0.15); color: #8c8; border: 1px solid rgba(100,180,100,0.3); }

    /* Status badges */
    .status-badge {
      font-size: 10px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 2px 7px;
      border-radius: 2px;
    }
    .status-done    { background: rgba(100,180,100,0.15); color: #8c8; border: 1px solid rgba(100,180,100,0.3); }
    .status-pending { background: rgba(136,136,136,0.1);  color: var(--muted); border: 1px solid rgba(136,136,136,0.25); }

    /* Buttons */
    button {
      font-family: var(--font-body);
      cursor: pointer;
      border-radius: 2px;
      transition: all 0.2s;
    }
    .btn-primary {
      background: transparent;
      border: 1px solid var(--gold);
      color: var(--gold);
      font-size: 12px;
      letter-spacing: 0.1em;
      padding: 7px 16px;
    }
    .btn-primary:hover { background: var(--gold); color: var(--bg); }

    .btn-ghost {
      background: transparent;
      border: 1px solid rgba(136,136,136,0.35);
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.08em;
      padding: 7px 16px;
    }
    .btn-ghost:hover { border-color: var(--cream); color: var(--cream); }

    .btn-danger {
      background: transparent;
      border: 1px solid rgba(200,60,60,0.4);
      color: #e88;
      font-size: 12px;
      letter-spacing: 0.08em;
      padding: 7px 16px;
    }
    .btn-danger:hover { background: rgba(200,60,60,0.15); }

    .btn-small {
      font-size: 11px;
      letter-spacing: 0.06em;
      padding: 4px 12px;
    }

    /* Edit forms */
    .edit-form { margin-top: 14px; }
    .edit-form label {
      display: block;
      font-size: 11px;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--gold);
      margin-bottom: 14px;
    }
    .edit-form input,
    .edit-form textarea,
    .edit-form select {
      display: block;
      width: 100%;
      margin-top: 5px;
      background: #1a1a1a;
      border: 1px solid var(--gold-dim);
      color: var(--cream);
      font-family: var(--font-body);
      font-size: 13px;
      padding: 8px 10px;
      border-radius: 2px;
      outline: none;
    }
    .edit-form input:focus,
    .edit-form textarea:focus,
    .edit-form select:focus { border-color: var(--gold); }
    .edit-form textarea { min-height: 72px; resize: vertical; }
    .edit-form select option { background: #1a1a1a; }
    .form-error {
      display: none;
      color: #e88;
      font-size: 12px;
      margin-bottom: 10px;
    }
    .form-actions {
      display: flex;
      gap: 8px;
      margin-top: 4px;
    }
  </style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <header class="header">
    <p class="header-eyebrow">Meeting Intelligence</p>
    <h1>歷史紀錄</h1>
    <div class="header-divider" aria-hidden="true">
      <div class="header-divider-line"></div>
      <div class="header-divider-diamond"></div>
      <div class="header-divider-line"></div>
    </div>
    <a href="index.html" class="back-home">← 返回首頁</a>
  </header>

  <!-- Server warning -->
  <div id="server-warning" class="warning-banner">
    無法連線至伺服器，請確認後端已啟動（uvicorn server:app --reload）。
  </div>

  <!-- List view -->
  <div id="list-view">
    <div id="meeting-list"></div>
    <div id="empty-state" class="empty-state" style="display:none">尚無會議紀錄</div>
  </div>

  <!-- Detail view -->
  <div id="detail-view" style="display:none">
    <button class="detail-back" id="back-btn">← 返回列表</button>
    <h2 class="detail-date" id="detail-date"></h2>

    <div class="detail-section">
      <div class="section-title">決議事項</div>
      <div id="decisions-list"></div>
    </div>

    <div class="detail-section">
      <div class="section-title">待辦事項</div>
      <div id="action-items-list"></div>
    </div>
  </div>

</div>
<script>
  const API = 'http://localhost:8000';
  let currentMeetingId = null;
  let activeEditType = null; // 'decision' | 'action'
  let activeEditId = null;

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // ── Init ──────────────────────────────────────────────
  async function init() {
    document.getElementById('back-btn').addEventListener('click', showList);
    try {
      const r = await fetch(`${API}/health`);
      if (!r.ok) throw new Error();
    } catch {
      document.getElementById('server-warning').style.display = 'block';
    }
    await loadMeetings();
  }

  // ── List view ─────────────────────────────────────────
  async function loadMeetings() {
    try {
      const r = await fetch(`${API}/meetings`);
      if (!r.ok) throw new Error();
      const data = await r.json();
      renderMeetingList(data.meetings);
    } catch {
      document.getElementById('server-warning').style.display = 'block';
    }
  }

  function renderMeetingList(meetings) {
    const list = document.getElementById('meeting-list');
    const empty = document.getElementById('empty-state');
    if (!meetings || meetings.length === 0) {
      list.innerHTML = '';
      empty.style.display = 'block';
      return;
    }
    empty.style.display = 'none';
    list.innerHTML = meetings.map(m => {
      const dt = (m.created_at || '').replace('T', ' ').slice(0, 16);
      const pending = m.pending_action_item_count ?? 0;
      return `
        <div class="meeting-card" data-id="${escapeHtml(m.id)}">
          <div class="meeting-card-meta">
            <span class="meeting-date">${escapeHtml(dt)}</span>
            <span class="badge">決議 ${m.decision_count}</span>
            <span class="badge">待辦 ${m.action_item_count}</span>
            <span class="badge badge-pending">待處理 ${pending}</span>
          </div>
          <div class="meeting-card-actions" id="actions-${escapeHtml(m.id)}">
            <button class="btn-primary btn-small" data-view="${escapeHtml(m.id)}">查看</button>
            <button class="btn-danger btn-small" data-delete="${escapeHtml(m.id)}">刪除</button>
          </div>
        </div>`;
    }).join('');

    list.querySelectorAll('[data-view]').forEach(btn => {
      btn.addEventListener('click', () => showDetail(btn.dataset.view));
    });
    list.querySelectorAll('[data-delete]').forEach(btn => {
      btn.addEventListener('click', () => confirmDelete(btn.dataset.delete));
    });
  }

  function confirmDelete(meetingId) {
    const actionsDiv = document.getElementById(`actions-${meetingId}`);
    actionsDiv.innerHTML = `
      <span class="confirm-msg">確認刪除此會議？</span>
      <button class="btn-primary btn-small" id="confirm-yes-${escapeHtml(meetingId)}">確認</button>
      <button class="btn-ghost btn-small" id="confirm-no-${escapeHtml(meetingId)}">取消</button>`;
    document.getElementById(`confirm-yes-${meetingId}`).addEventListener('click', () => doDelete(meetingId));
    document.getElementById(`confirm-no-${meetingId}`).addEventListener('click', loadMeetings);
  }

  async function doDelete(meetingId) {
    try {
      const r = await fetch(`${API}/meetings/${encodeURIComponent(meetingId)}`, { method: 'DELETE' });
      if (!r.ok) throw new Error();
      await loadMeetings();
    } catch {
      const actionsDiv = document.getElementById(`actions-${meetingId}`);
      if (actionsDiv) actionsDiv.querySelector('.confirm-msg').textContent = '刪除失敗，請再試一次。';
    }
  }

  // ── Detail view ───────────────────────────────────────
  async function showDetail(meetingId) {
    try {
      const r = await fetch(`${API}/meetings/${encodeURIComponent(meetingId)}`);
      if (!r.ok) { alert('找不到此會議'); return; }
      const meeting = await r.json();
      currentMeetingId = meetingId;
      activeEditType = null;
      activeEditId = null;
      const dt = (meeting.created_at || '').replace('T', ' ').slice(0, 16);
      document.getElementById('detail-date').textContent = dt;
      renderDecisions(meeting.decisions || []);
      renderActionItems(meeting.action_items || []);
      document.getElementById('list-view').style.display = 'none';
      document.getElementById('detail-view').style.display = 'block';
    } catch {
      alert('載入會議失敗');
    }
  }

  function showList() {
    currentMeetingId = null;
    activeEditType = null;
    activeEditId = null;
    document.getElementById('detail-view').style.display = 'none';
    document.getElementById('list-view').style.display = 'block';
    loadMeetings();
  }

  // ── Decisions ─────────────────────────────────────────
  function renderDecisions(decisions) {
    const container = document.getElementById('decisions-list');
    if (!decisions.length) {
      container.innerHTML = '<p class="empty-section">無決議事項</p>';
      return;
    }
    container.innerHTML = decisions.map(d => {
      const people = Array.isArray(d.related_people) ? d.related_people.join(', ') : (d.related_people || '');
      return `
        <div class="item-card" id="decision-${escapeHtml(d.id)}">
          <div id="decision-display-${escapeHtml(d.id)}">
            <p class="item-text">${escapeHtml(d.content)}</p>
            ${d.rationale ? `<p class="item-meta">依據：${escapeHtml(d.rationale)}</p>` : ''}
            ${people ? `<p class="item-meta">相關人員：${escapeHtml(people)}</p>` : ''}
            <div class="item-actions">
              <button class="btn-ghost btn-small" data-edit-decision="${escapeHtml(d.id)}">編輯</button>
            </div>
          </div>
          <form class="edit-form" id="decision-form-${escapeHtml(d.id)}" style="display:none">
            <label>內容<textarea name="content">${escapeHtml(d.content)}</textarea></label>
            <label>依據<input type="text" name="rationale" value="${escapeHtml(d.rationale || '')}"></label>
            <label>相關人員（逗號分隔）<input type="text" name="related_people" value="${escapeHtml(people)}"></label>
            <div class="form-error"></div>
            <div class="form-actions">
              <button type="submit" class="btn-primary btn-small">儲存</button>
              <button type="button" class="btn-ghost btn-small" data-cancel>取消</button>
            </div>
          </form>
        </div>`;
    }).join('');

    container.querySelectorAll('[data-edit-decision]').forEach(btn => {
      btn.addEventListener('click', () => openDecisionEditor(btn.dataset.editDecision));
    });
    container.querySelectorAll('.edit-form').forEach(form => {
      form.addEventListener('submit', e => {
        e.preventDefault();
        const did = form.id.replace('decision-form-', '');
        saveDecision(form, did);
      });
      form.querySelector('[data-cancel]').addEventListener('click', closeEditor);
    });
  }

  function openDecisionEditor(id) {
    closeEditor();
    activeEditType = 'decision';
    activeEditId = id;
    document.getElementById(`decision-display-${id}`).style.display = 'none';
    document.getElementById(`decision-form-${id}`).style.display = 'block';
  }

  async function saveDecision(form, decisionId) {
    const formError = form.querySelector('.form-error');
    formError.style.display = 'none';
    const people = form.elements.related_people.value
      .split(',').map(s => s.trim()).filter(Boolean);
    const body = {
      content: form.elements.content.value.trim(),
      rationale: form.elements.rationale.value.trim(),
      related_people: people,
    };
    try {
      const r = await fetch(
        `${API}/meetings/${encodeURIComponent(currentMeetingId)}/decisions/${encodeURIComponent(decisionId)}`,
        { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      );
      if (!r.ok) throw new Error();
      const mr = await fetch(`${API}/meetings/${encodeURIComponent(currentMeetingId)}`);
      const meeting = await mr.json();
      activeEditType = null; activeEditId = null;
      renderDecisions(meeting.decisions || []);
      renderActionItems(meeting.action_items || []);
    } catch {
      formError.textContent = '儲存失敗，請再試一次。';
      formError.style.display = 'block';
    }
  }

  // ── Action items ──────────────────────────────────────
  function renderActionItems(items) {
    const container = document.getElementById('action-items-list');
    if (!items.length) {
      container.innerHTML = '<p class="empty-section">無待辦事項</p>';
      return;
    }
    container.innerHTML = items.map(a => `
      <div class="item-card" id="action-${escapeHtml(a.id)}">
        <div id="action-display-${escapeHtml(a.id)}">
          <div class="item-header">
            <span class="priority-badge priority-${escapeHtml(a.priority || 'medium')}">${escapeHtml(a.priority || 'medium')}</span>
            <span class="status-badge ${a.status === 'done' ? 'status-done' : 'status-pending'}">${a.status === 'done' ? '已完成' : '待處理'}</span>
          </div>
          <p class="item-text">${escapeHtml(a.content)}</p>
          <p class="item-meta">負責人：${escapeHtml(a.assignee || '—')} ｜ 期限：${escapeHtml(a.deadline || '—')}</p>
          <div class="item-actions">
            <button class="btn-ghost btn-small" data-toggle="${escapeHtml(a.id)}" data-status="${escapeHtml(a.status)}">${a.status === 'done' ? '重新開啟' : '標記完成'}</button>
            <button class="btn-ghost btn-small" data-edit-action="${escapeHtml(a.id)}">編輯</button>
          </div>
        </div>
        <form class="edit-form" id="action-form-${escapeHtml(a.id)}" style="display:none">
          <label>內容<textarea name="content">${escapeHtml(a.content)}</textarea></label>
          <label>負責人<input type="text" name="assignee" value="${escapeHtml(a.assignee || '')}"></label>
          <label>期限<input type="date" name="deadline" value="${escapeHtml(a.deadline || '')}"></label>
          <label>優先順序
            <select name="priority">
              <option value="high"   ${a.priority === 'high'   ? 'selected' : ''}>高</option>
              <option value="medium" ${a.priority === 'medium' ? 'selected' : ''}>中</option>
              <option value="low"    ${a.priority === 'low'    ? 'selected' : ''}>低</option>
            </select>
          </label>
          <div class="form-error"></div>
          <div class="form-actions">
            <button type="submit" class="btn-primary btn-small">儲存</button>
            <button type="button" class="btn-ghost btn-small" data-cancel>取消</button>
          </div>
        </form>
      </div>`).join('');

    container.querySelectorAll('[data-toggle]').forEach(btn => {
      btn.addEventListener('click', () => toggleStatus(btn.dataset.toggle, btn.dataset.status));
    });
    container.querySelectorAll('[data-edit-action]').forEach(btn => {
      btn.addEventListener('click', () => openActionEditor(btn.dataset.editAction));
    });
    container.querySelectorAll('.edit-form').forEach(form => {
      form.addEventListener('submit', e => {
        e.preventDefault();
        const aid = form.id.replace('action-form-', '');
        saveActionItem(form, aid);
      });
      form.querySelector('[data-cancel]').addEventListener('click', closeEditor);
    });
  }

  function openActionEditor(id) {
    closeEditor();
    activeEditType = 'action';
    activeEditId = id;
    document.getElementById(`action-display-${id}`).style.display = 'none';
    document.getElementById(`action-form-${id}`).style.display = 'block';
  }

  async function saveActionItem(form, itemId) {
    const formError = form.querySelector('.form-error');
    formError.style.display = 'none';
    const body = {
      content: form.elements.content.value.trim(),
      assignee: form.elements.assignee.value.trim(),
      deadline: form.elements.deadline.value,
      priority: form.elements.priority.value,
    };
    try {
      const r = await fetch(
        `${API}/meetings/${encodeURIComponent(currentMeetingId)}/action-items/${encodeURIComponent(itemId)}`,
        { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      );
      if (!r.ok) throw new Error();
      const mr = await fetch(`${API}/meetings/${encodeURIComponent(currentMeetingId)}`);
      const meeting = await mr.json();
      activeEditType = null; activeEditId = null;
      renderDecisions(meeting.decisions || []);
      renderActionItems(meeting.action_items || []);
    } catch {
      formError.textContent = '儲存失敗，請再試一次。';
      formError.style.display = 'block';
    }
  }

  async function toggleStatus(itemId, currentStatus) {
    const newStatus = currentStatus === 'done' ? 'pending' : 'done';
    try {
      const r = await fetch(
        `${API}/meetings/${encodeURIComponent(currentMeetingId)}/action-items/${encodeURIComponent(itemId)}`,
        { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: newStatus }) }
      );
      if (!r.ok) throw new Error();
      const mr = await fetch(`${API}/meetings/${encodeURIComponent(currentMeetingId)}`);
      const meeting = await mr.json();
      activeEditType = null; activeEditId = null;
      renderDecisions(meeting.decisions || []);
      renderActionItems(meeting.action_items || []);
    } catch {
      alert('更新失敗，請再試一次。');
    }
  }

  function closeEditor() {
    if (!activeEditId) return;
    if (activeEditType === 'decision') {
      document.getElementById(`decision-display-${activeEditId}`).style.display = 'block';
      document.getElementById(`decision-form-${activeEditId}`).style.display = 'none';
    } else if (activeEditType === 'action') {
      document.getElementById(`action-display-${activeEditId}`).style.display = 'block';
      document.getElementById(`action-form-${activeEditId}`).style.display = 'none';
    }
    activeEditType = null;
    activeEditId = null;
  }

  init();
</script>
</body>
</html>
```

- [ ] **Step 2: Verify manually with server running**

Open `http://localhost:8000` in browser, then navigate to `history.html`. Check:
- List of meetings appears, newest first
- Each card shows date, decision count badge, action item count badge, pending count badge
- "查看" opens detail view with decisions and action items
- "← 返回列表" returns to list
- "刪除" shows inline confirm; confirming removes the card
- "編輯" on a decision expands inline form; opening a second editor closes the first
- "儲存" on a decision form sends PATCH and updates display without page reload
- "取消" closes the form without changes
- "標記完成" / "重新開啟" toggles status
- "編輯" on an action item expands form with all fields pre-filled
- Empty state shown when no meetings

- [ ] **Step 3: Commit**

```bash
git add history.html
git commit -m "feat: add history.html standalone page"
```

---

### Task 4: Add "歷史紀錄" link to index.html header

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add the link**

In `index.html`, find the header block (around line 598–608):

```html
    <!-- Header -->
    <header class="header">
      <p class="header-eyebrow">Meeting Intelligence</p>
      <h1>會議助理</h1>
      <div class="header-divider" aria-hidden="true">
        <div class="header-divider-line"></div>
        <div class="header-divider-diamond"></div>
        <div class="header-divider-line"></div>
      </div>
      <p class="subtitle">語音轉文字 &nbsp;·&nbsp; 標記決議與待辦 &nbsp;·&nbsp; 一鍵輸出摘要</p>
    </header>
```

Replace with:

```html
    <!-- Header -->
    <header class="header">
      <p class="header-eyebrow">Meeting Intelligence</p>
      <h1>會議助理</h1>
      <div class="header-divider" aria-hidden="true">
        <div class="header-divider-line"></div>
        <div class="header-divider-diamond"></div>
        <div class="header-divider-line"></div>
      </div>
      <p class="subtitle">語音轉文字 &nbsp;·&nbsp; 標記決議與待辦 &nbsp;·&nbsp; 一鍵輸出摘要</p>
      <a href="history.html" style="display:inline-block;margin-top:16px;color:var(--gold);text-decoration:none;font-size:13px;letter-spacing:0.08em;opacity:0.8;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.8'">歷史紀錄 →</a>
    </header>
```

- [ ] **Step 2: Verify manually**

Open `index.html`. Check:
- "歷史紀錄 →" link appears below the subtitle in the header
- Clicking it navigates to `history.html`

- [ ] **Step 3: Run full test suite to confirm no regressions**

```
pytest -v
```

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add history page link to index.html header"
```
