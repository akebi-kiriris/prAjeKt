# backend/blueprints

這層是 HTTP 入口。主要責任是接收 request、做路由與權限邊界處理、呼叫 service，最後回傳 API response。

## 常見檔案

- `tasks.py`, `timelines.py`, `groups.py`, `knowledge.py`: 各功能路由
- `copilot.py`: Copilot / Agent 相關 API 入口
- `auth.py`: 登入與驗證相關路由
- `guards.py`: 存取控制輔助
- `validation.py`: API 層輸入驗證與錯誤轉換輔助

## 這層應該負責什麼

- request 解析
- route-level 權限檢查
- 呼叫 service
- 把例外轉成穩定的 HTTP response

## 不應該放什麼

- 深層商業邏輯
- repository 查詢細節
- Agent graph 內部流程

## 修改判斷

- API 參數來源、HTTP status code、response shape 有變動：先看這層
- 如果只是業務規則改變，不要把邏輯直接塞在 blueprint，應回到 service
- Copilot / agent request 的 route 邊界、operator/user context 傳遞，優先看 `copilot.py`
