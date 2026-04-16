import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { useTaskStore } from '../../stores/tasks';

const phase7Mocks = vi.hoisted(() => ({
  confirm: vi.fn(),
  conflictCheck: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
  toastInfo: vi.fn(),
  toastWarning: vi.fn(),
  getMembers: vi.fn(),
  searchUser: vi.fn(),
  addMember: vi.fn(),
  removeMember: vi.fn(),
  getSubtasks: vi.fn(),
  createSubtask: vi.fn(),
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
}));

vi.mock('../../services/timelineService', () => ({
  timelineService: {
    conflictCheck: phase7Mocks.conflictCheck,
    getMembers: phase7Mocks.getMembers,
    searchUser: phase7Mocks.searchUser,
    addMember: phase7Mocks.addMember,
    removeMember: phase7Mocks.removeMember,
  },
}));

vi.mock('../../services/taskService', () => ({
  taskService: {
    getSubtasks: phase7Mocks.getSubtasks,
    createSubtask: phase7Mocks.createSubtask,
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
  },
}));

vi.mock('../../utils/taskDetails', () => ({
  loadTaskDetailResources: vi.fn().mockResolvedValue({ comments: [], files: [], subtasks: [] }),
  downloadFileFromUrl: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../../composables/useConfirm', () => ({
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

import TasksView from '../TasksView.vue';

describe('TasksView Phase 7.1', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());

    const store = useTaskStore();
    store.tasks = [
      {
        task_id: 77,
        name: '既有任務',
        completed: false,
        completed_at: null,
        timeline_id: 12,
        priority: 2,
        status: 'in_progress',
        tags: null,
        estimated_hours: null,
        actual_hours: null,
        members: [],
        subtasks: [],
        created_at: '2026-04-10T00:00:00Z',
        start_date: '2026-04-12T00:00:00Z',
        end_date: '2026-04-18T00:00:00Z',
        updated_at: '2026-04-12T00:00:00Z',
        task_remark: '備註',
        isWork: 1,
        is_owner: true,
      },
    ] as never;

    vi.spyOn(store, 'fetchTasks').mockResolvedValue(undefined);
    vi.spyOn(store, 'updateTask').mockResolvedValue(undefined);
    vi.spyOn(store, 'addTask').mockResolvedValue(undefined);

    phase7Mocks.conflictCheck.mockResolvedValue({
      data: {
        message: '偵測到 1 個衝突',
        timeline_id: 12,
        task_name: '既有任務',
        has_conflict: true,
        conflict_count: 1,
        assignee_user_id: 1,
        assignee_conflict_count: 1,
        project_conflict_count: 0,
        cross_project_conflict_count: 1,
        workload_overload_count: 1,
        workload_overload_days: [
          {
            date: '2026-04-20',
            existing_task_count: 3,
            projected_task_count: 4,
            threshold: 3,
            sample_tasks: ['衝突任務', '跨專案驗收'],
          },
        ],
        conflicts: [
          {
            task_id: 100,
            name: '衝突任務',
            status: 'in_progress',
            start_date: '2026-04-17',
            end_date: '2026-04-19',
            owner_name: 'Owner',
            same_assignee: true,
            reason: '與同成員既有任務日期重疊',
          },
        ],
        suggestion: {
          start_date: '2026-04-20',
          end_date: '2026-04-22',
        },
      },
    });
    phase7Mocks.confirm.mockResolvedValue(false);
  });

  it('編輯 timeline 任務時會先做衝突預檢，取消後不送出更新', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);

    const store = useTaskStore();
    store.tasks = [
      {
        task_id: 77,
        name: '既有任務',
        completed: false,
        completed_at: null,
        timeline_id: 12,
        priority: 2,
        status: 'in_progress',
        tags: null,
        estimated_hours: null,
        actual_hours: null,
        members: [],
        subtasks: [],
        created_at: '2026-04-10T00:00:00Z',
        start_date: '2026-04-12T00:00:00Z',
        end_date: '2026-04-18T00:00:00Z',
        updated_at: '2026-04-12T00:00:00Z',
        task_remark: '備註',
        isWork: 1,
        is_owner: true,
      },
    ] as never;

    const fetchSpy = vi.spyOn(store, 'fetchTasks').mockResolvedValue(undefined);
    const updateSpy = vi.spyOn(store, 'updateTask').mockResolvedValue(undefined);

    const wrapper = mount(TasksView, {
      global: {
        plugins: [pinia],
        stubs: {
          Teleport: true,
        },
      },
    });

    await flushPromises();
    expect(fetchSpy).toHaveBeenCalled();

    const editButton = wrapper
      .findAll('button')
      .find((button) => button.attributes('title') === '編輯');
    expect(editButton).toBeTruthy();
    if (!editButton) {
      throw new Error('找不到編輯按鈕');
    }

    await editButton.trigger('click');

    const dateInputs = wrapper.findAll('input[type="date"]');
    expect(dateInputs.length).toBeGreaterThan(1);
    await dateInputs[1].setValue('2026-04-20');

    const form = wrapper.find('form');
    await form.trigger('submit.prevent');
    await flushPromises();

    expect(phase7Mocks.conflictCheck).toHaveBeenCalled();
    expect(phase7Mocks.confirm).toHaveBeenCalled();
    expect(wrapper.text()).toContain('偵測到 1 個排程衝突');
    expect(wrapper.text()).toContain('過載日列表');
    expect(wrapper.text()).toContain('跨專案衝突：1 個');
    expect(wrapper.text()).toContain('既有任務：衝突任務、跨專案驗收');
    expect(updateSpy).not.toHaveBeenCalled();
  });
});
