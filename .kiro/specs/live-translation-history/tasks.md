# 實作任務清單

**功能：** live-translation-history
**產生日期：** 2026-04-13
**需求覆蓋：** FR-1.1 ~ FR-6.3（共 23 項）

---

## 任務概覽

| 階段 | 任務數 | 預估時間 |
|------|--------|----------|
| 1. 後端儲存模組 | 4 | 3-4 小時 |
| 2. 後端 REST API | 5 | 3-4 小時 |
| 3. 即時辨識管道 | 4 | 4-5 小時 |
| 4. WebSocket 端點 | 3 | 2-3 小時 |
| 5. 前端類型與 API | 3 | 2-3 小時 |
| 6. 前端 Composables | 3 | 2-3 小時 |
| 7. 前端頁面元件 | 5 | 4-5 小時 |
| 8. 整合與測試 | 3 | 3-4 小時 |
| **總計** | **30** | **24-31 小時** |

---

## 1. 後端儲存模組

**需求覆蓋：** FR-1.1, FR-1.3, FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-6.2

### 1.1 建立翻譯場次資料模型與儲存結構 (P)

- [x] 建立 `translation_storage.py` 模組，定義 `Sentence` 和 `Translation` dataclass
- [x] 實作 ID 產生邏輯（格式 `T-001`，自動遞增）
- [x] 建立 `translations/` 和 `audio/` 目錄結構
- [x] 實作 `save()` 和 `load()` 函式，處理 JSON 序列化

**驗收標準：** 可建立、儲存、讀取翻譯場次 JSON 檔案 ✅

### 1.2 實作列表查詢與篩選功能 (P)

- [x] 實作 `list_translations()` 函式，支援分頁（預設每頁 8 筆）
- [x] 實作狀態篩選（in_progress / completed / interrupted）
- [x] 實作語言對篩選（source_lang / target_lang）
- [x] 實作名稱關鍵字搜尋

**驗收標準：** 可依各種條件篩選並分頁列出翻譯場次 ✅

### 1.3 實作更新與刪除功能 (P)

- [x] 實作 `update_name()` 函式
- [x] 實作 `delete()` 函式，同時刪除對應音訊檔
- [x] 實作 `append_sentence()` 函式，用於即時新增句子
- [x] 實作 `update_sentence_translation()` 函式，用於更新譯文

**驗收標準：** 可更新場次名稱、刪除場次（含音訊）、新增/更新句子 ✅

### 1.4 撰寫儲存模組單元測試

- [x] 測試 ID 產生邏輯的唯一性與格式
- [x] 測試 CRUD 操作的正確性
- [x] 測試篩選與分頁邏輯
- [x] 測試刪除時音訊檔連動清除

**驗收標準：** 測試覆蓋率 ≥ 80% ✅ (97%)

---

## 2. 後端 REST API

**需求覆蓋：** FR-1.1, FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-4.1, FR-4.2, FR-5.1, FR-5.2, FR-5.3, FR-6.1, FR-6.2, FR-6.3

### 2.1 實作場次啟動端點

- [x] 新增 `POST /api/translations/start` 端點
- [x] 檢查是否已有 `in_progress` 場次，若有回傳 `409 Conflict`
- [x] 建立新場次並回傳 ID
- [x] 設定初始狀態為 `in_progress`

**驗收標準：** 可啟動新場次，並發限制生效 ✅

### 2.2 實作列表與詳情端點 (P)

- [x] 新增 `GET /api/translations` 端點，支援 page, limit, status, source_lang, target_lang, q 參數
- [x] 新增 `GET /api/translations/{id}` 端點，回傳完整場次資料含 sentences
- [x] 新增 `PATCH /api/translations/{id}` 端點，支援更新 name

**驗收標準：** 可列出、查詢、更新翻譯場次 ✅

### 2.3 實作刪除端點 (P)

- [x] 新增 `DELETE /api/translations/{id}` 端點
- [x] 呼叫 storage 的 delete 函式，連動刪除音訊
- [x] 回傳適當的成功/失敗狀態

