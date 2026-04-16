"""Phase 7 專案洞察提示詞模板。

包含兩類提示詞：
1. 週報摘要
2. 衝突建議
"""

from langchain_core.prompts import PromptTemplate

WEEKLY_REPORT_SUMMARY_PROMPT = PromptTemplate.from_template(
    """
你是一位專業的專案管理顧問。
請根據以下「週報分析上下文」，用繁體中文生成 2-3 句可直接貼到週報的管理摘要。

輸出要求：
1. 必須明確提到「本期目標達成率」與進度判讀（領先 / 穩定 / 落後）。
2. 必須提到至少 1 個「推進原因」（例如某角色/模組推進快）。
3. 必須提到至少 1 個「風險或阻塞訊號」與下一步建議。
4. 禁止空泛句（例如「整體還可以」），要有數據語氣。

週報分析上下文:
{status_text}

摘要:
""".strip()
)

CONFLICT_SUGGESTION_PROMPT = PromptTemplate.from_template(
    """
你是一位專案排程顧問。
請根據以下衝突資訊，用繁體中文生成 1-2 句精簡建議，語氣務實、可執行。

輸出要求：
1. 若有跨專案撞期，要明確指出「跨專案」風險。
2. 若有工作量過載日，要指出過載程度（例如某幾天任務過密）。
3. 若有建議改期區間，請自然提及。
4. 結尾需有明確動作建議（例如先調整哪類任務）。

衝突資訊:
{conflict_text}

建議改期區間:
{suggestion_date_range}

建議:
""".strip()
)
