# backend

這裡是 Learnlink / PrAjeKt 的 Flask 後端主體，包含 HTTP API、業務邏輯、資料存取、AI / agent 流程與測試。

## 目錄分工

- `blueprints/`: HTTP route 與 request / response 邊界
- `services/`: 業務流程、交易邊界、跨 repository 協調
- `repositories/`: 資料查詢、寫入與 session helper
- `models/`: SQLAlchemy ORM model 與資料結構
- `chains/`: LangChain / LangGraph / agent 流程
- `prompts/`: Prompt template 與 AI 文字模板
- `realtime/`: Socket.IO 即時事件
- `migrations/`: Alembic / Flask-Migrate migration
- `scripts/`: 一次性 backfill、DB 初始化與診斷腳本
- `tests/`: pytest 測試與共用測試設定
- `uploads/`: 本地執行時的附件與知識檔案
- `instance/`: 本地 SQLite 與 instance data

## 根層常見檔案

- `app.py`: Flask 應用入口
- `requirements.txt`: 後端開發 / 測試依賴
- `.env.example`: 後端環境變數範本

## 額外工具腳本

- `scripts/backfill/`: 舊資料補填腳本
- `scripts/db/`: DB 初始化 / migration 輔助 / SQLite 資料遷移腳本
- `scripts/diagnostics/`: 本地資料庫診斷腳本

## 這層應該負責什麼

- 對外提供 API 與即時通訊能力
- 承接專案、任務、知識庫、Copilot / agent 等後端主流程
- 維持服務層、資料層與 AI 流程層的責任邊界

## 不應該放什麼

- 前端展示邏輯
- 臨時筆記或分析文件
- 與專案無關的單次腳本長期留在根層

## 修改判斷

- API 行為、驗證與權限邊界：先看 `blueprints/` 與 `services/`
- 資料怎麼查、怎麼存：先看 `repositories/` 與 `models/`
- Agent / tool / LLM 流程：先看 `chains/`、`services/contracts/`、`services/tools/`
- migration、部署初始化與本地 DB 切換：先看 `migrations/`、`scripts/db/`、`scripts/`
