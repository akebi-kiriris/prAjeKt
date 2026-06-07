# Phase 6.6 LangChain 遷移指南

本文件說明 Learnlink 在 Phase 6.6 將 AI 流程從「服務層直接拼 prompt + 直接呼叫」重構為「LangChain Chain 化」的目的、現況與後續建議。

## 1. 目標

1. 統一 AI 呼叫入口，降低服務層與模型 SDK 的耦合。
2. 讓 Prompt 與解析邏輯可重用、可測試、可替換。
3. 為後續 LangGraph 多步驟流程（工具路由、任務規劃）鋪路。

## 2. 架構調整

### 2.1 重構前

- 服務層（例如 timeline / copilot）直接組 prompt，然後呼叫 provider。
- JSON 解析與容錯散落在多個 service 檔案中。

### 2.2 重構後

- `backend/prompts/`：集中管理 PromptTemplate。
- `backend/chains/`：集中管理 chain 與 JSON 解析邏輯。
- `backend/services/`：改為呼叫 chain 函式，保留必要 fallback。

## 3. 主要模組

### 3.1 Prompt 層（`backend/prompts/`）

#### `backend/prompts/task_generator.py`
- **用途**：任務生成的 PromptTemplate 定義
- **關鍵變數**：`{project_name}`, `{project_description}`, `{user_name}`, `{user_input}`
- **關鍵常數**：
  - `TASK_GENERATOR_PROMPT`：PromptTemplate 實例，輸出 JSON 陣列格式任務列表

#### `backend/prompts/tool_selector.py`
- **用途**：工具路由提示詞（Copilot MCP 工具選擇）
- **關鍵常數**：
  - `TOOL_SELECTOR_PROMPT`：PromptTemplate，輸出 JSON 物件（選中工具名稱 + 參數）

#### `backend/prompts/summary_templates.py`
- **用途**：群組快照與任務摘要提示詞
- **關鍵常數**：
  - `GROUP_SNAPSHOT_PROMPT`：生成群組摘要的 PromptTemplate
  - `TASK_SUMMARY_PROMPT`：生成單一任務摘要的 PromptTemplate

---

### 3.2 Chain 層（`backend/chains/`）

#### `backend/chains/llm_factory.py`
- **用途**：LLM 提供者工廠，統一封裝多種 AI 模型
- **關鍵函數**：
  - `get_default_llm(provider: str = None) -> Any`：取得預設 LLM 實例（目前主路徑 Google Generative AI）
  - `create_google_generative_ai(api_key: str, model: str, temperature: float) -> ChatGoogleGenerativeAI`：建立 Google Gemini LLM 實例
  - 其他 provider 工廠（如 OpenAI、Anthropic 等，預留擴展）

#### `backend/chains/prompt_manager.py`
- **用途**：集中管理 Prompt 配置（溫度、max_tokens、超時等）
- **關鍵類別**：`PromptManager`
- **關鍵方法**：
  - `get_config(prompt_type: str) -> Dict`：根據 prompt 類型回傳配置字典（temperature, max_tokens 等）
  - 內部映射表：`prompt_configs = {"task_generation": {...}, "tool_selection": {...}, ...}`

#### `backend/chains/task_generation_chain.py`
- **用途**：任務生成的完整 LangChain pipeline（包含 prompt、LLM、JSON 解析）
- **關鍵函數**：
  - `create_task_generation_chain(llm, prompt_template) -> Chain`：組建 chain 物件 (PromptTemplate | LLM | OutputParser)
  - `generate_tasks(llm, project_name, project_description, user_input, user_name) -> List[Dict]`：執行完整流程，回傳標準化後的任務清單
  - 內部輔助函數：
    - `_extract_json_from_response(raw_output: str) -> Dict`：從 LLM 回傳中提取 JSON（支援 markdown fence 清理）
    - `_validate_task_structure(task: Dict) -> Bool`：驗證單一任務物件結構

