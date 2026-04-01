# Transcript Display Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove per-segment tag buttons from the Step II transcript view, and add a collapsible transcript section to the history detail view.

**Architecture:** Two independent frontend-only changes to `index.html` and `history.html`. No backend or test file changes required.

**Tech Stack:** Vanilla HTML/CSS/JS.

---

### Task 1: Remove Tagging from index.html Step II Transcript

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Remove tag-button CSS rules**

In `index.html`, find and delete the following CSS blocks (lines ~389–420):

```css
    .segment-actions { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }

    .tag-btn {
      padding: 6px 12px;
      border-radius: 0;
      font-family: var(--font-body);
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      cursor: pointer;
      border: 1px solid;
      transition: all 0.2s;
      background: transparent;
    }
    .tag-btn-decision {
      border-color: rgba(212,175,55,0.4);
      color: rgba(212,175,55,0.6);
    }
    .tag-btn-decision.active, .tag-btn-decision:hover {
      background: var(--gold);
      color: #0A0A0A;
      border-color: var(--gold);
    }
    .tag-btn-action {
      border-color: rgba(242,240,228,0.18);
      color: rgba(242,240,228,0.35);
    }
    .tag-btn-action.active, .tag-btn-action:hover {
      background: var(--cream);
      color: #0A0A0A;
      border-color: var(--cream);
    }
```

Also simplify `.segment-item` — remove the `flex` and `gap` since there is only one child now. Replace:

```css
    .segment-item {
      display: flex;
      gap: 14px;
      align-items: flex-start;
      background: rgba(212,175,55,0.02);
      border: 1px solid rgba(212,175,55,0.08);
      padding: 16px;
      margin-bottom: 8px;
      transition: border-color 0.2s;
    }
```

With:

```css
    .segment-item {
      background: rgba(212,175,55,0.02);
      border: 1px solid rgba(212,175,55,0.08);
      padding: 16px;
      margin-bottom: 8px;
      transition: border-color 0.2s;
    }
```

- [ ] **Step 2: Simplify `renderSegments()`**

Find the `renderSegments()` function (around line 944). Replace it entirely with:

```javascript
    function renderSegments() {
      const list = document.getElementById('segments-list');
      list.innerHTML = '';
      segments.forEach(seg => {
        const div = document.createElement('div');
        div.className = 'segment-item';
        div.innerHTML = `<span class="segment-text">${escapeHtml(seg.text)}</span>`;
        list.appendChild(div);
      });
    }
```

- [ ] **Step 3: Remove `setTag()` function**

Find and delete the entire `setTag` function:

```javascript
    function setTag(id, tag) {
      const seg = segments.find(s => s.id === id);
      if (!seg) return;
      seg.tag = seg.tag === tag ? null : tag;
      renderSegments();
    }
```

- [ ] **Step 4: Remove tagged-segment fallbacks from `renderSummary()`**

Find `renderSummary()` (around line 1040). Replace it with the version below that removes the `taggedDecisions`/`taggedActions` variables and their `else if` fallback blocks:

```javascript
    function renderSummary() {
      const allText = segments.map(s => s.text).join('\n');

      let output = '【會議記錄】\n' + allText + '\n';

      if (decisions.length > 0) {
        output += '\n【決議事項】\n';
        decisions.forEach((d, i) => {
          output += `${i + 1}. ${d.content}`;
          if (d.rationale) output += `（${d.rationale}）`;
          output += '\n';
        });
      }

      if (actionItems.length > 0) {
        output += '\n【待辦事項】\n';
        actionItems.forEach((a, i) => {
          output += `${i + 1}. ${a.content}`;
          if (a.assignee) output += `（負責人：${a.assignee}）`;
          if (a.deadline) output += `（截止：${a.deadline}）`;
          output += '\n';
        });
      }

      document.getElementById('summary-output').textContent = output;
      loadHistoryPanel();
    }
```

- [ ] **Step 5: Update the Step 3 comment**

Find the comment:
```javascript
    // --- Step 3: Tag segments ---
```

Replace with:
```javascript
    // --- Step 3: Transcript ---
```

- [ ] **Step 6: Verify manually**

