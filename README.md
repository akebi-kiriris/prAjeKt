# PrAjeKt

基於 Vue 3 + Flask 的專案管理與協作平台，整合 Google Gemini AI 實現智能任務生成。

> **開發狀態**：Phase 1 & 2 全部完成 ✅（03/11 提前結束），Phase 3 TypeScript 遷移進行中 🔄（已完成基礎層 + Service + Store + Composables，元件層待做）。已完成 JWT token 自動刷新、AI 任務生成、任務留言／附件上傳、垃圾桶回收機制、多人協作專案管理、子任務 UI、通知系統（指派 / 邀請 / 到期提醒輪詢）、ConfirmDialog 取代原生 confirm()、數據分析儀表板（個人 + 專案雙層圖表）、行動版 RWD（底部導航 / 單欄佈局 / Header 收縮）等功能。

## 功能模組

- **專案管理**：卡片 / 看板 / 日曆 / 列表 四種視圖，專案進度追蹤、成員邀請
- **任務管理**：任務 CRUD、子任務、優先級、標籤、狀態拖曳切換、留言討論、附件上傳 / 下載、任務成員指派
- **待辦事項**：個人 Todo 列表，完成狀態管理
- **群組協作**：群組建立 / 邀請碼加入 / 即時訊息
- **個人資料**：個人資訊編輯、密碼變更、使用統計
- **數據分析儀表板**：整合於個人資料頁，Level 1 個人圖表（30 天完成趨勢、任務狀態分布、各專案任務量）+ Level 2 專案圖表（成員貢獻、任務狀態，負責人限定）
- **AI 任務生成**：Gemini 根據專案名稱自動生成任務建議，支援批次創建
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
| 後端 | Flask 3 + SQLAlchemy + Flask-Migrate |
| 認證 | Flask-JWT-Extended（access + refresh token）|
| 資料庫 | SQLite（開發）|
| AI | Google Gemini 2.0 Flash（LangChain）|

## 專案結構

```
PrAjeKt/
├── backend/
│   ├── app.py                    # Flask 應用入口，註冊 blueprints、JWT、CORS
│   ├── blueprints/               # 路由層（每個模組一個 blueprint）
│   │   ├── auth.py               # 登入 / 註冊 / token 刷新
│   │   ├── tasks.py              # 任務 CRUD、子任務、狀態切換、留言、附件
│   │   ├── todos.py              # 個人待辦 CRUD
│   │   ├── timelines.py          # 專案 CRUD、成員管理、AI 生成
│   │   ├── trash.py              # 垃圾桶：查詢 / 還原 / 永久刪除
│   │   ├── groups.py             # 群組 CRUD、邀請碼
│   │   ├── messages.py           # 群組訊息
│   │   └── profile.py            # 個人資料讀寫
│   ├── models/                   # SQLAlchemy ORM 模型
│   │   ├── user.py
│   │   ├── task.py / subtask.py / task_comment.py / task_user.py
│   │   ├── timeline.py / timeline_user.py
│   │   ├── group.py / message.py
│   │   ├── todo.py
│   │   └── notification.py / activity_log.py
│   ├── migrations/               # Flask-Migrate 版本控制
│   ├── uploads/                  # 上傳檔案存放
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Header.vue        # 頂部導覽列（用戶名、通知鈴鐺 30s 輪詢）
│       │   └── Sidebar.vue       # 側邊導覽列（可收合）
│       │   ├── ConfirmDialog.vue # 全域確認對話框（取代原生 confirm）
│       │   └── timelines/        # TimelineHeader / TimelineViewModes / TimelineDetailDialog
│       ├── services/             # API 封裝層（所有 HTTP 呼叫集中於此）
│       │   ├── api.ts            # Axios 實例 + JWT 自動刷新攔截器
│       │   ├── todoService.ts    # 待辦 API（5 個方法）
│       │   ├── taskService.ts    # 任務 API（含子任務、留言、附件）
│       │   ├── trashService.ts   # 垃圾桶 API（5 個方法）
│       │   ├── groupService.ts   # 群組 API（6 個方法）
│       │   ├── profileService.ts # 個人資料 API（getMe / update / getChartStats）
│       │   ├── notificationService.ts # 通知 API（列表/未讀/已讀）
│       │   └── timelineService.ts # 專案 API（含 AI 生成 / 成員統計）
│       ├── stores/               # Pinia 全域狀態
│       │   ├── auth.ts           # 登入狀態、token 儲存
│       │   ├── tasks.ts          # 任務狀態（全域）
│       │   ├── todos.ts          # 待辦狀態（全域）
│       │   ├── timelines.ts      # 專案狀態（urgentCount / sortedTimelines 等 computed）
│       │   ├── groups.ts         # 群組狀態（groups / messages / currentGroup）
│       │   ├── profile.ts        # 個人資料狀態（profile / stats / chartStats / ownedTimelines）
│       │   └── notifications.ts  # 通知狀態（notifications / unreadCount）
│       ├── composables/
│       │   └── useConfirm.ts     # Promise-based 確認對話框（全域單例）
│       ├── views/                # 頁面元件
│       │   ├── TimelinesView.vue   # 專案管理（多視圖切換）
│       │   ├── TasksView.vue       # 任務管理（Modal 表單 + 留言 / 附件）
│       │   ├── TodosView.vue       # 個人待辦
│       │   ├── GroupsView.vue      # 群組協作
│       │   ├── ProfileView.vue     # 個人資料
│       │   └── TrashView.vue       # 垃圾桶（已刪任務 / 專案）
│       └── router/index.js       # 路由設定（含導航守衛）
│
└── docs/                         # 開發筆記（不納入版控）
```

