@echo off
chcp 65001 >nul
REM 啟動 Learnlink 專案前後端

REM 啟動後端 (進入虛擬環境)
cd backend
call venv\Scripts\activate.bat
start cmd /k "flask run"
cd ..

REM 啟動前端
cd frontend
start cmd /k "npm run dev"
cd ..

echo 前後端啟動指令已執行。
pause
