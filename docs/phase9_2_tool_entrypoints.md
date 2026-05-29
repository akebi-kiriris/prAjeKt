# Phase 9.2 Tool Entrypoints（執行版）

> 目的：定義「哪些函式可給 agent 直接調用」與「哪些僅供內部使用」。  
> 判斷規則：  
> 1. `_` 開頭一律 internal。  
> 2. 非 `_` 開頭也不一定對外，僅 `exposed_to_agent=yes` 才能進 registry。  
> 3. 以高語意 use case 優先，避免暴露低階組裝函式。

---

## 欄位定義

- `function_name`：函式名稱
- `exposed_to_agent`：`yes/no`
- `preconditions`：前置條件
- `side_effects`：副作用（DB/通知/AI/檔案）
- `notes`：備註

---

## task_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `list_tasks_for_user` | yes | 有效 `user_id` | 讀 DB | 查詢入口 |
| `create_task_for_user` | yes | 必填欄位、成員/相依驗證通過 | 寫 DB、通知 | 主要建立入口 |
| `update_task_for_member` | yes | 任務存在、欄位合法 | 寫 DB | 更新入口 |
| `toggle_task_for_member` | yes | 任務存在 | 寫 DB | 狀態切換 |
| `list_task_comments_for_member` | yes | 任務可讀 | 讀 DB | 查詢留言 |
| `add_task_comment_for_member` | yes | 訊息非空 | 寫 DB、通知 | 新增留言 |
| `summarize_task_comments_for_member` | yes | 任務可讀 | 讀 DB、AI | AI 入口 |
| `upload_task_file_for_member` | yes | 格式/大小合法 | 寫 DB、檔案 IO | 檔案上傳 |
| `delete_task_file_for_user` | yes | 上傳者或負責人 | 寫 DB、檔案刪除 | 檔案刪除 |
| `resolve_task_file_download_for_user` | yes | 任務檔案可讀權限 | 讀 DB | 檔案下載解析 |
| `create_notification` | no | internal | 寫 DB | 內部共用 |
| `task_member_to_dict` | no | internal | 無 | 資料轉換 |

## timeline_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `list_timeline_items_for_user` | yes | 有效 `user_id` | 讀 DB | 查詢入口 |
| `create_timeline_for_user` | yes | 欄位合法 | 寫 DB | 建立專案 |
| `update_timeline_for_member` | yes | 成員權限、欄位合法 | 寫 DB | 更新專案 |
| `list_timeline_tasks_detail` | yes | 專案可讀 | 讀 DB | 任務明細 |
| `generate_timeline_tasks_with_ai` | yes | 專案權限、輸入合法 | 讀 DB、AI | AI 任務建議 |
| `build_weekly_report_for_timeline` | yes | 日期區間合法 | 讀 DB、可選 AI | 週報入口 |
| `check_timeline_task_conflicts` | yes | payload 合法 | 讀 DB、可選 AI | 衝突檢查 |
| `build_timeline_risk_analysis` | yes | 專案存在 | 讀 DB、可選 AI | 風險分析 |
| `add_timeline_member_for_owner` | yes | 擁有者權限 | 寫 DB、通知 | 成員管理 |
| `remove_timeline_member_for_owner` | yes | 擁有者權限 | 寫 DB | 成員移除 |
| `batch_create_tasks_for_timeline` | yes | payload 合法 | 寫 DB | 批次建立 |
| `timeline_list_item_to_dict` | no | internal | 無 | 資料轉換 |

## group_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `list_groups_for_user` | yes | 有效 `user_id` | 讀 DB | 查詢入口 |
| `create_group_for_user` | yes | 名稱合法 | 寫 DB | 建立群組 |
| `join_group_by_invite_code` | yes | 邀請碼合法 | 寫 DB | 加入群組 |
| `leave_group_for_user` | yes | 成員存在 | 寫 DB | 離開群組 |
| `list_group_members_payload` | yes | 群組存在 | 讀 DB | 查詢成員 |
| `list_group_messages_for_member` | yes | 成員權限 | 讀 DB | 查詢訊息 |
| `send_group_message_for_member` | yes | 成員權限、內容非空 | 寫 DB | 發送訊息 |
| `generate_group_snapshot` | yes | 訊息可用 | 讀 DB、AI、寫 DB | 快照生成 |
| `enqueue_snapshot_job` | yes | 可用 app context | 寫記憶體狀態、背景工作 | 非同步模式 |
| `get_snapshot_job_status` | yes | job 存在、權限合法 | 讀記憶體狀態 | 工作查詢 |
| `group_message_to_dict` | no | internal | 無 | 資料轉換 |

