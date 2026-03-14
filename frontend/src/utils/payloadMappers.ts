import type { CreateTaskPayload, CreateTodoPayload, TaskUpdatePayload, TodoForm, UpdateTodoPayload } from '../types';

type TaskCreateInput = Partial<CreateTaskPayload> & { name: string };
type TaskUpdateInput = Partial<TaskUpdatePayload>;
type TodoCreateInput = Partial<CreateTodoPayload> & Pick<TodoForm, 'title'>;
type TodoUpdateInput = Partial<UpdateTodoPayload>;

const hasKey = <T extends object>(obj: T, key: string): boolean =>
  Object.prototype.hasOwnProperty.call(obj, key);

const toDateOnlyOrNull = (value: unknown): string | null => {
  if (typeof value !== 'string' || value.trim() === '') return null;
  return new Date(value).toISOString().split('T')[0];
};

const toDateOnlyOrUndefined = (value: unknown): string | undefined => {
  if (typeof value !== 'string' || value.trim() === '') return undefined;
  return new Date(value).toISOString().split('T')[0];
};

const toTodoDeadlineOrNull = (value: unknown): string | null => {
  if (typeof value !== 'string' || value.trim() === '') return null;
  if (value.includes('T') && value.length === 16) {
    return `${value}:00`;
  }
  return value;
};

const toTodoDeadlineOrUndefined = (value: unknown): string | undefined => {
  const normalized = toTodoDeadlineOrNull(value);
  return normalized ?? undefined;
};

const toNumberOrUndefined = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
};

export const mapToCreateTaskPayload = (input: TaskCreateInput): CreateTaskPayload => {
  const payload: CreateTaskPayload = {
    name: input.name.trim(),
  };

  if (hasKey(input, 'start_date')) {
    payload.start_date = toDateOnlyOrNull(input.start_date);
  }
  if (hasKey(input, 'end_date')) {
    payload.end_date = toDateOnlyOrNull(input.end_date);
  }
  if (hasKey(input, 'task_remark')) {
    payload.task_remark = input.task_remark ?? null;
  }

  const priority = toNumberOrUndefined(input.priority);
  if (priority !== undefined) payload.priority = priority;

  if (hasKey(input, 'tags')) {
    payload.tags = input.tags ?? null;
  }

  if (typeof input.timeline_id === 'number') {
    payload.timeline_id = input.timeline_id;
  }

  return payload;
};

export const mapToUpdateTaskPayload = (input: TaskUpdateInput): TaskUpdatePayload => {
  const payload: TaskUpdatePayload = {};

  if (hasKey(input, 'name')) {
    payload.name = typeof input.name === 'string' ? input.name.trim() : input.name;
  }
  if (hasKey(input, 'timeline_id')) payload.timeline_id = input.timeline_id;

  const priority = toNumberOrUndefined(input.priority);
  if (hasKey(input, 'priority')) payload.priority = priority;

  if (hasKey(input, 'status')) payload.status = input.status;
  if (hasKey(input, 'tags')) payload.tags = input.tags ?? null;
  if (hasKey(input, 'estimated_hours')) payload.estimated_hours = input.estimated_hours;
  if (hasKey(input, 'actual_hours')) payload.actual_hours = input.actual_hours;
  if (hasKey(input, 'task_remark')) payload.task_remark = input.task_remark ?? null;
  if (hasKey(input, 'isWork')) payload.isWork = input.isWork;

  if (hasKey(input, 'start_date')) {
    payload.start_date = toDateOnlyOrNull(input.start_date);
  }
  if (hasKey(input, 'end_date')) {
    payload.end_date = toDateOnlyOrNull(input.end_date);
  }

  return payload;
};

export const mapToCreateTodoPayload = (input: TodoCreateInput): CreateTodoPayload => {
  const payload: CreateTodoPayload = {
    title: input.title.trim(),
  };

  if (hasKey(input, 'content')) payload.content = input.content ?? '';
  if (hasKey(input, 'type')) payload.type = input.type ?? null;

  const deadline = toTodoDeadlineOrUndefined(input.deadline);
  if (deadline !== undefined) payload.deadline = deadline;

  const priority = toNumberOrUndefined(input.priority);
  if (priority !== undefined) payload.priority = priority;

  return payload;
};

export const mapToUpdateTodoPayload = (input: TodoUpdateInput): UpdateTodoPayload => {
  const payload: UpdateTodoPayload = {};

  if (hasKey(input, 'title')) payload.title = typeof input.title === 'string' ? input.title.trim() : input.title;
  if (hasKey(input, 'content')) payload.content = input.content;
  if (hasKey(input, 'type')) payload.type = input.type ?? null;

  if (hasKey(input, 'deadline')) {
    payload.deadline = toTodoDeadlineOrNull(input.deadline);
  }

  const priority = toNumberOrUndefined(input.priority);
  if (hasKey(input, 'priority')) payload.priority = priority;

  if (hasKey(input, 'completed')) payload.completed = input.completed;

  return payload;
};
