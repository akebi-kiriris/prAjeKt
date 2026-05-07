refactor: 後端錯誤契約統一、資料層收斂與前端錯誤處理工程化

## 這次做了什麼

### 1) 後端錯誤回應格式全域統一
- 新增 `backend/blueprints/validation.py`，集中：
  - `validate_payload_or_400`
  - `error_response`
  - `error_from_exception`
  - `status_to_error_code`
- 將 blueprint 錯誤輸出統一為相容 envelope：
  - `error`（人類可讀訊息）
  - `error_code`（前端流程判斷主鍵）
  - `error_details`（可選）
- 套用到 auth / tasks / timelines / groups / todos / trash / profile / knowledge / notifications / messages / copilot / guards 等路由層

### 2) 分層邊界持續收斂（Service -> Repository）
- 延續既有架構方向，將 service 中資料庫操作進一步下沉到 repository
- 專注 task / timeline 相關流程，讓 route/service/query 責任邊界更清楚

### 3) 前端錯誤處理共用化
- 新增 `frontend/src/utils/apiError.ts`：
  - `getApiErrorMessage`
  - `getApiErrorCode`
  - `mapErrorCodeToMessage`
  - `shouldRedirectToLogin`
- 多個頁面與 store 改為共用錯誤解析，移除重複的 `axios.response?.data?.error` 手寫邏輯
  - TasksView / TimelinesView / TimelineDetailDialog / KnowledgeBaseView
  - GroupsView / TrashView / ProfileView / RegisterView
  - auth store
- `frontend/src/services/api.ts` 攔截器補上 `UNAUTHORIZED` error_code 對齊 refresh/login flow

### 4) 契約文件與工程文檔同步
- 新增/更新 `docs/API_錯誤碼表.md`：
  - 統一錯誤碼表
  - 前端建議行為
  - 建議文案對照
- 更新重構與追蹤文件（`docs/` 與根目錄雙份同步）：
  - `重構計畫.md`
  - `進度追蹤.md`
- 更新 `README.md`：補充錯誤碼契約與共用處理策略

### 5) 其他
- `.gitignore` 加入 upload 目錄相關忽略

## 驗證
- 後端：先前全量回歸 `189 passed`
- 前端：目標測試於本機可通過（3 files / 9 tests）；部分環境有 `spawn EPERM` 啟動限制，屬環境問題非邏輯回歸

## 影響與收益
- API 錯誤契約穩定化：前後端可用 `error_code` 做一致分流
- 程式碼維護成本下降：錯誤處理與驗證邏輯集中化
- 分層清晰度提升：查詢責任回歸 repository，service 專注業務規則
- 文檔可落地：前端可直接依錯誤碼表實作 UI 行為
