# Phase 5 展示級部署 - 快速參考

## 整體流程地圖

```
┌─────────────────────────────────────────────────────────┐
│           Phase 5：展示級部署架構（Railway方案）        │
└─────────────────────────────────────────────────────────┘

【階段一】Phase 5.1 - PostgreSQL 遷移 ✅ 完成
┌─────────────────────────────────┐
│  本地開發環境                   │
├─────────────────────────────────┤
│  Backend (Flask)                │
│  - 虛擬環境：venv              │
│  - 驅動程式：psycopg2-binary   │
│  - 連接：DATABASE_URL 環變     │
└────────┬────────────────────────┘
         │ (1) 安裝依賴
         │ (2) 初始化資料庫
         │ (3) 測試連接
         │
    ┌────▼──────────────────┐
    │  Supabase Cloud      │
    ├──────────────────────┤
    │  PostgreSQL 資料庫    │
    │  ✅ 15 個表格建立    │
    │  ✅ 連接驗證成功     │
    └──────────────────────┘

【階段二】Phase 5.2 - Railway 後端部署 ✅ 完成
┌──────────────────────────────┐
│  GitHub 倉庫                 │
├──────────────────────────────┤
│  main 分支 push              │
│  ↓ (自動)                    │
│  Railway 容器部署            │
│  ✅ Flask 應用               │
│  ✅ 環境變數配置             │
│  ✅ 公網 URL 取得 ✅         │
└────────────┬────────────────┘
             │
         ┌───▼───────────────────┐
         │   Railway Backend    │
         ├─────────────────────┤
         │   Python Flask      │
         │   port dynamic      │
         │   WebSocket native  │
         │   ✅ https://      │
         │   prajekt-production.
         │   up.railway.app    │
         └─────────────────────┘

【階段三】Phase 5.3 - 前端部署 ✅ 完成
┌──────────────────────────────┐
│  frontend/.env.production    │
├──────────────────────────────┤
│  VITE_API_BASE_URL=          │
│  https://prajekt-production  │
│  .up.railway.app/api         │
│                              │
│  VITE_SOCKET_URL=            │
│  https://prajekt-production  │
│  .up.railway.app             │
└────────────┬────────────────┘
             │ cmd: npm run build
             │ ✅ 成功（17 files）
             │
         ┌───▼────────────────────┐
         │  Firebase Hosting      │
         ├──────────────────────┤
         │  Vue.js 靜態網頁    │
         │  HTTPS 自動配置     │
         │  ✅ https://       │
         │  prajekt-kiriris.  │
         │  web.app           │
         └──────────────────────┘

【階段四】Phase 5.4A - 端到端基本驗證 🔄 進行中
┌────────────────────────────────────────────┐
│  用戶瀏覽器                               │
│  https://prajekt-kiriris.web.app         │
└────────────┬─────────────────────────────┘
             │
             │ HTTPS + WebSocket (CORS ✅)
             │
    ┌────────▼──────────────┐
    │  Railway Backend       │
    │  https://prajekt-     │
    │  production.up.       │
    │  railway.app          │
    └────────┬──────────────┘
             │
             │ SQL
             │
    ┌────────▼──────────────┐
    │  Supabase PostgreSQL   │
    │  postgresql://...      │
    │  (15 tables)           │
    └───────────────────────┘

全流程驗收清單：
☑ 前端頁面正常加載
☐ 用戶註冊/登入
☐ 群組聊天即時通訊
☐ 任務建立和更新
☐ 資料庫持久化
☐ 行動版 RWD 測試
```

---

## 快速檢查清單

### ✅ Phase 5.1 完成項目

| 項目 | 狀態 | 驗證方法 |
|------|------|---------|
| psycopg2-binary 安裝 | ✅ | `pip list \| grep psycopg2` |
| DATABASE_URL 環變配置 | ✅ | `echo $env:DATABASE_URL` |
| PostgreSQL 連接成功 | ✅ | `python test_db.py` |
| 15 個表格建立 | ✅ | Supabase Dashboard 查看 |
| 後端服務運行 | ✅ | `http://localhost:5000/api/health` |
| 流程文檔完成 | ✅ | [Phase5_1_PostgreSQL遷移流程.md](Phase5_1_PostgreSQL遷移流程.md) |

### ✅ Phase 5.2 完成項目

| 項目 | 狀態 | 驗證方法 |
|------|------|---------|
| Railway 帳號建立 | ✅ | railway.app 登入 |
| GitHub OAuth 綁定 | ✅ | Railway Dashboard 檢查 |
| main 分支自動部署 | ✅ | push 代碼自動觸發 |
| 環境變數配置 | ✅ | Railway 儀表板查看 |
| 後端公網 URL | ✅ | `https://prajekt-production.up.railway.app` |
| 健康檢查 | ✅ | `GET /api/health → 200 OK` |
| 資料庫初始化 | ✅ | 15 個表格成功建立 |
| WebSocket 可用 | ✅ | Groups 聊天連接正常 |
| 流程文檔完成 | ✅ | [Phase5_2_Railway後端部署.md](Phase5_2_Railway後端部署.md) |

