# LearnLink - 學習管理平台

基於 Vue 3 + Flask 的現代化學習管理系統，提供專案管理、任務追蹤、課程管理、群組協作等功能。

## 🚀 技術架構

### 前端
- **Vue 3** - 使用 Composition API
- **Vite** - 快速的開發伺服器和構建工具
- **Pinia** - 狀態管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客戶端

### 後端
- **Flask 3.x** - Web 框架
- **Flask-SQLAlchemy** - ORM
- **Flask-JWT-Extended** - JWT 認證
- **Flask-CORS** - 跨域請求處理
- **PyMySQL** - MySQL 驅動
- **Werkzeug** - 密碼加密和檔案處理

### 資料庫
- **MySQL** - 關聯式資料庫

## 📦 功能模組

### ✅ 已完成功能

1. **使用者認證系統**
   - JWT Token 登入/登出
   - 使用者註冊
   - 密碼加密存儲
   - 自動 Token 刷新

2. **專案管理 (Timelines)**
   - 建立、編輯、刪除專案
   - 專案進度追蹤
   - 任務關聯與管理
   - 檔案上傳與下載
   - 視覺化進度條

3. **任務管理 (Tasks)**
   - 任務 CRUD 操作
   - 任務狀態切換
   - 任務期限設定
   - 任務分配功能

4. **待辦事項 (Todos)**
   - 待辦事項列表
   - 完成/未完成分類顯示
   - 逾期提醒
   - 快速新增與編輯

5. **課程管理 (Courses)**
   - 課程建立與瀏覽
   - 教師管理
   - 課程檔案上傳
   - 課程詳情查看

6. **群組協作 (Groups)**
   - 建立群組
   - 邀請碼加入機制
   - 即時訊息功能
   - 成員管理

7. **個人資料 (Profile)**
   - 個人資料編輯
   - 密碼變更
   - 使用統計儀表板
   - 系所年級管理

## 🛠️ 安裝與設定

### 環境需求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+

### 後端設定

1. 進入後端目錄並安裝依賴：
```bash
cd backend
pip install -r requirements.txt
```

2. 建立 MySQL 資料庫：
```sql
CREATE DATABASE learnlink CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. 複製環境變數範本並設定：
```bash
cp .env.example .env
```

編輯 `.env` 檔案：
```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=mysql+pymysql://root:password@localhost/learnlink
```

4. 初始化資料庫：
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. 啟動後端伺服器：
```bash
python app.py
```

後端將運行在 `http://localhost:5000`

### 前端設定

1. 進入前端目錄並安裝依賴：
```bash
cd frontend
npm install
```

2. 設定環境變數（已包含在 `.env` 檔案）：
```env
VITE_API_BASE_URL=http://localhost:5000/api
```

3. 啟動開發伺服器：
```bash
npm run dev
```

前端將運行在 `http://localhost:5173`

## 📂 專案結構

```
Learnlink/
├── backend/                 # Flask 後端
│   ├── app.py              # 應用程式入口
│   ├── blueprints/         # API 藍圖
│   │   ├── auth.py         # 認證端點
│   │   ├── tasks.py        # 任務管理
│   │   ├── todos.py        # 待辦事項
│   │   ├── timelines.py    # 專案管理
│   │   ├── courses.py      # 課程管理
│   │   ├── groups.py       # 群組功能
│   │   ├── messages.py     # 訊息功能
│   │   └── profile.py      # 個人資料
│   ├── models/             # 資料模型
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── todo.py
│   │   ├── timeline.py
│   │   ├── course.py
│   │   └── message.py
│   ├── uploads/            # 檔案上傳目錄
│   ├── requirements.txt    # Python 依賴
│   └── .env.example        # 環境變數範本
│
├── frontend/               # Vue 前端
│   ├── src/
│   │   ├── components/     # 共用元件
│   │   │   ├── Header.vue
│   │   │   └── Sidebar.vue
│   │   ├── views/          # 頁面元件
│   │   │   ├── LoginView.vue
│   │   │   ├── RegisterView.vue
│   │   │   ├── HomeView.vue
│   │   │   ├── TimelinesView.vue
│   │   │   ├── TasksView.vue
│   │   │   ├── TodosView.vue
│   │   │   ├── CoursesView.vue
│   │   │   ├── GroupsView.vue
│   │   │   └── ProfileView.vue
│   │   ├── stores/         # Pinia 狀態管理
│   │   │   └── auth.js
│   │   ├── services/       # API 服務
│   │   │   └── api.js
│   │   ├── router/         # 路由設定
│   │   │   └── index.js
│   │   ├── App.vue         # 根元件
│   │   └── main.js         # 應用程式入口
│   ├── package.json
│   ├── vite.config.js
│   └── .env
│
├── PLAN.md                 # 重構計畫（英文）
├── 重構計畫.md             # 重構計畫（繁體中文）
└── README.md               # 專案說明
```

