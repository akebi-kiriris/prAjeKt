@echo off
chcp 65001 >nul
REM 啟動 PrAjeKt 專案前後端（PostgreSQL 本地主線）

echo [1/5] 啟動 PostgreSQL 容器...
docker compose up -d postgres
if errorlevel 1 (
    echo [ERROR] PostgreSQL 容器啟動失敗，請先確認 Docker Desktop 已啟動。
    pause
    exit /b 1
)

echo [2/5] 套用資料庫 migration...
cd /d backend
call venv\Scripts\python.exe -m flask --app app.py db upgrade
if errorlevel 1 (
    echo [ERROR] 資料庫 migration 失敗。
    pause
    exit /b 1
)
cd /d ..

echo [3/5] 清理舊後端進程（避免多個 app.py 同時監聽 5000）...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq PrAjeKt Backend" >nul 2>&1

echo [4/5] 啟動後端（本地 PostgreSQL）...
start "PrAjeKt Backend" cmd /k "cd /d backend && call venv\Scripts\activate.bat && set PYTHONUNBUFFERED=1 && python -u app.py"

REM 小延遲，確保後端啟動
timeout /T 2 /NOBREAK >nul

echo [5/5] 寫入前端環境設定並啟動...
(
    echo VITE_API_BASE_URL=http://localhost:5000/api
    echo VITE_SOCKET_URL=http://localhost:5000
) > "frontend\.env.development"

start "PrAjeKt Frontend" cmd /k "cd /d frontend && npm run dev"

echo 前後端啟動完成。前端連接本地後端：http://localhost:5000
echo 後端連接本地 PostgreSQL：postgresql://postgres:postgres@localhost:5433/prajekt
pause
