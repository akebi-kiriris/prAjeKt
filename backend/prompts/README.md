# backend/prompts

這層集中放 AI 能力使用的 prompt template 與文字模板，避免 prompt 內容散落在 chain 或 service 裡。

## 常見檔案

- `rag_planning.py`: RAG 規劃相關 prompt
- `summary_templates.py`: 摘要類 prompt
- `task_generator.py`: 任務生成 prompt
- `timeline_insights.py`: 專案洞察 / 分析 prompt
- `timeline_task_request.py`: 任務請求整理 prompt
- `tool_selector.py`: 工具選擇 prompt

## 這層應該負責什麼

- prompt 內容
- 文字模板組織
- 與 LLM 輸入輸出說明直接相關的固定文案

## 不應該放什麼

- Graph 節點流程控制
- 業務邏輯判斷
- 工具註冊與 handler 邏輯
- 資料庫查詢

## 修改判斷

- 如果模型理解使用者意圖、任務規劃方式、摘要語氣需要調整，先看這層
- 如果只是節點順序或 route 邏輯改變，先看 `backend/chains/`
- prompt 改動若會影響 schema，記得同步檢查 `services/contracts/`
