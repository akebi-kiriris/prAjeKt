# Phase 6.6 LangChain + LangGraph 重構計劃

## 1. 目標與原則

- 目標：從 `google-generativeai` 直接 SDK 呼叫，遷移為 LangChain/LangGraph 抽象層。
- 原則：
  - 服務層不直接耦合模型 SDK。
  - Prompt、模型、解析器分層。
  - 先保功能穩定，再引入 LangGraph 流程編排。

## 2. 現況問題

- `backend/services/ai_provider.py` 直接使用 Google SDK，與服務邏輯耦合高。
- `backend/chains/*.py` 使用舊版 LangChain API（如 `langchain.chains`、`langchain.schema.output_parser`）。
- `timeline_service` 與 `copilot_service` 仍走 `provider.generate_content()`，未使用 chain。
- `prompts/tool_selector.py` 的欄位命名與服務層使用不一致。

## 3. 重構範圍

- 核心層：
  - `backend/chains/llm_factory.py`
  - `backend/chains/task_generation_chain.py`
  - `backend/chains/tool_selection_chain.py`
  - `backend/chains/summary_chain.py`
- 服務層：
  - `backend/services/timeline_service.py`
  - `backend/services/copilot_service.py`
  - `backend/services/ai_provider.py`（轉為薄 adapter）
- 依賴：
  - `backend/requirements.txt` 補回 LangChain/LangGraph 套件。

## 4. 分階段實施

### 階段 A：修核心（先做）

1. `llm_factory` 改用 `langchain_google_genai.ChatGoogleGenerativeAI`。
2. chains 改為 LCEL + `JsonOutputParser` / `StrOutputParser`。
3. prompts 參數命名與 chain 呼叫對齊。

驗收：
- `from chains import get_default_llm` 可正常 import。
- `generate_tasks()`、`select_tools()` 可回傳可解析 JSON。

### 階段 B：接服務層（本輪開始）

1. `timeline_service.generate_timeline_tasks_with_ai()` 改接 `generate_tasks()`。
2. `copilot_service._ai_select_tool()` 改接 `select_tools()`。
3. 保留 keyword fallback，避免 AI 不可用時功能中斷。

驗收：
- 任務生成功能可用。
- 工具選擇可用，錯誤時可 fallback。

### 階段 C：LangGraph 初始節點（下一輪）

1. 建立 `langgraph` 基礎 state（tool-selection -> execution）。
2. 先接一條流程（timeline_generate_tasks）。

驗收：
- 可用 LangGraph 跑完整最小流程。

## 5. 回滾策略

- 服務層保留 fallback 邏輯。
- 每個階段完成後先做 smoke test，再往下階段推進。

## 6. 本次實作清單（Start Implement）

- [x] 撰寫本計劃文件。
- [ ] 升級 `llm_factory.py`。
- [ ] 重寫 task/tool/summary chains。
- [ ] 改接 `timeline_service.py`。
- [ ] 改接 `copilot_service.py`。
- [ ] 更新 requirements 並驗證。
