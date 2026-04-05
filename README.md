# prajekt

基於 Vue 3 + Flask 的專案管理與協作平台，整合 Google Gemini AI 實現智能任務生成。

> **開發狀態**：Phase 1~5.6 已完成 ✅（前端 `85/85`、後端最新回歸 `144 passed`）；Backend CI 已啟用 pytest + coverage 報告，Phase 6 主線為「AI 產品化 + PostgreSQL 開發遷移 + 群組快照」。

## 功能模組

- **專案管理**：卡片 / 看板 / 日曆 / 列表 四種視圖，專案進度追蹤、成員邀請
- **任務管理**：任務 CRUD、子任務、優先級、標籤、狀態拖曳切換、留言討論、附件上傳 / 下載、任務成員指派
- **待辦事項**：個人 Todo 列表，完成狀態管理
- **群組協作**：群組建立 / 邀請碼加入 / 即時聊天（Socket.IO，含 REST fallback）
- **個人資料**：個人資訊編輯、密碼變更、使用統計
- **數據分析儀表板**：整合於個人資料頁，Level 1 個人圖表（30 天完成趨勢、任務狀態分布、各專案任務量）+ Level 2 專案圖表（成員貢獻、任務狀態，負責人限定）
- **AI 任務生成**：自然語言輸入 → AI 工具路由 → MCP 執行，支援批次創建與自動化（MCP Copilot 整合）
- **AI 群組快照（RAG-B 核心）**：群組聊天可生成「行動導向 Digest」（一句重點 / 你現在要做什麼 / 阻塞風險 / 精簡決議）
- **Copilot + MCP 整合**：自然語言 AI 路由至後端工具，無需 Inspector；支援任務知識摘要、群組快照、自動化創建
- **垃圾桶回收機制**：已刪任務 / 專案暫存，支援還原或永久刪除；非建立者唯讀
- **通知系統**：任務指派 / 專案邀請通知、鈴鐺 30 秒輪詢更新、主頁即將到期提醒區塊（3 天內截止或進度 ≥80%）

## 技術架構

| 層級 | 技術 |
|------|------|
| 前端框架 | Vue 3 + Vite（Composition API / `<script setup>`）|
| 狀態管理 | Pinia |
| 路由 | Vue Router |
| HTTP | Axios（含 JWT 自動刷新攔截器）|
| 樣式 | Tailwind CSS |
| UI 元件 | Headless UI（ConfirmDialog）、vue-sonner（Toast）|
| 圖表 | vue-echarts + ECharts 6 |
| 後端 | Flask 3 + SQLAlchemy + Flask-Migrate + Flask-SocketIO |
| 即時通訊 | Socket.IO（flask-socketio / socket.io-client） |
| 認證 | Flask-JWT-Extended（access + refresh token）|
| 資料庫 | PostgreSQL（Supabase + Phase 6 本地遷移主線）/ SQLite（舊環境相容） |
| AI | Google Gemini（Provider 可切換：`gemini` / `mock`）|

## 專案結構

```
prajekt/
├── .github/
│   └── workflows/
│       ├── backend-tests.yml
│       └── frontend-tests.yml
├── backend/
│   ├── app.py                    # Flask 應用入口
│   ├── blueprints/               # Route 層
│   ├── services/                 # Business 層
│   ├── repositories/             # 資料查詢層（2026/04 收斂）
│   ├── models/                   # SQLAlchemy ORM
│   ├── realtime/                 # Socket 事件
│   │   └── socket_events.py
│   ├── tests/                    # pytest
│   ├── migrations/               # Flask-Migrate
│   ├── uploads/                  # 任務附件
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ConfirmDialog.vue
│       │   ├── Header.vue
│       │   ├── Sidebar.vue
│       │   └── timelines/
│       ├── services/             # API 封裝層（含 __tests__）
│       ├── stores/               # Pinia（含 __tests__）
│       ├── composables/
│       ├── utils/
│       ├── types/
│       ├── views/
│       └── router/
│
├── docs/                         # 開發筆記與流程文件（納入版控）
├── scripts/
│   └── count_loc.py
├── 重構計畫.md
└── 進度追蹤.md
```

## 快速本地部署（PostgreSQL 主線）

### 0. 前置需求

- Docker Desktop
- Python 3.10+
- Node.js 18+

### 1. 一鍵初始化 + 啟動（Windows，推薦）

```bat
bootstrap_pg_local.bat
```

此腳本會自動完成：
- 啟動本地 PostgreSQL 容器（`localhost:5433`）
- 套用資料庫 migration（`flask db upgrade`）
- 首次將 SQLite 舊資料遷移到 PostgreSQL（目標已有資料時自動略過）
- 啟動後端與前端開發服務