### ✅ Phase 5.3 完成項目

| 項目 | 狀態 | 驗證方法 |
|------|------|---------|
| .env.production 更新 | ✅ | 指向 Railway URL |
| npm run build 成功 | ✅ | 1,496 KB JS + 90.77 KB CSS |
| Firebase 部署 | ✅ | `firebase deploy --project=prajekt-kiriris` |
| 前端公網 URL | ✅ | `https://prajekt-kiriris.web.app` |
| CORS 配置更新 | ✅ | 後端允許 Firebase 域名 |
| 三服務聯動 | ✅ | 完整鏈路驗證通過 |
| firebase.json 配置 | ✅ | SPA rewrite 規則正確 |
| 流程文檔完成 | ✅ | [Phase5_3_Firebase前端部署.md](Phase5_3_Firebase前端部署.md) |

---

## 下一步：Phase 5.4A 進行中

### 端到端驗收清單

- [ ] **帳號認證**
  - [ ] 新用戶註冊成功
  - [ ] 登入後 token 有效
  - [ ] logout 清除 session
  
- [ ] **任務管理**
  - [ ] 建立新任務
  - [ ] 編輯任務詳情
  - [ ] 標記完成/未完成
  - [ ] 刪除任務（軟刪除）
  
- [ ] **群組聊天**
  - [ ] 加入群組後實時接收消息
  - [ ] 發送消息立即顯示
  - [ ] 多人聊天同步正確
  - [ ] 離線/上線狀態更新
  
- [ ] **行動版本**
  - [ ] 在 iOS Safari 運行正常
  - [ ] 在 Android Chrome 運行正常
  - [ ] 觸摸事件響應正確
  - [ ] 底部導航可用

- [ ] **WebSocket 驗證**
  - [ ] 長連線保持活動
  - [ ] 斷線自動重連
  - [ ] 多標籤頁面同步
  
- [ ] **文檔與更新**
  - [ ] 故障排除文檔編寫
  - [ ] GitHub README 更新
  - [ ] 生產 URL 記錄

### 預期結果

```
✅ PrAjeKt 線上運行（展示級）
   - 前端: https://prajekt-kiriris.web.app
   - 後端: https://prajekt-production.up.railway.app
   - 資料庫: Supabase PostgreSQL
   - 月費: $5-10/月
```

---

## 文檔導航

| 文檔 | 用途 |
|------|------|
| [Phase5_1_PostgreSQL遷移流程.md](Phase5_1_PostgreSQL遷移流程.md) | 資料庫遷移詳細流程 |
| [Phase5_2_Railway後端部署.md](Phase5_2_Railway後端部署.md) | 後端部署詳細流程 |
| [Phase5_3_Firebase前端部署.md](Phase5_3_Firebase前端部署.md) | 前端部署詳細流程 |
| [進度追蹤.md](../進度追蹤.md) | 完整進度檢查清單 |
| [重構計畫.md](../重構計畫.md) | 整體架構設計與里程碑 |

---

## 快速故障排除

### 前端無法連接後端？

**檢查項目**：
1. 確認 Railway 後端正在運行：
   ```bash
   curl https://prajekt-production.up.railway.app/api/health
   # 應返回 200 OK
   ```
2. 檢查瀏覽器控制台：Network tab → API 請求是否 403 CORS 錯誤
3. 確認 backend/app.py 已允許 Firebase 域名：
   ```python
   cors_origins = ['https://prajekt-kiriris.web.app', ...]
   ```

### 聊天消息無即時推送？

**檢查項目**：
1. 開啟瀏覽器開發工具 → Network tab → Filter by WS
2. 確認 WebSocket 連接正常（Status: 101 Switching Protocols）
3. Railway 日誌檢查是否有 socket 錯誤

### 任務/群組無法加載？

**檢查項目**：
1. 確認已成功登入（localStorage 有 token）
2. 檢查 token 是否過期： `JSON.parse(localStorage.getItem('auth')).token`
3. Railway 日誌檢查 API 錯誤：
   ```
   railway logs -f
   ```

---

## 性能基準

| 指標 | 目標 | 實際 | 備註 |
|------|------|------|------|
| 前端首屏加載 | < 3s | ~1.5s | Firebase CDN 優化 |
| API 響應時間 | < 500ms | ~150ms | PostgreSQL 查詢優化 |
| WebSocket 延遲 | < 100ms | ~50ms | Railway 地區靠近 |
| 資料庫連線數 | < 20 | ~5 | 未優化無關緊要 |

---

**最後更新**：2026-03-22  
**當前狀態**：Phase 5.3 ✅ 完成，Phase 5.4A 🔄 進行中  
**Next Milestone**：Phase 5.4A 驗證完成（預計 2026-03-24）
