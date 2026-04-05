@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================================
REM PrAjeKt MCP Inspector 啟動腳本
REM ============================================================================
REM 功能：一鍵啟動 MCP Inspector 來測試 RAG 工具
REM 前置：確保後端已運行（start_all.bat）
REM ============================================================================

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo.
echo [步驟 1/3] 檢查依賴...

if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] 找不到後端 Python 虛擬環境
    echo 請執行：start_all.bat
    pause
    exit /b 1
)

where npx >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 找不到 Node.js（npx）
    echo 請安裝 Node.js：https://nodejs.org
    pause
    exit /b 1
)

echo [✓] 依賴檢查完成

echo.
echo [步驟 2/3] 準備 MCP 依賴...

REM 確保 Python 包已安裝
call backend\venv\Scripts\pip.exe install -q mcp requests python-dotenv 2>nul

echo [✓] MCP 依賴準備完成

echo.
echo [步驟 3/3] 啟動 MCP Inspector...
echo.
echo 工具清單：
echo   - task_comment_summary（任務評論摘要）
echo   - group_snapshot（群組快照）
echo.
echo [提示] 開啟後請按左側 Connect。
echo [提示] 請選 Server Entry，不要選 Servers File（避免讀到舊的 localhost:3001/sse 設定）。
echo [提示] 本腳本已關閉 Inspector Proxy Token 驗證，避免網址 token 造成連線失敗。
echo.

REM 關鍵：用完整路徑執行
set "DANGEROUSLY_OMIT_AUTH=true"
call npx -y @modelcontextprotocol/inspector --transport stdio "%ROOT_DIR%backend\venv\Scripts\python.exe" "mcp_server.py"

pause
