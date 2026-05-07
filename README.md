# prajekt

基於 Vue 3 + Flask 的專案管理與協作平台，整合 Google Gemini AI 實現智能任務生成。

> **開發狀態**：Phase 1~6.6+ 已完成 ✅；Phase 7.1、7.2 已完成核心功能 ✅；Phase 7.3 核心閉環已完成 ✅（個人知識庫頁、專案檔案區、RAG 規劃 API 與來源契約已串接；後續聚焦生成品質與評測收斂）。

## 功能模組

- **專案管理**：卡片 / 看板 / 日曆 / 列表 四種視圖，專案進度追蹤、成員邀請
- **任務管理**：任務 CRUD、子任務、優先級、標籤、狀態拖曳切換、留言討論、附件上傳 / 下載、任務成員指派
- **排程協作（Phase 7.1）**：任務建立可多選指派（`assignee_user_ids`）、建立與再指派前皆可做衝突預檢（同專案/跨專案/過載日）
- **專案週報（Phase 7.1）**：一鍵生成週報（完成項目、風險清單、近期留言、下一步建議、AI 摘要）
- **進度風險分析（Phase 7.2）**：專案 Critical Path 分析、風險分級（high/medium/low）、資料品質警示（循環依賴/缺漏排程）
- **任務依賴管理（Phase 7.2）**：支援 `depends_on_task_ids` 編輯、任務詳情維護前置依賴、風險面板可視化依賴圖（SVG 自動佈局 + 關鍵路徑標記）
- **待辦事項**：個人 Todo 列表，完成狀態管理
- **群組協作**：群組建立 / 邀請碼加入 / 即時聊天（Socket.IO，含 REST fallback；群組成員清單預設不含 email 且需成員驗證）
- **個人資料**：個人資訊編輯、密碼變更、使用統計
- **數據分析儀表板**：整合於個人資料頁，Level 1 個人圖表（30 天完成趨勢、任務狀態分布、各專案任務量）+ Level 2 專案圖表（成員貢獻、任務狀態，負責人限定）
- **AI 任務生成**：自然語言輸入 → AI 工具路由 → MCP 執行，支援批次創建與自動化（MCP Copilot 整合）；生成任務可帶入依賴欄位，缺漏時會套用順序鏈 fallback
- **AI 群組快照（RAG-B 核心）**：群組聊天可生成「行動導向 Digest」（一句重點 / 你現在要做什麼 / 阻塞風險 / 精簡決議）
- **個人知識庫（Phase 7.3）**：`/knowledge` 支援 md/txt/pdf 上傳、列表、狀態、搜尋、篩選、排序、刪除與重建索引，採 per-user 隔離檢索
- **專案檔案區（Phase 7.3）**：Timeline 詳情內可管理 project-scoped knowledge files，支援上傳、篩選、批次刪除/重建、下載、預覽與最近操作紀錄
- **AI 規劃建議（Phase 7.3）**：`/api/timelines/ai-suggest-plan` 會整合歷史任務、個人知識與專案文件，回傳可追溯 `source_references`，並具備文字 fallback 與 LLM timeout fallback
- **Copilot + MCP 整合**：自然語言 AI 路由至後端工具，無需 Inspector；支援任務知識摘要、群組快照、自動化創建
- **垃圾桶回收機制**：已刪任務 / 專案暫存，支援還原或永久刪除；非建立者唯讀
- **通知系統**：任務指派 / 專案邀請通知、鈴鐺 30 秒輪詢更新、主頁即將到期提醒區塊（3 天內截止或進度 ≥80%）

## 技術架構