**驗收標準：** 可刪除場次及對應音訊檔 ✅

### 2.4 實作音訊下載端點

- [x] 新增 `GET /api/translations/{id}/audio` 端點
- [x] 驗證場次存在且有音訊檔
- [x] 以 StreamingResponse 回傳音訊檔
- [x] 若場次為 `in_progress` 或無音訊，回傳 `404`

**驗收標準：** 可下載已完成場次的音訊檔 ✅

### 2.5 實作 DOCX 匯出端點

- [x] 新增 `GET /api/translations/{id}/export/docx` 端點
- [x] 產生包含場次資訊與逐句對照的 DOCX 檔案
- [x] 信心分數低於 0.65 的句子加底色標示
- [x] 以 StreamingResponse 回傳檔案

**驗收標準：** 可匯出含格式標記的 DOCX 檔案 ✅

---

## 3. 即時辨識管道

**需求覆蓋：** FR-1.2, FR-1.4, FR-2.1, FR-2.2, FR-2.3

### 3.1 建立即時翻譯器模組框架

- [x] 建立 `live_translator.py` 模組
- [x] 定義 `LiveTranslator` 類別與 callback 型別
- [x] 實作 `start()` 方法，初始化場次狀態
- [x] 實作 `stop()` 方法，完成場次並儲存音訊

**驗收標準：** 可建立 LiveTranslator 實例並管理場次生命週期 ✅

### 3.2 實作音訊緩衝與轉換邏輯

- [x] 新增 pydub 依賴
- [x] 實作音訊 buffer 累積邏輯（累積至 ≥3 秒）
- [x] 實作 WebM → WAV 格式轉換
- [x] 實作完整音訊檔儲存（錄音結束時）

**驗收標準：** 可接收 WebM chunks、轉換為 WAV、儲存完整音訊 ✅

### 3.3 整合 ASR 辨識引擎

- [x] 整合現有 faster-whisper 模型（共用 `_whisper_model`）
- [x] 實作 `process_audio()` 方法，處理轉換後的 WAV
- [x] 擷取辨識結果與信心分數（從 `avg_logprob` 轉換）
- [x] 偵測來源語言並記錄

**驗收標準：** 可辨識音訊並取得文字、信心分數、語言 ✅

### 3.4 整合翻譯引擎

- [x] 整合現有 Ollama 翻譯（參考 `analyzer.py` 模式）
- [x] 實作非同步翻譯，辨識完成後觸發
- [x] 透過 callback 回傳翻譯結果
- [x] 處理翻譯逾時，保留原文

**驗收標準：** 可將辨識結果翻譯為目標語言 ✅

---

## 4. WebSocket 端點

**需求覆蓋：** FR-2.4

### 4.1 實作 WebSocket 連線管理

- [x] 新增 `@app.websocket("/api/translations/{id}/stream")` 端點
- [x] 驗證場次 ID 存在且狀態為 `in_progress`
- [x] 實作連線建立與關閉處理
- [x] 實作錯誤處理與異常斷線

**驗收標準：** 可建立 WebSocket 連線並正確管理生命週期 ✅

### 4.2 實作音訊接收與訊息推送

- [x] 接收 binary 訊息（音訊 chunks）
- [x] 將音訊傳遞給 LiveTranslator 處理
- [x] 透過 WebSocket 推送 sentence 訊息
- [x] 透過 WebSocket 推送 translation 訊息

**驗收標準：** 可接收音訊、即時推送辨識與翻譯結果 ✅

### 4.3 實作停止與狀態更新

- [x] 接收 text 訊息 `{ "type": "stop" }`
- [x] 呼叫 LiveTranslator.stop() 完成場次
- [x] 推送 `{ "type": "status", "status": "completed" }` 訊息
- [x] 關閉 WebSocket 連線

**驗收標準：** 可正確終止錄音並更新場次狀態 ✅

---

## 5. 前端類型與 API

