# PrAjeKt

PrAjeKt 是一個面向個人與小團隊的協作系統，目標是補上聊天工具在任務承接、進度追蹤與脈絡整理上的不足。  
它希望保留溝通的彈性，同時提供更正式、但不過度複雜的專案、任務、知識與協作管理能力。

它的定位介於即時聊天工具與傳統專案管理工具之間，適合需要協作，但又不想一開始就導入過重流程的使用情境。

## 想解決的問題

- LINE、Discord 適合快速溝通，但不適合正式承接任務與追進度
- 討論、決策、檔案與待辦常常分散在不同地方，難以回頭整理
- 小團隊或個人協作需要秩序，但不一定需要過重的企業級流程

## 核心能力

- 專案與時程管理：用專案、視圖與進度資訊承接一段計畫或一個實際協作主題
- 任務管理：把討論真正落成可追蹤、可指派、可調整的工作項目
- 協作脈絡整理：透過留言、活動與進度資訊保留決策上下文，而不是只留在聊天紀錄裡
- 團隊協作：支援成員分工、多人協作與群組互動，而不只是單人待辦管理
- 知識集中：將文件、規則與參考資料收斂到同一個系統裡，降低資訊散落的成本

## 技術架構

| 層級 | 目前採用 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Vue Router |
| 後端 | Flask + Flask-SQLAlchemy + Flask-Migrate + Flask-SocketIO |
| AI / Workflow | LangChain + LangGraph + Pydantic v2 + MCP |
| 資料庫 | PostgreSQL（Supabase / 本地 Docker） |
| 測試 | Vitest + pytest + coverage |
| 部署 | Railway（Backend）+ Firebase Hosting（Frontend） |

## 專案結構

```text
prajekt/
├── backend/                     # Flask 後端、service、repository、tests
├── frontend/                    # Vue 前端、stores、components、views
├── docs/                        # Phase、架構、runbook、reference、guides
├── scripts/                     # 開發輔助腳本與本地啟動腳本
├── mcp_server.py                # MCP Server 入口
├── docker-compose.yml           # 本地 PostgreSQL 開發基礎設施
├── requirements.txt             # Root deployment requirements
└── README.md
```

## 快速啟動

### 前置需求

- Docker Desktop
- Python 3.10+
- Node.js 18+

### Windows 一鍵初始化

```bat
scripts\dev\bootstrap_pg_local.bat
```

此腳本會自動：

- 啟動本地 PostgreSQL 容器
- 套用 migration
- 視情況遷移既有 SQLite 資料
- 啟動後端與前端開發服務

### 已初始化後的日常啟動

```bat
scripts\dev\start_all.bat
```

### 手動啟動

```bat
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
cd ..
docker compose up -d postgres
cd backend
venv\Scripts\python.exe scripts\db\safe_migrate.py
venv\Scripts\python.exe app.py
```

```bat
cd frontend
npm install
npm run dev
```

預設：

- Backend：`http://localhost:5000`
- Frontend：`http://localhost:5173`

## 測試

- Frontend：`cd frontend && npm run test:coverage`
- Backend：`cd backend && pytest tests --cov=blueprints --cov=services --cov=models --cov-report=term-missing`

## 文件入口

- `docs/重構計畫.md`
- `docs/進度追蹤.md`
- `docs/architecture/PrAjeKt_專案目的與功能定位_2026-06-07.md`
- `docs/reference/payload-contracts.md`
- `docs/reference/API_錯誤碼表.md`
- `docs/runbooks/本地開發測試部署_Runbook.md`
- `docs/runbooks/完整啟動指南.md`
