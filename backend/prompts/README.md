# backend/prompts

這層集中放 AI 能力使用的 prompt template、輸入說明與 prompt 組裝 helper，目的是把「模型要看到什麼文字規則」集中管理，避免 prompt 散落在 chain、service 或 route 裡。

可以把它理解成：

- `chains/` 決定什麼時候叫模型、前後流程怎麼跑
- `services/` 決定業務上要做什麼
- `prompts/` 決定模型在某一步到底看到什麼指令與格式要求

## 目前檔案與角色

- `task_generator.py`
  - 任務生成 prompt
  - 偏單純模板型，重點在欄位要求與輸出 JSON 格式
- `tool_selector.py`
  - 工具單選路由 prompt
  - 重點是限制只能從可用工具中挑一個
- `tool_planner.py`
  - agent tool planning prompt 與組裝 helper
  - 除了固定規則，也負責把 `tool_lines`、`context`、保護欄位等資料整理成最終 prompt
- `timeline_task_request.py`
  - timeline 任務生成請求文字組裝
  - 先把現有任務轉成模型易讀的文字，再代入模板
- `timeline_insights.py`
  - 週報摘要、衝突建議等分析型 prompt
- `summary_templates.py`
  - 任務摘要、群組摘要等摘要型 prompt
- `rag_planning.py`
  - RAG 規劃 prompt，吃檢索結果後輸出可落地規劃

## 這層應該負責什麼

- prompt 固定規則
- LLM 任務描述
- 輸出格式要求
- few-shot 或範例文字
- 把動態資料整理成 prompt 文字的 helper

## 這層不應該負責什麼

- Graph 節點流程控制
- 什麼情況該走哪條流程
- 真正的商業邏輯判斷
- 工具註冊與 handler 呼叫
- repository / database 查詢

## 最重要的分界

### prompt 層負責

- 模型要遵守哪些規則
- 模型輸出要長什麼格式
- context 應該如何被描述給模型看
- 清單、結構化資料、限制條件怎麼轉成模型易讀文字

### service / chain 層負責

- 是否要呼叫模型
- 呼叫哪個模型
- 模型結果是否可接受
- 失敗時怎麼 fallback
- 後續是不是要真的寫入系統

一句話版本：

- `prompts/` 負責「怎麼說」
- `services/` / `chains/` 負責「何時做、做完怎麼處理」

## 目前 prompt 的兩種主要型態

### 1. `PromptTemplate` 型

這類 prompt 骨架相對穩定，只需要代入少量欄位。

常見特徵：

- 只有少數 placeholder，例如 `user_input`、`context`、`project_name`
- 不需要先展開複雜清單
- 固定規則遠多於動態資料

目前例子：

- `task_generator.py`
- `tool_selector.py`
- `timeline_insights.py`
- `summary_templates.py`
- `rag_planning.py`

適合情境：

- 請模型摘要
- 請模型根據幾個欄位輸出 JSON
- 請模型根據固定上下文做分類、判斷、生成

### 2. `build_xxx_prompt(...)` 型

這類 prompt 不只是代入變數，而是要先做一層文字組裝。

常見特徵：

- 要先把多筆資料整理成條列文字
- 要把結構化資料轉成 JSON 字串
- 要根據輸入動態補出限制段落
- 直接在 service 內拼字串會讓 service 變得很亂

目前例子：

- `timeline_task_request.py`
- `tool_planner.py`

適合情境：

- 給模型看的工具清單是動態的
- 現有任務、檢索結果、限制欄位很多
- prompt 不只是「插值」，而是「先整理資料再描述給模型」

## 怎麼判斷該用哪一種

可以用這個簡單判斷：

- 只有 3 到 5 個簡單欄位要代入：先用 `PromptTemplate`
- 有列表、巢狀資料、JSON 片段要先組：考慮 builder helper
- service 裡開始出現大量 `"\n".join(...)`、`json.dumps(...)`、限制段落拼接：通常應該往 `prompts/` 抽

## 實作原則

- 固定規則留在 `prompts/`
- 動態資料的「文字組裝」可以留在 `prompts/`
- 真正的 domain 決策不要塞進 helper
- helper 只處理「怎麼把資料講給模型聽」，不要處理「業務上應不應該做」

## builder helper 的責任邊界

### 可以做

- 展開清單
- 組出條列文字
- 把資料序列化成 JSON
- 插入輸出格式說明
- 根據欄位有無補充 prompt 段落

### 不該做

- 決定要不要建立 timeline
- 判斷目前應走哪條 agent flow
- 決定 fallback 策略
- 修改資料本身的商業意義

如果 helper 已經開始知道：

- 哪個工具應該先跑
- 哪個 domain 行為才是正確流程
- 哪種失敗要怎麼補償

那通常代表它已經不是 prompt helper，而是在偷做 service / chain 的事了。

## 變更 prompt 時要一起檢查什麼

### 改輸出格式時

同步檢查：

- `services/contracts/`
- prompt 結果解析程式
- 前端或後端依賴該格式的 consumer

### 改意圖判斷規則時

同步檢查：

- `chains/` 的節點流程
- tool registry / planner metadata
- fallback 是否仍合理

### 改語氣或摘要要求時

同步檢查：

- 前端呈現是否仍適合直接顯示
- 測試是否有寫死字串或格式假設

## 修改判斷速查

- 模型誤解需求：先看 `prompts/`
- 模型輸出格式老是錯：先看 `prompts/`，再看 parser
- 同樣資料被組成很醜的 prompt：先看 builder helper
- 節點順序錯了：先看 `backend/chains/`
- 真正業務流程不對：先看 `backend/services/`

## 建議的命名方式

- 單純模板：`XXX_PROMPT`
- 需要文字組裝：`build_xxx_prompt(...)`
- 若同檔同時有固定規則與 helper，可採：
  - `XXX_SYSTEM_PROMPT`
  - `build_xxx_prompt(...)`

## 目前這層的目標

這層不是要把所有 AI 相關 code 都搬進來，而是要讓 prompt 有明確歸屬：

- prompt 規則看這裡
- prompt 組裝看這裡
- 流程控制不要混進來

這樣後續你在調整 agent、RAG、摘要、planner 時，才不會每次都要重新追整條 service 流。  