### 2. 日常啟動（已初始化後）

```bat
start_all.bat
```

### 3. 手動流程（可選）

```bat
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

在 `backend/` 目錄下建立或更新 `.env.local`：

```env
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
GOOGLE_API_KEY=your-google-api-key
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/prajekt
```

```bat
cd ..
docker compose up -d postgres
cd backend
venv\Scripts\python.exe safe_migrate.py
venv\Scripts\python.exe migrate_sqlite_to_postgres.py --sqlite-path instance/prajekt.db --pg-dsn postgresql://postgres:postgres@localhost:5433/prajekt --skip-if-not-empty
venv\Scripts\python.exe app.py
```

```bat
cd frontend
npm install
npm run dev
npm run guardrails:payload
```

後端運行於 `http://localhost:5000`，前端運行於 `http://localhost:5173`。

`npm run guardrails:payload` 會檢查兩個規則：
- 禁止在 mutation payload 使用 `Partial<Entity>`
- 禁止 `service.update(..., { ...entity })` 的 over-posting 寫法

## 測試與 CI/CD 現況

### 前端測試（Vitest）

- 結果：`85/85` tests 通過，平均 statements coverage `88.85%`
- 主要涵蓋：`services`、`stores`、`utils`、`composables`
- 指令：

```bash
cd frontend
npm run test:run
```

### 後端測試（pytest + coverage）

- 結果：最新回歸 `136 passed`（coverage 基線 `80.59%`）
- 覆蓋範圍：`blueprints`、`services`、`models`
- 指令：

```bash
cd backend
pytest --cov=blueprints --cov=services --cov=models --cov-report=term-missing --cov-report=xml --cov-report=html
```

### GitHub Actions

- 已啟用：`backend-tests.yml`（PR/Push 自動執行 pytest + coverage 報告）
- 已建立：`frontend-tests.yml`（後續可接 branch protection）

## API 端點

### 認證

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/auth/register` | 註冊新帳號 |
| POST | `/api/auth/login` | 登入，回傳 access + refresh token |
| POST | `/api/auth/refresh` | 用 refresh token 換新 access token |

### 專案（Timelines）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/timelines` | 取得所有專案列表 |
| POST | `/api/timelines` | 建立新專案 |
| PUT | `/api/timelines/:id` | 更新專案資訊 |
| DELETE | `/api/timelines/:id` | 刪除專案 |
| GET | `/api/timelines/:id/tasks` | 取得專案下的任務 |
| POST | `/api/timelines/:id/generate-tasks` | AI 生成任務建議 |
| POST | `/api/timelines/:id/batch-create-tasks` | 批次建立任務 |
| GET | `/api/timelines/:id/members` | 取得專案成員列表 |
| POST | `/api/timelines/:id/members` | 加入成員（同時發送邀請通知）|
| DELETE | `/api/timelines/:id/members/:uid` | 移除成員 |
| GET | `/api/timelines/upcoming` | 即將到期 / 進度落後的專案（3 天內 or ≥80%）|
| GET | `/api/timelines/:id/member-stats` | 成員任務貢獻統計（負責人限定）|

### 任務（Tasks）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/tasks` | 取得任務列表 |
| GET | `/api/tasks/upcoming` | 即將到期 / 進度落後的任務（3 天內 or ≥80%）|
| POST | `/api/tasks` | 建立任務 |
| PUT | `/api/tasks/:id` | 更新任務 |
| DELETE | `/api/tasks/:id` | 刪除任務（軟刪除）|
| PATCH | `/api/tasks/:id/status` | 更新任務狀態（看板拖曳） |
| PATCH | `/api/tasks/:id/toggle` | 快速切換完成狀態 |
| GET | `/api/tasks/:id/subtasks` | 取得子任務 |
| POST | `/api/tasks/:id/subtasks` | 建立子任務 |
| PATCH | `/api/tasks/:id/subtasks/:sid/toggle` | 子任務完成狀態切換 |
| GET | `/api/tasks/:id/comments` | 取得留言 |
| POST | `/api/tasks/:id/comments` | 新增留言 |
| DELETE | `/api/tasks/:id/comments/:cid` | 刪除留言 |
| POST | `/api/tasks/:id/ai-comment-summary` | AI 摘要任務留言（決議/風險/下一步） |
| GET | `/api/tasks/:id/files` | 取得附件列表 |
| POST | `/api/tasks/:id/upload` | 上傳附件 |
| GET | `/api/tasks/files/:filename` | 下載/預覽附件 |
| DELETE | `/api/tasks/:id/files/:fid` | 刪除附件 |

