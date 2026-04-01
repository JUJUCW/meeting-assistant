# 匯出功能設計文件

**日期：** 2026-03-29
**狀態：** 已核准

---

## 目標

讓使用者從 history.html 的會議詳情頁，將單筆會議記錄下載為 Markdown（供人閱讀備份）或 JSON（供系統備份）。

---

## 範圍

- **匯出格式：** Markdown (.md) 和 JSON (.json)
- **匯出粒度：** 單筆會議（從會議詳情頁觸發）
- **實作位置：** 純前端（history.html），不新增後端 API

---

## UI

在 history.html 會議詳情區塊的標題列，於刪除按鈕旁新增兩個按鈕：

```
[ 2026-03-29_14-30 ]  [匯出 MD]  [匯出 JSON]  [刪除]
```

點擊後瀏覽器直接下載對應檔案，檔名格式：
- `meeting-{meeting_id}.md`
- `meeting-{meeting_id}.json`

---

## Markdown 格式

```markdown
# 會議記錄 YYYY-MM-DD HH:MM

**建立時間：** {created_at}

---

## 逐字稿

{transcript 全文，移除換行符號，單行呈現}

---

## 決議事項

| # | 決議內容 | 依據 | 相關人員 | 狀態 |
|---|---|---|---|---|
| d-1 | ... | ... | 小明, 小花 | confirmed |

---

## 待辦事項

| # | 事項 | 負責人 | 截止日期 | 優先順序 | 狀態 |
|---|---|---|---|---|---|
| a-1 | ... | 小明 | 2026-04-01 | high | pending |
```

**逐字稿處理：** `meeting.transcript.replace(/\n/g, '')` 移除所有換行，單行呈現。時間戳記不在本版本範圍內，留待 segments 儲存功能完成後再加。

**related_people 陣列：** 以 `, ` 串接為字串。空陣列顯示為 `—`。空字串欄位（assignee、deadline）顯示為 `—`。

**空清單處理：** decisions 或 action_items 為空陣列時，該 section 顯示 `（無）`，不產生表格。

---

## JSON 格式

直接使用 `JSON.stringify(meeting, null, 2)`，輸出當前 meeting 物件的完整內容（含 id、created_at、transcript、decisions、action_items）。

---

## 實作

**新增兩個函式於 history.html：**

```javascript
function exportMarkdown(meeting) {
  // 組合 Markdown 字串
  // 建立 Blob('text/markdown') → <a> download → click() → revoke
}

function exportJson(meeting) {
  // JSON.stringify(meeting, null, 2)
  // 建立 Blob('application/json') → <a> download → click() → revoke
}
```

**觸發：** 在 `openDetail(meeting)` 渲染會議詳情時，將 meeting 物件綁定至兩個匯出按鈕的 click handler。

**無新 API、無新檔案、無後端變更。**

---

## 測試要點

- 匯出 Markdown：逐字稿為單行、決議表格欄位正確、空欄位顯示 `—`
- 匯出 JSON：可被 `JSON.parse` 解析、內容與 storage 中的 meeting 一致
- 檔名含正確的 meeting_id
- 無決議或無待辦時，對應 section 顯示「（無）」而非空表格

---

## 不在範圍

- 全部會議批次匯出
- PDF 格式
- 逐字稿時間戳記（待 segments 儲存功能完成後再加）
- 匯入功能
