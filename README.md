# prajekt

基於 Vue 3 + Flask 的專案管理與協作平台，整合 Google Gemini AI 實現智能任務生成。

> **開發狀態**：Phase 1~6.6+ 已完成 ✅；Phase 7.1、7.2 已完成核心功能 ✅；Phase 7.3 核心閉環已完成 ✅；Phase 8.1~8.7 已完成 ✅（交易邊界收斂、前端大型元件拆分、後端 service 契約化、CI/Deploy 拆分、單人精簡護欄與後端測試工廠化）；Phase 9.1~9.5 已完成 ✅（型別基線、Docstring/tool 契約、單體 Tool Registry、雙階段確認、模型提案式 plan + replan 強制二次確認）；下一步進入 Phase 9.6 可觀測性與評測基線。

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
- **Copilot Agent（Phase 9.5）**：已完成單體 tool registry + LangGraph ReAct 最小閉環，並升級為 `plan -> confirm -> execute` 雙階段流程、模型提案式 plan、replan 強制重新提案與二次確認，前端 `CopilotDock` 可顯示步驟預覽、風險提示、提案來源與提案理由
- **AI 群組快照（RAG-B 核心）**：群組聊天可生成「行動導向 Digest」（一句重點 / 你現在要做什麼 / 阻塞風險 / 精簡決議）
- **個人知識庫（Phase 7.3）**：`/knowledge` 支援 md/txt/pdf 上傳、列表、狀態、搜尋、篩選、排序、刪除與重建索引，採 per-user 隔離檢索
- **專案檔案區（Phase 7.3）**：Timeline 詳情內可管理 project-scoped knowledge files，支援上傳、篩選、批次刪除/重建、下載、預覽與最近操作紀錄
- **AI 規劃建議（Phase 7.3）**：`/api/timelines/ai-suggest-plan` 會整合歷史任務、個人知識與專案文件，回傳可追溯 `source_references`，並具備文字 fallback 與 LLM timeout fallback
- **後端抽象收斂（Phase 8）**：knowledge/task/timeline 主線已收斂 `commit/rollback` 至 transaction helper；任務與專案建立流程改用 repository/entity builder；service 層 session 操作統一走 `add_entity/flush_session/delete_entity` helper，並補上群組唯一性約束與防重覆加入策略
- **Copilot + MCP 整合**：自然語言 AI 路由至後端工具，無需 Inspector；支援任務知識摘要、群組快照、自動化創建
- **垃圾桶回收機制**：已刪任務 / 專案暫存，支援還原或永久刪除；非建立者唯讀
- **通知系統**：任務指派 / 專案邀請通知、鈴鐺 30 秒輪詢更新、主頁即將到期提醒區塊（3 天內截止或進度 ≥80%）
- **錯誤契約統一（工程化）**：後端錯誤回應統一為 `error` + `error_code` + `error_details`，前端以共用 `apiError` 工具做解析與分流

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
│       ├── frontend-tests.yml
│       └── frontend-deploy.yml
├── backend/
│   ├── app.py                    # Flask 應用入口
│   ├── blueprints/               # Route 層
│   ├── services/                 # Use case / Business 層（transaction helper 已收斂主線）
│   ├── repositories/             # 查詢、ORM entity builder 與 session helper（Phase 8 收斂）
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

- 前端：`cd frontend && npm run test:coverage`
- 後端：`cd backend && pytest tests --cov=blueprints --cov=services --cov=models --cov-report=term-missing`

CI（GitHub Actions）：
- `.github/workflows/frontend-tests.yml`：frontend 測試 + build + payload guardrails
- `.github/workflows/backend-tests.yml`：backend pytest + coverage report
- coverage 結果會上傳為 artifact，並嘗試上傳 Codecov

## 注意事項

- **API Base URL**：前端透過 `VITE_API_BASE_URL` 環境變數配置，預設為 `http://localhost:5000/api`
- **Token 刷新**：access token 過期時，Axios 攔截器會自動使用 refresh token 換新，無需手動處理
- **開發資料庫**：Phase 6 主線改為 PostgreSQL；SQLite 保留舊環境相容與資料比對用途
- **AI 功能**：需要有效的 Google API Key，可於 [Google AI Studio](https://aistudio.google.com/app/apikey) 免費申請；目前已完成本地完整鏈路，雲端環境建議以受控方式逐步驗證
- **Payload 契約**：請參考 `docs/payload-contracts.md`，前後端 update/create 請遵守 allowlist
- **錯誤碼契約**：請參考 `docs/API_錯誤碼表.md`，前端流程判斷請優先依 `error_code`
- **文件同步流程**：請參考 `docs/文件更新與發布流程.md`


## 核心工程文件（架構/契約/Runbook）

- `架構與責任邊界.md`
- `API_契約與錯誤處理.md`
- `本地開發測試部署_Runbook.md`


## 環境需求

- Python 3.10+
- Node.js 18+
- Google API Key（AI 功能必要）
