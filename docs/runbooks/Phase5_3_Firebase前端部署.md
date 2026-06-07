# Phase 5.3 - Firebase 前端部署

> **目標：** 將 Vue 3 前端從本地部署到 Firebase Hosting（連接到 Railway 後端）
> **成本：** $0（Firebase 免費版）
> **部署時間：** ~5-10 分鐘

---

## 📋 快速開始

### 前置條件
- ✅ Railway 後端部署成功，取得公網 URL
- ✅ Google / Firebase 帳號（已有）
- ✅ PrAjeKt 倉庫已推送
- ✅ 本地前端可正常運行（`npm run dev`）

---

## 🚀 部署步驟

### 步驟 1：配置環境變數

更新 `frontend/.env.production`：

```bash
# frontend/.env.production

# Railway 後端 URL（替換為你的實際 Railway URL）
VITE_API_BASE_URL=https://your-railway-url/api
VITE_SOCKET_URL=https://your-railway-url

# Firebase 配置（保持不變）
VITE_FIREBASE_API_KEY=your-firebase-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

**⚠️ 重要：**
- `VITE_API_BASE_URL` 和 `VITE_SOCKET_URL` 必須指向 Railway 公網 URL
- 兩個 URL 需要包含 protocol（`https://`）和末尾不帶 `/`
- 測試連接：在瀏覽器中訪問 `https://your-railway-url/api/health` → 應返回 `{"status": "ok"}`

**獲取 Railway URL 的步驟：**

```
1. 訪問 Railway Dashboard → 你的 PrAjeKt 服務
2. 在「Settings」標籤找「Domains」
3. 複製生成的自訂域名（格式：PrAjeKt-production.railway.app）
```

---

### 步驟 2：配置 CORS（Railway 後端）

為了允許前端從 Firebase Hosting 域名發起請求，需要在後端配置 CORS。

修改 `backend/app.py`：

```python
# app.py 中的 socketio.init_app() 部分

socketio.init_app(
    app,
    cors_allowed_origins=[
        'http://localhost:5173',                    # 本地開發
        'https://your-firebase-project.web.app',   # Firebase Hosting（生產）
        'https://your-firebase-project.firebaseapp.com'  # Firebase 備用域名
    ],
    cors_credentials=True,
    async_mode='threading'
)
```

**提交此變更並推送到 GitHub：**

```bash
git add backend/app.py
git commit -m "chore(cors): 配置 CORS 允許 Firebase Hosting 域名"
git push origin main
```

Railway 將自動檢測變更並重新部署（約 1-2 分鐘）。

---

### 步驟 3：本地測試構建

確保前端可以成功編譯：

```bash
cd frontend

# 安裝依賴（如果未安裝）
npm install

# 縮減構建（開發環境）
npm run build
```

**預期結果：**
```
vite v6.x.x building for production...
✓ compiled successfully in x.xx s

dist/
├── index.html
├── assets/
│   ├── index-xxx.js
│   ├── index-xxx.css
│   └── ...
└── ...
```

**常見問題：**
- ❌ `Module not found: 'xyz'` → 執行 `npm install`
- ❌ TypeScript 錯誤 → 運行 `npm run build:check` 查看詳細錯誤信息
- ❌ 環境變數未定義 → 確認 `.env.production` 存在且包含所有必需變數

---

### 步驟 4：安裝 Firebase CLI

全局安裝 Firebase 命令行工具：

```bash
# 安裝 Firebase CLI（全局）
npm install -g firebase-tools

# 驗證安裝
firebase --version

# 預期輸出：
# Firebase CLI 13.x.x
```

---

### 步驟 5：Firebase 初始化（首次部署）

在你的 Firebase 專案中初始化部署配置：

```bash
cd frontend

# 登入 Firebase
firebase login

# 初始化 Firebase（會出現互動式提示）
firebase init hosting
```

**初始化過程中的選項：**

