# Phase 5.1 - PostgreSQL 資料庫遷移流程

## 📚 流程概述

這份文檔說明如何將應用從本地 SQLite 遷移到遠端 Supabase PostgreSQL。

### 核心概念

```
原始狀態                  →              目標狀態
┌─────────────────┐              ┌──────────────────┐
│ 本地 SQLite     │              │ 雲端 PostgreSQL   │
│  (prajekt.db)   │  ┌─────────→ │   (Supabase)     │
└─────────────────┘              └──────────────────┘
```

---

## 🔄 完整流程步驟

### 階段 1：準備環境（已完成 ✅）

#### 1.1 安裝 PostgreSQL 驅動
```bash
# 虛擬環境激活
cd backend
.\venv\Scripts\Activate.ps1

# 安裝依賴（包含 psycopg2-binary）
pip install -r requirements.txt
```

**為什麼需要？**
- `psycopg2-binary`：Python 連接 PostgreSQL 的驅動程式
- 舊驅動 `pymysql` 是為 MySQL 設計，不相容 PostgreSQL

#### 1.2 獲取 Supabase 連接字串
```
postgresql://postgres:YourPassword@db.xxxxx.supabase.co:5432/postgres
```

**連接字串結構解析：**
```
postgresql://  ← 協議
├── postgres   ← 預設用戶名
├── :password  ← 資料庫密碼
├── @db.xxx.supabase.co ← Supabase 主機
├── :5432      ← PostgreSQL 端口
└── /postgres  ← 資料庫名稱
```

---

### 階段 2：建立資料庫表格（已完成 ✅）

#### 2.1 設定環境變量
```powershell
$env:DATABASE_URL="postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres"
```

**原理：**
- Flask 應用在 `app.py` 中檢查環境變量 `DATABASE_URL`
- 若存在 → 使用 PostgreSQL
- 若不存在 → 回到本地 SQLite

#### 2.2 初始化資料庫表格
執行 `scripts/db/init_db.py` 腳本：
```bash
python scripts/db/init_db.py
```

**執行示例：**
```
正在建立資料庫表格...
✅ 資料庫初始化成功！
```

**建立的表格清單（15 個）：**
```
1. users              - 使用者帳號
2. groups            - 群組
3. group_members     - 群組成員
4. tasks             - 任務
5. task_users        - 任務指派用戶
6. task_comments     - 任務評論
7. subtasks          - 子任務
8. timelines         - 時間線
9. timeline_users    - 時間線成員
10. messages         - 聊天訊息
11. todos            - 待辦事項
12. notifications    - 通知
13. activity_logs    - 活動日誌
14. message_content  - 訊息內容（如果存在）
15. pushnotifications - 推送通知（如果存在）
```

#### 2.3 驗證連接
執行 `test_db.py` 腳本：
```bash
python test_db.py
```

**預期輸出：**
```
✅ PostgreSQL 連接成功！
📊 資料庫 URI: postgresql://***:***@db.xxxxx.supabase.co:5432/postgres
📋 已建立 15 個表格
```

---

### 階段 3：後端服務運行（進行中 🔄）

#### 3.1 啟動 Flask 後端
```bash
# 設定環境變量
$env:DATABASE_URL="postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres"

# 啟動應用
python app.py
```

**預期輸出：**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

#### 3.2 測試 API 端點
```bash
# 測試資料庫連接
curl http://localhost:5000/api/health

# 預期回應：
# {"status": "ok"}
```

#### 3.3 測試實際 CRUD 操作
```bash
# 1. 註冊新用戶
POST /api/auth/register
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}

# 2. 建立群組
POST /api/groups
{
  "name": "My Group"
}

# 3. 發送聊天訊息
POST /api/groups/{group_id}/messages
{
  "content": "Hello World"
}
```

✅ **若資料成功寫入 Supabase → 連接正常**

---

## 🚀 Phase 5.2-5.4 後續步驟

### Phase 5.2：後端部署到 Railway

**目標：** 將後端服務從本地遷移到雲端

```
本地後端 (Python)  →  連接  →  Railway (Python)
                              └→ Supabase PostgreSQL
```

**步驟：**
1. 在 Railway 建立新服務
2. 連接 GitHub repo
3. 配置環境變量（DATABASE_URL）
4. 自動部署（git push）

---

### Phase 5.3：前端部署到 Firebase

**目標：** 將前端 Vue 應用部署到 Firebase Hosting

```
本地前端 (Vue.js)  →  npm build  →  Firebase Hosting
```