**需求覆蓋：** 全部（基礎設施）

### 5.1 定義 TypeScript 類型 (P)

- [x] 建立 `frontend/src/types/translation.ts`
- [x] 定義 `Sentence`, `Translation`, `TranslationListItem`, `TranslationStatus` 類型
- [x] 定義 `PaginatedTranslations` 回應類型

**驗收標準：** 所有翻譯相關類型定義完成，無 `any` 使用 ✅

### 5.2 實作翻譯 API 客戶端 (P)

- [x] 建立 `frontend/src/api/translations.ts`
- [x] 實作 `startTranslation()`, `listTranslations()`, `getTranslation()` 函式
- [x] 實作 `updateTranslationName()`, `deleteTranslation()` 函式
- [x] 實作 `getAudioUrl()`, `getExportUrl()` 輔助函式

**驗收標準：** 所有 REST API 有對應的 typed 客戶端函式 ✅

### 5.3 設定路由 (P)

- [x] 在 `router/index.ts` 新增 `/live-translate` 路由
- [x] 新增 `/translation-history` 路由
- [x] 新增 `/translation/:id` 路由（詳情頁）

**驗收標準：** 三個新頁面路由可正常訪問 ✅

---

## 6. 前端 Composables

**需求覆蓋：** FR-1.1, FR-1.2, FR-2.4, FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-4.1, FR-4.2, FR-6.1

### 6.1 實作 useTranslations Composable (P)

- [x] 建立 `frontend/src/composables/useTranslations.ts`
- [x] 實作 `list()`, `get()`, `updateName()`, `remove()` 方法
- [x] 管理 `translations`, `total`, `currentPage`, `loading`, `error` 狀態
- [x] 實作篩選參數處理

**驗收標準：** 可透過 composable 操作翻譯場次 CRUD ✅

### 6.2 實作 useLiveTranslate Composable

- [x] 建立 `frontend/src/composables/useLiveTranslate.ts`
- [x] 實作 WebSocket 連線管理
- [x] 實作 `start()`, `stop()`, `sendAudioChunk()` 方法
- [x] 管理 `sentences`, `status`, `error`, `sourceLanguage` 狀態
- [x] 整合現有 `useAudioRecorder`，擴充支援 timeslice 模式

**驗收標準：** 可透過 composable 控制即時錄音與接收辨識結果 ✅

### 6.3 實作 WebSocket 重連邏輯

- [x] 偵測連線斷開事件
- [x] 實作自動重連（最多 3 次，間隔遞增）
- [x] 重連期間顯示狀態提示
- [x] 重連失敗後更新 error 狀態

**驗收標準：** WebSocket 斷線後可自動重連 ✅

---

## 7. 前端頁面元件

**需求覆蓋：** FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-4.1, FR-4.2, FR-4.3, FR-4.4, FR-4.5, FR-6.3

### 7.1 實作即時翻譯操作頁

- [x] 建立 `frontend/src/views/LiveTranslateView.vue`
- [x] 實作開始/停止錄音按鈕
- [x] 即時顯示辨識與翻譯結果列表
- [x] 顯示錄音時長與狀態指示器
- [x] 錄音結束後提供跳轉到詳情頁的連結

**驗收標準：** 可操作即時錄音並看到即時辨識結果 ✅

### 7.2 實作歷史列表頁

- [x] 建立 `frontend/src/views/TranslationHistoryView.vue`
- [x] 實作篩選條件（狀態、語言對、關鍵字）
- [x] 實作分頁控制（每頁 8 筆）
- [x] 顯示場次卡片列表

**驗收標準：** 可瀏覽、篩選、分頁翻譯場次列表 ✅

### 7.3 實作場次卡片元件

- [x] 建立 `frontend/src/components/translation/TranslationCard.vue`
- [x] 顯示場次基本資訊（ID、名稱、時間、語言對、句數、狀態）
- [x] 實作操作按鈕（檢視、音訊下載、匯出）
- [x] 音訊下載按鈕依狀態停用