#### `backend/chains/tool_selection_chain.py`
- **用途**：工具選擇路由的 LangChain pipeline（Copilot MCP 工具決策）
- **關鍵函數**：
  - `create_tool_selection_chain(llm, available_tools) -> Chain`：組建工具選擇 chain
  - `select_tools(llm, user_query, available_tools) -> Dict`：執行工具選擇，回傳 `{tool_name: str, parameters: Dict}`

#### `backend/chains/summary_chain.py`
- **用途**：摘要/快照生成的 LangChain pipeline
- **關鍵函數**：
  - `create_summary_chain(llm, summary_type) -> Chain`：組建摘要 chain（type: "group_snapshot" 或 "task_summary"）
  - `generate_summary(llm, content, summary_type) -> Dict`：執行摘要生成，回傳 `{summary: str, tags: List[str]}`

#### `backend/chains/workflows.py`
- **用途**：LangGraph 工作流定義（多步驟工具路由）
- **關鍵函數**：
  - `create_tool_routing_workflow() -> CompiledStateGraph`：建立 LangGraph 工作流（工具選擇 → 執行 → 結果整理）
  - `run_workflow(input_state: Dict) -> Dict`：執行工作流

---

### 3.3 服務層接線（已完成部分）

#### `backend/services/timeline_service.py`
- **用途**：專案時間軸的業務邏輯層（包含 AI 任務生成編排）
- **關鍵函數**：
  - `generate_timeline_tasks_with_ai(timeline_id, project_name, description) -> Dict`：主業務方法，編排 AI 流程
    - 步驟 1：收集現有任務上下文
    - 步驟 2：構造完整 prompt
    - 步驟 3：取得 LLM 實例
    - 步驟 4：呼叫 `chains.generate_tasks()`
    - 步驟 5：標準化結果，回傳 `{message, tasks, existingCount, generatedCount}`
  - 內部輔助函數：
    - `_build_existing_tasks_info(timeline_id) -> List[Dict]`：查詢既有任務
    - `_build_ai_task_prompt(project_name, description, existing_tasks) -> str`：融合上下文組建 prompt
    - `_normalize_generated_tasks(parsed_tasks, timeline_id) -> List[Dict]`：補充標籤、timeline_id、status 等

#### `backend/services/copilot_service.py`
- **用途**：Copilot MCP 工具路由服務
- **關鍵函數**：
  - `_ai_select_tool(user_query, available_tools) -> Dict`：已改接 `chains.select_tools()`，回傳選中工具資訊

#### `backend/services/ai_provider.py`
- **用途**：統一的 AI 提供者入口（廢止舊的直接調用模式）
- **關鍵函數**：
  - `invoke_ai(prompt, chain_type, **kwargs) -> Any`：已全面改為透過 LangChain 呼叫

---

### 3.4 路由層（`backend/blueprints/`）

#### `backend/blueprints/timelines.py`
- **用途**：專案時間軸的 HTTP API 端點
- **關鍵路由**：
  - `GET /api/timelines` - 列出時間軸
  - `POST /api/timelines/{id}/generate-tasks` - **AI 任務生成入口**
    - 接收：`{project_name, description}`
    - 調用：`timeline_service.generate_timeline_tasks_with_ai()`
    - 回傳：`{message, tasks[], existingCount, generatedCount}`
  - `POST /api/timelines/{id}/batch-create-tasks` - 批量建立任務（由前端預覽後觸發）

---

### 3.5 前端集成（`frontend/src/`）

#### `frontend/src/services/timelineService.ts`
- **用途**：前端 HTTP 服務層，包裝時間軸 API 呼叫
- **關鍵函數**：
  - `generateTasks(timelineId, projectName, description) -> Promise<{tasks, message, ...}>`：發起 POST 請求至 `/api/timelines/{id}/generate-tasks`
  - 類型定義：TypeScript 嚴格模式，Query/Mutation 分離

