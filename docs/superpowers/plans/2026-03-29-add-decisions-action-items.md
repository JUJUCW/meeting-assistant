# Add Decisions and Action Items Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow users to manually add new decisions and action items from the history detail view.

**Architecture:** New `add_decision` and `add_action_item` functions in `storage.py`, exposed via `POST /meetings/{id}/decisions` and `POST /meetings/{id}/action-items` in `server.py`. In `history.html`, each section gets a static "＋ 新增" button that expands an inline add form, wired through the existing `activeEditorCleanup` pattern.

**Tech Stack:** Python/FastAPI backend, pytest, vanilla JS/HTML frontend.

---

### Task 1: Add `add_decision` and `add_action_item` to storage.py

**Files:**
- Modify: `storage.py`
- Modify: `tests/test_storage.py`

- [ ] **Step 1: Write failing tests for `add_decision`**

Append to `tests/test_storage.py`:

```python
def test_add_decision_returns_new_item():
    storage.save_meeting(_sample_meeting())
    result = storage.add_decision("2026-03-28_14-30", {
        "content": "新決議", "rationale": "效率", "related_people": ["小明"]
    })
    assert result is not None
    assert result["id"] == "d-2"  # existing d-1, next is d-2
    assert result["content"] == "新決議"
    assert result["status"] == "confirmed"


def test_add_decision_persists():
    storage.save_meeting(_sample_meeting())
    storage.add_decision("2026-03-28_14-30", {"content": "新決議", "rationale": "", "related_people": []})
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert len(loaded["decisions"]) == 2
    assert loaded["decisions"][1]["content"] == "新決議"


def test_add_decision_first_item_gets_id_d1():
    m = _sample_meeting()
    m["decisions"] = []
    storage.save_meeting(m)
    result = storage.add_decision("2026-03-28_14-30", {"content": "第一個決議", "rationale": "", "related_people": []})
    assert result["id"] == "d-1"


def test_add_decision_missing_meeting_returns_none():
    assert storage.add_decision("nonexistent", {"content": "x", "rationale": "", "related_people": []}) is None
```

- [ ] **Step 2: Run tests to verify they fail**

```
cd /Users/ju/Desktop/my-project/.worktrees/add-items && source /Users/ju/Desktop/my-project/venv/bin/activate && python -m pytest tests/test_storage.py::test_add_decision_returns_new_item tests/test_storage.py::test_add_decision_persists tests/test_storage.py::test_add_decision_first_item_gets_id_d1 tests/test_storage.py::test_add_decision_missing_meeting_returns_none -v
```

Expected: FAIL with `AttributeError: module 'storage' has no attribute 'add_decision'`

- [ ] **Step 3: Implement `add_decision`**

Add to `storage.py` after `update_action_item`:

```python
def add_decision(meeting_id: str, data: dict) -> dict | None:
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
python -m pytest tests/test_storage.py::test_add_decision_returns_new_item tests/test_storage.py::test_add_decision_persists tests/test_storage.py::test_add_decision_first_item_gets_id_d1 tests/test_storage.py::test_add_decision_missing_meeting_returns_none -v
```

Expected: PASS

- [ ] **Step 5: Write failing tests for `add_action_item`**

Append to `tests/test_storage.py`:

```python
def test_add_action_item_returns_new_item():
    storage.save_meeting(_sample_meeting())
    result = storage.add_action_item("2026-03-28_14-30", {
        "content": "新任務", "assignee": "小花", "deadline": "2026-04-10", "priority": "high"
    })
    assert result is not None
    assert result["id"] == "a-2"  # existing a-1, next is a-2
    assert result["content"] == "新任務"
    assert result["status"] == "pending"
    assert result["priority"] == "high"


def test_add_action_item_persists():
    storage.save_meeting(_sample_meeting())
    storage.add_action_item("2026-03-28_14-30", {
        "content": "新任務", "assignee": "", "deadline": "", "priority": "medium"
    })
    loaded = storage.load_meeting("2026-03-28_14-30")
    assert len(loaded["action_items"]) == 2
    assert loaded["action_items"][1]["content"] == "新任務"


def test_add_action_item_first_item_gets_id_a1():
    m = _sample_meeting()
    m["action_items"] = []
    storage.save_meeting(m)
    result = storage.add_action_item("2026-03-28_14-30", {
        "content": "第一個任務", "assignee": "", "deadline": "", "priority": "low"
    })
    assert result["id"] == "a-1"


def test_add_action_item_missing_meeting_returns_none():
    assert storage.add_action_item("nonexistent", {
        "content": "x", "assignee": "", "deadline": "", "priority": "medium"
    }) is None
```