**驗收標準：** 卡片正確顯示資訊，按鈕狀態正確 ✅

### 7.4 實作詳情頁

- [x] 建立 `frontend/src/views/TranslationDetailView.vue`
- [x] 實作摘要卡片列（總時長、語言對、句數、平均信心）
- [x] 實作頁面頂部（返回、名稱編輯、音訊/匯出按鈕）

**驗收標準：** 可查看場次詳情與摘要資訊 ✅

### 7.5 實作逐句對照表元件

- [x] 建立 `frontend/src/components/translation/SentenceTable.vue`
- [x] 顯示句序、時間戳、原文、譯文、信心分數
- [x] 實作信心分數色條（綠/橘/紅）
- [x] 實作關鍵字搜尋篩選
- [x] 實作分頁（每頁 20 句）

**驗收標準：** 可瀏覽、搜尋、分頁逐句對照表 ✅

---

## 8. 整合與測試

**需求覆蓋：** 全部

### 8.1 導航整合

- [x] 在現有 `index.html` 或 `App.vue` 加入導航連結
- [x] 新增「即時翻譯」入口，與「會議紀錄」並列
- [x] 確保導航樣式與現有系統一致

**驗收標準：** 使用者可從任意頁面導航至即時翻譯功能 ✅

### 8.2 後端整合測試

- [x] 撰寫 REST API 整合測試（pytest + httpx）
- [x] 撰寫 WebSocket 端點測試（pytest + websockets）
- [x] 測試完整錄音流程（啟動 → 串流 → 停止 → 查詢）

**驗收標準：** 後端測試覆蓋率 ≥ 80% ✅ (116 tests passing)

### 8.3 端對端測試

- [x] 撰寫 Playwright E2E 測試
- [x] 測試即時錄音完整流程
- [x] 測試列表篩選與分頁
- [x] 測試詳情頁與匯出功能

**驗收標準：** 關鍵使用者流程 E2E 測試通過 ✅

---

## 需求追溯

| 需求 ID | 任務 |
|---------|------|
| FR-1.1 | 1.1, 2.1, 6.2, 7.1 |
| FR-1.2 | 3.1, 4.3, 6.2, 7.1 |
| FR-1.3 | 1.1, 3.1 |
| FR-1.4 | 3.2, 3.1 |
| FR-2.1 | 3.3 |
| FR-2.2 | 3.4 |
| FR-2.3 | 3.3 |
| FR-2.4 | 4.1, 4.2, 6.2 |
| FR-3.1 | 1.2, 2.2, 6.1, 7.2 |
| FR-3.2 | 1.2, 2.2, 7.2 |
| FR-3.3 | 1.2, 2.2, 7.2 |
| FR-3.4 | 1.2, 2.2, 7.2 |
| FR-4.1 | 7.4 |
| FR-4.2 | 7.5 |
| FR-4.3 | 7.5 |
| FR-4.4 | 7.5 |
| FR-4.5 | 7.5 |
| FR-5.1 | 2.5 |
| FR-5.2 | 2.5 |
| FR-5.3 | 2.5 |
| FR-6.1 | 2.4, 7.3 |
| FR-6.2 | 1.3, 2.3 |
| FR-6.3 | 7.3 |

---

## 並行開發建議

以下任務可同時進行（標記 `(P)`）：

| 並行群組 | 任務 | 說明 |
|----------|------|------|
| A | 1.1, 1.2, 1.3 | 儲存模組各功能獨立 |
| B | 2.2, 2.3 | 列表與刪除 API 獨立 |
| C | 5.1, 5.2, 5.3 | 前端基礎設施 |
| D | 6.1 | 與後端 API 完成後可並行 |
| E | 7.2, 7.3 | 列表頁元件 |

**關鍵依賴路徑：**
```
1.1-1.3 → 2.1-2.5 → 4.1-4.3
              ↓
         3.1-3.4 → 4.1-4.3

5.1-5.3 → 6.1-6.3 → 7.1-7.5
```
