export type TaskStatus = 'pending' | 'in_progress' | 'review' | 'completed' | 'cancelled';

export interface TaskMember {
  user_id: number;
  name: string;
  username?: string | null;
  email: string;
  role: 0 | 1;
}

export interface SearchUserResult {
  id: number;
  name: string;
  username?: string | null;
  email: string;
}

export interface AiGeneratedTask {
  name: string;
  start_date?: string | null;
  end_date?: string | null;
  priority: number;
  tags?: string | null;
  remark?: string | null;
  task_remark?: string | null;
}

export type GenerateTasksResponse = AiGeneratedTask[] | { tasks: AiGeneratedTask[] };

export interface Subtask {
  id: number;
  task_id: number;
  name: string;
  completed: boolean;
  sort_order: number;
  created_at: string | null;
}

export interface TaskComment {
  comment_id: number;
  task_id: number;
  user_id: number;
  user_name: string;
  task_message: string;
  created_at: string;
}

export interface TaskFile {
  id: number;
  task_id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  uploaded_at: string;
  uploaded_by: number;
}

export interface Task {
  task_id: number;
  name: string;
  completed: boolean;
  timeline_id: number | null;
  priority: number;
  status: TaskStatus;
  tags: string | null;
  estimated_hours: number | null;
  actual_hours: number | null;
  members: TaskMember[];
  subtasks: Subtask[];
  created_at: string | null;
  start_date: string | null;
  end_date: string | null;
  updated_at: string | null;
  task_remark: string | null;
  isWork: number;
  is_owner: boolean;
}

export interface CreateTaskPayload {
  name: string;
  start_date?: string | null;
  end_date?: string | null;
  task_remark?: string | null;
  priority?: number;
  tags?: string | null;
  timeline_id?: number;
}

export type TaskUpdatePayload = Partial<Pick<
  Task,
  | 'name'
  | 'timeline_id'
  | 'priority'
  | 'status'
  | 'tags'
  | 'estimated_hours'
  | 'actual_hours'
  | 'start_date'
  | 'end_date'
  | 'task_remark'
  | 'isWork'
>>;
