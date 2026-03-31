# 會議標籤與分類 Design Spec

## Goal

為每場會議加上「分類」（單選、ID 穩定）和「標籤」（多選、自由字串），支援從列表卡片快速標記，並能點擊標籤 / 分類即時篩選列表。設計上預留未來跨會議依分類彙整資訊的可擴充性。

---

## Data Model

### `categories.json`（專案根目錄）

```json
[
  { "id": "cat-1", "name": "週會" },
  { "id": "cat-2", "name": "產品" },
  { "id": "cat-3", "name": "一對一" },
  { "id": "cat-4", "name": "全員會議" }
]
```

- 不存在時自動建立並寫入上述 4 個預設值
- ID 格式：`cat-{uuid[:8]}`（新增時產生）

### Meeting JSON（新增欄位）

```json
{
  "id": "2026-03-29_11-06",
  "created_at": "...",
  "transcript": "...",
  "decisions": [...],
  "action_items": [...],
  "category_id": "cat-2",
  "tags": ["Q2", "UI改版"]
}
```

- `category_id`：字串或 `null`（未分類）
- `tags`：字串陣列，預設 `[]`
- 舊會議無此欄位，讀取時視為 `null` / `[]`，不需要 migration

---

## API

### 分類管理

| 方法 | 路徑 | 說明 |
|---|---|---|
| `GET` | `/categories` | 取得所有分類，回傳 `{"categories": [...]}` |
| `POST` | `/categories` | 新增分類，body `{"name": "xxx"}`，回傳新物件 |
| `DELETE` | `/categories/{id}` | 刪除分類，回傳 `{"status": "deleted"}` 或 404 |

### 會議標籤更新

| 方法 | 路徑 | 說明 |
|---|---|---|
| `PATCH` | `/meetings/{meeting_id}/tags` | 更新 `category_id` 和/或 `tags`，兩欄位都 optional |

`PATCH /meetings/{id}/tags` request body：
```json
{ "category_id": "cat-2", "tags": ["Q2", "UI改版"] }
```
只傳其中一個欄位則只更新該欄位，另一個保持不變。

---

## Backend（storage.py）

新增函式：

- `load_categories() -> list[dict]`：讀 `categories.json`；不存在時建立並回傳預設 4 個
- `save_categories(categories: list[dict]) -> None`：寫入 `categories.json`
- `add_category(name: str) -> dict`：產生 ID、append、儲存，回傳新物件
- `delete_category(cat_id: str) -> bool`：移除後儲存；找不到回傳 `False`
- `update_meeting_tags(meeting_id: str, updates: dict) -> dict | None`：更新 meeting 的 `category_id` / `tags`；meeting 不存在回傳 `None`

`update_meeting_tags` 只允許更新 `category_id` 和 `tags` 兩個欄位（whitelist），其餘欄位忽略。

---

## Frontend（history.html）

### 卡片顯示

- 卡片底部加一排 chips：分類（藍色）+ 標籤（灰色）
- 若無分類與標籤，不顯示 chips 列
- 每個 chip 可點擊，點擊後觸發該維度的篩選

### 快速標記 Popover

- 卡片右上角「＋ 標籤」按鈕，點擊打開 popover
- Popover 內容：
  - **分類區**：所有分類 chips，單選，已選的高亮；「＋ 新增分類…」觸發 inline 輸入框新增
  - **標籤區**：過去用過的標籤 chips（多選），輸入框可新增新標籤（Enter 送出）
- 點 popover 外部或 Esc 關閉，自動儲存（`PATCH /meetings/{id}/tags`）
- 一次只能有一個 popover 開著

### 篩選

- 點卡片上的分類 chip：篩選同分類的所有會議，分類 chip 高亮
- 點卡片上的標籤 chip：篩選含該標籤的所有會議，標籤 chip 高亮
- 再次點同一個 chip：取消篩選，恢復完整列表
- 搜尋與篩選可同時作用（AND 邏輯）：搜尋結果中再依標籤過濾
- 篩選狀態為純前端，不呼叫新 API（對現有 `allMeetings` 陣列 filter）

### 搜尋整合

搜尋（`GET /meetings/search`）不搜分類名稱（meeting 只存 ID），只搜逐字稿 / 決議 / 待辦。搜尋結果顯示時，標籤 chips 仍正常顯示，可點擊進一步篩選。

---

## Testing

### test_storage.py

- `test_load_categories_returns_defaults`：`categories.json` 不存在時回傳 4 個預設值
- `test_load_categories_returns_saved`：儲存後再讀取一致
- `test_add_category_returns_new_item`：id 格式正確、name 正確
- `test_add_category_persists`：新增後 load 看得到
- `test_delete_category_returns_true`：刪除成功
- `test_delete_category_missing_returns_false`
- `test_update_meeting_tags_persists`：更新後 load 確認 category_id + tags
- `test_update_meeting_tags_partial_category_only`：只傳 category_id，tags 不變
- `test_update_meeting_tags_partial_tags_only`：只傳 tags，category_id 不變
- `test_update_meeting_tags_missing_meeting_returns_none`

### test_server.py

- `test_get_categories_returns_list`
- `test_post_category_adds_item`
- `test_delete_category_success`
- `test_delete_category_not_found`
- `test_patch_meeting_tags_success`
- `test_patch_meeting_tags_not_found`
