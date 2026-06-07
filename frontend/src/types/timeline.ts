import type { TaskStatus } from './task';
import type { TaskPriority } from './task';

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

export type WeeklyReportAiSummarySource =
  | 'llm'
  | 'cache'
  | 'fallback-empty'
  | 'fallback-timeout'
  | 'fallback-error';

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
  ai_summary_source?: WeeklyReportAiSummarySource;
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
  ai_summary_source?: WeeklyReportAiSummarySource;
  analysis?: WeeklyReportAnalysis;
}

export type RiskSeverity = 'high' | 'medium' | 'low';

export interface RiskWarning {
  code: string;
  message: string;
  task_id?: number;
  dependency_task_id?: number | string;
  source_task_id?: number;
  target_task_id?: number;
  task_ids?: number[];
}

export interface CriticalPathTask {
  task_id: number;
  name: string;
  start_date: string | null;
  end_date: string | null;
  duration_days: number;
  earliest_start: number;
  earliest_finish: number;
  latest_start: number;
  latest_finish: number;
  float_days: number;
  is_completed: boolean;
  depends_on_task_ids: number[];
}

export interface RiskItem {
  task_id: number;
  name: string;
  severity: RiskSeverity;
  impact_days: number;
  reasons: string[];
  suggested_actions: string[];
  due_date: string | null;
  depends_on_task_ids: number[];
  float_days: number;
  is_critical: boolean;
}

export interface RiskAnalysisGraphNode {
  task_id: number;
  name: string;
  status: TaskStatus | string;
  start_date: string | null;
  end_date: string | null;
  duration_days: number;
  float_days: number;
  is_critical: boolean;
  depends_on_task_ids: number[];
}

export interface RiskAnalysisGraphEdge {
  source_task_id: number;
  target_task_id: number;
  is_critical: boolean;
}

export interface CriticalPathSummary {
  total_tasks: number;
  projected_duration_days: number;
  critical_path_task_count: number;
  critical_path_duration_days: number;
  risk_item_count: number;
  high_risk_count: number;
  warning_count: number;
}

export interface CriticalPathAnalysisResponse {
  message: string;
  timeline_id: number;
  timeline_name: string;
  generated_at: string;
  summary: CriticalPathSummary;
  critical_path: CriticalPathTask[];
  risk_items: RiskItem[];
  warnings: RiskWarning[];
  graph: {
    nodes: RiskAnalysisGraphNode[];
    edges: RiskAnalysisGraphEdge[];
  };
}

export interface ConflictCheckPayload {
  task_id?: number;
  name?: string;
  start_date: string;
  end_date: string;
  assignee_user_id?: number;
  priority?: TaskPriority;
  include_ai_suggestion?: boolean;
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
  include_ai_suggestion?: boolean;
}

export interface SourceReference {
  source_type: 'timeline_task' | 'knowledge_chunk';
  source_id: string;
  title: string;
  snippet: string;
  score: number;
}

export interface AIPlanSuggestedTimeline {
  name: string;
  objective: string;
}

export interface AIPlanSuggestedTask {
  name: string;
  reason: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  estimated_days: number;
  depends_on: string[];
}

export interface AIPlanSuggestionResponse {
  message: string;
  suggested_timeline: AIPlanSuggestedTimeline;
  suggested_tasks: AIPlanSuggestedTask[];
  source_references: SourceReference[];
  summary?: string;
  meta?: {
    fallback_used?: boolean;
    generated_at?: string;
    use_personal_knowledge?: boolean;
    use_project_knowledge?: boolean;
    project_id?: number | null;
    retrieved_history_count?: number;
    retrieved_knowledge_count?: number;
  };
}

export interface AIPlanSuggestionRequest {
  request: string;
  use_personal_knowledge?: boolean;
  use_project_knowledge?: boolean;
  project_id?: number;
  max_sources?: number;
}

export interface KnowledgeDocumentItem {
  id: number;
  filename: string;
  project_id?: number | null;
  mime_type?: string | null;
  file_path?: string | null;
  storage_key?: string | null;
  original_filename?: string | null;
  size_bytes?: number | null;
  sha256?: string;
  status: 'uploaded' | 'indexing' | 'ready' | 'failed' | string;
  error_message?: string | null;
  chunk_count?: number;
  has_source_text?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface KnowledgeDocumentEventItem {
  id: number;
  document_id?: number | null;
  project_id: number;
  actor_user_id: number;
  event_type: string;
  event_payload: Record<string, unknown>;
  created_at?: string | null;
}

export interface KnowledgeDocumentsResponse {
  message: string;
  documents: KnowledgeDocumentItem[];
  meta: {
    limit: number;
    offset: number;
    count: number;
  };
}

export interface KnowledgeDocumentEventsResponse {
  message: string;
  events: KnowledgeDocumentEventItem[];
  meta: {
    limit: number;
    offset: number;
    count: number;
  };
}