## 快速啟動

### 後端

```bash
cd backend
pip install -r requirements.txt
```

在 `backend/` 目錄下建立 `.env`：

```env
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
GOOGLE_API_KEY=your-google-api-key
```

```bash
flask db upgrade
python app.py
```

後端運行於 `http://localhost:5000`

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端運行於 `http://localhost:5173`

### 一鍵啟動

```bat
start_all.bat
```

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
| GET | `/api/timelines/:id/members` | 搜尋可加入成員 |
| POST | `/api/timelines/:id/add-member` | 加入成員（同時發送邀請通知）|
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
| PATCH | `/api/tasks/:id/status` | 切換任務狀態 |
| GET | `/api/tasks/:id/subtasks` | 取得子任務 |
| POST | `/api/tasks/:id/subtasks` | 建立子任務 |
| PATCH | `/api/tasks/:id/subtasks/:sid/toggle` | 子任務完成狀態切換 |
| GET | `/api/tasks/:id/comments` | 取得留言 |
| POST | `/api/tasks/:id/comments` | 新增留言 |
| DELETE | `/api/tasks/:id/comments/:cid` | 刪除留言 |
| GET | `/api/tasks/:id/files` | 取得附件列表 |
| POST | `/api/tasks/:id/files` | 上傳附件 |
| GET | `/api/tasks/:id/files/:fid/download` | 下載附件 |
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

### 其他

| 資源 | 路徑 |
|------|------|
| 待辦 | `CRUD /api/todos` + `PATCH /api/todos/:id/toggle` |
| 群組 | `CRUD /api/groups` + `POST /api/groups/join` + `GET/POST /api/groups/:id/messages` |

## 注意事項

- **API Base URL**：前端透過 `VITE_API_BASE_URL` 環境變數配置，預設為 `http://localhost:5000/api`
- **Token 刷新**：access token 過期時，Axios 攔截器會自動使用 refresh token 換新，無需手動處理
- **開發資料庫**：使用 SQLite（`backend/instance/`），不需要額外安裝資料庫服務
- **AI 功能**：需要有效的 Google API Key，可於 [Google AI Studio](https://aistudio.google.com/app/apikey) 免費申請

## 環境需求

- Python 3.10+
- Node.js 18+
- Google API Key（AI 功能必要）
