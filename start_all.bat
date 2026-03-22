@echo off
chcp 65001 >nul
REM 啟動 PrAjeKt 專案前後端

REM 啟動後端 (進入虛擬環境)
cd backend
call venv\Scripts\activate.bat
start cmd /k "set DATABASE_URL=sqlite:///instance/prajekt.db&& set FLASK_ENV=development&& python app.py"
cd ..

REM 啟動前端
cd frontend
start cmd /k "set VITE_API_BASE_URL=http://localhost:5000/api&& set VITE_SOCKET_URL=http://localhost:5000&& npm run dev"
cd ..

echo 前後端啟動指令已執行。
pause
