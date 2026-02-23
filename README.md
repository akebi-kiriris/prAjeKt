# LearnLink

基於 Vue 3 + Flask 的專案管理與協作平台，整合 Google Gemini AI 實現智能任務生成。

> **開發狀態**：持續迭代中。目前已完成服務層重構、JWT token 自動刷新、AI 任務生成等核心功能。

## 功能模組

- **專案管理**：卡片 / 看板 / 日曆 / 列表 四種視圖，專案進度追蹤、成員邀請
- **任務管理**：任務 CRUD、子任務、優先級、標籤、狀態拖曳切換
- **待辦事項**：個人 Todo 列表，完成狀態管理
- **群組協作**：群組建立 / 邀請碼加入 / 即時訊息
- **個人資料**：個人資訊編輯、密碼變更、使用統計
- **AI 任務生成**：Gemini 根據專案名稱自動生成任務建議，支援批次創建

## 技術架構

| 層級 | 技術 |
|------|------|
| 前端框架 | Vue 3 + Vite（Composition API / `<script setup>`）|
| 狀態管理 | Pinia |
| 路由 | Vue Router |
| HTTP | Axios（含 JWT 自動刷新攔截器）|
| 樣式 | Tailwind CSS |
| 後端 | Flask 3 + SQLAlchemy + Flask-Migrate |
| 認證 | Flask-JWT-Extended（access + refresh token）|
| 資料庫 | SQLite（開發）|
| AI | Google Gemini 2.0 Flash（LangChain）|

## 專案結構

```
Learnlink/
├── backend/
│   ├── app.py                    # Flask 應用入口，註冊 blueprints、JWT、CORS
│   ├── blueprints/               # 路由層（每個模組一個 blueprint）
│   │   ├── auth.py               # 登入 / 註冊 / token 刷新
│   │   ├── tasks.py              # 任務 CRUD、子任務、狀態切換
│   │   ├── todos.py              # 個人待辦 CRUD
│   │   ├── timelines.py          # 專案 CRUD、成員管理、AI 生成、留言
│   │   ├── groups.py             # 群組 CRUD、邀請碼
│   │   ├── messages.py           # 群組訊息
│   │   └── profile.py            # 個人資料讀寫
│   ├── models/                   # SQLAlchemy ORM 模型
│   │   ├── user.py
│   │   ├── task.py / subtask.py / task_comment.py
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
│       │   ├── Header.vue        # 頂部導覽列（用戶名、登出）
│       │   └── Sidebar.vue       # 側邊導覽列（可收合）
│       ├── services/             # API 封裝層（所有 HTTP 呼叫集中於此）
│       │   ├── api.js            # Axios 實例 + JWT 自動刷新攔截器
│       │   ├── todoService.js    # 待辦 API（5 個方法）
│       │   ├── taskService.js    # 任務 API（10 個方法，含子任務）
│       │   ├── groupService.js   # 群組 API（6 個方法）
│       │   ├── profileService.js # 個人資料 API（2 個方法）
│       │   └── timelineService.js # 專案 API（14 個方法，含 AI 生成）
│       ├── stores/               # Pinia 全域狀態
│       │   └── auth.js           # 登入狀態、token 儲存
│       ├── views/                # 頁面元件
│       │   ├── TimelinesView.vue   # 專案管理（多視圖切換）
│       │   ├── TasksView.vue       # 任務管理（Modal 表單）
│       │   ├── TodosView.vue       # 個人待辦
│       │   ├── GroupsView.vue      # 群組協作
│       │   └── ProfileView.vue     # 個人資料
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
| POST | `/api/timelines/:id/add-member` | 加入成員 |
| GET | `/api/timelines/:id/comments` | 取得留言 |
| POST | `/api/timelines/:id/comments` | 新增留言 |

### 任務（Tasks）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/tasks` | 取得任務列表 |
| POST | `/api/tasks` | 建立任務 |
| PUT | `/api/tasks/:id` | 更新任務 |
| DELETE | `/api/tasks/:id` | 刪除任務 |
| PATCH | `/api/tasks/:id/toggle` | 切換完成狀態 |
| GET | `/api/tasks/:id/subtasks` | 取得子任務 |
| POST | `/api/tasks/:id/subtasks` | 建立子任務 |
| PATCH | `/api/tasks/:id/subtasks/:sid/toggle` | 子任務完成狀態切換 |

### 其他

| 資源 | 路徑 |
|------|------|
| 待辦 | `CRUD /api/todos` + `PATCH /api/todos/:id/toggle` |
| 群組 | `CRUD /api/groups` + `POST /api/groups/join` + `GET/POST /api/groups/:id/messages` |
| 個人資料 | `GET/PUT /api/profile/me` |

## 注意事項

- **API Base URL**：前端透過 `VITE_API_BASE_URL` 環境變數配置，預設為 `http://localhost:5000/api`
- **Token 刷新**：access token 過期時，Axios 攔截器會自動使用 refresh token 換新，無需手動處理
- **開發資料庫**：使用 SQLite（`backend/instance/`），不需要額外安裝資料庫服務
- **AI 功能**：需要有效的 Google API Key，可於 [Google AI Studio](https://aistudio.google.com/app/apikey) 免費申請

## 環境需求

- Python 3.10+
- Node.js 18+
- Google API Key（AI 功能必要）