#### `frontend/src/components/timelines/TimelineDetailDialog.vue`
- **用途**：時間軸詳情 Modal 組件，包含 AI 任務生成 UI
- **關鍵方法**：
  - `generateTasksWithAi()`：調用 `timelineService.generateTasks()`，顯示載入狀態
  - `batchCreateAiTasks()`：發起 POST 至 `/api/timelines/{id}/batch-create-tasks`，建立選中任務
  - `toggleAllAiTasks()`：全選/反選生成的任務
  - 渲染：任務預覽卡片、優先級標籤、預估時間、記號分類

---

### 3.6 測試集成（`backend/tests/`）

#### `backend/tests/test_phase6_6_chains.py`
- **用途**：LangChain 各 chain 的單元與集成測試
- **關鍵測試用例**：
  - `test_llm_factory_get_default_llm()`：工廠取得 LLM 實例
  - `test_prompt_manager_config()`：配置管理器讀取溫度/max_tokens
  - `test_task_generation_chain_create()`：chain 組建
  - `test_generate_tasks_full_flow()`：端到端任務生成（使用 Mock LLM）
  - `test_json_extraction_robustness()`：JSON 解析容錯 (markdown fence、多餘空白)
  - `test_tool_selection_chain()`：工具選擇 chain
  - `test_summary_chain()`：摘要 chain
  - 測試方式：MagicMock LLM，驗證 chain 邏輯而非外部 API

---

### 3.7 完整文件樹狀圖

```
backend/
├── chains/                           # LangChain 核心層
│   ├── __init__.py
│   ├── llm_factory.py               ← LLM 實例工廠
│   ├── prompt_manager.py            ← 配置管理
│   ├── task_generation_chain.py     ← 任務生成 chain
│   ├── tool_selection_chain.py      ← 工具選擇 chain
│   ├── summary_chain.py             ← 摘要 chain
│   └── workflows.py                 ← LangGraph 工作流
│
├── prompts/                          # Prompt 模板層
│   ├── __init__.py
│   ├── task_generator.py            ← 任務生成 PromptTemplate
│   ├── tool_selector.py             ← 工具選擇 PromptTemplate
│   └── summary_templates.py         ← 摘要 PromptTemplate
│
├── services/                         # 業務邏輯層
│   ├── timeline_service.py          ← 時間軸服務（含 AI 編排）
│   ├── copilot_service.py           ← Copilot MCP 服務
│   └── ai_provider.py               ← AI 提供者統一入口
│
├── blueprints/                       # HTTP 路由層
│   ├── timelines.py                 ← 時間軸路由（含 /generate-tasks）
│   ├── tasks.py
│   ├── messages.py
│   └── ...
│
└── tests/
    ├── test_phase6_6_chains.py      ← Chain 單元測試
    ├── services/
    │   ├── test_timeline_service.py
    │   └── ...
    └── blueprints/
        ├── test_timelines.py
        └── ...

frontend/
├── src/
│   ├── services/
│   │   └── timelineService.ts       ← HTTP 服務層
│   │
│   └── components/
│       └── timelines/
│           └── TimelineDetailDialog.vue  ← UI 組件
```

---

## 4. 完整流程：前端 → 後端 → LangChain → 回傳（以任務生成為例）

### 4.1 架構拓樸圖

