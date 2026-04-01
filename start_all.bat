@echo off
chcp 65001 >nul
REM 啟動 PrAjeKt 專案前後端（本地開發版本）

echo [1/3] 清理舊後端進程（避免多個 app.py 同時監聽 5000）...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq PrAjeKt Backend" >nul 2>&1

echo [2/3] 啟動後端（本地 SQLite）...
start "PrAjeKt Backend" cmd /k "cd /d backend && call venv\Scripts\activate.bat && set PYTHONUNBUFFERED=1 && python -u app.py"

REM 小延遲，確保後端啟動
timeout /T 2 /NOBREAK >nul

echo [3/3] 寫入前端環境設定並啟動...
(
    echo VITE_API_BASE_URL=http://localhost:5000/api
    echo VITE_SOCKET_URL=http://localhost:5000
) > "frontend\.env.development"

start "PrAjeKt Frontend" cmd /k "cd /d frontend && npm run dev"

echo 前後端啟動完成。前端連接本地後端：http://localhost:5000
echo 後端連接本地 SQLite：instance/prajekt.db
pause
