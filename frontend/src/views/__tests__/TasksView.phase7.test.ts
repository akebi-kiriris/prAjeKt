import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { useTaskStore } from '../../stores/tasks';
import type { Task, TaskMember } from '../../types';

const phase7Mocks = vi.hoisted(() => ({
  confirm: vi.fn(),
  conflictCheck: vi.fn(),
  routerReplace: vi.fn(),
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

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ replace: phase7Mocks.routerReplace }),
}));

vi.mock('../../services/timelineService', () => ({
  timelineService: {
    conflictCheck: phase7Mocks.conflictCheck,
    getMembers: phase7Mocks.getMembers,
  },
}));

vi.mock('../../services/taskService', () => ({
  taskService: {
    getMembers: phase7Mocks.getMembers,
    searchUser: phase7Mocks.searchUser,
    addMember: phase7Mocks.addMember,
    removeMember: phase7Mocks.removeMember,
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

type TaskFixtureOverrides = {
  [Key in keyof Task]?: Task[Key];
};

const makeTask = (overrides: TaskFixtureOverrides = {}): Task => ({
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
  end_date: '2026-12-18T00:00:00Z',
  updated_at: '2026-04-12T00:00:00Z',
  task_remark: '備註',
  isWork: 1,
  is_owner: true,
  ...overrides,
});

const findButton = (wrapper: VueWrapper, label: string) => {
  const button = wrapper
    .findAll('button')
    .find((candidate) => candidate.text().trim() === label);
  if (!button) {
    throw new Error(`找不到「${label}」按鈕`);
  }
  return button;
};

const mountView = (tasks: Task[]) => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const store = useTaskStore();
  store.tasks = tasks;

  const spies = {
    fetch: vi.spyOn(store, 'fetchTasks').mockResolvedValue(undefined),
    update: vi.spyOn(store, 'updateTask').mockResolvedValue(undefined),
    add: vi.spyOn(store, 'addTask').mockResolvedValue(undefined),
    remove: vi.spyOn(store, 'removeTask').mockResolvedValue(undefined),
    toggle: vi.spyOn(store, 'toggleTask').mockResolvedValue(undefined),
  };

  const wrapper = mount(TasksView, {
    global: {
      plugins: [pinia],
      stubs: {
        Teleport: true,
      },
    },
  });

  return { wrapper, store, spies, pinia };
};

const noConflictResponse = {
  data: {
    message: '沒有衝突',
    timeline_id: 12,
    task_name: '既有任務',
    has_conflict: false,
    conflict_count: 0,
    assignee_user_id: null,
    assignee_conflict_count: 0,
    project_conflict_count: 0,
    cross_project_conflict_count: 0,
    workload_overload_count: 0,
    workload_overload_days: [],
    conflicts: [],
    suggestion: null,
  },
};

const conflictResponse = {
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
};

describe('TasksView Phase 7.1', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    phase7Mocks.conflictCheck.mockResolvedValue(conflictResponse);
    phase7Mocks.confirm.mockResolvedValue(false);
    phase7Mocks.getMembers.mockResolvedValue({ data: [] });
    phase7Mocks.addMember.mockResolvedValue({ data: {} });
    phase7Mocks.removeMember.mockResolvedValue({ data: {} });
    phase7Mocks.updateMemberRole.mockResolvedValue({ data: {} });
  });

  it('顯示摘要，並可依關鍵字、狀態、逾期與優先級篩選排序', async () => {
    const member: TaskMember = {
      user_id: 9,
      name: '王怡君',
      email: 'yijun@example.com',
      role: 1,
    };
    const { wrapper } = mountView([
      makeTask({ task_id: 1, name: '低優先未來任務', priority: 3, end_date: '2026-12-30T00:00:00Z' }),
      makeTask({
        task_id: 2,
        name: '高優先逾期任務',
        priority: 1,
        end_date: '2026-01-01T00:00:00Z',
        tags: ['後端'],
        members: [member],
      }),
      makeTask({
        task_id: 3,
        name: '已完成任務',
        completed: true,
        completed_at: '2026-05-01T00:00:00Z',
        status: 'completed',
        end_date: '2026-05-01T00:00:00Z',
      }),
    ]);
    await flushPromises();

    expect(wrapper.text()).toContain('全部任務');
    expect(wrapper.text()).toContain('進行中');
    expect(wrapper.text()).toContain('已完成');
    expect(wrapper.text()).toContain('逾期');
    expect(wrapper.text()).toContain('目前顯示 3 / 3 筆任務');

    const search = wrapper.get('input[placeholder="搜尋任務名稱 / 備註 / 成員 / 標籤"]');
    await search.setValue('怡君');
    expect(wrapper.text()).toContain('目前顯示 1 / 3 筆任務');
    expect(wrapper.text()).toContain('高優先逾期任務');
    expect(wrapper.text()).not.toContain('低優先未來任務');

    await search.setValue('');
    const selects = wrapper.findAll('select');
    await selects[0].setValue('completed');
    expect(wrapper.text()).toContain('目前顯示 1 / 3 筆任務');
    expect(wrapper.text()).toContain('已完成任務');
    expect(wrapper.text()).not.toContain('高優先逾期任務');

    await selects[0].setValue('overdue');
    expect(wrapper.text()).toContain('高優先逾期任務');
    expect(wrapper.text()).not.toContain('已完成任務');

    await selects[0].setValue('active');
    await selects[1].setValue('priority_desc');
    const taskNames = wrapper.findAll('article').map((article) => article.find('button').text().trim());
    expect(taskNames).toEqual(['高優先逾期任務', '低優先未來任務']);
  });

  it('截止日期缺失或格式錯誤時仍能穩定排序且不會誤判逾期', async () => {
    const { wrapper } = mountView([
      makeTask({ task_id: 1, name: '有截止日期', end_date: '2026-08-01T00:00:00Z' }),
      makeTask({ task_id: 2, name: '沒有截止日期', end_date: null }),
      makeTask({ task_id: 3, name: '錯誤截止日期', end_date: 'not-a-date' }),
    ]);
    await flushPromises();

    expect(wrapper.text()).toContain('目前顯示 3 / 3 筆任務');
    expect(wrapper.text()).not.toContain('已逾期');
    expect(wrapper.findAll('article').map((article) => article.find('button').text().trim())).toEqual([
      '有截止日期',
      '沒有截止日期',
      '錯誤截止日期',
    ]);

    const selects = wrapper.findAll('select');
    await selects[1].setValue('due_desc');
    expect(wrapper.findAll('article').map((article) => article.find('button').text().trim())).toEqual([
      '有截止日期',
      '沒有截止日期',
      '錯誤截止日期',
    ]);
  });

  it('可切換任務狀態，刪除取消時不呼叫 store，確認後才刪除', async () => {
    const { wrapper, spies } = mountView([makeTask()]);
    await flushPromises();

    await findButton(wrapper, '完成').trigger('click');
    expect(spies.toggle).toHaveBeenCalledWith(77);

    phase7Mocks.confirm.mockResolvedValueOnce(false).mockResolvedValueOnce(true);
    await findButton(wrapper, '刪除').trigger('click');
    await flushPromises();
    expect(spies.remove).not.toHaveBeenCalled();

    await findButton(wrapper, '刪除').trigger('click');
    await flushPromises();
    expect(spies.remove).toHaveBeenCalledWith(77);
  });

  it('新增一般任務時送出表單內容，成功後關閉並重設表單', async () => {
    const { wrapper, spies } = mountView([]);
    await flushPromises();

    await findButton(wrapper, '新增任務').trigger('click');
    await wrapper.get('input[placeholder="請輸入任務名稱"]').setValue('撰寫測試報告');
    const dateInputs = wrapper.findAll('input[type="date"]');
    await dateInputs[0].setValue('2026-07-01');
    await dateInputs[1].setValue('2026-07-05');
    await wrapper.get('textarea[placeholder="輸入任務備註..."]').setValue('整理驗證結果');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();

    expect(spies.add).toHaveBeenCalledWith({
      name: '撰寫測試報告',
      start_date: '2026-07-01',
      end_date: '2026-07-05',
      task_remark: '整理驗證結果',
      depends_on_task_ids: [],
    });
    expect(wrapper.find('form').exists()).toBe(false);

    await findButton(wrapper, '新增任務').trigger('click');
    expect(wrapper.get('input[placeholder="請輸入任務名稱"]').element).toHaveProperty('value', '');
  });

  it('編輯 timeline 任務且無衝突時會送出更新並關閉表單', async () => {
    phase7Mocks.conflictCheck.mockResolvedValue(noConflictResponse);
    const { wrapper, spies } = mountView([makeTask()]);
    await flushPromises();

    await findButton(wrapper, '編輯').trigger('click');
    await wrapper.get('input[placeholder="請輸入任務名稱"]').setValue('更新後任務');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();

    expect(phase7Mocks.conflictCheck).toHaveBeenCalledWith(12, expect.objectContaining({
      task_id: 77,
      name: '更新後任務',
    }));
    expect(spies.update).toHaveBeenCalledWith(77, expect.objectContaining({
      name: '更新後任務',
      depends_on_task_ids: [],
    }));
    expect(wrapper.find('form').exists()).toBe(false);
  });

  it('更新、刪除與切換狀態失敗時顯示錯誤，且畫面維持可操作', async () => {
    phase7Mocks.conflictCheck.mockResolvedValue(noConflictResponse);
    phase7Mocks.confirm.mockResolvedValue(true);
    const { wrapper, spies } = mountView([makeTask()]);
    await flushPromises();

    spies.update.mockRejectedValueOnce(new Error('update failed'));
    await findButton(wrapper, '編輯').trigger('click');
    await wrapper.get('input[placeholder="請輸入任務名稱"]').setValue('更新失敗仍保留');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();
    expect(phase7Mocks.toastError).toHaveBeenCalledWith('儲存任務失敗');
    expect(wrapper.find('form').exists()).toBe(true);
    expect(wrapper.get('input[placeholder="請輸入任務名稱"]').element).toHaveProperty(
      'value',
      '更新失敗仍保留',
    );

    await findButton(wrapper, '取消').trigger('click');
    spies.remove.mockRejectedValueOnce(new Error('delete failed'));
    await findButton(wrapper, '刪除').trigger('click');
    await flushPromises();
    expect(phase7Mocks.toastError).toHaveBeenCalledWith('刪除任務失敗');
    expect(wrapper.text()).toContain('既有任務');

    spies.toggle.mockRejectedValueOnce(new Error('toggle failed'));
    await findButton(wrapper, '完成').trigger('click');
    await flushPromises();
    expect(phase7Mocks.toastError).toHaveBeenCalledWith('更新任務狀態失敗');
    expect(findButton(wrapper, '編輯').exists()).toBe(true);
  });

  it('編輯 timeline 任務時會先做衝突預檢，取消後不送出更新', async () => {
    const { wrapper, spies } = mountView([makeTask({ end_date: '2026-04-18T00:00:00Z' })]);
    await flushPromises();

    await findButton(wrapper, '編輯').trigger('click');
    const dateInputs = wrapper.findAll('input[type="date"]');
    await dateInputs[1].setValue('2026-04-20');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();

    expect(phase7Mocks.conflictCheck).toHaveBeenCalled();
    expect(phase7Mocks.confirm).toHaveBeenCalled();
    expect(wrapper.text()).toContain('偵測到 1 個排程衝突');
    expect(wrapper.text()).toContain('過載日列表');
    expect(wrapper.text()).toContain('跨專案衝突：1 個');
    expect(wrapper.text()).toContain('既有任務：衝突任務、跨專案驗收');
    expect(spies.update).not.toHaveBeenCalled();
  });

  it('開啟成員面板會載入任務與專案成員，衝突取消時不指派', async () => {
    const currentMember: TaskMember = {
      user_id: 1,
      name: '目前負責人',
      email: 'owner@example.com',
      role: 0,
    };
    const candidate: TaskMember = {
      user_id: 2,
      name: '候選成員',
      email: 'candidate@example.com',
      role: 1,
    };
    phase7Mocks.getMembers
      .mockResolvedValueOnce({ data: [currentMember] })
      .mockResolvedValueOnce({ data: [currentMember, candidate] });

    const { wrapper } = mountView([makeTask()]);
    await flushPromises();
    await findButton(wrapper, '成員').trigger('click');
    await flushPromises();

    expect(phase7Mocks.getMembers).toHaveBeenNthCalledWith(1, 77);
    expect(phase7Mocks.getMembers).toHaveBeenNthCalledWith(2, 12);
    expect(wrapper.text()).toContain('成員管理 — 既有任務');
    expect(wrapper.text()).toContain('目前負責人');
    expect(wrapper.text()).toContain('候選成員');

    await findButton(wrapper, '指派').trigger('click');
    await flushPromises();

    expect(phase7Mocks.conflictCheck).toHaveBeenCalledWith(12, expect.objectContaining({
      task_id: 77,
      assignee_user_id: 2,
    }));
    expect(phase7Mocks.confirm).toHaveBeenCalledWith(expect.objectContaining({
      title: '指派給 候選成員 前偵測到衝突，仍要指派？',
    }));
    expect(phase7Mocks.addMember).not.toHaveBeenCalled();
  });

  it('成員無衝突時可指派，並可確認移除與設為主責人', async () => {
    const collaborator: TaskMember = {
      user_id: 3,
      name: '協作者甲',
      email: 'member@example.com',
      role: 1,
    };
    const candidate: TaskMember = {
      user_id: 4,
      name: '候選成員乙',
      email: 'candidate2@example.com',
      role: 1,
    };
    phase7Mocks.conflictCheck.mockResolvedValue(noConflictResponse);
    phase7Mocks.confirm.mockResolvedValue(true);
    phase7Mocks.getMembers
      .mockResolvedValueOnce({ data: [collaborator] })
      .mockResolvedValueOnce({ data: [collaborator, candidate] })
      .mockResolvedValue({ data: [collaborator] });

    const { wrapper, spies } = mountView([makeTask()]);
    await flushPromises();
    await findButton(wrapper, '成員').trigger('click');
    await flushPromises();

    await findButton(wrapper, '指派').trigger('click');
    await flushPromises();
    expect(phase7Mocks.addMember).toHaveBeenCalledWith(77, 4);
    expect(spies.fetch).toHaveBeenCalledTimes(2);
    expect(phase7Mocks.toastSuccess).toHaveBeenCalledWith('已指派 候選成員乙');

    await wrapper.get('button[title="移除成員"]').trigger('click');
    await flushPromises();
    expect(phase7Mocks.removeMember).toHaveBeenCalledWith(77, 3);

    await wrapper.get('button[title="設為主責人"]').trigger('click');
    await flushPromises();
    expect(phase7Mocks.updateMemberRole).toHaveBeenCalledWith(77, 3, 0);
    expect(phase7Mocks.toastSuccess).toHaveBeenCalledWith('已將 協作者甲 設為主責人');
  });

  it('Email 搜尋會處理找不到使用者與已是成員的情況', async () => {
    const currentMember: TaskMember = {
      user_id: 5,
      name: '現有成員',
      email: 'existing@example.com',
      role: 1,
    };
    phase7Mocks.getMembers
      .mockResolvedValueOnce({ data: [currentMember] })
      .mockResolvedValueOnce({ data: [currentMember] });
    phase7Mocks.searchUser
      .mockRejectedValueOnce(new Error('not found'))
      .mockResolvedValueOnce({ data: { id: 5, name: '現有成員' } });

    const { wrapper } = mountView([makeTask()]);
    await flushPromises();
    await findButton(wrapper, '成員').trigger('click');
    await flushPromises();

    const emailInput = wrapper.get('input[placeholder="輸入 Email 搜尋使用者"]');
    await emailInput.setValue('missing@example.com');
    await findButton(wrapper, '搜尋').trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('找不到使用者');

    await emailInput.setValue('existing@example.com');
    await findButton(wrapper, '搜尋').trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('此使用者已是成員');
    expect(wrapper.findAll('button').some((button) => button.text().trim() === '邀請')).toBe(false);
  });

  it('Email 搜尋成功後可邀請協作者，邀請失敗則保留搜尋結果與錯誤訊息', async () => {
    phase7Mocks.conflictCheck.mockResolvedValue(noConflictResponse);
    phase7Mocks.getMembers.mockResolvedValue({ data: [] });
    phase7Mocks.searchUser.mockResolvedValue({ data: { id: 8, name: '新協作者' } });

    const { wrapper, spies } = mountView([makeTask()]);
    await flushPromises();
    await findButton(wrapper, '成員').trigger('click');
    await flushPromises();

    const emailInput = wrapper.get('input[placeholder="輸入 Email 搜尋使用者"]');
    await emailInput.setValue('new@example.com');
    await findButton(wrapper, '搜尋').trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('新協作者');

    phase7Mocks.addMember.mockRejectedValueOnce(new Error('invite failed'));
    await findButton(wrapper, '邀請').trigger('click');
    await flushPromises();
    expect(wrapper.text()).toContain('新增失敗');
    expect(wrapper.text()).toContain('新協作者');

    phase7Mocks.addMember.mockResolvedValueOnce({ data: {} });
    await findButton(wrapper, '邀請').trigger('click');
    await flushPromises();
    expect(phase7Mocks.addMember).toHaveBeenLastCalledWith(77, 8);
    expect(phase7Mocks.toastSuccess).toHaveBeenCalledWith('已成功指派成員');
    expect(spies.fetch).toHaveBeenCalledTimes(2);
    expect(wrapper.findAll('button').some((button) => button.text().trim() === '邀請')).toBe(false);
    expect(wrapper.get('input[placeholder="輸入 Email 搜尋使用者"]').element).toHaveProperty('value', '');
  });

  it('快速指派 API 失敗時顯示錯誤且成員面板保持開啟', async () => {
    const candidate: TaskMember = {
      user_id: 10,
      name: '指派失敗成員',
      email: 'failed@example.com',
      role: 1,
    };
    phase7Mocks.conflictCheck.mockResolvedValue(noConflictResponse);
    phase7Mocks.getMembers
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [candidate] });
    phase7Mocks.addMember.mockRejectedValueOnce(new Error('assign failed'));

    const { wrapper } = mountView([makeTask()]);
    await flushPromises();
    await findButton(wrapper, '成員').trigger('click');
    await flushPromises();
    await findButton(wrapper, '指派').trigger('click');
    await flushPromises();

    expect(phase7Mocks.toastError).toHaveBeenCalledWith('指派失敗');
    expect(wrapper.text()).toContain('成員管理 — 既有任務');
    expect(wrapper.text()).toContain('指派失敗成員');
  });
});