```
? Which Firebase project do you want to associate with this directory?
→ 選擇你的 Firebase 專案（如 "PrAjeKt-prod"）

? What do you want to use as your public directory?
→ 若在 repo root 初始化，輸入：frontend/dist

? Configure as a single-page app (rewrite all urls to /index.html)?
→ 選擇：Yes

? File frontend/dist/index.html already exists. Overwrite?
→ 選擇：No
```

**目前 repo 採用的結果：** 會在 root 生成 `firebase.json` 與 `.firebaserc`

```json
{
  "hosting": {
    "public": "frontend/dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

---

### 步驟 6：部署到 Firebase Hosting

執行部署命令：

```bash
# 在 repo root 執行，使用 root 的 firebase.json / .firebaserc
firebase deploy
```

**部署過程日誌：**
```
Deploying to project [PrAjeKt-prod]...

✔  Deploy complete!

Site URL: https://PrAjeKt-prod.web.app
Details: https://console.firebase.google.com/
```

**預期結果：** 會得到一個 Firebase Hosting 的公網 URL

---

### 步驟 7：驗證部署

訪問 Firebase Hosting URL（如 `https://PrAjeKt-prod.web.app`）：

**檢查清單：**

- [ ] 頁面正常加載（不是 404）
- [ ] 可以看到登入頁面
- [ ] Header 和 Sidebar 正常顯示
- [ ] **功能驗證：**
  - [ ] 登入成功（登錄後跳轉到首頁）
  - [ ] 可以看到任務列表
  - [ ] 可以看到時程表
  - [ ] WebSocket 連接成功（聊天功能工作）
  - [ ] 可以創建新任務/時程表

**troubleshooting：**

如果頁面無法加載或顯示 404：

1. 檢查 Firebase Console 的構建日誌：
   ```
   Firebase Console → Hosting → 構建和部署 → 最近的部署
   ```

2. 確認 `frontend/dist/` 目錄存在且包含 `index.html`

3. 強制刷新瀏覽器（Ctrl+Shift+R 或 Cmd+Shift+R）

---

## 🔧 常見問題排查

### Q1：WebSocket 連接失敗

**症狀：**
```
WebSocket connection failed
聊天功能無法使用
```

**排查步驟：**

1. 檢查 `frontend/.env.production` 中的 `VITE_SOCKET_URL` 是否正確

2. 驗證 Railway 後端健康檢查：
   ```bash
   curl https://your-railway-url/api/health
   # 預期回應：{"status": "ok"}
   ```

3. 檢查 `backend/app.py` 中 CORS 是否包含 Firebase 域名

4. 在瀏覽器開發者工具（F12）中查看 Network 標籤：
   - 搜索 WebSocket 連接
   - 檢查是否成功建立連接（Connection: 101 Switching Protocols）

---

### Q2：登入後頁面空白或 404

**症狀：**
```
登入成功但頁面無法加載
或顯示 Cannot GET /timelines
```

**原因：** SPA（Single Page Application）路由配置問題

**解決：**

Firebase 的 SPA 重寫規則應該已經在 `firebase.json` 中配置好了：

```json
"rewrites": [
  {
    "source": "**",
    "destination": "/index.html"
  }
]
```

如果沒有，手動添加後重新部署：

```bash
firebase deploy
```

---

### Q3：靜態資源 404（CSS/JS 無法加載）

**症狀：**
```
Failed to load script: /assets/index-xxx.js (404)
頁面無樣式、無功能
```

**排查步驟：**

1. 確認 `dist/` 目錄有 `assets/` 資料夾

2. 重新構建：
   ```bash
   npm run build
   ```

3. 檢查 `firebase.json` 中 `public` 是否設為 `dist`

4. 重新部署：
   ```bash
   firebase deploy
   ```

---

### Q4：API 請求返回 CORS 錯誤

**症狀：**
```
Access to XMLHttpRequest at 'https://railway-url/api/...' 
from origin 'https://firebase-url.web.app' 
has been blocked by CORS policy
```