| 層級 | 目前採用（2026/04） |
|------|------|
| 前端核心 | Vue 3.5.17 + TypeScript 5.9.3 + Vite 7.2.4（Composition API / script setup） |
| 狀態管理 / 路由 | Pinia 3.0.4 + Vue Router 4.6.4 |
| API / 認證 | Axios 1.13.2（含 JWT 自動刷新 Queue） + Flask-JWT-Extended |
| 樣式與 UI | Tailwind CSS 4.1.18 + @tailwindcss/vite + Headless UI 1.7.23 + vue-sonner 2.0.9 |
| 任務視圖能力 | FullCalendar 6.1.20 + vuedraggable 4.1.0 + frappe-gantt 1.2.2 |
| 圖表 | ECharts 6.0.0 + vue-echarts 8.0.1 |
| 即時通訊 | Flask-SocketIO 5.3.x + socket.io-client 4.8.1 |
| 後端核心 | Flask 3.x + Flask-SQLAlchemy + Flask-Migrate + Flask-CORS |
| AI 應用層 | LangChain + LangChain Core + LangGraph + Pydantic v2 |
| AI 模型提供者 | LangChain Provider 架構（預設 Google Gemini；Embeddings 可切換 google/openai/huggingface/ollama） |
| MCP | mcp Python SDK + stdio JSON-RPC Bridge（Copilot 路由到後端工具） |
| 資料庫 | PostgreSQL（Supabase + 本地 Docker 主線）+ pg8000 驅動；SQLite 僅保留遷移/比對用途 |
| 測試與品質 | Vitest 4.1.2、pytest/pytest-cov/pytest-flask、Stryker 9.6.0 |
| 部署 | Railway（Backend）+ Firebase Hosting（Frontend）+ Supabase（PostgreSQL） |

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
│   ├── chains/                   # LangChain chains/workflows（Phase 6.6）
│   ├── prompts/                  # PromptTemplate 管理（Phase 6.6）
│   ├── models/                   # SQLAlchemy ORM
│   ├── realtime/                 # Socket 事件
│   │   └── socket_events.py
│   ├── tests/                    # pytest
│   ├── migrations/               # Flask-Migrate
│   ├── uploads/                  # 任務附件與專案知識檔案（本機執行資料，不納入版控）
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
│       ├── types/                # `index.ts` + domain type files
│       ├── styles/
│       ├── views/                # 頁面層，含 KnowledgeBaseView
│       └── router/
│
├── docs/                         # 開發筆記與流程文件（納入版控）
│   ├── 進度追蹤.md
│   ├── 重構計畫.md
│   └── workflows/
├── mcp_server.py                 # MCP 工具伺服器
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

- 結果：最新全量回歸 `187 passed`（coverage 基線持續維護中）
- 覆蓋範圍：`blueprints`、`services`、`models`
- 指令：

```bash
cd backend
pytest --cov=blueprints --cov=services --cov=models --cov-report=term-missing --cov-report=xml --cov-report=html
```

### GitHub Actions

- 已啟用：`backend-tests.yml`（PR/Push 自動執行 pytest + coverage 報告）
- 已建立：`frontend-tests.yml`（後續可接 branch protection）

### 本輪 Phase 7.3 聚焦驗證（2026/05/08）

- 前端：`npm run test -- timelineService.test.ts KnowledgeBaseView.test.ts TimelineDetailDialog.phase7.test.ts`（3 files / 11 tests passed）
- 後端：`venv\Scripts\python.exe -m pytest`（189 passed，僅 `.pytest_cache` 權限 warning）
- 後端語法檢查：`python -m py_compile services\rag_planning_service.py repositories\knowledge_repository.py services\knowledge_service.py`

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
| GET | `/api/timelines/:id/weekly-report` | 取得專案週報（完成/風險/留言/下一步/AI 摘要） |
| GET | `/api/timelines/:id/risk-analysis` | 取得專案風險分析（critical path、風險清單、依賴圖資料） |
| POST | `/api/timelines/:id/risk-analysis/notify` | 發送風險通知給專案成員（負責人限定） |
| POST | `/api/timelines/:id/conflict-check` | 檢查排程衝突（同專案/跨專案/過載日，含建議改期） |
| POST | `/api/timelines/ai-suggest-plan` | AI 規劃建議（整合歷史任務 + 個人知識 + 專案文件，回傳 `timeline_task` / `knowledge_chunk` 來源） |
| POST | `/api/timelines/:id/generate-tasks` | AI 生成任務建議 |
| POST | `/api/timelines/:id/batch-create-tasks` | 批次建立任務 |
| GET | `/api/timelines/:id/members` | 取得專案成員列表 |
| POST | `/api/timelines/:id/members` | 加入成員（同時發送邀請通知）|
| POST | `/api/timelines/search_user` | 專案內使用者搜尋（需 `timeline_id`；僅同專案 owner/member 可查） |
| DELETE | `/api/timelines/:id/members/:uid` | 移除成員 |
| GET | `/api/timelines/upcoming` | 即將到期 / 進度落後的專案（3 天內 or ≥80%）|
| GET | `/api/timelines/:id/member-stats` | 成員任務貢獻統計（負責人限定）|