```mermaid
graph TB
    A["🖥️ 前端<br/>(Vue 3)"] -->|1. POST /api/timelines/{id}/generate-tasks<br/>Content: description| B["⚙️ Flask Blueprint<br/>(timelines.py)"]
    B -->|2. 驗證 JWT + 權限| B
    B -->|3. 呼叫 Service| C["🔧 Service層<br/>(timeline_service.py)"]
    C -->|4a. 收集上下文| D["📊 資料庫查詢<br/>existing_tasks"]
    C -->|4b. 編排 AI 流程| E["🔗 LangChain Chain<br/>(task_generation_chain.py)"]
    
    E -->|5. 提取 PromptTemplate| F["📝 Prompt層<br/>(task_generator.py)"]
    F -->|6. 填充變數| G["🎯 填充後的 Prompt"]
    
    G -->|7. 呼叫 LLM| H["🤖 Google Gemini API"]
    H -->|8. 回傳 JSON| I["✨ AI 輸出<br/>task list"]
    
    I -->|9. JSON 解析<br/>& 標準化| J["📋 標準化 Task 物件"]
    J -->|10. 回傳至 Service| E
    
    E -->|11. 組裝回應| C
    C -->|12. 回傳 JSON| B
    B -->|13. HTTP 200 OK| A
    A -->|14. 渲染預覽| A
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#fff3e0
    style E fill:#f3e5f5
    style H fill:#fce4ec
```

### 4.2 詳細流程說明

#### **第 1-2 步：前端發起請求**

**前端代碼**（`frontend/src/services/timelineService.ts`）：

```typescript
export async function generateTasks(
  timelineId: number,
  projectName: string,
  description: string
) {
  // 發起 POST 請求到後端 API
  const response = await apiClient.post(
    `/timelines/${timelineId}/generate-tasks`,
    {
      project_name: projectName,
      description: description,  // 用戶輸入：「生成 Q2 的後端開發任務」
    }
  );
  return response.data;
}
```

**前端調用**（`TimelineDetailDialog.vue`）：

```vue
<script setup>
async function handleGenerateTasks() {
  loading.value = true;
  try {
    // 調用 service，發起 POST 請求
    const result = await generateTasks(
      selectedTimeline.value.id,
      selectedTimeline.value.name,
      aiPrompt.value  // 例如：「根據後端分層重構計畫生成任務」
    );
    
    // 後端回傳任務清單
    generatedTasks.value = result.tasks;
    showPreview.value = true;
  } catch (error) {
    error_message.value = error.message;
  } finally {
    loading.value = false;
  }
}
</script>
```

**HTTP 請求內容**：

```http
POST /api/timelines/42/generate-tasks HTTP/1.1
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "project_name": "Learnlink Phase 6.6",
  "description": "生成 Q2 的後端架構優化任務"
}
```

---

#### **第 3 步：後端路由層驗證**

**後端代碼**（`backend/blueprints/timelines.py`）：

```python
@timelines_bp.route('/<int:timeline_id>/generate-tasks', methods=['POST'])
@jwt_required()
@require_timeline_role('member')  # ✅ 驗證用戶是否為專案成員
def generate_tasks_endpoint(timeline_id):
    """生成任務 API 端點"""
    
    # 1️⃣ 驗證 JSON 格式（防呆）
    data = _get_json_dict_or_400({
        'project_name': str,
        'description': str,
    })
    
    project_name = data['project_name']
    description = data['description']
    
    # 2️⃣ 取得當前用戶 ID
    user_id = int(get_jwt_identity())
    
    try:
        # 3️⃣ 呼叫 Service 層
        result = generate_timeline_tasks_with_ai(
            timeline_id=timeline_id,
            project_name=project_name,
            description=description
        )
        return jsonify(result), 200
    except TimelineAIGenerationError as e:
        return jsonify({'error': e.message}), e.code
    except Exception as e:
        # ⚠️ 例外隱蔽：不直接回傳例外訊息
        return jsonify({'error': 'AI 生成失敗，請稍後再試'}), 500
```

---

#### **第 4-5 步：服務層收集上下文 + 編排流程**

**後端代碼**（`backend/services/timeline_service.py`）：

