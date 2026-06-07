# backend/repositories

這層負責資料存取。每個 repository 針對一類資料模型封裝查詢與寫入，避免 SQLAlchemy / session 細節散落到 service 各處。

## 常見檔案

- `task_repository.py`
- `timeline_repository.py`
- `group_repository.py`
- `knowledge_repository.py`
- `session_repository.py`

## 這層應該負責什麼

- 查詢、建立、更新、刪除資料
- 常用資料抓取模式封裝
- 與 session / transaction 配合的存取細節

## 不應該放什麼

- 使用者流程判斷
- API response 組裝
- Agent tool envelope
- LangGraph 狀態流轉

## 修改判斷

- 如果需求是「資料怎麼查、怎麼存」，看這層
- 如果需求是「什麼情況下應該查 / 應該存」，通常屬於 service 層
- 若同一查詢模式在多個 service 重複出現，考慮收斂到 repository