### 任務（Tasks）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/tasks` | 取得任務列表 |
| GET | `/api/tasks/upcoming` | 即將到期 / 進度落後的任務（3 天內 or ≥80%）|
| POST | `/api/tasks` | 建立任務（支援 `assignee_user_ids` 多選指派與 `depends_on_task_ids` 前置依賴） |
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

### 知識庫（Knowledge）

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/knowledge/documents` | 上傳知識文件並建立索引；不帶 `project_id` 為個人知識庫，帶 `project_id` 為專案檔案 |
| GET | `/api/knowledge/documents` | 取得知識文件列表，支援 `q` / `status` / `sort` / `limit` / `offset` / `project_id` |
| DELETE | `/api/knowledge/documents/:id` | 刪除知識文件；個人知識庫為單檔刪除，專案檔案會記錄事件並清理實體檔 |
| POST | `/api/knowledge/documents/:id/reindex` | 重建指定知識文件索引 |
| POST | `/api/knowledge/documents/batch-delete` | 專案檔案批次刪除（需 `project_id`） |
| POST | `/api/knowledge/documents/batch-reindex` | 專案檔案批次重建索引（需 `project_id`） |
| GET | `/api/knowledge/documents/:id/download` | 專案檔案下載（需 `project_id`，JWT 驗證） |
| GET | `/api/knowledge/documents/:id/preview` | 專案檔案預覽（需 `project_id`，JWT 驗證） |
| GET | `/api/knowledge/documents/events` | 專案檔案最近操作紀錄（需 `project_id`） |

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
| GET | `/api/groups/:id/members` | 群組成員列表（成員限定；預設不含 email） |
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
- **AI 功能**：需要有效的 Google API Key，可於 [Google AI Studio](https://aistudio.google.com/app/apikey) 免費申請；目前已完成本地完整鏈路，雲端環境建議以受控方式逐步驗證
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
	- 6.4：群組與專案聯動 / RAG-C 週回顧（待開始）⏳
	- 6.5：MCP 工具擴展與文檔收斂（2/3 工具）🟡
	- 6.6：LangChain 遷移與統一路徑（PromptTemplate 修復 + 文檔化）✅
	- **6.3+**：Copilot + MCP 整合（自然語言路由至後端工具）✅
	- 邊界：不建立 staging、不新增雲端擴展部署
- **Phase 7 精簡路線（進行中）**：
	- 7.1：週報 + 衝突檢查 MVP（含過載日列表、多指派、隱私遮罩）✅
	- 7.2：進度風險分析 MVP 核心（critical path + 依賴管理 + 依賴圖）✅
	- 7.3：核心閉環完成（個人知識庫 `/knowledge` + Project Files + RAG 規劃 API + source references）✅
	- 7.3+：後端測試工程化收斂（models/task/timeline 大型測試檔拆分），全量後端回歸 `185 passed` ✅
	- 7.3 後續：RAG 生成品質、評測資料集、來源排序與 prompt 調校 🟡

## 環境需求

- Python 3.10+
- Node.js 18+
- Google API Key（AI 功能必要）