**解決：**

1. 驗證 Railway 後端的 CORS 配置包含 Firebase Hosting 域名

2. 推送更新：
   ```bash
   git add backend/app.py
   git commit -m "chore(cors): 更新 CORS 配置"
   git push origin main
   ```

3. 等待 Railway 重新部署（約 1-2 分鐘）

4. 強制刷新前端頁面（Ctrl+Shift+R）

---

## 🔄 自動部署配置

Firebase 部署後，你可以設置自動部署：

### 從 GitHub 自動部署（可選）

1. 訪問 Firebase Console → Hosting

2. 點擊「Connect Repository」

3. 授權 GitHub 並選擇 PrAjeKt 倉庫

4. 配置構建設定：
   ```
   Build command: npm run build
   Publish directory: dist
   ```

5. 確認後，Firebase 將自動監視 main 分支的變更並自動部署

---

## 📊 部署後的檢查清單

| 項目 | 完成 |
|------|------|
| Railway 後端健康檢查通過 | ☐ |
| `frontend/.env.production` 已配置 | ☐ |
| 後端 CORS 已更新 | ☐ |
| 本地構建成功 (`npm run build`) | ☐ |
| Firebase CLI 已安裝 | ☐ |
| Firebase 初始化完成 | ☐ |
| `firebase.json` 已生成 | ☐ |
| Firebase Hosting 部署成功 | ☐ |
| 前端頁面可訪問 | ☐ |
| 登入功能正常 | ☐ |
| API 請求成功 | ☐ |
| WebSocket 連接成功 | ☐ |

---

## 🎯 部署完成後

**你將獲得：**

前端公網 URL：
```
https://PrAjeKt-prod.web.app
```

**下一步行動：**

1. ✅ 分享前端 URL 給用戶
2. ✅ 測試完整工作流（登入 → 創建 → 聊天 → 任務）
3. ✅ 監控 Firebase Console 的流量
4. ✅ 進入 Phase 5.4 — 端到端測試與監控

---

## 📈 部署架構圖

```
┌─────────────────────────────────────────────────────┐
│         PrAjeKt 生產部署架構                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  用戶瀏覽器                                          │
│      ↓ 訪問                                         │
│  ┌─────────────────────────────────────┐            │
│  │  Firebase Hosting                   │            │
│  │  (https://PrAjeKt.web.app)       │            │
│  │  ├─ Vue 3 SPA                      │            │
│  │  └─ TypeScript + Vite              │            │
│  └─────────────────────────────────────┘            │
│      ↓ API 請求                                    │
│  ┌─────────────────────────────────────┐            │
│  │  Railway 後端                       │            │
│  │  (https://PrAjeKt.railway.app)   │            │
│  │  ├─ Flask + Socket.IO              │            │
│  │  ├─ Gunicorn + Eventlet            │            │
│  │  └─ Python 業務邏輯                │            │
│  └─────────────────────────────────────┘            │
│      ↓ SQL 連接                                    │
│  ┌─────────────────────────────────────┐            │
│  │  Supabase PostgreSQL                │            │
│  │  (15 個表格，免費版)                │            │
│  └─────────────────────────────────────┘            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🆘 快速支援

| 問題 | 快速檢查 |
|------|---------|
| 頁面無法加載 | Firebase 部署成功嗎？`firebase.json` 配置正確嗎？ |
| API 失敗 | Railway 健康檢查通過嗎？CORS 配置包含 Firebase 域名嗎？ |
| WebSocket 不工作 | `VITE_SOCKET_URL` 正確嗎？後端已重新部署嗎？ |
| 靜態資源 404 | `npm run build` 生成了 `dist/` 嗎？ |

---

**預計時間：** 5-10 分鐘  
**難度：** ⭐⭐ 中等  
**成功率：** >90%（如遵循步驟）

開始部署吧！🚀
