import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  collectTasksWithPotentiallyDroppedDependencies,
  getAiPriorityClass,
  getDefaultWeeklyReportRange,
  getPriorityBadgeClass,
  getPriorityLabel,
  getSourceReferenceLabel,
  getWeeklyReportAiSummarySourceLabel,
  mapRagPriorityToTaskPriority,
  mapRagResponseToGeneratedTasks,
  normalizeGeneratedTasks,
  normalizeIdList,
  normalizeStringList,
  toDateOnly,
} from '../timelineDetailUtils';
import type { AIPlanSuggestionResponse, TimelineBatchTaskPayload } from '../../types';

describe('mapRagPriorityToTaskPriority', () => {
  it.each([
    ['CRITICAL', 1],
    ['HIGH', 1],
    ['high', 1],
    ['LOW', 3],
    ['low', 3],
    ['MEDIUM', 2],
    ['unknown', 2],
    ['', 2],
    [undefined, 2],
  ] as const)('maps %s to %s', (priority, expected) => {
    expect(mapRagPriorityToTaskPriority(priority)).toBe(expected);
  });
});

describe('timelineDetailUtils basic normalizers', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-06-24T08:00:00.000Z'));
  });

  it('labels source references and weekly report summary sources', () => {
    expect(getSourceReferenceLabel('timeline_task')).toBe('歷史任務');
    expect(getSourceReferenceLabel('knowledge_document')).toBe('知識文件');
    expect(getWeeklyReportAiSummarySourceLabel('llm')).toBe('AI 直接生成');
    expect(getWeeklyReportAiSummarySourceLabel('cache')).toBe('AI 快取結果');
    expect(getWeeklyReportAiSummarySourceLabel('fallback-timeout')).toBe('模板回退（AI 逾時）');
    expect(getWeeklyReportAiSummarySourceLabel('fallback-error')).toBe('模板回退（AI 錯誤）');
    expect(getWeeklyReportAiSummarySourceLabel('fallback-empty')).toBe('模板回退（AI 回傳空內容）');
    expect(getWeeklyReportAiSummarySourceLabel('unknown')).toBe('未標記');
  });

  it('normalizes dates, ids and string lists defensively', () => {
    expect(toDateOnly('2026-06-24T15:30:00.000Z')).toBe('2026-06-24');
    expect(toDateOnly('not-a-date')).toBeNull();
    expect(toDateOnly(null)).toBeNull();

    expect(normalizeIdList([1, '2', '2', 0, -1, 'abc', 1.5])).toEqual([1, 2]);
    expect(normalizeStringList([' 設計 ', '', '設計', '開發', 123])).toEqual(['設計', '開發']);
    expect(normalizeStringList('設計')).toEqual([]);
  });

  it('computes the default weekly report range from today and the prior six days', () => {
    expect(getDefaultWeeklyReportRange()).toEqual({
      start_date: '2026-06-18',
      end_date: '2026-06-24',
    });
  });

  it('returns priority labels and badge classes with safe defaults', () => {
    expect(getPriorityLabel(1)).toBe('🔴 高');
    expect(getPriorityLabel(2)).toBe('🟡 中');
    expect(getPriorityLabel(3)).toBe('🟢 低');
    expect(getPriorityLabel(99)).toBe('🟡 中');
    expect(getPriorityBadgeClass(1)).toContain('text-red-700');
    expect(getPriorityBadgeClass(99)).toContain('bg-gray-100');
    expect(getAiPriorityClass(3)).toContain('text-green-700');
    expect(getAiPriorityClass(99)).toContain('bg-gray-100');
  });
});

describe('timelineDetailUtils task dependency helpers', () => {
  it('collects new tasks whose dependencies would be dropped from the selected import set', () => {
    const tasks = [
      {
        name: '既有任務',
        task_id: 10,
        isExisting: true,
      },
      {
        name: '前端切版',
        isExisting: false,
        depends_on_task_refs: ['不存在的任務'],
      },
      {
        name: 'API 串接',
        task_id: 20,
        isExisting: false,
        depends_on_task_ids: [10, 20],
      },
      {
        name: '測試補強',
        isExisting: false,
        depends_on_task_refs: ['前端切版'],
        depends_on_task_ids: [10],
      },
    ] as TimelineBatchTaskPayload[];

    expect(collectTasksWithPotentiallyDroppedDependencies(tasks)).toEqual(['前端切版', 'API 串接']);
  });
});

describe('timelineDetailUtils AI payload helpers', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-06-24T08:00:00.000Z'));
  });

  it('normalizes generated task payloads from array, object and invalid inputs', () => {
    const task = { name: '任務 A' };

    expect(normalizeGeneratedTasks([task, null, 'bad'])).toEqual([task]);
    expect(normalizeGeneratedTasks({ tasks: [task, undefined] })).toEqual([task]);
    expect(normalizeGeneratedTasks({ tasks: 'bad' })).toEqual([]);
    expect(normalizeGeneratedTasks(null)).toEqual([]);
  });

  it('maps RAG suggested tasks into editable generated tasks with defaults', () => {
    const payload = {
      suggested_tasks: [
        {
          name: '需求盤點',
          priority: 'HIGH',
          estimated_days: 2,
          reason: '先釐清範圍',
          depends_on: [' kickoff '],
        },
        {
          name: '',
          priority: 'LOW',
          estimated_days: 0,
          reason: '',
          depends_on: 'bad',
        },
      ],
    } as unknown as AIPlanSuggestionResponse;

    expect(mapRagResponseToGeneratedTasks(payload)).toEqual([
      {
        name: '需求盤點',
        priority: 1,
        estimated_days: 2,
        start_date: '2026-06-24',
        end_date: '2026-06-25',
        remark: '先釐清範圍',
        task_remark: '先釐清範圍',
        depends_on_task_refs: [' kickoff '],
        status: 'pending',
      },
      {
        name: '建議任務 2',
        priority: 3,
        estimated_days: 3,
        start_date: '2026-06-25',
        end_date: '2026-06-27',
        remark: null,
        task_remark: null,
        depends_on_task_refs: [],
        status: 'pending',
      },
    ]);
  });
});
