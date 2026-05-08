# 本地開發、測試與部署 Runbook

> 更新日期：2026-05-08  
> 目的：讓專案可重現、可驗證、可回滾。

---

## 1. 本地啟動（推薦）

### 1.1 一鍵初始化（首次）

```bat
bootstrap_pg_local.bat
```

### 1.2 日常啟動

```bat
start_all.bat
```

---

## 2. 手動啟動（除錯用）

### 2.1 Backend

```bat
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python.exe app.py
```

### 2.2 Frontend

```bat
cd frontend
npm install
npm run dev
```

---

## 3. 測試分層（建議固定）

## 3.1 Smoke（每次改動至少跑）

- 前端：改動頁面對應測試檔
- 後端：改動 blueprint/service 對應測試檔

## 3.2 Domain（同一模組較大改動時）

- `tasks` / `timelines` / `knowledge` 主題測試

## 3.3 Full（發版前）

```bat
cd backend
venv\Scripts\python.exe -m pytest
```

```bat
cd frontend
npm run test:run
```

---

## 4. 常見問題處理

## 4.1 Vitest `spawn EPERM`

現象：啟動測試時卡在 esbuild/vite config 載入。  
處理順序：

1. 確認 Node LTS 版本
2. 重新安裝依賴（刪 `node_modules` + lockfile 後重裝）
3. 以系統管理員權限啟動終端
4. 檢查防毒/Defender 是否攔截 `node_modules` 執行

## 4.2 `.pytest_cache` 權限 warning（Windows）

若是 warning 且測試數量全綠，視為非致命；必要時清快取重跑。

---

## 5. 提交與發版建議

1. 小步提交（一次只做一類變更）  
2. 每個 commit 附上測試證據（至少 smoke）  
3. 發版前更新三份文件：
   - 架構與責任邊界
   - API 契約與錯誤處理
   - 本 Runbook

---

## 6. 回滾策略

- 短期：`git stash` 保留工作快照  
- 穩定點：`git commit`（可 `git revert <sha>`）  
- 重大修改建議分兩波提交，第一波可用時先封存再做第二波

