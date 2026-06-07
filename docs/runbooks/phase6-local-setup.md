# Phase 6 本地啟動（MCP + RAG）

## 大綱

1. 適用範圍
2. 前置需求
3. 環境變數
4. 啟動後端服務
5. 啟動 MCP Server
6. Gemini API 調用路徑
7. 快速驗證
8. 常見問題

---

## 1) 適用範圍

本文件用於 Phase 6.5 本地接線，目前已可用工具：

- `task_comment_summary(task_id)`（RAG-A / 6.2）
- `group_snapshot(group_id)`（RAG-B / 6.3）

`weekly_review(user_id, week)` 會在 Phase 6.4 API 完成後再接入。

---

## 2) 前置需求

- Windows PowerShell
- Python 3.10+
- Docker Desktop
- 專案既有 PostgreSQL 本地啟動流程可正常使用

---

## 3) 環境變數

### 3.1 後端（`backend/.env.local`）

最小建議設定：

```env
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
GOOGLE_API_KEY=your-google-api-key
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/prajekt
AI_PROVIDER=gemini
AI_MODEL=gemini-2.0-flash
```

### 3.2 MCP（根目錄 `.env.local`）

MCP Server 會從根目錄的 `.env.local` 讀取認證設定。

可選 token 模式或帳密模式。

模式 A：token（最簡單）

```env
PRAJEKT_API_BASE_URL=http://127.0.0.1:5000/api
PRAJEKT_ACCESS_TOKEN=<access-token>
PRAJEKT_TIMEOUT_SEC=30
```

模式 B：帳密（長時段開發較方便）

```env
PRAJEKT_API_BASE_URL=http://127.0.0.1:5000/api
PRAJEKT_EMAIL=<your-login-email>
PRAJEKT_PASSWORD=<your-login-password>
PRAJEKT_TIMEOUT_SEC=30
```

⚠️ **重要**：`mcp_server.py` 會自動讀取根目錄的 `.env.local`，無須其他步驟。

---

## 4) 啟動後端服務

在專案根目錄：

```powershell
scripts\dev\bootstrap_pg_local.bat
```

若已初始化過：

```powershell
scripts\dev\start_all.bat
```

健康檢查：

- 開啟 `http://127.0.0.1:5000/api/health`
- 預期回傳 `status: ok`

---

## 5) 啟動 MCP Server

若尚未安裝依賴：

```powershell
cd backend
venv\Scripts\pip install -r requirements.txt
cd ..
```

啟動 MCP：

```powershell
python mcp_server.py
```

目前使用 `FastMCP` 預設 stdio transport。

如果你目前沒有 MCP 主機，可直接用 Inspector 當主機：

```powershell
scripts\dev\start_mcp_inspector.bat
```

Inspector 會啟動 Web UI，並連線 `mcp_server.py` 讓你直接測試工具。

---

## 6) Gemini API 調用路徑

可以，現在已可透過 Gemini API 調用，流程如下：

1. MCP 工具被呼叫（`task_comment_summary` 或 `group_snapshot`）
2. `mcp_server.py` 轉呼叫既有後端 API
3. 後端 `services/ai_provider.py` 依 `AI_PROVIDER=gemini` 使用 Gemini
4. Gemini 回傳結果後，由後端回應給 MCP

也就是：MCP 本身不直接呼叫 Gemini，而是透過後端既有 AI Provider 抽象層，確保與目前 6.2/6.3 行為一致。

補充：前端不用改呼叫 API。前端本來就該走 `http://localhost:5000/api`，MCP 是給外部 AI 主機（例如 Inspector、Claude Desktop）使用的平行入口。

---

## 7) 快速驗證

預期行為：

1. `task_comment_summary(task_id)`
- 呼叫 `POST /api/tasks/{task_id}/ai-comment-summary`
- 取得 `decisions`、`risks`、`next_actions`

2. `group_snapshot(group_id)`
- 呼叫 `POST /api/groups/{group_id}/ai-snapshot`
- 可處理同步（200）與非同步（202）
- 非同步模式會輪詢 `/api/groups/snapshot-jobs/{job_id}`

---

## 8) 常見問題

1. `缺少認證設定`
- 請設定 `PRAJEKT_ACCESS_TOKEN`，或 `PRAJEKT_EMAIL` + `PRAJEKT_PASSWORD`。

2. `API 呼叫失敗（401）`
- Token 過期或帳密錯誤，重新登入後重試。

3. `AI 服務配置不完整`
- 檢查後端 `GOOGLE_API_KEY`、`AI_PROVIDER`、`AI_MODEL`。

4. `group snapshot timeout`
- 增加 `timeout_sec`，或稍後查最新快照。