**步驟：**
1. 在 Firebase Console 建立項目
2. 更新 `.env.production`：
   ```
   VITE_API_BASE_URL=https://railway-app-url/api
   VITE_SOCKET_URL=https://railway-app-url
   ```
3. 執行 `npm run build`
4. 部署到 Firebase

---

### Phase 5.4：端到端測試

**測試流程：**
```
瀏覽器
  ↓
Firebase Hosting (前端)
  ↓ (HTTP/WebSocket)
Railway Backend
  ↓ (SQL)
Supabase PostgreSQL
```

**驗證項目：**
- [ ] 前端頁面正常加載
- [ ] 用戶註冊/登入功能
- [ ] 群組聊天即時通訊
- [ ] 任務建立和更新
- [ ] 時間線操作
- [ ] 資料庫持久化

---

## 🔍 當前狀態總結

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **PostgreSQL 驅動** | ✅ 已安裝 | psycopg2-binary |
| **Supabase 連接** | ✅ 已配置 | DATABASE_URL |
| **資料庫表格** | ✅ 已建立 | 15 個表格 |
| **連接驗證** | ✅ 已測試 | 連接成功 |
| **後端服務** | 🔄 運行中 | Flask app.py |
| **前端部署** | ⏳ 待開始 | Phase 5.3 |
| **Railway 部署** | ⏳ 待開始 | Phase 5.2 |

---

## 📊 架構圖

### 開發架構（Phase 5.1）
```
┌─────────────────────────┐
│   本地開發環境          │
├─────────────────────────┤
│ Frontend (Vue)          │
│ ← Socket.IO →           │
│ Backend (Flask)         │
│ ← SQLAlchemy →          │
└────────────┬────────────┘
             │ DATABASE_URL
             │
         [網際網路]
             │
         ┌───▼────────────────┐
         │  Supabase Cloud    │
         ├────────────────────┤
         │ PostgreSQL DB      │
         │ (15 Tables)        │
         └────────────────────┘
```

### 生產架構（Phase 5.2-5.4）
```
┌──────────────────────┐
│   用戶的瀏覽器        │
└──────────┬───────────┘
           │ HTTPS
           ▼
┌──────────────────────┐
│ Firebase Hosting     │
│ (Vue 前端)          │
└──────────┬───────────┘
           │ HTTP/WebSocket
           ▼
┌──────────────────────┐
│ Railway Backend      │
│ (Flask 應用)        │
└──────────┬───────────┘
           │ SQL
           ▼
┌──────────────────────┐
│ Supabase PostgreSQL  │
│ (15 個表格)         │
└──────────────────────┘
```

---

## 🛠️ 常見問題排查

### Q1：連接字串格式錯誤？
**症狀：** `psycopg2.OperationalError: could not translate host name`

**解決：**
```python
# ❌ 錯誤
DATABASE_URL = "postgres://user:pass@host/db"  # 舊格式

# ✅ 正確
DATABASE_URL = "postgresql://user:pass@host/db"  # 新格式
```

---

### Q2：密碼中有特殊字符？
**症狀：** `psycopg2.ProgrammingError: Authentication failed`

**解決：** URL encode 特殊字符
```python
import urllib.parse
password = ",U7a3A%NxfH7+-3"
encoded = urllib.parse.quote(password, safe='')
# 或直接在連接字串中使用編碼後的密碼
```

---

### Q3：連接超時？
**症狀：** `psycopg2.OperationalError: timeout expired`

**解決：**
1. 確認 Supabase IP 白名單設定
2. 檢查網路連線
3. 驗證 PostgreSQL 端口（5432）是否開放

---

## 📝 快速參考

### 必要檔案清單
```
backend/
├── requirements.txt          # Python 依賴（已更新）
├── app.py                    # Flask 應用（無需修改）
├── scripts/
│   └── db/
│       └── init_db.py       # 初始化資料庫（Phase 5.1）
├── test_db.py               # 測試連接（Phase 5.1）
├── models/
│   ├── user.py
│   ├── group.py
│   ├── task.py
│   ├── timeline.py
│   ├── message.py
│   └── ...
└── venv/                     # Python 虛擬環境
```

### 環境變量設定
```powershell
# Windows PowerShell
$env:DATABASE_URL="postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres"

# 驗證設定
echo $env:DATABASE_URL
```

---

## ✅ 下一步行動

1. **確認後端運行中** → 看到 `Running on http://127.0.0.1:5000`
2. **測試 API 端點** → 驗證資料庫連接正常
3. **準備 Phase 5.2** → Railway 後端部署

---

**文檔更新時間：** 2026-03-22  
**流程階段：** Phase 5.1 - PostgreSQL 遷移（進行中）