### 垃圾桶（Trash）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/trash` | 查詢已刪任務與專案 |
| PATCH | `/api/trash/tasks/:id/restore` | 還原任務 |
| DELETE | `/api/trash/tasks/:id` | 永久刪除任務（含附件）|
| PATCH | `/api/trash/timelines/:id/restore` | 還原專案 |
| DELETE | `/api/trash/timelines/:id` | 永久刪除專案（cascade 清子任務）|

### 通知（Notifications）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/notifications` | 取得通知列表 |
| GET | `/api/notifications/unread-count` | 未讀數量 |
| PATCH | `/api/notifications/:id/read` | 標記為已讀 |
| PATCH | `/api/notifications/read-all` | 全部標記已讀 |

### 個人資料 / 統計

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/profile/me` | 取得個人資料 |
| PUT | `/api/profile/me` | 更新個人資料 |
| POST | `/api/profile/search` | 搜尋使用者（username / email）|
| GET | `/api/profile/chart-stats` | 個人圖表資料（30 天趨勢、狀態分布、各專案量）|

### AI 與自動化

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/tasks/:id/ai-comment-summary` | Task 留言 AI 摘要（決議/風險/下一步） |
| POST | `/api/groups/:id/ai-snapshot` | 群組知識快照生成（行動導向 Digest） |
| GET | `/api/groups/:id/ai-snapshot/latest` | 取得最新群組快照 |
| GET | `/api/groups/snapshot-jobs/:job_id` | 查詢快照生成進度 |
| POST | `/api/copilot/mcp/execute` | Copilot MCP 工具執行（自然語言路由至後端工具） |

### 其他

| 方法 | 路徑 | 說明 |
|------|------|------|
| CRUD | `/api/todos` | 待辦事項管理 |
| PATCH | `/api/todos/:id/toggle` | 待辦完成狀態切換 |
| GET/POST | `/api/groups` | 群組清單與建立 |
| POST | `/api/groups/join` | 使用邀請碼加入群組 |
| POST | `/api/groups/:id/leave` | 離開群組 |
| GET | `/api/groups/:id/members` | 群組成員列表 |
| GET/POST | `/api/groups/:id/messages` | 群組訊息 |

### WebSocket 事件（群組聊天室）

| 事件 | 方向 | 說明 |
|------|------|------|
| `join-group` | Client → Server | 加入指定群組房間（成員驗證） |
| `leave-group` | Client → Server | 離開指定群組房間 |
| `send-message` | Client → Server | 送出訊息（寫入 DB 後廣播） |
| `new-message` | Server → Client | 同房間推播新訊息 |
| `error` | Server → Client | 授權失敗/參數錯誤等錯誤事件 |

## 注意事項

- **API Base URL**：前端透過 `VITE_API_BASE_URL` 環境變數配置，預設為 `http://localhost:5000/api`
- **Token 刷新**：access token 過期時，Axios 攔截器會自動使用 refresh token 換新，無需手動處理
- **開發資料庫**：Phase 6 主線改為 PostgreSQL；SQLite 保留舊環境相容與資料比對用途
- **AI 功能**：需要有效的 Google API Key，可於 [Google AI Studio](https://aistudio.google.com/app/apikey) 免費申請；目前生產驗收不包含 AI 任務生成
- **Payload 契約**：請參考 `docs/payload-contracts.md`，前後端 update/create 請遵守 allowlist
- **文件同步流程**：請參考 `docs/文件更新與發布流程.md`

## Roadmap（近程）

- **Phase 5（已完成）**：
	- 5.1~5.3（Supabase + Railway + Firebase）完成
	- 5.4A（單人核心流程驗收）完成
	- 5.5（前端測試基線）完成
	- 5.6（後端測試 + CI coverage 報告）完成
- **CI/CD（輕量版，進行中）**：
	- 已完成：Backend PR checks + coverage 報告
	- 待完成：Frontend PR checks、branch protection、`docs/CI_CD_最小流程.md`
- **Phase 6 AI 主線（本地執行中，未納入雲端上線）**：
	- 6.0：開發資料庫遷移到 PostgreSQL（SQLite → PG）✅
	- 6.1：AI Provider 收斂（Gemini 主線 + 可替換 Adapter）✅
	- 6.2：Task Comment 智能摘要（已完成核心版）✅
	- 6.3：RAG-B 群組快照（核心流程完成，採行動導向 Digest）✅
	- **6.3+**：Copilot + MCP 整合（自然語言路由至後端工具）✅
	- 6.4：群組與專案聯動 / RAG-C 週回顧（待開始）⏳
	- 邊界：不建立 staging、不新增雲端擴展部署

## 環境需求

- Python 3.10+
- Node.js 18+
- Google API Key（AI 功能必要）
