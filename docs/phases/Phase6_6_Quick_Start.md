"""Phase 6.6 LangChain Infrastructure - Quick Start

本文件提供快速導航 Phase 6.6 實裝的入口。
"""

# Phase 6.6 LangChain 快速啟動

## 🎯 本階段目標
統一 LLM 應用的打包模式與 Prompt 管理，為 Phase 7 多步驟 AI 工作流預留可擴展架構。

## ✅ 已完成（2026/04/06）

### 1. 新增檔案結構
```
backend/
├── requirements.txt                    # 新增 langchain 3 個依賴
├── prompts/
│   ├── __init__.py                    # 導出所有 prompt
│   ├── tool_selector.py               # 工具選擇 prompt
│   ├── task_generator.py              # 任務生成 prompt
│   └── summary_templates.py           # 摘要 prompt
├── chains/
│   ├── __init__.py                    # 導出所有 chain 函數
│   ├── prompt_manager.py              # LLM 配置中央管理
│   ├── task_generation_chain.py       # Task 生成鏈
│   ├── summary_chain.py               # 摘要生成鏈
│   ├── tool_selection_chain.py        # 工具選擇鏈
│   └── llm_factory.py                 # LLM 工廠函數
└── tests/
    └── test_phase6_6_chains.py        # Phase 6.6 測試
docs/
└── Phase6_6_LangChain_Migration_Guide.md  # 遷移指南文檔
```

### 2. 核心 API

#### PromptManager（中央配置）
```python
from chains import PromptManager

mgr = PromptManager()
config = mgr.get_config("task_generation")
# Returns: {"temperature": 0.7, "max_tokens": 2048}
```

#### LLM 工廠
```python
from chains import get_default_llm

llm = get_default_llm("google-generativeai")
# 支持 google-generativeai 或 vertex-ai
```

#### Task 生成鏈
```python
from chains import generate_tasks

tasks = generate_tasks(
    llm,
    project_name="我的專案",
    project_description="描述",
    user_input="生成 3 個任務"
)
# Returns: [{"title": "...", "description": "...", ...}, ...]
```

#### 摘要生成鏈
```python
from chains import generate_task_summary, generate_group_snapshot

# Task 摘要
summary = generate_task_summary(
    llm,
    task_title="任務名",
    task_description="描述",
    fallback_summary="備用摘要"
)

# Group 快照
snapshot = generate_group_snapshot(
    llm,
    group_name="群組名",
    members_count=5,
    active_tasks=10,
    completed_tasks=20,
    pending_tasks=5
)
```

#### 工具選擇鏈
```python
from chains import select_tools

tools = select_tools(
    llm,
    user_input="我需要建立任務",
    available_tools=[
        {"name": "create_task", "description": "建立新任務"},
        {"name": "list_tasks", "description": "列出任務"}
    ]
)
```

## 🔧 快速測試

```bash
# 1. 安裝依賴
cd /backend
pip install -r requirements.txt

# 2. 運行 Phase 6.6 測試
pytest tests/test_phase6_6_chains.py -v

# 3. 檢查匯入
python -c "from chains import (
    PromptManager,
    get_default_llm,
    generate_tasks,
    generate_task_summary,
    select_tools
); print('✓ All imports OK')"
```

## 📝 環境配置

### .env.local 或部署環境變數
```bash
# 必須
GOOGLE_API_KEY=your-api-key-here

# 可選
GOOGLE_CLOUD_PROJECT=your-project-id  # Vertex AI 用
LLM_PROVIDER=google-generativeai       # google-generativeai 或 vertex-ai
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

## 📚 檔案導覽

| 檔案 | 用途 | 備註 |
|------|------|------|
| `prompts/tool_selector.py` | AI 工具路由 | 1 個 PromptTemplate |
| `prompts/task_generator.py` | 任務批量生成 | 1 個 PromptTemplate |
| `prompts/summary_templates.py` | 2 個摘要提示詞 | TASK_SUMMARY + GROUP_SNAPSHOT |
| `chains/prompt_manager.py` | 中央配置 | 控制溫度、token、版本 |
| `chains/task_generation_chain.py` | Task 鏈 | 含 generate_tasks() 函數 |
| `chains/summary_chain.py` | 摘要鏈 | 含 2 個 generate_* 函數 |
| `chains/tool_selection_chain.py` | 工具選擇鏈 | 含 select_tools() 函數 |
| `chains/llm_factory.py` | LLM 工廠 | 初始化 Google / Vertex |
| `docs/Phase6_6_LangChain_Migration_Guide.md` | **遷移指南** | 架構 + 配置 + Migration Plan |

## 🚀 下一步（Phase 6.6 第二階段）

### Week 12 待辦
1. [ ] 更新 `ai_provider.py`
   - 新增 `from_langchain()` 方法
   - 暴露 LangChain LLM 給 Phase 7

2. [ ] 遷移 `copilot_service.py`
   - `_ai_select_tool()` 使用 `tool_selection_chain`
   - 保持 JSON fallback 向後相容

3. [ ] 測試驗收
   - `pytest tests -q` 全數通過
   - 驗證輸出格式不變
   - 驗證回應時間 ±10%

4. [ ] 服務層清理
   - 移除重複 prompt 邏輯
   - 統一使用 PromptManager

## ⚠️ 向後相容性

所有 chain 設計保留 fallback 機制：
- **JSON 解析錯誤**：使用提供的 fallback 字串
- **LLM 超時**：返回默認值
- **Provider 切換**：工廠函數支持多個提供者

## 📖 詳細文檔

完整遷移計劃與架構說明：
👉 [Phase6_6_LangChain_Migration_Guide.md](Phase6_6_LangChain_Migration_Guide.md)

## 💡 Prompt Templates 查看

```bash
# 查看 tool selector prompt
python -c "from prompts import TOOL_SELECTOR_PROMPT; print(TOOL_SELECTOR_PROMPT.template)"

# 查看 task generator prompt
python -c "from prompts import TASK_GENERATOR_PROMPT; print(TASK_GENERATOR_PROMPT.template)"
```

## 🔍 調試技巧

```python
# 檢查 PromptManager 配置
from chains import PromptManager
mgr = PromptManager()
print(mgr.get_config("task_generation"))

# 直接測試 chain
from chains import create_task_generation_chain, get_default_llm
llm = get_default_llm()
chain = create_task_generation_chain(llm)
result = chain.invoke({"project_name": "測試", "project_description": "...", "user_input": "..."})
print(result)
```

---

** Phase 6.6 Infrastructure 100% 完成 ✅**

下一階段：服務層遷移與測試驗收（Week 12）
