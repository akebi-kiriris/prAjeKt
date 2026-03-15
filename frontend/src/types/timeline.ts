import type { TaskStatus } from './task';

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

export type UpdateTimelinePayload = Partial<CreateTimelinePayload>;

export interface MemberStat {
  user_id: number;
  name: string;
  total: number;
  completed: number;
}

export interface ProjectMemberStat {
  name: string;
  total_tasks: number;
  completed_tasks: number;
}

export interface ProjectStats {
  total_tasks: number;
  members: ProjectMemberStat[];
  status_distribution: Partial<Record<TaskStatus, number>>;
}
