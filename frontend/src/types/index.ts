/**
 * PrAjeKt 全站共用 TypeScript 型別定義
 *
 * 命名規則：
 * - API 回傳的 Timeline/Task 命名欄位依後端實際 JSON key（timelines 用 camelCase，tasks 用 snake_case）
 * - 前端 store 內部使用的物件與 API 回傳一致，不額外轉換
 */

// ─────────────────────────────────────────────────────────────
//  通用
// ─────────────────────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
}

/** getDaysRemaining() 回傳值（timelines store 與 TimelineViewModes 共用） */
export interface DaysRemainingResult {
  days: number | null;
  text: string;
  display: string;
  colorClass: string;
}

// ─────────────────────────────────────────────────────────────
//  使用者
// ─────────────────────────────────────────────────────────────

export interface User {
  id: number;
  name: string;
  username: string | null;
  email: string;
  phone: string | null;
  avatar: string | null;
  bio: string | null;
}

// ─────────────────────────────────────────────────────────────
//  待辦事項（API 回傳 snake_case）
// ─────────────────────────────────────────────────────────────

export interface Todo {
  id: number;
  title: string;
  content: string;
  type: string | null;
  deadline: string | null;
  completed: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface CreateTodoPayload {
  title: string;
  content?: string;
  deadline?: string;
  priority?: number;
}

// ─────────────────────────────────────────────────────────────
//  任務（API 回傳 snake_case）
// ─────────────────────────────────────────────────────────────

export interface TaskMember {
  user_id: number;
  name: string;
  email: string;
  role: 0 | 1;
}

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
  status: 'pending' | 'in_progress' | 'review' | 'completed' | 'cancelled';
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
  timeline_id?: number;
}

// ─────────────────────────────────────────────────────────────
//  專案（API 回傳 camelCase — timelines 後端手動轉換）
// ─────────────────────────────────────────────────────────────

export interface Timeline {
  id: number;
  name: string;
  startDate: string | null;
  endDate: string | null;
  remark: string | null;
  role: 0 | 1;
  totalTasks: number;
  completedTasks: number;
}

export interface CreateTimelinePayload {
  name: string;
  start_date?: string;
  end_date?: string;
  remark?: string;
}

export interface MemberStat {
  user_id: number;
  name: string;
  total: number;
  completed: number;
}

// ─────────────────────────────────────────────────────────────
//  群組
// ─────────────────────────────────────────────────────────────

export interface Group {
  group_id: number;
  group_name: string;
  group_inviteCode: string;
  created_by: number;
  description: string | null;
  is_active: boolean;
}

export interface Message {
  id: number;
  group_id: number;
  user_id: number;
  user_name: string;
  content: string;
  created_at: string;
}

// ─────────────────────────────────────────────────────────────
//  通知
// ─────────────────────────────────────────────────────────────

export type NotificationType =
  | 'task_assigned'
  | 'timeline_invited'
  | 'comment'
  | 'deadline'
  | 'mention';

export interface Notification {
  id: number;
  user_id: number;
  type: NotificationType;
  title: string;
  content: string | null;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

// ─────────────────────────────────────────────────────────────
//  個人資料
// ─────────────────────────────────────────────────────────────

export interface Profile {
  id: number;
  name: string;
  username: string | null;
  email: string;
  phone: string | null;
  avatar: string | null;
  bio: string | null;
}

export interface ChartStats {
  daily_completions: { date: string; count: number }[];
  status_distribution: { status: string; count: number }[];
  timeline_task_counts: { name: string; total: number; completed: number }[];
}