## knowledge_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `upload_and_index_knowledge_document` | yes | 檔案合法 | 寫 DB、檔案 IO、embedding | 文件上傳索引 |
| `list_knowledge_documents` | yes | 有效 `user_id` | 讀 DB | 文件列表 |
| `delete_knowledge_document` | yes | 文件存在、權限合法 | 寫 DB、可刪檔 | 刪除文件 |
| `reindex_knowledge_document` | yes | 原文存在 | 寫 DB、embedding | 重建索引 |
| `batch_delete_knowledge_documents` | yes | 文件 id 清單合法 | 寫 DB、可刪檔 | 批次刪除 |
| `batch_reindex_knowledge_documents` | yes | 文件 id 清單合法 | 寫 DB、embedding | 批次重建 |
| `get_project_knowledge_document_file` | yes | 文件存在、權限合法 | 讀 DB、事件寫入 | 下載/開啟 |
| `list_project_knowledge_events` | yes | 專案存在 | 讀 DB | 事件查詢 |
| `_decode_text_content` | no | internal | 無 | 解析 helper |

## message_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `get_unread_message_count` | yes | 有效 `user_id` | 讀 DB | 查詢未讀數 |
| `mark_all_unread_messages_as_read` | yes | 有效 `user_id` | 寫 DB | 全部已讀 |
| `create_group_message` | yes | 發送者存在 | 寫 DB | 建立訊息 |
| `serialize_group_message` | no | internal | 無 | 資料轉換 |

## profile_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `get_profile_user_or_404` | yes | 使用者存在 | 讀 DB | 查詢入口 |
| `update_profile_for_user` | yes | payload 合法、密碼驗證通過 | 寫 DB | 更新個資 |
| `search_user_by_query` | yes | query 非空 | 讀 DB | 搜尋使用者 |
| `build_chart_stats_for_user` | yes | 使用者可讀 | 讀 DB | 儀表板統計 |
| `profile_to_dict` | no | internal | 無 | 資料轉換 |

## todo_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `list_todos_for_user` | yes | 有效 `user_id` | 讀 DB | 列表 |
| `create_todo_for_user` | yes | payload 合法 | 寫 DB | 建立 |
| `update_todo_for_user` | yes | todo 存在、欄位合法 | 寫 DB | 更新 |
| `soft_delete_todo_for_user` | yes | todo 存在 | 寫 DB | 軟刪除 |
| `toggle_todo_for_user` | yes | todo 存在 | 寫 DB | 切換狀態 |

## notification_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `get_notifications_for_user` | yes | 有效 `user_id` | 讀 DB | 列表 |
| `get_unread_count_for_user` | yes | 有效 `user_id` | 讀 DB | 未讀數 |
| `mark_notification_as_read` | yes | 通知存在且屬於使用者 | 寫 DB | 單筆已讀 |
| `mark_all_notifications_as_read` | yes | 有效 `user_id` | 寫 DB | 全部已讀 |
| `delete_notification_for_user` | yes | 通知存在且屬於使用者 | 寫 DB | 刪除 |

## auth_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `register_user` | yes | payload 合法、email 未重複 | 寫 DB | 註冊 |
| `authenticate_user` | yes | 帳密存在且正確 | 讀 DB | 登入驗證 |
| `get_current_user_or_404` | yes | user_id 存在 | 讀 DB | 查詢當前使用者 |
| `auth_user_to_dict` | no | internal | 無 | 資料轉換 |

## rag_planning_service.py / copilot_service.py / mcp_bridge_service.py

| function_name | exposed_to_agent | preconditions | side_effects | notes |
|---|---|---|---|---|
| `suggest_plan_with_rag` | yes | request 非空、權限合法 | 讀 DB、檢索、AI | RAG 規劃入口 |
| `execute_copilot_mcp_request` | no（目前） | 依現有 API 權限 | 呼叫 MCP bridge | 9.3 單體版先不納入 |
| `list_mcp_tools` | no（目前） | MCP server 可用 | 子程序啟動、RPC | backlog |
| `execute_mcp_tool` | no（目前） | 工具存在 | 子程序/RPC | backlog |

---

## 9.3 Registry 最小納入建議（第一批）

1. `create_task_for_user`
2. `update_task_for_member`
3. `list_tasks_for_user`
4. `generate_timeline_tasks_with_ai`
5. `check_timeline_task_conflicts`
6. `generate_group_snapshot`
7. `upload_and_index_knowledge_document`
8. `list_knowledge_documents`
9. `summarize_task_comments_for_member`