Open `index.html` in a browser (with the server running). Upload an audio file, proceed to Step II. Confirm:
- Each transcript segment shows only text — no 決議 / 待辦 buttons
- Step III analysis cards still render correctly
- Step IV summary output shows 【會議記錄】, 【決議事項】, 【待辦事項】 sections

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "feat: remove segment tagging from Step II transcript"
```

---

### Task 2: Add Collapsible Transcript to history.html Detail View

**Files:**
- Modify: `history.html`

- [ ] **Step 1: Add transcript CSS**

In `history.html`, find the `/* ── Detail View ── */` CSS section (around line 280). Add these rules after the existing detail view styles:

```css
    /* ── Transcript Collapsible ── */
    .transcript-toggle {
      background: none;
      border: none;
      cursor: pointer;
      width: 100%;
      text-align: left;
      padding: 0;
      color: var(--gold);
      font-family: var(--font-display);
      font-size: 14px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .transcript-toggle::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--gold-dim);
    }
    .toggle-icon {
      font-size: 10px;
      transition: transform 0.2s;
      flex-shrink: 0;
    }
    .transcript-toggle[aria-expanded="true"] .toggle-icon {
      transform: rotate(90deg);
    }
    .transcript-body {
      margin-top: 16px;
    }
    #transcript-text {
      font-size: 13px;
      line-height: 1.8;
      color: var(--muted);
      white-space: pre-wrap;
      letter-spacing: 0.02em;
    }
```

- [ ] **Step 2: Add transcript HTML in detail view**

In `history.html`, find the detail view HTML (around line 581):

```html
    <!-- Detail View -->
    <div id="detail-view">
      <button id="back-btn">← 返回列表</button>
      <div id="detail-date"></div>

      <div class="section" id="decisions-section">
```

Insert the transcript section between `<div id="detail-date"></div>` and the decisions section:

```html
    <!-- Detail View -->
    <div id="detail-view">
      <button id="back-btn">← 返回列表</button>
      <div id="detail-date"></div>

      <div class="section" id="transcript-section" style="display:none">
        <button class="transcript-toggle" id="transcript-toggle" aria-expanded="false">
          逐字稿 <span class="toggle-icon">▶</span>
        </button>
        <div class="transcript-body" id="transcript-body" style="display:none">
          <p id="transcript-text"></p>
        </div>
      </div>

      <div class="section" id="decisions-section">
```

- [ ] **Step 3: Populate transcript in `openDetail`**

In `history.html`, find the `openDetail` function. After the lines that render decisions and actions (the calls to `renderDecisions` and `renderActions`), add:

```javascript
        // Transcript
        const transcript = meeting.transcript || '';
        const transcriptSection = document.getElementById('transcript-section');
        const transcriptText = document.getElementById('transcript-text');
        const transcriptToggle = document.getElementById('transcript-toggle');
        const transcriptBody = document.getElementById('transcript-body');
        if (transcript) {
          transcriptSection.style.display = 'block';
          transcriptText.textContent = transcript;
          transcriptToggle.setAttribute('aria-expanded', 'false');
          transcriptBody.style.display = 'none';
        } else {
          transcriptSection.style.display = 'none';
        }
```

- [ ] **Step 4: Wire up the toggle**

In the `init` function (near the bottom of the `<script>` block, where other event listeners are registered such as `document.getElementById('back-btn').addEventListener(...)`), add:

```javascript
      document.getElementById('transcript-toggle').addEventListener('click', () => {
        const toggle = document.getElementById('transcript-toggle');
        const body = document.getElementById('transcript-body');
        const expanded = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', String(!expanded));
        body.style.display = expanded ? 'none' : 'block';
      });
```

- [ ] **Step 5: Verify manually**

Open `history.html` in a browser (with the server running and at least one meeting saved). Click 查看 on a meeting. Confirm:
- "逐字稿 ▶" section appears above 決議事項
- Clicking it expands to show the full transcript text
- Clicking again collapses it
- The ▶ icon rotates to point down when expanded
- If a meeting has no transcript, the section is hidden entirely

- [ ] **Step 6: Commit**

```bash
git add history.html
git commit -m "feat: add collapsible transcript section to history detail view"
```
