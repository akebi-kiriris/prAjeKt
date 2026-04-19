import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

const phase7Mocks = vi.hoisted(() => ({
  confirm: vi.fn(),
  getWeeklyReport: vi.fn(),
  getRiskAnalysis: vi.fn(),
  conflictCheck: vi.fn(),
  updateRemark: vi.fn(),
  getMembers: vi.fn(),
  searchUser: vi.fn(),
  addMember: vi.fn(),
  removeMember: vi.fn(),
  generateTasks: vi.fn(),
  batchCreateTasks: vi.fn(),
  createTask: vi.fn(),
  getTaskMembers: vi.fn(),
  createSubtask: vi.fn(),
  getSubtasks: vi.fn(),
  toggleSubtask: vi.fn(),
  deleteSubtask: vi.fn(),
  addComment: vi.fn(),
  getComments: vi.fn(),
  deleteComment: vi.fn(),
  summarizeComments: vi.fn(),
  uploadFile: vi.fn(),
  getFiles: vi.fn(),
  deleteFile: vi.fn(),
  updateMemberRole: vi.fn(),
  addTaskMember: vi.fn(),
  removeTaskMember: vi.fn(),
  executeMcp: vi.fn(),
  loadTaskDetailResourcesWithMembers: vi.fn(),
  downloadFileFromUrl: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
  toastInfo: vi.fn(),
  toastWarning: vi.fn(),
}));

vi.mock('../../../services/timelineService', () => ({
  timelineService: {
    getWeeklyReport: phase7Mocks.getWeeklyReport,
    getRiskAnalysis: phase7Mocks.getRiskAnalysis,
    conflictCheck: phase7Mocks.conflictCheck,
    updateRemark: phase7Mocks.updateRemark,
    getMembers: phase7Mocks.getMembers,
    searchUser: phase7Mocks.searchUser,
    addMember: phase7Mocks.addMember,
    removeMember: phase7Mocks.removeMember,
    generateTasks: phase7Mocks.generateTasks,
    batchCreateTasks: phase7Mocks.batchCreateTasks,
  },
}));

vi.mock('../../../services/taskService', () => ({
  taskService: {
    create: phase7Mocks.createTask,
    getMembers: phase7Mocks.getTaskMembers,
    createSubtask: phase7Mocks.createSubtask,
    getSubtasks: phase7Mocks.getSubtasks,
    toggleSubtask: phase7Mocks.toggleSubtask,
    deleteSubtask: phase7Mocks.deleteSubtask,
    addComment: phase7Mocks.addComment,
    getComments: phase7Mocks.getComments,
    deleteComment: phase7Mocks.deleteComment,
    summarizeComments: phase7Mocks.summarizeComments,
    uploadFile: phase7Mocks.uploadFile,
    getFiles: phase7Mocks.getFiles,
    deleteFile: phase7Mocks.deleteFile,
    updateMemberRole: phase7Mocks.updateMemberRole,
    addMember: phase7Mocks.addTaskMember,
    removeMember: phase7Mocks.removeTaskMember,
  },
}));

vi.mock('../../../services/copilotService', () => ({
  copilotService: {
    executeMcp: phase7Mocks.executeMcp,
  },
}));

vi.mock('../../../utils/taskDetails', () => ({
  loadTaskDetailResourcesWithMembers: phase7Mocks.loadTaskDetailResourcesWithMembers,
  downloadFileFromUrl: phase7Mocks.downloadFileFromUrl,
}));

vi.mock('../../../composables/useConfirm', () => ({
  useConfirm: () => ({ confirm: phase7Mocks.confirm }),
}));

vi.mock('vue-sonner', () => ({
  toast: {
    success: phase7Mocks.toastSuccess,
    error: phase7Mocks.toastError,
    info: phase7Mocks.toastInfo,
    warning: phase7Mocks.toastWarning,
  },
}));

import TimelineDetailDialog from '../TimelineDetailDialog.vue';

const baseTimeline = {
  id: 99,
  name: 'Phase7 專案',
  startDate: '2026-04-10',
  endDate: '2026-04-30',
  remark: '本週重點任務',
  role: 0 as const,
  totalTasks: 5,
  completedTasks: 2,
};