- [ ] **Step 6: Run tests to verify they fail**

```
python -m pytest tests/test_storage.py::test_add_action_item_returns_new_item tests/test_storage.py::test_add_action_item_persists tests/test_storage.py::test_add_action_item_first_item_gets_id_a1 tests/test_storage.py::test_add_action_item_missing_meeting_returns_none -v
```

Expected: FAIL with `AttributeError`

- [ ] **Step 7: Implement `add_action_item`**

Add to `storage.py` after `add_decision`:

```python
def add_action_item(meeting_id: str, data: dict) -> dict | None:
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
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
```

- [ ] **Step 8: Run tests to verify they pass**

```
python -m pytest tests/test_storage.py::test_add_action_item_returns_new_item tests/test_storage.py::test_add_action_item_persists tests/test_storage.py::test_add_action_item_first_item_gets_id_a1 tests/test_storage.py::test_add_action_item_missing_meeting_returns_none -v
```

Expected: PASS

- [ ] **Step 9: Run all storage tests**

```
python -m pytest tests/test_storage.py -v
```

Expected: All pass (20 existing + 8 new = 28 tests)

- [ ] **Step 10: Commit**

```bash
git add storage.py tests/test_storage.py
git commit -m "feat: add add_decision and add_action_item to storage"
```

---

### Task 2: Add POST API Endpoints

**Files:**
- Modify: `server.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Write failing tests for `POST /meetings/{id}/decisions`**

Append to `tests/test_server.py`:

```python
@pytest.mark.anyio
async def test_create_decision_success(monkeypatch):
    new_d = {"id": "d-2", "content": "新決議", "rationale": "", "related_people": [], "status": "confirmed"}
    monkeypatch.setattr(storage, "add_decision", lambda mid, data: new_d)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/2026-03-28_14-30/decisions",
            json={"content": "新決議", "rationale": "", "related_people": []},
        )
    assert response.status_code == 200
    assert response.json()["id"] == "d-2"


@pytest.mark.anyio
async def test_create_decision_not_found(monkeypatch):
    monkeypatch.setattr(storage, "add_decision", lambda mid, data: None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/nonexistent/decisions",
            json={"content": "x", "rationale": "", "related_people": []},
        )
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```
python -m pytest tests/test_server.py::test_create_decision_success tests/test_server.py::test_create_decision_not_found -v
```

Expected: FAIL with `405 Method Not Allowed`

- [ ] **Step 3: Add `POST /meetings/{id}/decisions` to `server.py`**

Add after the `patch_decision` endpoint:

```python
@app.post("/meetings/{meeting_id}/decisions")
def create_decision(meeting_id: str, body: dict = Body(...)):
    result = storage.add_decision(meeting_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

```
python -m pytest tests/test_server.py::test_create_decision_success tests/test_server.py::test_create_decision_not_found -v
```

Expected: PASS

- [ ] **Step 5: Write failing tests for `POST /meetings/{id}/action-items`**

Append to `tests/test_server.py`:

```python
@pytest.mark.anyio
async def test_create_action_item_success(monkeypatch):
    new_a = {"id": "a-2", "content": "新任務", "assignee": "", "deadline": "", "priority": "medium", "status": "pending"}
    monkeypatch.setattr(storage, "add_action_item", lambda mid, data: new_a)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/2026-03-28_14-30/action-items",
            json={"content": "新任務", "assignee": "", "deadline": "", "priority": "medium"},
        )
    assert response.status_code == 200
    assert response.json()["id"] == "a-2"


@pytest.mark.anyio
async def test_create_action_item_not_found(monkeypatch):
    monkeypatch.setattr(storage, "add_action_item", lambda mid, data: None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/meetings/nonexistent/action-items",
            json={"content": "x", "assignee": "", "deadline": "", "priority": "medium"},
        )
    assert response.status_code == 404
