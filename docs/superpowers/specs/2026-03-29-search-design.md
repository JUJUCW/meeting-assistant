# 搜尋功能設計文件

**日期：** 2026-03-29
**狀態：** 已核准

---

## 目標

讓使用者在 history.html 的會議列表頁，輸入關鍵字即時過濾會議，並在卡片上顯示命中位置的上下文片段。

---

## 範圍

- **搜尋欄位：** 逐字稿 (`transcript`)、決議內容 (`decisions[].content`)、決議依據 (`decisions[].rationale`)、待辦事項內容 (`action_items[].content`)、待辦負責人 (`action_items[].assignee`)
- **搜尋方式：** 全文關鍵字，大小寫不分（substring match）
- **觸發方式：** 即時搜尋，debounce 300ms
- **實作位置：** `storage.py`（搜尋函式）、`server.py`（API 端點）、`history.html`（UI）

---

## 架構

```
storage.py           → search_meetings(query) 函式
server.py            → GET /meetings/search?q=... 端點
history.html         → 搜尋框 + debounce + 片段渲染
tests/test_storage.py → search 測試
```

前端輸入關鍵字 → debounce 300ms → 呼叫 API → 後端掃描所有 JSON 檔 → 回傳符合會議 + 命中片段 → 前端過濾列表並顯示片段。

空白關鍵字：前端直接還原 `renderList(allMeetings)`，不呼叫 API。

---

## 後端

### `storage.search_meetings(query: str) -> list[dict]`

- `query` 為空字串時回傳 `[]`
- 大小寫不分：`query.lower()` 比對
- 掃描所有 `meetings/*.json`，損毀檔案跳過（同 `list_meetings`）
- 每筆會議依序比對以下欄位群組，每群組最多 1 個命中片段：
  1. `transcript`（整段文字）
  2. `decisions`：對每筆決議比對 `content` 與 `rationale`，取第一個命中
  3. `action_items`：對每筆待辦比對 `content` 與 `assignee`，取第一個命中
- 至少有一個命中才加入結果
- 片段擷取：命中位置前後各 30 字元，頭尾補 `…`（若已在開頭/結尾則不補）

**回傳格式：** 與 `list_meetings()` 相同欄位，額外加 `hits` 陣列：

```json
{
  "id": "2026-03-28_14-30",
  "created_at": "2026-03-28T14:30:00",
  "decision_count": 1,
  "action_item_count": 1,
  "pending_action_item_count": 1,
  "hits": [
    { "field": "transcript", "snippet": "…今天決定採用新系統，效率…" },
    { "field": "decisions",  "snippet": "採用新系統" }
  ]
}
```

`field` 值：`"transcript"` | `"decisions"` | `"action_items"`

### `GET /meetings/search?q=...`

- `q` 空字串 → 回傳 `{"meetings": []}`
- 正常搜尋 → 回傳 `{"meetings": [...]}`，順序同 `search_meetings` 回傳（以 `created_at` 降冪，由 `storage` 排序）

---

## 前端

### HTML 結構

在 `#list-view` 的標題區塊下方、`#meeting-list` 上方新增搜尋框：

```html
<div id="search-bar" style="margin-bottom:20px;">
  <input class="form-input" type="text" id="search-input"
         placeholder="搜尋逐字稿、決議、待辦…" style="width:100%;box-sizing:border-box;">
</div>
```

### JS 行為

- 監聽 `#search-input` 的 `input` 事件，debounce 300ms
- `query.trim()` 為空 → `renderList(allMeetings)`，清除 empty-state 自訂訊息
- 非空 → 呼叫 `GET /meetings/search?q=<query>`，以結果呼叫 `renderSearchResults(meetings)`
- 無結果 → empty-state 顯示「找不到符合「{query}」的會議記錄」

### 卡片上的 hits 顯示

`renderSearchResults(meetings)` 與 `renderList(meetings)` 基本相同，差別在：若該會議有 `hits` 陣列，在 badges 下方新增 hits 區塊：

```html
<div class="search-hits">
  <div class="search-hit">逐字稿：「…今天決定採用新系統…」</div>
  <div class="search-hit">決議：「採用新系統」</div>
</div>
```

`field` 對應中文：`transcript` → 逐字稿、`decisions` → 決議、`action_items` → 待辦

**樣式：** `font-size: 12px`，顏色比 badges 偏暗（`color: #888`），`letter-spacing: 0.04em`。

---

## 不在範圍

- 關鍵字高亮（片段中的關鍵字不標色）
- 多關鍵字 AND/OR 邏輯
- 日期範圍篩選
- 搜尋歷史記錄

---

## 測試要點

- `search_meetings` 能在 transcript 中找到關鍵字
- `search_meetings` 能在 decisions 中找到關鍵字
- `search_meetings` 能在 action_items 中找到關鍵字
- 大小寫不分
- 無命中時回傳空清單
- 空字串 query 回傳空清單
- 片段長度正確（含前後各 30 字元上限）
- 損毀檔案不影響其他結果