describe('TimelineDetailDialog Phase 7.1', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    phase7Mocks.getWeeklyReport.mockResolvedValue({
      data: {
        message: '週報生成成功',
        timeline_id: 99,
        timeline_name: 'Phase7 專案',
        period: {
          start_date: '2026-04-14',
          end_date: '2026-04-20',
        },
        overview: {
          total_tasks: 6,
          completed_tasks: 2,
          completion_rate: 33.3,
          at_risk_tasks: 1,
          comment_count: 1,
        },
        completed_tasks: [
          {
            task_id: 1001,
            name: '完成 API 合約',
            completed_at: '2026-04-16T08:30:00Z',
            due_date: '2026-04-16',
            is_late: false,
            owner_name: 'Owner',
          },
        ],
        risk_items: [
          {
            task_id: 1002,
            name: '部署驗證',
            status: 'in_progress',
            due_date: '2026-04-18',
            reason: '本期到期',
            days_overdue: 0,
            days_remaining: 2,
          },
        ],
        recent_comments: [],
        next_actions: ['優先處理「部署驗證」（截止：2026-04-18）'],
      },
    });

    phase7Mocks.getRiskAnalysis.mockResolvedValue({
      data: {
        message: '風險分析完成',
        timeline_id: 99,
        timeline_name: 'Phase7 專案',
        generated_at: '2026-04-19T00:00:00Z',
        summary: {
          total_tasks: 6,
          projected_duration_days: 18,
          critical_path_task_count: 3,
          critical_path_duration_days: 9,
          risk_item_count: 2,
          high_risk_count: 1,
          warning_count: 1,
        },
        critical_path: [
          {
            task_id: 1001,
            name: '完成 API 合約',
            start_date: '2026-04-14',
            end_date: '2026-04-16',
            duration_days: 3,
            earliest_start: 0,
            earliest_finish: 3,
            latest_start: 0,
            latest_finish: 3,
            float_days: 0,
            is_completed: false,
            depends_on_task_ids: [],
          },
        ],
        risk_items: [
          {
            task_id: 1002,
            name: '部署驗證',
            severity: 'high',
            impact_days: 2,
            reasons: ['位於關鍵路徑'],
            suggested_actions: ['每日追蹤'],
            due_date: '2026-04-18',
            depends_on_task_ids: [1001],
            float_days: 0,
            is_critical: true,
          },
        ],
        warnings: [
          {
            code: 'missing_dependency',
            message: '依賴任務不存在、已刪除或不在同一專案，已忽略',
            task_id: 1002,
            dependency_task_id: 9999,
          },
        ],
        graph: {
          nodes: [],
          edges: [],
        },
      },
    });

    phase7Mocks.confirm.mockResolvedValue(true);
    phase7Mocks.conflictCheck.mockResolvedValue({
      data: {
        message: '未偵測到排程衝突',
        timeline_id: 99,
        task_name: '新任務',
        has_conflict: false,
        conflict_count: 0,
        assignee_user_id: 1,
        assignee_conflict_count: 0,
        project_conflict_count: 0,
        conflicts: [],
        suggestion: null,
      },
    });
    phase7Mocks.createTask.mockResolvedValue({ data: { message: 'ok' } });
  });

  it('顯示週報任務與風險列表', async () => {
    const wrapper = mount(TimelineDetailDialog, {
      props: {
        selectedTimeline: baseTimeline,
        timelineTasks: [],
        apiBaseUrl: 'http://localhost:5000/api',
      },
    });

    await flushPromises();

    expect(phase7Mocks.getWeeklyReport).not.toHaveBeenCalled();
    expect(phase7Mocks.getRiskAnalysis).not.toHaveBeenCalled();

    const expandButtons = wrapper.findAll('button').filter((button) => button.text().trim() === '展開');
    expect(expandButtons.length).toBeGreaterThanOrEqual(2);

    await expandButtons[0].trigger('click');
    await flushPromises();
    await expandButtons[1].trigger('click');
    await flushPromises();

    expect(phase7Mocks.getWeeklyReport).toHaveBeenCalled();
    expect(phase7Mocks.getRiskAnalysis).toHaveBeenCalled();
    expect(wrapper.text()).toContain('週報預覽');
    expect(wrapper.text()).toContain('完成 API 合約');
    expect(wrapper.text()).toContain('部署驗證');
    expect(wrapper.text()).toContain('風險分析（Critical Path）');
    expect(wrapper.text()).toContain('高風險任務');
  });

  it('新增任務時若有衝突會顯示提示且可取消送出', async () => {
    phase7Mocks.confirm.mockResolvedValue(false);
    phase7Mocks.conflictCheck.mockResolvedValue({
      data: {
        message: '偵測到 1 個衝突',
        timeline_id: 99,
        task_name: '新任務',
        has_conflict: true,
        conflict_count: 1,
        assignee_user_id: 1,
        assignee_conflict_count: 1,
        project_conflict_count: 0,
        cross_project_conflict_count: 1,
        workload_overload_count: 1,
        workload_overload_days: [
          {
            date: '2026-04-18',
            existing_task_count: 3,
            projected_task_count: 4,
            threshold: 3,
            sample_tasks: ['既有排程任務', '跨專案驗收'],
          },
        ],
        conflicts: [
          {
            task_id: 2001,
            name: '既有排程任務',
            status: 'in_progress',
            start_date: '2026-04-15',
            end_date: '2026-04-17',
            owner_name: 'Owner',
            same_assignee: true,
            reason: '與同成員既有任務日期重疊',
          },
        ],
        suggestion: {
          start_date: '2026-04-18',
          end_date: '2026-04-20',
        },
      },
    });

    const wrapper = mount(TimelineDetailDialog, {
      props: {
        selectedTimeline: baseTimeline,
        timelineTasks: [],
        apiBaseUrl: 'http://localhost:5000/api',
      },
    });

    await flushPromises();

    const addTaskButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('新增任務'));

    expect(addTaskButton).toBeTruthy();
    if (!addTaskButton) {
      throw new Error('找不到新增任務按鈕');
    }
    await addTaskButton.trigger('click');

    const addTaskForm = wrapper
      .findAll('form')
      .find((form) => form.find('input[placeholder="輸入任務名稱"]').exists());
    expect(addTaskForm).toBeTruthy();
    if (!addTaskForm) {
      throw new Error('找不到新增任務表單');
    }

    const nameInput = addTaskForm.find('input[placeholder="輸入任務名稱"]');
    await nameInput.setValue('新任務');

    const dateInputs = addTaskForm.findAll('input[type="date"]');
    expect(dateInputs.length).toBe(2);
    await dateInputs[1].setValue('2026-04-18');

    await addTaskForm.trigger('submit.prevent');
    await flushPromises();

    expect(phase7Mocks.conflictCheck).toHaveBeenCalled();
    expect(phase7Mocks.confirm).toHaveBeenCalled();
    expect(wrapper.text()).toContain('偵測到 1 個排程衝突');
    expect(wrapper.text()).toContain('過載日列表');
    expect(wrapper.text()).toContain('跨專案衝突：1 個');
    expect(wrapper.text()).toContain('既有任務：既有排程任務、跨專案驗收');
    expect(wrapper.text()).toContain('既有排程任務');
    expect(phase7Mocks.createTask).not.toHaveBeenCalled();
  });
});