```

- [ ] **Step 6: Run tests to verify they fail**

```
python -m pytest tests/test_server.py::test_create_action_item_success tests/test_server.py::test_create_action_item_not_found -v
```

Expected: FAIL

- [ ] **Step 7: Add `POST /meetings/{id}/action-items` to `server.py`**

Add after `create_decision`:

```python
@app.post("/meetings/{meeting_id}/action-items")
def create_action_item(meeting_id: str, body: dict = Body(...)):
    result = storage.add_action_item(meeting_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return result
```

- [ ] **Step 8: Run all server tests**

```
python -m pytest tests/test_server.py -v
```

Expected: All pass (44 existing + 4 new = 48 tests)

- [ ] **Step 9: Commit**

```bash
git add server.py tests/test_server.py
git commit -m "feat: add POST /meetings/{id}/decisions and /action-items endpoints"
```

---

### Task 3: Add "＋ 新增" UI to history.html

**Files:**
- Modify: `history.html`

- [ ] **Step 1: Add add-form HTML to the decisions section**

In `history.html`, find this block (around line 637):

```html
      <div class="section" id="decisions-section">
        <div class="section-heading">決議事項</div>
        <div id="decisions-list"></div>
      </div>
```

Replace with:

```html
      <div class="section" id="decisions-section">
        <div class="section-heading">決議事項</div>
        <div id="decisions-list"></div>
        <div id="add-decision-form" class="decision-item" style="display:none">
          <div class="edit-form visible">
            <div class="form-group">
              <label class="form-label">決議內容（必填）</label>
              <textarea class="form-textarea" id="add-decision-content"></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">依據</label>
              <input class="form-input" type="text" id="add-decision-rationale">
            </div>
            <div class="form-group">
              <label class="form-label">相關人員（逗號分隔）</label>
              <input class="form-input" type="text" id="add-decision-people">
            </div>
            <div class="form-buttons">
              <button class="btn-save" id="save-add-decision">儲存</button>
              <button class="btn-cancel" id="cancel-add-decision">取消</button>
            </div>
            <div class="form-error" id="add-decision-error" style="display:none;color:#e88;font-size:12px;letter-spacing:0.06em;margin-top:8px;"></div>
          </div>
        </div>
        <button class="btn-edit" id="add-decision-btn" style="margin-top:12px;display:block">＋ 新增決議</button>
      </div>
```

- [ ] **Step 2: Add add-form HTML to the actions section**

Find:

```html
      <div class="section" id="actions-section">
        <div class="section-heading">行動項目</div>
        <div id="actions-list"></div>
      </div>
```

Replace with:

```html
      <div class="section" id="actions-section">
        <div class="section-heading">行動項目</div>
        <div id="actions-list"></div>
        <div id="add-action-form" class="action-item" style="display:none">
          <div class="edit-form visible">
            <div class="form-group">
              <label class="form-label">行動內容（必填）</label>
              <textarea class="form-textarea" id="add-action-content"></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">負責人</label>
              <input class="form-input" type="text" id="add-action-assignee">
            </div>
            <div class="form-group">
              <label class="form-label">截止日期</label>
              <input class="form-input" type="date" id="add-action-deadline">
            </div>
            <div class="form-group">
              <label class="form-label">優先級</label>
              <select class="form-select" id="add-action-priority">
                <option value="high">高</option>
                <option value="medium" selected>中</option>
                <option value="low">低</option>
              </select>
            </div>
            <div class="form-buttons">
              <button class="btn-save" id="save-add-action">儲存</button>
              <button class="btn-cancel" id="cancel-add-action">取消</button>
            </div>
            <div class="form-error" id="add-action-error" style="display:none;color:#e88;font-size:12px;letter-spacing:0.06em;margin-top:8px;"></div>
          </div>
        </div>
        <button class="btn-edit" id="add-action-btn" style="margin-top:12px;display:block">＋ 新增待辦事項</button>
      </div>
```

- [ ] **Step 3: Hide add forms when opening a new detail view**

In `openDetail`, find the lines:

```javascript
        currentMeeting = meeting;
        activeEditorCleanup = null;
```

After `activeEditorCleanup = null;`, add:

```javascript
        document.getElementById('add-decision-form').style.display = 'none';
        document.getElementById('add-action-form').style.display = 'none';
```

- [ ] **Step 4: Wire up the add-decision button and form in `init`**

In the `init` function, after the transcript toggle listener, add:

```javascript
      // Add decision
      document.getElementById('add-decision-btn').addEventListener('click', () => {
        if (activeEditorCleanup) activeEditorCleanup();
        document.getElementById('add-decision-content').value = '';
        document.getElementById('add-decision-rationale').value = '';
        document.getElementById('add-decision-people').value = '';
        document.getElementById('add-decision-error').style.display = 'none';
        document.getElementById('add-decision-form').style.display = 'block';
        activeEditorCleanup = () => {
          document.getElementById('add-decision-form').style.display = 'none';
          activeEditorCleanup = null;
        };
      });

      document.getElementById('cancel-add-decision').addEventListener('click', () => {
        document.getElementById('add-decision-form').style.display = 'none';
        activeEditorCleanup = null;
      });

      document.getElementById('save-add-decision').addEventListener('click', async () => {
        const errEl = document.getElementById('add-decision-error');
        errEl.style.display = 'none';
        const content = document.getElementById('add-decision-content').value.trim();
        if (!content) {
          errEl.textContent = '內容為必填欄位。';
          errEl.style.display = 'block';
          return;
        }
        const rationale = document.getElementById('add-decision-rationale').value.trim();
        const related_people = document.getElementById('add-decision-people').value
          .split(',').map(s => s.trim()).filter(Boolean);
        try {
          const r = await fetch(
            `${API}/meetings/${encodeURIComponent(currentMeeting.id)}/decisions`,
            { method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ content, rationale, related_people }) }
          );
          if (!r.ok) throw new Error();
          const newDecision = await r.json();
          document.getElementById('add-decision-form').style.display = 'none';
          activeEditorCleanup = null;
          currentMeeting.decisions = currentMeeting.decisions || [];
          currentMeeting.decisions.push(newDecision);
          renderDecisions(currentMeeting);
        } catch {
          errEl.textContent = '新增失敗，請再試一次。';
          errEl.style.display = 'block';
        }
      });
