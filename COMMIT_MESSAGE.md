feat(deploy): 完成 Phase 5.1 PostgreSQL 遷移與 Phase 5.2 Railway 部署準備

## Summary
- 完成 SQLite -> Supabase PostgreSQL 遷移流程
- 新增 Railway 部署啟動與進程配置
- 調整 Flask 啟動方式以支援雲端動態 Port
- 更新專案進度追蹤與重構計畫到 Phase 5.2

## Backend Changes
- `backend/app.py`
  - 加入 dotenv 載入流程
  - 啟動改為讀取 `PORT` 環境變數
  - 綁定 `0.0.0.0` 以相容 Railway 執行環境
- `backend/requirements.txt`
  - 新增 `psycopg2-binary` 供 PostgreSQL 連線
- `backend/init_db.py`
  - 新增資料庫初始化腳本（建立核心資料表）
- `backend/test_db.py`
  - 新增連線與資料表驗證腳本

## Deployment Files
- `start.sh`
  - Linux 啟動腳本（安裝依賴、初始化 DB、啟動後端）
- `Procfile`
  - 定義 Railway web process 啟動命令
- `railway.json`
  - 指定 Railway 使用 nixpacks builder

## Docs & Tracking
- 更新 `進度追蹤.md`
  - 標記 Phase 5.1 完成
  - 標記 Phase 5.2 進行中並補齊任務清單
- 更新 `重構計畫.md`
  - 同步 Phase 5 上線整合狀態與里程碑

## Result
- 專案已具備：
  - Supabase PostgreSQL 連線與初始化流程
  - Railway 可部署所需基礎檔案
  - 與現況一致的部署追蹤文件
