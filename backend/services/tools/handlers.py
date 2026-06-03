from io import BytesIO
from typing import Any

from werkzeug.datastructures import FileStorage

from services.contracts.tool_envelopes import make_failure, make_success
from services.contracts.tool_inputs import (
    CreateTimelineToolInput,
    CreateTaskToolInput,
    GroupSnapshotToolInput,
    KnowledgeListToolInput,
    KnowledgeUploadToolInput,
    ListTasksToolInput,
    TaskCommentSummaryToolInput,
    TimelineConflictCheckToolInput,
    TimelineBatchCreateTasksToolInput,
    TimelineGenerateTasksToolInput,
    UpdateTaskToolInput,
)
from services.contracts.tool_outputs import (
    CommonToolOutput,
    CreateTimelineToolOutput,
    GroupSnapshotToolOutput,
    KnowledgeListToolOutput,
    KnowledgeUploadToolOutput,
    ListTasksToolOutput,
    TaskCommentSummaryToolOutput,
    TaskCreateToolOutput,
    TimelineConflictCheckToolOutput,
    TimelineBatchCreateTasksToolOutput,
    TimelineGenerateTasksToolOutput,
)
from services.group_service import generate_group_snapshot
from services.knowledge_service import list_knowledge_documents, upload_and_index_knowledge_document
from services.task_service import (
    create_task_for_user,
    list_tasks_for_user,
    summarize_task_comments_for_member,
    update_task_for_member,
)
from services.timeline_service import (
    batch_create_tasks_for_timeline,
    check_timeline_task_conflicts,
    create_timeline_for_user,
    generate_timeline_tasks_with_ai,
)
from services.tools.error_mapper import map_exception_to_tool_error


def _build_filestorage(filename: str, content: str, mime_type: str | None = None) -> FileStorage:
    """將字串內容包裝成 Flask 可處理的檔案物件。

    Args:
        filename: 檔名（需含副檔名）。
        content: 檔案文字內容。
        mime_type: 可選的 MIME 類型。

    Returns:
        FileStorage: 可直接交由知識服務處理的上傳檔案物件。
    """
    payload = content.encode("utf-8")
    stream = BytesIO(payload)
    return FileStorage(stream=stream, filename=filename, content_type=mime_type or "text/markdown")