```

- [ ] **Step 5: Wire up the add-action button and form in `init`**

Immediately after the add-decision block, add:

```javascript
      // Add action item
      document.getElementById('add-action-btn').addEventListener('click', () => {
        if (activeEditorCleanup) activeEditorCleanup();
        document.getElementById('add-action-content').value = '';
        document.getElementById('add-action-assignee').value = '';
        document.getElementById('add-action-deadline').value = '';
        document.getElementById('add-action-priority').value = 'medium';
        document.getElementById('add-action-error').style.display = 'none';
        document.getElementById('add-action-form').style.display = 'block';
        activeEditorCleanup = () => {
          document.getElementById('add-action-form').style.display = 'none';
          activeEditorCleanup = null;
        };
      });

      document.getElementById('cancel-add-action').addEventListener('click', () => {
        document.getElementById('add-action-form').style.display = 'none';
        activeEditorCleanup = null;
      });

      document.getElementById('save-add-action').addEventListener('click', async () => {
        const errEl = document.getElementById('add-action-error');
        errEl.style.display = 'none';
        const content = document.getElementById('add-action-content').value.trim();
        if (!content) {
          errEl.textContent = '內容為必填欄位。';
          errEl.style.display = 'block';
          return;
        }
        const assignee = document.getElementById('add-action-assignee').value.trim();
        const deadline = document.getElementById('add-action-deadline').value;
        const priority = document.getElementById('add-action-priority').value;
        try {
          const r = await fetch(
            `${API}/meetings/${encodeURIComponent(currentMeeting.id)}/action-items`,
            { method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ content, assignee, deadline, priority }) }
          );
          if (!r.ok) throw new Error();
          const newItem = await r.json();
          document.getElementById('add-action-form').style.display = 'none';
          activeEditorCleanup = null;
          currentMeeting.action_items = currentMeeting.action_items || [];
          currentMeeting.action_items.push(newItem);
          renderActionItems(currentMeeting);
        } catch {
          errEl.textContent = '新增失敗，請再試一次。';
          errEl.style.display = 'block';
        }
      });
```

- [ ] **Step 6: Run full test suite**

```
python -m pytest -q
```

Expected: All tests pass (72 existing + 12 new from Tasks 1–2 = 84 tests)

- [ ] **Step 7: Verify manually**

Open `history.html` in browser (server running). Open any meeting detail view. Confirm:
- "＋ 新增決議" button appears below the decisions list
- "＋ 新增待辦事項" button appears below the action items list
- Clicking "＋ 新增決議" shows the add form; existing edit forms close
- Submitting with empty 內容 shows "內容為必填欄位。" error inline
- Valid submit adds the item to the list and collapses the form
- "取消" hides the form without saving
- Switching meetings resets (forms are hidden)

- [ ] **Step 8: Commit**

```bash
git add history.html
git commit -m "feat: add inline add-decision and add-action-item forms to history detail view"
```