```python
def generate_timeline_tasks_with_ai(
    timeline_id: int,
    project_name: str,
    description: str = ''
) -> dict:
    """
    AI 生成任務的主編排入口。
    
    流程：
    1. 收集現有任務（上下文）
    2. 構造 prompt
    3. 呼叫 LangChain chain 執行 AI
    4. 標準化結果
    5. 回傳 tasks 清單
    """
    
    # 4️⃣ 第一步：收集現有任務資訊（上下文）
    existing_tasks_info = _build_existing_tasks_info(timeline_id)
    # 回傳結構例：[
    #   {'name': 'Setup database', 'priority': 1, 'estimated_days': 3},
    #   {'name': 'API authentication', 'priority': 1, 'estimated_days': 5}
    # ]
    
    # 5️⃣ 第二步：構造 AI prompt（融合上下文）
    prompt = _build_ai_task_prompt(
        project_name,
        description,
        existing_tasks_info
    )
    # prompt 內容例：
    # """
    # 你是專案管理助手。
    # 專案名稱: Learnlink Phase 6.6
    # 專案描述: 生成 Q2 的後端架構優化任務
    # 
    # 現有任務：
    # 1. Setup database (優先級:1, 預估:3天)
    # 2. API authentication (優先級:1, 預估:5天)
    # 
    # 請根據上述背景生成 5-8 個新任務...
    # """
    
    try:
        # 6️⃣ 第三步：取得 LLM 實例
        llm = get_default_llm(provider="google-generativeai")
        
        # 7️⃣ 第四步：呼叫 LangChain chain 執行 AI
        parsed = generate_tasks(
            llm=llm,
            project_name=project_name,
            project_description=description if isinstance(description, str) else "",
            user_input=prompt,    # ← 完整 prompt
            user_name="timeline_member"
        )
        # 回傳的 parsed 是 JSON 陣列，例如：
        # [
        #   {'name': 'Schema migration', 'priority': 1, 'estimated_days': 2, 'task_remark': '...'},
        #   {'name': 'ORM layer refactor', 'priority': 2, 'estimated_days': 3, 'task_remark': '...'}
        # ]
        
    except (RuntimeError, ValueError) as exc:
        error_str = str(exc)
        if "GOOGLE_API_KEY" in error_str:
            raise TimelineAIGenerationError('missing_api_key', 'AI 服務配置不完整')
        raise TimelineAIGenerationError('generation_failed', 'AI 生成失敗，請稍後再試')
    
    # 8️⃣ 第五步：標準化生成的任務
    generated_tasks = _normalize_generated_tasks(parsed, timeline_id)
    # 回傳結構例：
    # [
    #   {
    #     'timeline_id': 42,
    #     'status': 'pending',
    #     'name': 'Schema migration',
    #     'priority': 1,
    #     'estimated_days': 2,
    #     'task_remark': '...',
    #     'isExisting': False
    #   },
    #   ...
    # ]
    
    # 合併現有任務與新生成任務
    all_tasks = existing_tasks_info + generated_tasks
    
    # 9️⃣ 回傳結果
    return {
        'message': f'現有 {len(existing_tasks_info)} 個任務，AI 生成 {len(generated_tasks)} 個新任務',
        'tasks': all_tasks,
        'existingCount': len(existing_tasks_info),
        'generatedCount': len(generated_tasks),
    }
```

---

#### **第 6-9 步：LangChain Chain 執行（核心 AI 引擎）**

**LangChain Chain 層**（`backend/chains/task_generation_chain.py`）：

