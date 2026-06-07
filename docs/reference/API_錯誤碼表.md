# API 錯誤碼表（Error Envelope）

這份文件對應目前後端 blueprint 統一後的錯誤格式，供前端直接依 `error_code` 做 UI 行為分流。

## 回應格式

錯誤回應（相容版）：

```json
{
  "error": "priority 必須是數字",
  "error_code": "VALIDATION_ERROR",
  "error_details": {
    "field": "priority"
  }
}
```

欄位說明：

- `error`: 人類可讀訊息（可直接顯示）
- `error_code`: 穩定錯誤代碼（前端判斷邏輯請優先用這個）
- `error_details`: 可選欄位，放欄位、上下文等細節

## 錯誤碼清單

> 來源：`backend/blueprints/validation.py` 的 `status_to_error_code`

| HTTP Status | error_code            | 用途說明 |
|---|---|---|
| `400` | `BAD_REQUEST` | 請求格式不合法、缺參數、欄位值非法 |
| `400` | `VALIDATION_ERROR` | Pydantic 輸入驗證失敗 |
| `401` | `UNAUTHORIZED` | 未登入、token 無效或過期 |
| `403` | `FORBIDDEN` | 有登入但沒有操作權限 |
| `404` | `NOT_FOUND` | 查無資源 |
| `409` | `CONFLICT` | 資源衝突（例如重複加入） |
| `422` | `UNPROCESSABLE_ENTITY` | 語意正確但內容不可處理 |
| `429` | `RATE_LIMITED` | 觸發頻率限制 |
| `500` | `INTERNAL_ERROR` | 伺服器內部錯誤 |
| `503` | `SERVICE_UNAVAILABLE` | 外部依賴/服務暫時不可用 |
| 其他 | `UNKNOWN_ERROR` | 未映射狀態碼的保底值 |

## 前端建議行為

1. 表單驗證錯誤（`VALIDATION_ERROR` / `BAD_REQUEST`）
   - 顯示 `error` 訊息
   - 若有 `error_details.field`，可高亮對應欄位

2. 權限與登入（`UNAUTHORIZED` / `FORBIDDEN`）
   - `UNAUTHORIZED`：導向登入或觸發 refresh token flow
   - `FORBIDDEN`：保留在頁面並顯示無權限提示

3. 不存在與衝突（`NOT_FOUND` / `CONFLICT`）
   - `NOT_FOUND`：導向列表頁或顯示空狀態
   - `CONFLICT`：顯示可重試或刷新提示

4. 系統錯誤（`INTERNAL_ERROR` / `SERVICE_UNAVAILABLE` / `UNKNOWN_ERROR`）
   - 顯示通用錯誤 toast
   - 允許重試按鈕
   - 可附帶回報追蹤資訊（request id / time）

## 前端建議文案對照（可直接用）

| error_code | 建議文案 |
|---|---|
| `BAD_REQUEST` | 請求內容有誤，請檢查後再試 |
| `VALIDATION_ERROR` | 輸入資料驗證失敗，請檢查欄位 |
| `UNAUTHORIZED` | 登入已失效，請重新登入 |
| `FORBIDDEN` | 你沒有權限執行此操作 |
| `NOT_FOUND` | 找不到指定資源 |
| `CONFLICT` | 資料衝突，請重新整理後再試 |
| `UNPROCESSABLE_ENTITY` | 資料格式正確，但內容無法處理 |
| `RATE_LIMITED` | 操作太頻繁，請稍後再試 |
| `INTERNAL_ERROR` | 伺服器發生錯誤，請稍後再試 |
| `SERVICE_UNAVAILABLE` | 服務暫時不可用，請稍後再試 |
| `UNKNOWN_ERROR` | 發生未知錯誤，請稍後再試 |

## 前端實作建議（最小版）

```ts
type ApiError = {
  error: string;
  error_code?: string;
  error_details?: Record<string, unknown>;
};

function handleApiError(e: ApiError) {
  switch (e.error_code) {
    case "UNAUTHORIZED":
      // 導登入或 refresh
      break;
    case "FORBIDDEN":
      // 顯示無權限
      break;
    case "VALIDATION_ERROR":
    case "BAD_REQUEST":
      // 表單提示
      break;
    default:
      // 通用錯誤
      break;
  }
}
```

目前專案中的共用位置：

- `frontend/src/utils/apiError.ts`
  - `getApiErrorMessage(error, fallback)`
  - `getApiErrorCode(error)`
  - `mapErrorCodeToMessage(errorCode)`
  - `shouldRedirectToLogin(errorCode)`
- `frontend/src/services/api.ts`
  - response interceptor 會在 `UNAUTHORIZED` 或 token 失效時走 refresh/login flow

## 備註

- 目前為「相容過渡格式」：`error` 仍是字串，方便舊前端不改也可運作。
- 新功能請一律以 `error_code` 判斷流程，不要靠 `error` 文案做程式判斷。
