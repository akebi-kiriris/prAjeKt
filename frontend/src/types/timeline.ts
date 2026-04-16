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

export interface WeeklyReportPeriod {
  start_date: string;
  end_date: string;
}

export interface WeeklyReportOverview {
  total_tasks: number;
  completed_tasks: number;
  completion_rate: number;
  at_risk_tasks: number;
  comment_count: number;
}

export interface WeeklyReportCompletedTask {
  task_id: number;
  name: string;
  completed_at: string | null;
  due_date: string | null;
  is_late: boolean;
  owner_name: string | null;
}

export interface WeeklyReportRiskItem {
  task_id: number;
  name: string;
  status: TaskStatus | string;
  due_date: string;
  reason: string;
  days_overdue: number;
  days_remaining: number | null;
}

export interface WeeklyReportCommentItem {
  comment_id: number;
  task_id: number;
  task_name: string | null;
  user_id: number;
  message: string;
  created_at: string | null;
}

export interface WeeklyReportAnalysis {
  weekly_goal_total: number;
  weekly_goal_completed: number;
  weekly_goal_completion_rate: number;
  previous_completed_tasks: number;
  progress_delta: number;
  progress_signal: string;
  top_owner: string | null;
  top_tags: string[];
  blocking_comment_count: number;
}

export interface WeeklyReportResponse {
  message: string;
  timeline_id: number;
  timeline_name: string;
  period: WeeklyReportPeriod;
  overview: WeeklyReportOverview;
  completed_tasks: WeeklyReportCompletedTask[];
  risk_items: WeeklyReportRiskItem[];
  recent_comments: WeeklyReportCommentItem[];
  next_actions: string[];
  ai_summary: string;
  analysis?: WeeklyReportAnalysis;
}

export interface ConflictCheckPayload {
  task_id?: number;
  name?: string;
  start_date?: string | null;
  end_date?: string | null;
  assignee_user_id?: number;
  priority?: number;
}

export interface ResourceConflictItem {
  task_id: number;
  name: string;
  status: TaskStatus | string;
  start_date: string;
  end_date: string;
  owner_name: string | null;
  same_assignee: boolean;
  reason: string;
  timeline_id?: number;
  timeline_name?: string | null;
  is_cross_project?: boolean;
}

export interface ResourceConflictSuggestion {
  start_date: string;
  end_date: string;
}

export interface ResourceConflictResponse {
  message: string;
  timeline_id: number;
  task_name: string | null;
  priority?: number;
  priority_label?: string;
  has_conflict: boolean;
  conflict_count: number;
  assignee_user_id: number;
  assignee_name?: string | null;
  is_task_name_redacted?: boolean;
  assignee_conflict_count: number;
  project_conflict_count: number;
  cross_project_conflict_count?: number;
  workload_overload_count?: number;
  workload_overload_days?: Array<{
    date: string;
    existing_task_count: number;
    projected_task_count: number;
    threshold: number;
    sample_tasks: string[];
  }>;
  conflicts: ResourceConflictItem[];
  suggestion: ResourceConflictSuggestion | null;
  ai_suggestion: string;
}
