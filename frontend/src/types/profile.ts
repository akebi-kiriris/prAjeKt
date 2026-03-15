import type { TaskStatus } from './task';

export interface Profile {
  id: number;
  name: string;
  username: string | null;
  email: string;
  phone: string | null;
  avatar: string | null;
  bio: string | null;
  created_at?: string | null;
}

export interface ChartStats {
  daily_completions: { date: string; count: number }[];
  status_distribution: Partial<Record<TaskStatus, number>>;
  tasks_by_project: { name: string; count: number }[];
  timeline_task_counts?: { name: string; total: number; completed: number }[];
}

export interface ProfileForm {
  name: string;
  username: string;
  email: string;
  phone: string;
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface ProfileUpdatePayload {
  name?: string;
  username?: string | null;
  email?: string;
  phone?: string | null;
  avatar?: string | null;
  bio?: string | null;
  current_password?: string;
  new_password?: string;
}
