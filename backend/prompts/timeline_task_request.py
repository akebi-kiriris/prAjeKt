"""專案任務生成請求提示詞模板。

此模組專門處理 timeline 情境下的任務生成請求組裝，
避免耦合通用的 TASK_GENERATOR_PROMPT。
"""

from typing import Any, Iterable, Mapping

from langchain_core.prompts import PromptTemplate

TIMELINE_TASK_REQUEST_PROMPT = PromptTemplate.from_template(
    """
你是一個專業的專案管理助手。請根據以下專案資訊，為使用者生成合理的任務清單。

專案名稱: {project_name}
專案描述: {project_description}

{existing_tasks_text}

要求：
1. 如果有現有任務，請參考它們來生成互補的任務（避免重複，找出缺失環節）
2. 如果沒有現有任務，請生成數個完整的任務
3. 生成的任務要考慮現有任務的優先級和邏輯順序

請務必回傳一個 JSON 陣列，每個任務物件必須包含以下欄位：
1. name（string）：任務名稱，10-30字，繁體中文
2. priority（integer）：優先級，1=高，2=中，3=低
3. estimated_days（integer）：預估完成天數，根據任務複雜度合理估計
4. task_remark（string）：任務備註，20-50字，繁體中文

不要使用 task_name、priority: "高" 這種格式，請嚴格依照上方欄位與型別。
按照邏輯順序排列（從準備、進行、到完成）
""".strip()
)


def build_timeline_task_request(
    project_name: str,
    project_description: str,
    existing_tasks_info: Iterable[Mapping[str, Any]],
) -> str:
    """組裝 timeline 任務生成請求內容。"""
    existing_lines = []
    for idx, task in enumerate(existing_tasks_info, 1):
        existing_lines.append(
            f"{idx}. {task.get('name', '未命名任務')} (優先級:{task.get('priority', 2)}, 預估:{task.get('estimated_days', 3)}天)"
        )

    existing_tasks_text = (
        "現有任務：\n" + "\n".join(existing_lines)
        if existing_lines
        else "現有任務：\n（目前無現有任務）"
    )
    safe_description = (
        project_description
        if isinstance(project_description, str) and project_description.strip()
        else "無"
    )

    return TIMELINE_TASK_REQUEST_PROMPT.format(
        project_name=project_name,
        project_description=safe_description,
        existing_tasks_text=existing_tasks_text,
    )