```python
def generate_tasks(
    llm: Any,
    project_name: str,
    project_description: str,
    user_input: str,
    user_name: str = "User",
) -> List[Dict[str, Any]]:
    """
    使用 LangChain 生成任務清單。
    
    流程：
    1. 取得 Prompt 與 LLM 配置
    2. 組建 chain (PromptTemplate | LLM | OutputParser)
    3. 執行 chain
    4. 解析 JSON 並回傳
    """
    
    # 6️⃣ 取得 PromptTemplate（已在專案層定義）
    prompt_mgr = PromptManager()
    config = prompt_mgr.get_config("task_generation")
    llm_for_call = _bind_llm_config(llm, config)
    
    # ❌ 舊方式（已廢止）
    # prompt = f"生成 {project_name} 的任務..."  # ← 直接字串拼接，難以重用
    
    # ✅ 新方式：使用 TASK_GENERATOR_PROMPT（PromptTemplate）
    # 模板內容：
    # """
    # 你是任務生成引擎。
    # 專案名稱: {project_name}
    # 專案描述: {project_description}
    # 使用者: {user_name}
    # 使用者需求: {user_input}
    # 
    # 輸出 JSON 陣列：[{{"name": "...", "priority": 1, ...}}, ...]
    # """
    
    # 7️⃣ 組建 chain：PromptTemplate → LLM → OutputParser
    chain = TASK_GENERATOR_PROMPT | llm_for_call | StrOutputParser()
    
    # TASK_GENERATOR_PROMPT 會自動填充變數：
    # {project_name} → "Learnlink Phase 6.6"
    # {project_description} → "生成 Q2..."
    # {user_name} → "timeline_member"
    # {user_input} → 完整 prompt（含現有任務上下文）
    
    # ❌ 修復前的 PromptTemplate（錯誤的跳脫）
    # 例子陣列中的 { } 被誤認為變數：
    # [
    #   {
    #     "name": "任務",
    #     "priority": 1 | 2 | 3  ← 這個 { } 被認為是變數！
    #   }
    # ]
    
    # ✅ 修復後的 PromptTemplate（正確的跳脫）
    # [
    #   {{
    #     "name": "任務",
    #     "priority": 1 | 2 | 3  ← 改為 {{ }} 才是字面意思
    #   }}
    # ]
    
    # 8️⃣ 執行 chain（調用 Gemini API）
    try:
        raw_output = chain.invoke({
            "project_name": project_name,
            "project_description": project_description,
            "user_name": user_name,
            "user_input": user_input,
        })
        # raw_output 例：
        # [
        #   {"name": "...", "priority": 1, "estimated_days": 2, "task_remark": "..."},
        #   {"name": "...", "priority": 2, "estimated_days": 3, "task_remark": "..."}
        # ]
        
    except Exception as e:
        raise ValueError(f"LLM 執行失敗: {str(e)}")
    
    # 9️⃣ 解析 JSON 並回傳
    try:
        parsed_tasks = json.loads(raw_output)
        if not isinstance(parsed_tasks, list):
            raise ValueError("AI 回傳不是陣列")
        return parsed_tasks
    except json.JSONDecodeError as e:
        raise ValueError(f"AI 回傳無法解析為 JSON: {str(e)}")
```

**Prompt 層定義**（`backend/prompts/task_generator.py`）：

```python
from langchain_core.prompts import PromptTemplate

# ✅ 關鍵修復：JSON 範例中的 { } 改為 {{ }}
TASK_GENERATOR_PROMPT = PromptTemplate.from_template("""
你是 PrAjeKt 專案管理系統的任務生成引擎。

## 職責
根據使用者的自然語言需求，生成結構化的任務清單。

## 專案背景
- 專案名稱: {project_name}
- 專案描述: {project_description}
- 使用者: {user_name}

## 任務生成規則
1. 任務應具體、可檢驗、有明確時間邊界
2. 優先級: 1（最高）~ 3（普通）
3. 預估工時: 整數天數，建議 1~5 天
4. 標籤: 按功能域分類（ex: 設計、開發、測試、運營）

## 使用者需求
{user_input}

## 輸出格式
必須輸出 JSON 陣列，每個元素是一個任務物件：
[
  {{
    "name": "任務名稱",
    "priority": 1 | 2 | 3,
    "estimated_days": 整數,
    "task_remark": "備註（可選）"
  }},
  ...
]

立即開始生成並輸出 JSON 陣列。
""")
```

---

#### **第 10-14 步：回傳前端 + 渲染**

**後端回傳 JSON**（HTTP 200）：

