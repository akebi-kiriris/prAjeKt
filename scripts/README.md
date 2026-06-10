# scripts

這裡放 repo 根層的輔助腳本，原則上是開發或維護用途，不屬於正式應用執行流程。

## 目前檔案

- `count_loc.py`: 粗略統計程式碼行數用的輔助腳本

## 這層應該負責什麼

- 開發輔助
- 結構盤點
- 一次性分析型腳本

## 不應該放什麼

- 需要正式部署時執行的應用主流程
- 與 backend 啟動強耦合的 operational script

## 修改判斷

- 如果腳本只是幫你本地分析 repo、整理數據、統計結構，放這裡合理
- 如果腳本開始直接依賴後端 app context、DB migration 或診斷流程，優先考慮收進 `backend/scripts/`
