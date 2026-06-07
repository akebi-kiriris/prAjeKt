# Payload Contracts

本文件定義前後端 mutation endpoint 的 payload 白名單與禁止欄位，作為開發與 Code Review 的依據。

## Tasks

### `POST /api/tasks`
- Allowed fields: `name`, `timeline_id`, `priority`, `status`, `tags`, `estimated_hours`, `start_date`, `end_date`, `task_remark`, `isWork`
- Required fields: `name`, `end_date`
- Forbidden examples: `members`, `created_at`, `updated_at`, `deleted_at`, `user_id`, `task_id`

### `PUT /api/tasks/:task_id`
- Allowed fields: `name`, `timeline_id`, `priority`, `status`, `tags`, `estimated_hours`, `actual_hours`, `start_date`, `end_date`, `task_remark`, `isWork`
- Forbidden examples: `members`, `subtasks`, `comments`, `files`, `created_at`, `updated_at`, `deleted_at`, `user_id`, `task_id`

## Timelines

### `PUT /api/timelines/:timeline_id`
- Allowed fields: `name`, `start_date`, `end_date`, `remark`
- Forbidden examples: `role`, `totalTasks`, `completedTasks`, `deleted_at`, `user_id`, `id`

## Todos

### `POST /api/todos`
- Allowed fields: `title`, `content`, `type`, `deadline`, `priority`
- Forbidden examples: `id`, `completed`, `completed_at`, `created_at`, `updated_at`, `deleted_at`, `user_id`

### `PUT /api/todos/:todo_id`
- Allowed fields: `title`, `content`, `type`, `deadline`, `priority`, `completed`
- Forbidden examples: `id`, `completed_at`, `created_at`, `updated_at`, `deleted_at`, `user_id`

## Profile

### `PUT /api/profile/me`
- Allowed fields: `name`, `username`, `phone`, `email`, `avatar`, `bio`, `current_password`, `new_password`
- Forbidden examples: `id`, `password`, `created_at`, `updated_at`, `deleted_at`, `role`

## Guardrails

- 請使用 `frontend/src/utils/payloadMappers.ts` 組裝 create/update payload。
- 禁止在 mutation payload 使用 `Partial<Entity>`（例如 `Partial<Task>`）。
- 禁止直接 `...entity` 傳入 `service.update(...)`。
- CI 或本機可執行：
  - `npm run guardrails:payload`（在 `frontend` 目錄）