```json
{
  "message": "現有 2 個任務，AI 生成 6 個新任務",
  "tasks": [
    {
      "task_id": null,
      "timeline_id": 42,
      "name": "Setup database (existing)",
      "priority": 1,
      "estimated_days": 3,
      "isExisting": true
    },
    {
      "task_id": null,
      "timeline_id": 42,
      "name": "Schema migration",
      "priority": 1,
      "estimated_days": 2,
      "task_remark": "遷移 SQLite 配置至 PostgreSQL",
      "isExisting": false
    },
    {
      "task_id": null,
      "timeline_id": 42,
      "name": "ORM layer refactor",
      "priority": 2,
      "estimated_days": 3,
      "task_remark": "統一 SQLAlchemy 查詢模式",
      "isExisting": false
    },
    ...
  ],
  "existingCount": 2,
  "generatedCount": 6
}
```

**前端接收 + 渲染**（`TimelineDetailDialog.vue`）：

```vue
<script setup lang="ts">
const generatedTasks = ref<Task[]>([]);

async function handleGenerateTasks() {
  try {
    const result = await generateTasks(
      selectedTimeline.value.id,
      selectedTimeline.value.name,
      aiPrompt.value
    );
    
    // ✅ 前端收到任務清單
    generatedTasks.value = result.tasks;
    
    // 計算統計
    const existingCount = result.tasks.filter(t => t.isExisting).length;
    const generatedCount = result.tasks.filter(t => !t.isExisting).length;
    
    // 展示預覽
    showPreview.value = true;
  } catch (error) {
    errorMessage.value = error.message;
  }
}
</script>

<template>
  <!-- 任務預覽 Modal -->
  <div v-if="showPreview" class="modal">
    <h3>AI 生成任務預覽</h3>
    
    <!-- 統計卡 -->
    <div class="stats">
      <div class="stat-card">
        <span class="label">現有任務</span>
        <span class="count">{{ existingCount }}</span>
      </div>
      <div class="stat-card">
        <span class="label">新生成</span>
        <span class="count" style="color: green">{{ generatedCount }}</span>
      </div>
    </div>
    
    <!-- 任務清單 -->
    <ul class="task-list">
      <li v-for="task in generatedTasks" :key="task.name" class="task-item">
        <div class="task-header">
          <strong>{{ task.name }}</strong>
          <span v-if="task.isExisting" class="badge">既有</span>
          <span v-else class="badge new">新增</span>
          <span class="priority">優先級: {{ task.priority }}</span>
        </div>
        <div class="task-meta">
          <span>預估: {{ task.estimated_days }} 天</span>
          <span v-if="task.task_remark">{{ task.task_remark }}</span>
        </div>
      </li>
    </ul>
    
    <!-- 操作按鈕 -->
    <button @click="createAllTasks">✓ 建立任務</button>
    <button @click="showPreview = false">✕ 取消</button>
  </div>
</template>
```

---

### 4.3 數據結構轉換流程圖

```
前端輸入
  ↓
{project_name, description}
  ↓
POST /api/timelines/{id}/generate-tasks
  ↓
後端 Service 收集上下文
  ↓
existing_tasks_info = [{name, priority, estimated_days}, ...]
  ↓
_build_ai_task_prompt(name, desc, existing_tasks)
  ↓
完整 prompt（含上下文）
  ↓
LangChain chain 執行
  ├─ PromptTemplate.invoke() → 補充所有變數
  ├─ LLM (Gemini) → 呼叫 API
  └─ StrOutputParser() → 抽取文字
  ↓
raw_json_output = "[{name, priority, ...}, ...]"
  ↓
json.loads() → parsed_tasks (list[dict])
  ↓
_normalize_generated_tasks() → 補充 timeline_id 等
  ↓
all_tasks = existing + generated
  ↓
HTTP 200 | {message, tasks, count}
  ↓
前端顯示預覽
  ↓
使用者確認/修改
  ↓
createAllTasks() → POST /api/timelines/{id}/tasks (批量建立)
```

---

