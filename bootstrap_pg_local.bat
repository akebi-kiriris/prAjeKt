@echo off
chcp 65001 >nul
REM 一鍵初始化本地 PostgreSQL + 遷移 SQLite 舊資料 + 啟動前後端

echo [1/4] 啟動 PostgreSQL 容器...
docker compose up -d postgres
if errorlevel 1 (
  echo [ERROR] PostgreSQL 容器啟動失敗，請先確認 Docker Desktop 已啟動。
  pause
  exit /b 1
)

echo [2/4] 套用 schema migration...
cd /d backend
call venv\Scripts\python.exe -m flask --app app.py db upgrade
if errorlevel 1 (
  echo [ERROR] flask db upgrade 失敗。
  pause
  exit /b 1
)

echo [3/4] 遷移 SQLite 舊資料（目標若已有資料將自動略過）...
call venv\Scripts\python.exe migrate_sqlite_to_postgres.py --sqlite-path instance/prajekt.db --pg-dsn postgresql://postgres:postgres@localhost:5433/prajekt --skip-if-not-empty
if errorlevel 1 (
  echo [ERROR] SQLite -> PostgreSQL 資料遷移失敗。
  pause
  exit /b 1
)
cd /d ..

echo [4/4] 啟動前後端...
call start_all.bat
