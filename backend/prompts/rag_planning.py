from langchain_core.prompts import PromptTemplate


RAG_PLAN_SUGGESTION_PROMPT = PromptTemplate.from_template(
    """
你是 Learnlink 的專案規劃助手，請根據需求與已檢索來源，產生可落地的專案規劃。

使用者需求：
{user_request}

檢索來源（已排序）：
{retrieval_context}

請遵守：
1. 任務要具體可執行，避免空泛描述。
2. 任務優先級只能是 CRITICAL/HIGH/MEDIUM/LOW。
3. 優先使用提供的來源，不要虛構來源。
4. source_references 只能引用檢索來源中已出現的資料。
5. 請嚴格輸出 JSON，且符合格式要求。

{format_instructions}
"""
)
