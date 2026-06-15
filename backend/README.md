# Backend 目錄說明

`backend/` 是 Learnlink 的 Flask 後端主體，負責 API、業務流程、資料存取、AI/agent 流程、即時通訊與後端測試。

## 目錄分工

1. `blueprints/`
   - HTTP route、request/response 邊界與 API 層驗證。
2. `contracts/`
   - backend 共用契約層，供 blueprint / service / tool 共用 schema、envelope 與純欄位驗證。
3. `services/`
   - 業務流程、交易協調與跨 repository orchestration。
4. `repositories/`
   - 資料查詢、寫入與 session 存取封裝。
5. `models/`
   - SQLAlchemy ORM model 與資料結構定義。
6. `chains/`
   - LangGraph、LLM chain 與 agent 流程控制。
7. `prompts/`
   - AI prompt template 與 prompt 組裝 helper。
8. `realtime/`
   - Socket.IO 即時事件與連線邏輯。
9. `migrations/`
   - Alembic / Flask-Migrate schema 版本管理。
10. `scripts/`
   - 維護型腳本、初始化工具與診斷腳本。
11. `tests/`
   - pytest 測試與共用測試設定。

## 根層文件與入口

`backend/` 根層保留後端啟動與環境相關檔案，例如應用入口、依賴清單與環境範本。與單一子模組明確相關的文件或腳本，應優先放入對應子目錄。

## 責任邊界

`backend/` 應負責以下事項：

1. 對外提供 HTTP API 與即時通訊能力
2. 承接任務、專案、知識庫與 Copilot/agent 等後端主流程
3. 維持 API、service、repository、AI 流程之間的責任分層

以下內容不應長期堆放在本層：

1. 前端展示邏輯
2. 純文件或分析筆記
3. 與專案主流程無關的一次性程式碼

## 維護原則

1. 涉及目錄責任變動時，應同步更新對應子目錄 README。
2. 後端結構調整應優先維持 API、service、repository 與 chain 的清楚分界。
3. 若某類維護工具已穩定成日常流程，應重新評估其放置位置與命名方式。