### 4.4 關鍵責任分工

| 層級 | 職責 | 技術細節 |
|------|------|----------|
| **前端** | 收集用戶輸入 + 發起 HTTP 請求 + 預覽結果 | Vue 3 + TypeScript + fetch/axios |
| **Blueprint** | 驗證 JWT + 檢查權限 + 路由轉發 | `@jwt_required` + `@require_timeline_role` |
| **Service** | 編排業務流程 + 收集上下文 + 錯誤標準化 | timeline_service.py 統一發起點 |
| **Chain** | 執行 LangChain pipeline + 解析結果 | task_generation_chain.invoke() |
| **Prompt** | 定義模板 + 變數填充 | PromptTemplate 實例 |
| **LLM** | 調用外部 AI 模型 | Google Gemini API |

---

## 5. 目前完成度

### 5.1 已完成

1. LangChain/LangGraph 依賴接入。
2. Prompt 與 chain 結構建立。
3. timeline 與 copilot 關鍵路徑改接 chains。
4. 例外處理收斂（避免過寬 except 直接吞錯）。
5. 關鍵回歸測試通過。

### 5.2 待續（建議）

1. `group_service.py` 的快照流程可逐步改接 `summary_chain`。
2. `task_service.py` 的留言摘要流程可逐步改接 `summary_chain`。
3. 擴充 LangGraph workflow（不只單節點工具路由）。

## 6. 設定說明

建議在 `.env` 或部署環境設定：

```bash
GOOGLE_API_KEY=your-api-key
AI_MODEL=gemini-2.5-flash-lite

LLM_PROVIDER=google-generativeai
LLM_TEMPERATURE_DEFAULT=0.2
LLM_TEMPERATURE_CREATIVE=0.7
LLM_MAX_TOKENS_DEFAULT=2000
LLM_MAX_TOKENS_LONG=4000
```

## 7. 驗證命令

```bash
# 後端依賴安裝（建議固定使用 backend requirements）
c:/Users/USER/Desktop/0611/0611/Learnlink/backend/venv/Scripts/python.exe -m pip install -r c:/Users/USER/Desktop/0611/0611/Learnlink/backend/requirements.txt

# Phase6.6 chain 測試
cd backend
venv/Scripts/python.exe -m pytest tests/test_phase6_6_chains.py -q

# 關鍵流程回歸
venv/Scripts/python.exe -m pytest tests/services/test_services.py -k "generate_timeline_tasks_with_ai" -q
venv/Scripts/python.exe -m pytest tests/blueprints/test_timelines.py -k "generate_tasks_with_ai" -q
venv/Scripts/python.exe -m pytest tests/services/test_group_snapshot.py -q
```

## 8. 常見問題

### Q1：`GOOGLE_API_KEY` 未設定

現象：初始化 provider 時拋出設定錯誤。

處理：確認環境變數或 `.env` 已正確設置。

### Q2：AI 回傳不是純 JSON

現象：出現 markdown fence、前後多餘文字，導致 JSON 解析失敗。

處理：
1. chain 已內建清理 markdown fence。
2. 仍失敗時會嘗試擷取首個合法 JSON 區塊。
3. 若最終仍失敗，會回到服務層既有錯誤語義。

### Q3：安裝到錯的 requirements

現象：版本被 root `requirements.txt` 覆蓋。

處理：一律指定 backend 檔案絕對路徑安裝。

## 9. 成功標準

1. 任務生成 API 維持既有 JSON 契約。
2. 工具路由流程在 AI 異常時仍可 fallback。
3. 關鍵回歸測試通過。
4. 服務層不再擴散 prompt/解析重複邏輯。

## 10. 後續建議

1. 把 `group_service.py`、`task_service.py` 逐步全面 chain 化。
2. 為 `workflows.py` 加上多節點狀態流與失敗重試策略。
3. 補齊 Phase 6.6 完整整合測試（含 Socket.IO / MCP 端到端）。
