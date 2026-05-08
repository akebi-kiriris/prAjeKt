# API 契約與錯誤處理（Contract Guide）

> 更新日期：2026-05-08  
> 目的：提供前後端共用的契約基準，避免「文案驅動邏輯」。

---

## 1. 成功回應原則

- 成功回應保留既有 domain payload 結構（不做過度包裝）
- mutation 類 API 優先回傳：
  - 變更後資源
  - 或明確 `message` + `id` / `count`

---

## 2. 失敗回應統一格式

```json
{
  "error": "priority 必須是數字",
  "error_code": "VALIDATION_ERROR",
  "error_details": {
    "field": "priority"
  }
}
```

欄位語意：

- `error`：可直接顯示給使用者
- `error_code`：前端流程判斷鍵（穩定）
- `error_details`：欄位或上下文細節（可選）

---

## 3. error_code 建議語意

- `BAD_REQUEST`：請求格式或欄位值不合法
- `VALIDATION_ERROR`：schema 驗證失敗
- `UNAUTHORIZED`：未登入或 token 無效
- `FORBIDDEN`：已登入但無權限
- `NOT_FOUND`：資源不存在
- `CONFLICT`：狀態衝突（重複操作）
- `INTERNAL_ERROR`：伺服器內部錯誤

完整映射與建議文案請見：[API_錯誤碼表.md](./docs/API_錯誤碼表.md)

---

## 4. 前端處理規範

### 4.1 共用入口

- 使用 `frontend/src/utils/apiError.ts`：
  - `getApiErrorMessage`
  - `getApiErrorCode`
  - `mapErrorCodeToMessage`
  - `shouldRedirectToLogin`

### 4.2 流程判斷

1. 先看 `error_code` 做流程分支  
2. 再決定 UI 呈現（toast / inline / redirect）

範例：

- `UNAUTHORIZED`：refresh 失敗後導登入
- `FORBIDDEN`：留在頁面，顯示無權限
- `VALIDATION_ERROR`：欄位提示 + 防止重送

---

## 5. 後端實作規範

- 使用 `backend/blueprints/validation.py` 統一輸出：
  - `error_response`
  - `error_from_exception`
  - `validate_payload_or_400`
- 新增 blueprint 路由時，禁止回退到散落式 `jsonify({'error': ...})`

---

## 6. 契約變更流程（建議）

1. 更新 `types` / `schema`  
2. 更新 `docs/API_錯誤碼表.md` 與本文件  
3. 更新 service / view 呼叫端  
4. 跑對應測試（至少 smoke + 該 domain 測試）