## 🔐 API 端點

### 認證
- `POST /api/auth/register` - 註冊
- `POST /api/auth/login` - 登入
- `POST /api/auth/logout` - 登出
- `GET /api/auth/me` - 取得當前使用者

### 專案管理
- `GET /api/timelines` - 取得專案列表
- `POST /api/timelines` - 建立專案
- `GET /api/timelines/:id` - 取得專案詳情
- `PUT /api/timelines/:id` - 更新專案
- `DELETE /api/timelines/:id` - 刪除專案
- `GET /api/timelines/:id/tasks` - 取得專案任務
- `POST /api/timelines/:id/files` - 上傳檔案
- `GET /api/timelines/tasks/:id/files` - 取得任務檔案

### 任務
- `GET /api/tasks` - 取得任務列表
- `POST /api/tasks` - 建立任務
- `PUT /api/tasks/:id` - 更新任務
- `DELETE /api/tasks/:id` - 刪除任務
- `PATCH /api/tasks/:id/toggle` - 切換完成狀態

### 待辦事項
- `GET /api/todos` - 取得待辦列表
- `POST /api/todos` - 建立待辦
- `PUT /api/todos/:id` - 更新待辦
- `DELETE /api/todos/:id` - 刪除待辦
- `PATCH /api/todos/:id/toggle` - 切換完成狀態

### 課程
- `GET /api/courses` - 取得課程列表
- `POST /api/courses` - 建立課程
- `GET /api/courses/:id` - 取得課程詳情
- `GET /api/courses/teachers` - 取得教師列表

### 群組
- `GET /api/groups` - 取得群組列表
- `POST /api/groups` - 建立群組
- `POST /api/groups/join` - 加入群組
- `GET /api/groups/:id/messages` - 取得訊息
- `POST /api/groups/:id/messages` - 發送訊息

### 個人資料
- `GET /api/profile/me` - 取得個人資料
- `PUT /api/profile/me` - 更新個人資料

## 🎨 UI 特色

- **響應式設計** - 支援桌面與行動裝置
- **深色模式友善** - 使用現代化配色
- **直覺式操作** - 清晰的使用者介面
- **即時反饋** - 操作後立即顯示結果
- **視覺化進度** - 進度條與統計圖表

## 🔒 安全性

- JWT Token 認證
- 密碼 Bcrypt 加密
- CORS 跨域保護
- SQL Injection 防護（ORM）
- XSS 防護
- 檔案上傳驗證

## 📝 開發注意事項

1. **CORS 設定**：開發環境已設定允許 localhost:5173，生產環境需調整
2. **Token 過期**：Access Token 1 小時，Refresh Token 30 天
3. **檔案上傳**：限制檔案大小與類型，存放於 backend/uploads
4. **資料庫連線**：確保 MySQL 服務運行並正確設定連線字串

## 🐛 疑難排解

### 前端無法連接後端
- 確認後端服務運行在 port 5000
- 檢查 `.env` 中的 `VITE_API_BASE_URL`
- 確認 CORS 設定正確

### Token 認證失敗
- 清除瀏覽器 localStorage
- 重新登入取得新 Token
- 檢查 JWT_SECRET_KEY 設定

### 資料庫連線錯誤
- 確認 MySQL 服務運行
- 檢查 DATABASE_URL 格式
- 驗證資料庫使用者權限

## 📞 支援與回饋

如有問題或建議，請聯繫開發團隊。

## 📄 授權

此專案為教育用途開發。
