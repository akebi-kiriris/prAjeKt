import type {
  AIPlanSuggestionResponse,
  AiGeneratedTask,
  SourceReference,
  TimelineBatchTaskPayload,
  TaskPriority,
  WeeklyReportAiSummarySource,
} from '../types';

export const getSourceReferenceLabel = (sourceType: SourceReference['source_type']): string => {
  if (sourceType === 'timeline_task') return '歷史任務';
  return '知識文件';
};

export const toDateOnly = (value?: string | null): string | null => {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed.toISOString().split('T')[0];
};

export const normalizeIdList = (values: Array<number | string>): number[] => {
  return Array.from(
    new Set(
      values
        .map((value) => Number(value))
        .filter((value) => Number.isInteger(value) && value > 0),
    ),
  );
};

export const normalizeStringList = (values: unknown): string[] => {
  if (!Array.isArray(values)) {
    return [];
  }

  return Array.from(
    new Set(
      values
        .map((value) => (typeof value === 'string' ? value.trim() : ''))
        .filter((value) => value.length > 0),
    ),
  );
};

export const collectTasksWithPotentiallyDroppedDependencies = (
  tasks: TimelineBatchTaskPayload[],
): string[] => {
  const selectedTaskNames = new Set<string>();
  const selectedExistingTaskIds = new Set<number>();

  for (const task of tasks) {
    const name = String(task.name ?? '').trim();
    if (name) {
      selectedTaskNames.add(name);
    }

    if (task.isExisting) {
      const taskId = Number(task.task_id);
      if (Number.isInteger(taskId) && taskId > 0) {
        selectedExistingTaskIds.add(taskId);
      }
    }
  }

  const affectedTaskNames = new Set<string>();

  for (const task of tasks) {
    if (task.isExisting) {
      continue;
    }

    const taskName = String(task.name ?? '').trim();
    if (!taskName) {
      continue;
    }

    const dependencyRefs = normalizeStringList(task.depends_on_task_refs);
    const dependencyIds = normalizeIdList(task.depends_on_task_ids || []);

    const hasMissingRef = dependencyRefs.some((ref) => !selectedTaskNames.has(ref));

    const currentTaskId = Number(task.task_id);
    const hasCurrentTaskId = Number.isInteger(currentTaskId) && currentTaskId > 0;
    const hasMissingId = dependencyIds.some((dependencyId) => {
      if (hasCurrentTaskId && dependencyId === currentTaskId) {
        return true;
      }
      return !selectedExistingTaskIds.has(dependencyId);
    });

    if (hasMissingRef || hasMissingId) {
      affectedTaskNames.add(taskName);
    }
  }

  return Array.from(affectedTaskNames);
};

export const getDefaultWeeklyReportRange = (): { start_date: string; end_date: string } => {
  const end = new Date();
  const start = new Date(end);
  start.setDate(end.getDate() - 6);

  return {
    start_date: start.toISOString().split('T')[0],
    end_date: end.toISOString().split('T')[0],
  };
};

export const getWeeklyReportAiSummarySourceLabel = (
  source?: WeeklyReportAiSummarySource | string,
): string => {
  switch (source) {
    case 'llm':
      return 'AI 直接生成';
    case 'cache':
      return 'AI 快取結果';
    case 'fallback-timeout':
      return '模板回退（AI 逾時）';
    case 'fallback-error':
      return '模板回退（AI 錯誤）';
    case 'fallback-empty':
      return '模板回退（AI 回傳空內容）';
    default:
      return '未標記';
  }
};

export const normalizeGeneratedTasks = (payload: unknown): AiGeneratedTask[] => {
  if (Array.isArray(payload)) {
    return payload.filter((item): item is AiGeneratedTask => Boolean(item && typeof item === 'object'));
  }

  if (payload && typeof payload === 'object' && 'tasks' in payload) {
    const candidate = payload.tasks;
    if (Array.isArray(candidate)) {
      return candidate.filter((item): item is AiGeneratedTask => Boolean(item && typeof item === 'object'));
    }
  }

  return [];
};

export const mapRagPriorityToTaskPriority = (priority: string | undefined): TaskPriority => {
  const normalized = String(priority || '').toUpperCase();
  if (normalized === 'CRITICAL' || normalized === 'HIGH') return 1;
  if (normalized === 'LOW') return 3;
  return 2;
};

export const mapRagResponseToGeneratedTasks = (payload: AIPlanSuggestionResponse): AiGeneratedTask[] => {
  const tasks = Array.isArray(payload.suggested_tasks) ? payload.suggested_tasks : [];
  const today = new Date();
  return tasks.map((task, index) => {
    const estimatedDays = Number(task.estimated_days) > 0 ? Number(task.estimated_days) : 3;
    const startDate = new Date(today);
    const endDate = new Date(today);
    startDate.setDate(today.getDate() + index);
    endDate.setDate(startDate.getDate() + Math.max(estimatedDays - 1, 0));

    return {
      name: task.name || `建議任務 ${index + 1}`,
      priority: mapRagPriorityToTaskPriority(task.priority),
      estimated_days: estimatedDays,
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
      remark: task.reason || null,
      task_remark: task.reason || null,
      depends_on_task_refs: Array.isArray(task.depends_on) ? task.depends_on : [],
      status: 'pending',
    };
  });
};

export const getPriorityLabel = (priority: number): string => (
  { 1: '🔴 高', 2: '🟡 中', 3: '🟢 低' }[priority] || '🟡 中'
);

export const getPriorityBadgeClass = (priority: number): string => (
  {
    1: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border border-red-200',
    2: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border border-yellow-200',
    3: 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200',
  }[priority] || 'bg-gray-100 text-gray-700 border border-gray-200'
);

export const getAiPriorityClass = (priority: number): string => (
  {
    1: 'bg-red-100 text-red-700',
    2: 'bg-yellow-100 text-yellow-700',
    3: 'bg-green-100 text-green-700',
  }[priority] || 'bg-gray-100 text-gray-700'
);