def handle_create_task_for_user(data: CreateTaskToolInput) -> dict[str, Any]:
    """建立任務工具入口。

    用途:
        建立新任務，並回傳建立後的 `task_id`。
    前置條件:
        `raw_input` 需符合 `CreateTaskToolInput` 契約，且使用者需具備建立任務權限。
    副作用:
        會寫入資料庫，並可能觸發通知流程。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功為 `{ok: true, data: ...}`）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        task_id = create_task_for_user(user_id=data.user_id, data=data.data)
        output = TaskCreateToolOutput(task_id=task_id)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_update_task_for_member(data: UpdateTaskToolInput) -> dict[str, Any]:
    """更新任務工具入口。

    用途:
        依據輸入欄位更新既有任務內容。
    前置條件:
        `raw_input` 需符合 `UpdateTaskToolInput`，且呼叫者需具備任務更新權限。
    副作用:
        會寫入資料庫。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含 `updated=true`）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        update_task_for_member(task_id=data.task_id, data=data.data)
        output = CommonToolOutput(updated=True)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_list_tasks_for_user(data: ListTasksToolInput) -> dict[str, Any]:
    """列出任務工具入口。

    用途:
        查詢指定使用者可見的任務清單。
    前置條件:
        `raw_input` 需符合 `ListTasksToolInput`。
    副作用:
        僅讀取資料庫，不進行寫入。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含任務清單）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        tasks = list_tasks_for_user(user_id=data.user_id)
        output = ListTasksToolOutput(tasks=tasks)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_generate_timeline_tasks_with_ai(data: TimelineGenerateTasksToolInput) -> dict[str, Any]:
    """AI 任務建議工具入口。

    用途:
        依專案脈絡與描述生成任務建議。
    前置條件:
        `raw_input` 需符合 `TimelineGenerateTasksToolInput`。
    副作用:
        會呼叫 AI 服務，但不直接寫入任務資料表。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含建議任務內容）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        result = generate_timeline_tasks_with_ai(
            timeline_id=data.timeline_id,
            project_name=data.project_name,
            description=data.description,
        )
        output = TimelineGenerateTasksToolOutput.model_validate(result)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_create_timeline_for_user(data: CreateTimelineToolInput) -> dict[str, Any]:
    """建立專案工具入口。

    用途:
        建立新專案並回傳 `timeline_id`。
    前置條件:
        `raw_input` 需符合 `CreateTimelineToolInput`。
    副作用:
        會寫入資料庫，新增專案與擁有者成員關係。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含 `timeline_id`）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        timeline_id = create_timeline_for_user(user_id=data.user_id, data=data.data)
        output = CreateTimelineToolOutput(timeline_id=timeline_id)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_batch_create_tasks_for_timeline(data: TimelineBatchCreateTasksToolInput) -> dict[str, Any]:
    """批次建立任務工具入口。

    用途:
        將任務清單一次寫入專案，並處理前置依賴解析。
    前置條件:
        `raw_input` 需符合 `TimelineBatchCreateTasksToolInput`。
    副作用:
        會寫入資料庫，可能軟刪除未保留舊任務並建立新任務依賴。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含批次建立結果）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        result = batch_create_tasks_for_timeline(
            timeline_id=data.timeline_id,
            user_id=data.user_id,
            task_payloads=data.tasks,
        )
        output = TimelineBatchCreateTasksToolOutput(result=result)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_check_timeline_task_conflicts(data: TimelineConflictCheckToolInput) -> dict[str, Any]:
    """衝突檢查工具入口。

    用途:
        檢查任務在時間區間內的排程與人力衝突。
    前置條件:
        `raw_input` 需符合 `TimelineConflictCheckToolInput`，且 actor 具專案操作權限。
    副作用:
        主要為資料讀取，特定情境可能呼叫 AI 產生建議。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含衝突分析結果）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        result = check_timeline_task_conflicts(
            timeline_id=data.timeline_id,
            payload=data.payload,
            actor_user_id=data.actor_user_id,
        )
        output = TimelineConflictCheckToolOutput(result=result)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_generate_group_snapshot(data: GroupSnapshotToolInput) -> dict[str, Any]:
    """群組快照工具入口。

    用途:
        彙整群組近期訊息並生成快照摘要。
    前置條件:
        `raw_input` 需符合 `GroupSnapshotToolInput`，且呼叫者具群組存取權限。
    副作用:
        會讀取群組訊息、呼叫 AI，並將快照寫入資料庫。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含快照內容）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        result = generate_group_snapshot(
            group_id=data.group_id,
            window_days=data.window_days,
            created_by=data.created_by,
            force=data.force,
        )
        output = GroupSnapshotToolOutput(snapshot=result)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_upload_and_index_knowledge_document(data: KnowledgeUploadToolInput) -> dict[str, Any]:
    """知識文件上傳與索引工具入口。

    用途:
        上傳單一知識文件並完成切塊、向量化與索引入庫。
    前置條件:
        `raw_input` 需符合 `KnowledgeUploadToolInput`，檔名與內容不可為空。
    副作用:
        會寫入資料庫並呼叫 embedding 服務。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含文件與索引結果）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        file_storage = _build_filestorage(data.filename, data.content, data.mime_type)
        result = upload_and_index_knowledge_document(
            user_id=data.user_id,
            file_storage=file_storage,
            project_id=data.project_id,
        )
        output = KnowledgeUploadToolOutput(result=result)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_list_knowledge_documents(data: KnowledgeListToolInput) -> dict[str, Any]:
    """知識文件列表工具入口。

    用途:
        查詢知識文件清單，支援分頁與條件過濾。
    前置條件:
        `raw_input` 需符合 `KnowledgeListToolInput`。
    副作用:
        僅讀取資料庫，不進行寫入。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含文件清單與 meta）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        result = list_knowledge_documents(
            user_id=data.user_id,
            limit=data.limit,
            offset=data.offset,
            project_id=data.project_id,
            q=data.q,
            sort=data.sort,
            status=data.status,
        )
        output = KnowledgeListToolOutput(result=result)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))


def handle_summarize_task_comments_for_member(data: TaskCommentSummaryToolInput) -> dict[str, Any]:
    """任務留言摘要工具入口。

    用途:
        彙整指定任務留言並產生摘要內容。
    前置條件:
        `raw_input` 需符合 `TaskCommentSummaryToolInput`，且呼叫者需可讀取該任務。
    副作用:
        會讀取任務與留言資料，並呼叫 AI 服務產生摘要。

    Args:
        data: 已驗證的工具輸入模型。

    Returns:
        dict[str, Any]: 統一 envelope（成功時含摘要資料）。

    Raises:
        無；例外會在函式內轉換為錯誤 envelope 回傳。
    """
    try:
        result = summarize_task_comments_for_member(task_id=data.task_id)
        output = TaskCommentSummaryToolOutput(result=result)
        return make_success(output.model_dump())
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))
