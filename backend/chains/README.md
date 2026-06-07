# backend/chains

這層負責 AI / agent 的流程控制，包含 LangGraph state、nodes、graph 接線，以及部分 LLM chain 組裝。

## Phase 9 最重要的檔案

- `agent_state.py`: Agent 共用狀態模型
- `agent_nodes.py`: intent parse、tool select、tool execute、error route、finalize 等核心節點
- `agent_graph.py`: LangGraph 接線與執行入口

## 其他常見檔案

- `tool_selection_chain.py`: 工具選擇相關 chain
- `rag_planning_chain.py`: RAG 規劃相關 chain
- `summary_chain.py`: 摘要生成
- `llm_factory.py`: LLM 建立與設定

## 這層應該負責什麼

- Agent 狀態如何在節點間流動
- 工具執行順序與錯誤路由
- LLM / chain 的流程編排
- Graph 的 entry point 與 conditional edge

## 不應該放什麼

- 具體資料庫讀寫
- 直接寫大量核心業務邏輯
- 前端互動細節

## 修改判斷

- 如果是在問「下一步該跑哪個 tool」或「錯誤後要 retry / stop / ask_user」，先看這層
- 如果是在問「某個能力真正怎麼建立任務 / 更新資料」，先看 `backend/services/`
- 若只是調整工具 schema，不要直接改 chain，先檢查 `backend/services/contracts/`
