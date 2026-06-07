# Phase 5.2 - Railway 後端部署

> **目標：** 將 Flask 後端從本地部署到 Railway（支援 WebSocket）
> **成本：** $5-10/月
> **部署時間：** ~10-15 分鐘

---

## 📋 快速開始

### 前置條件
- ✅ GitHub 帳號（已有）
- ✅ PrAjeKt 倉庫已推送（commit 21b8b1f）
- ✅ 本地後端連接 Supabase 成功
- ✅ `.env` 文件中有 `DATABASE_URL`

---

## 🚀 部署步驟

### 步驟 1：創建 Railway 帳號

訪問 [railway.app](https://railway.app)

```
1. 點擊 "Start New Project"
2. 選擇 "GitHub" 登入 (或用 Email 註冊)
3. 授權 Railway 訪問你的 GitHub
```

**預期結果：** Railway Dashboard 加載完成

---

### 步驟 2：新建 Flask 服務

在 Railway Dashboard：

```
1. 點擊 "New Project"
2. 選擇 "GitHub Repo"
3. 搜尋 "PrAjeKt" 倉庫選中
4. 確認倉庫名稱：PrAjeKt （或你的倉庫名）
5. 點擊 "Deploy Now"
```

**預期結果：** 開始初始構建（Build）

```
Railway 自動偵測：
├── Python 項目（找到 requirements.txt）
├── 啟動命令：python app.py
└── PORT 預設 8000
```

---

### 步驟 3：配置環境變量

在 Railway Dashboard → 你的服務 → Variables

**添加以下環境變量：**

```
DATABASE_URL=postgresql://postgres:,U7a3A%NxfH7+-3@db.ojtdiktwjscfmagqepcg.supabase.co:5432/postgres
SECRET_KEY=your-secret-key-here (改為複雜密鑰)
JWT_SECRET_KEY=your-jwt-secret-key-here (改為複雜密鑰)
FLASK_ENV=production
```

**⚠️ 重要：**
- Railway 會自動設定 `PORT` 環境變量
- Flask 需要支援這個 `PORT`（已在 `app.py` 中支援）

---

### 步驟 4：修改 Flask 啟動方式

Railway 需要 Flask 監聽 `0.0.0.0:$PORT`

檢查 `backend/app.py` 的最後幾行：

```python
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)
```

確認 `host='0.0.0.0'` 和 `port=int(os.getenv('PORT', 5000))`

（如果使用 Flask 默認的 `app.run()`，需要改成上面這樣）

---

### 步驟 5：監控部署過程

在 Railway Dashboard → Deployments

```
✅ Building...  (1-3 分鐘)
   └─ Installing dependencies (pip install -r requirements.txt)
   
✅ Deploying...  (1-2 分鐘)
   └─ Starting Flask app
   
✅ Running  (綠色狀態)
   └─ Service URL: https://XXXX-production.railway.app
```

**可能遇到：**
- ⚠️ Build 失敗 → 檢查 `requirements.txt` 是否有語法錯誤
- ⚠️ Runtime 失敗 → 檢查 `app.py` 啟動命令

---

### 步驟 6：驗證部署

Railway 自動分配公網 URL，格式：
```
https://PrAjeKt-production.railway.app
```

**測試健康檢查：**

```bash
# 瀏覽器或 curl
curl https://PrAjeKt-production.railway.app/api/health

# 預期回應：
# {"status": "ok"}
```

✅ 若看到 200 OK → **後端部署成功！**

---

## ⚠️ 實際部署遇到的問題與解決方案

本次部署過程中遇到了多個問題。以下是完整的問題列表、原因分析和解決方案，供後續參考：

### 問題 1：Railpack 構建檢測失敗

**症狀：**
```
ERROR: Could not find build script
Railpack 無法自動偵測構建方式
```

**原因：**
- Railway 平台需要構建配置文件（Procfile 或 railway.json）
- 缺少根目錄 `requirements.txt` 導致 Python 項目無法被識別

**解決方案：**
1. 在根目錄創建 `requirements.txt`（聚合所有依賴）
2. 創建 `Procfile` 指定啟動命令：
   ```
   web: bash start.sh
   ```
3. 創建 `railway.json` 配置 Nixpacks：
   ```json
   {
     "build": {
       "builder": "nixpacks"
     }
   }
   ```
4. 創建 `start.sh` 處理環境變量和暖啟動

> 以上四個檔案目前都保留在 repo root，因為 Railway / Nixpacks 偵測入口就是看根目錄。

**提交：** Commit ee7ea55

---

### 問題 2：Nixpacks 構建計劃生成失敗

**症狀：**
```
ERROR: Unable to generate build plan
start.sh 路徑解析錯誤
```

**原因：**
- `start.sh` 中使用的相對路徑在 Railway 環境中解析不正確
- 資料庫初始化腳本多次執行導致衝突

**解決方案：**
1. 改進 `start.sh` 中的路徑處理：
   ```bash
   cd "$(dirname "$0")"  # 確保在正確的目錄
   ```
2. 添加資料庫初始化冪等性檢查：
   ```bash
   if [ ! -f ".db_init_done" ]; then
       python scripts/db/create_missing_tables.py
       touch .db_init_done
   fi
   ```
3. 條件啟動邏輯：
   ```bash
   if [ "$FLASK_ENV" = "production" ]; then
       gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
   else
       python app.py
   fi
   ```

**提交：** Commit ee7ea55（與問題 1 同次，優化 start.sh）

---

### 問題 3：依賴版本衝突

**症狀：**
```
ERROR: Could not find version that satisfies the requirement google-generativeai==0.3.5
Collecting google-generativeai==0.3.5
  ERROR: No matching distribution found for google-generativeai==0.3.5
```

**原因：**
- `google-generativeai==0.3.5` 版本不存在於 PyPI
- 原始 requirements.txt 中指定的版本過舊且已被移除
- 該包當前最新穩定版本為 0.8.0+

**解決方案：**
- 將 requirements.txt 中的版本改為：
  ```
  google-generativeai>=0.8.0
  ```
- 使用范圍版本允許更新且保持相容性
- 驗證所有其他版本兼容性

**提交：** Commit 8eb2145 (`fix(deps): 修正 google-generativeai 版本號`)

---

### 問題 4：Werkzeug 生產服務器錯誤

**症狀：**
```
RuntimeError: The Werkzeug web server is not designed to run in production and does not support reliable signal handling.
RuntimeError: The Werkzeug WSGI server is not designed to run in production and does not support reliable signal handling.
```

**原因：**
- Flask 的內置 Werkzeug 開發服務器在生產環境運行時拋出錯誤
- `socketio.run()` 默認使用 Werkzeug，不適合生產部署
- 需要使用生產級 WSGI 服務器（如 gunicorn）

**解決方案：**
1. 更新 requirements.txt 添加：
   ```
   gunicorn==21.2.0
   eventlet==0.33.3  # 用於 WebSocket 支持
   ```
2. 修改 `app.py` 添加允許 Werkzeug 的參數（開發場景）：
   ```python
   socketio.run(app, 
               host='0.0.0.0', 
               port=int(os.getenv('PORT', 5000)),
               allow_unsafe_werkzeug=True)  # 開發模式允許
   ```
3. 優化 start.sh 的條件啟動：
   ```bash
   # 生產環境
   gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
   
   # 開發環境
   python app.py
   ```

**提交：** Commit ee7ea55 (`fix(socketio): 修復 Flask-SocketIO 生產環境 Werkzeug 錯誤`)

---

### 問題 5～8：循環導入問題（4 波修復）

循環導入問題分四波解決，根本原因是架構調整導致的連鎖反應。

#### **問題 5-1：Blueprints 循環導入（第一波）**

**症狀：**
```
ImportError: cannot import name 'db' from partially initialized module 'app' 
(most likely due to a circular import) from backend/blueprints/auth.py
```

**原因：**
- 原架構：`app.py` 內有 `if __name__ == '__main__': app = create_app()`（安全）
- 新需求：gunicorn 要求模塊級別 `app = create_app()` 
- 循環依賴鏈：
  ```
  app → 導入 blueprints
  blueprints (auth.py) → 導入 `from app import db`
  → app 模塊未初始化完成 → 循環導入
  ```

**解決方案：**
- 將所有 9 個 blueprints 改為：
  ```python
  # 舊方法：
  from app import db
  
  # 新方法：
  from models import db
  ```
- 文件列表：
  - `blueprints/auth.py`
  - `blueprints/groups.py`
  - `blueprints/messages.py`
  - `blueprints/notifications.py`
  - `blueprints/profile.py`
  - `blueprints/tasks.py`
  - `blueprints/timelines.py`
  - `blueprints/todos.py`
  - `blueprints/trash.py`

**提交：** Commit 2314114 (`fix(imports): 修復循環導入問題 (blueprints)`)

---

#### **問題 5-2：tasks.py 單獨循環導入（第二波）**

**症狀：**
```
ImportError: cannot import name 'db' from app
```

**原因：**
- tasks.py 仍保留了 `from app import db` 的舊版本

**解決方案：**
- 修復 `backend/blueprints/tasks.py` 導入語句

**提交：** Commit 4b2aa2c (`fix(tasks): 修復 tasks.py 循環導入`)

---

#### **問題 5-3：Services 層循環導入（第三波）**

**症狀：**
```
ImportError: cannot import name 'db'
在 services/task_service.py 和 services/message_service.py 中發生
```

**原因：**
- 業務邏輯層服務也從 `app` 導入 `db`
- 服務被 blueprints 調用，形成導入鏈條

**解決方案：**
- 修復 `services/task_service.py` 和 `services/message_service.py`：
  ```python
  from models import db  # 替代 from app import db
  ```

**提交：** Commit 45eb790 (`fix(services): 修復 services 中的循環導入`)

---

#### **問題 5-4：Realtime 模塊循環導入（第四波）**

**症狀：**
```
ImportError: cannot import name 'db'
在 backend/realtime/socket_events.py 中發生
```

**原因：**
- WebSocket 事件處理模塊也有相同的導入問題

**解決方案：**
- 修復 `backend/realtime/socket_events.py`：
  ```python
  from models import db  # 替代 from app import db
  ```

**提交：** Commit af7b938 (`fix(realtime): 修復 socket_events.py 循環導入`)

---

#### **架構改進的結果：**

✅ **現在的導入結構更清晰：**
- `models/` → 數據庫配置單一源
- `blueprints/`, `services/`, `realtime/` → 都從 `models` 導入
- `app.py` → 工廠函數创建应用，可安全地进行模块级别导出

✅ **同時支持兩種運行方式：**
- 本地開發：`python app.py` （使用 Werkzeug）
- 生產部署：`gunicorn` WSGI 服務器 + Eventlet workers

---

## 🔧 常見問題排查

### Q1：部署失敗，Build 錯誤？

**症狀：**
```
ERROR: Could not find a Python environment
```

**解決：**
1. 檢查根目錄是否有 `requirements.txt`
2. Python 版本：Railway 預設支援 3.9+
3. 清除快取：Railway Dashboard → Settings → Trigger Redeploy

---

### Q2：環境變量未被讀取？

**症狀：** Flask 連接失敗，使用本地 SQLite

**解決：**
1. Railway Dashboard → Variables，確認 `DATABASE_URL` 已添加
2. 點擊服務 → Redeploy
3. 檢查部署日誌（Logs 標籤頁）

---

### Q3：連接超時？

**症狀：**
```
psycopg2.OperationalError: timeout expired
```

**解決：**
1. 確認 Supabase 連接字串正確
2. Railway 會自動配置防火牆，應該沒問題
3. 如還是超時，檢查 Supabase Dashboard → Project Settings → Networking

---

### Q4：WebSocket 連接失敗？

**症狀：** 聊天功能不工作（Socket.IO 連接 101）

**解決：**
```python
# app.py 中確認有這行
socketio.init_app(
    app,
    cors_allowed_origins=['https://your-firebase-url.web.app'],  # Phase 5.3 添加
)
```

---

## 📊 Railway 監控

### 日誌查看

Railway Dashboard → Logs 標籤：

```
看實時日誌，確認：
✅ Flask 啟動成功
✅ 資料庫連接成功
✅ 請求日誌正常
```

### 告警設置

Railway Dashboard → Settings → Health Checks：

```
✅ Enable Health Checks
URL: /api/health
Interval: 30s
Timeout: 10s
```

---

## 🎯 部署後的檢查清單

| 項目 | 完成 |
|------|------|
| Railway 帳號建立 | ☐ |
| GitHub 倉庫綁定 | ☐ |
| 初次部署成功 | ☐ |
| 環境變量已設定 | ☐ |
| 健康檢查通過 (200 OK) | ☐ |
| API 端點可訪問 | ☐ |
| WebSocket 準備就緒（待 5.3） | ☐ |
| 日誌監控啟用 | ☐ |

---

## 🔄 後續：自動部署配置

Railway 默認已啟用 **自動部署**：

```
main 分支 push → GitHub webhook → Railway 自動構建與部署
```

**驗證自動部署：**
1. 本地修改代碼 → `git push`
2. Railway Dashboard 自動觸發 Redeploy
3. 約 2-5 分鐘後新版本上線

---

## 📈 監控與成本

### 月度使用估計

```
| 指標 | 估計值 |
|------|--------|
| 計算時間 | 600-750 小時/月 |
| 頻寬 | 10-50 GB/月 |
| 月費 | $5-10 |
```

**為什麼這麼便宜？**
- 展示級項目流量小
- 計算資源消耗低（Flask 輕量）
- Supabase 免費版足夠

### 監控設置

```
Railway Dashboard → Monitors：
✅ Uptime 監控
✅ CPU 使用率告警（> 80%）
✅ 記憶體告警（> 512MB）
```

---

## 🚀 部署完成後

**你將獲得：**
```
Railway 公網 URL：
https://PrAjeKt-production.railway.app

這個 URL 會在 Phase 5.3 用於前端連接
```

**保存此 URL：**
```
VITE_API_BASE_URL=https://PrAjeKt-production.railway.app/api
VITE_SOCKET_URL=https://PrAjeKt-production.railway.app
```

---

## 📝 下一步（Phase 5.3）

1. 更新 `frontend/.env.production`
2. 配置 CORS：後端允許 Firebase 域名
3. 構建前端：`npm run build`
4. 部署到 Firebase Hosting

---

## 🆘 快速支援

| 問題 | 快速檢查 |
|------|---------|
| 部署失敗 | `pip install -r requirements.txt` 能否運行 |
| 連接失敗 | DATABASE_URL 環變正確嗎 |
| WebSocket 不工作 | 前端 CORS origin 添加了嗎 |
| 性能問題 | Railway 監控 CPU/記憶體使用率 |

---

**預計時間：** 10-15 分鐘  
**難度：** ⭐⭐ 中等（大部分自動化）  
**成功率：** >95%（如遵循步驟）

開始部署吧！🚀
