# backend/models

這層定義 SQLAlchemy ORM model，是資料表結構與關聯在程式中的對應。

## 常見檔案

- `task.py`, `subtask.py`, `task_comment.py`, `task_user.py`
- `timeline.py`, `timeline_user.py`
- `group.py`, `message.py`, `group_ai_snapshot.py`
- `knowledge.py`
- `notification.py`, `activity_log.py`
- `user.py`, `todo.py`

## 這層應該負責什麼

- 表欄位定義
- model 關聯
- 與資料結構直接相關的 helper

## 不應該放什麼

- 業務流程判斷
- HTTP response 組裝
- Agent tool 流程邏輯
- 大量跨 model 協調

## 修改判斷

- 如果需求是在問「資料表有哪些欄位、關聯怎麼接」，先看這層
- 如果需求是在問「什麼時候要建立 / 更新這些資料」，通常先回到 `services/`
- 欄位改動通常要同步檢查 `migrations/`、`repositories/`、`services/contracts/`
