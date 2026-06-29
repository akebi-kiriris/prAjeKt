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
  listKnowledgeDocuments: vi.fn(),
  listKnowledgeDocumentEvents: vi.fn(),
  uploadKnowledgeDocument: vi.fn(),
  batchDeleteKnowledgeDocuments: vi.fn(),
  batchReindexKnowledgeDocuments: vi.fn(),
  downloadKnowledgeDocumentFile: vi.fn(),
  previewKnowledgeDocumentFile: vi.fn(),
  generateTasks: vi.fn(),
  batchCreateTasks: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
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

vi.mock('../../../services/knowledgeService', () => ({
  knowledgeService: {
    listDocuments: phase7Mocks.listKnowledgeDocuments,
    listDocumentEvents: phase7Mocks.listKnowledgeDocumentEvents,
    uploadDocument: phase7Mocks.uploadKnowledgeDocument,
    batchDeleteDocuments: phase7Mocks.batchDeleteKnowledgeDocuments,
    batchReindexDocuments: phase7Mocks.batchReindexKnowledgeDocuments,
    downloadDocumentFile: phase7Mocks.downloadKnowledgeDocumentFile,
    previewDocumentFile: phase7Mocks.previewKnowledgeDocumentFile,
  },
}));

vi.mock('../../../services/taskService', () => ({
  taskService: {
    create: phase7Mocks.createTask,
    update: phase7Mocks.updateTask,
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

const ownerMember = {
  user_id: 1,
  name: 'Owner',
  username: 'owner',
  email: 'owner@example.com',
  role: 0 as const,
};

const helperMember = {
  user_id: 2,
  name: 'Helper',
  username: 'helper',
  email: 'helper@example.com',
  role: 1 as const,
};

const baseTask = {
  task_id: 1001,
  name: '完成 API 合約',
  completed: false,
  completed_at: null,
  timeline_id: 99,
  priority: 2 as const,
  status: 'in_progress' as const,
  tags: [],
  estimated_hours: null,
  actual_hours: null,
  members: [],
  subtasks: [],
  created_at: '2026-04-10T00:00:00Z',
  start_date: '2026-04-14',
  end_date: '2026-04-16',
  updated_at: '2026-04-15T00:00:00Z',
  task_remark: '任務備註',
  isWork: 1,
  depends_on_task_ids: [],
  can_manage_members: true,
  is_owner: true,
};

const dependencyTask = {
  ...baseTask,
  task_id: 1002,
  name: '部署驗證',
  priority: 1 as const,
  status: 'pending' as const,
  task_remark: null,
  depends_on_task_ids: [],
};

const mountDialogWithTasks = async () => {
  const wrapper = mount(TimelineDetailDialog, {
    props: {
      selectedTimeline: baseTimeline,
      timelineTasks: [baseTask, dependencyTask],
      apiBaseUrl: 'http://localhost:5000/api',
    },
  });

  await flushPromises();
  const taskName = wrapper.findAll('span').find((node) => node.text() === baseTask.name);
  expect(taskName).toBeTruthy();
  if (!taskName) {
    throw new Error('找不到任務名稱');
  }
  await taskName.trigger('click');
  await flushPromises();

  return wrapper;
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
    phase7Mocks.updateTask.mockResolvedValue({ data: { message: 'updated' } });
    phase7Mocks.getMembers.mockResolvedValue({ data: [ownerMember, helperMember] });
    phase7Mocks.loadTaskDetailResourcesWithMembers.mockResolvedValue({
      comments: [
        {
          comment_id: 501,
          task_id: 1001,
          user_id: 1,
          user_name: 'Owner',
          task_message: '需要補 API 文件',
          created_at: '2026-04-15T12:00:00Z',
        },
      ],
      files: [
        {
          id: 701,
          filename: 'spec.pdf',
          original_filename: '規格書.pdf',
          file_size: 2048,
          uploaded_at: '2026-04-15T12:30:00Z',
        },
      ],
      subtasks: [
        {
          id: 301,
          task_id: 1001,
          name: '整理 API 合約',
          completed: false,
          sort_order: 1,
          created_at: '2026-04-15T10:00:00Z',
        },
      ],
      members: [ownerMember],
    });
    phase7Mocks.createSubtask.mockResolvedValue({ data: { message: 'created' } });
    phase7Mocks.getSubtasks.mockResolvedValue({
      data: [
        {
          id: 301,
          task_id: 1001,
          name: '整理 API 合約',
          completed: true,
          sort_order: 1,
          created_at: '2026-04-15T10:00:00Z',
        },
        {
          id: 302,
          task_id: 1001,
          name: '補充錯誤碼',
          completed: false,
          sort_order: 2,
          created_at: '2026-04-15T11:00:00Z',
        },
      ],
    });
    phase7Mocks.toggleSubtask.mockResolvedValue({ data: { message: 'toggled' } });
    phase7Mocks.deleteSubtask.mockResolvedValue({ data: { message: 'deleted' } });
    phase7Mocks.addComment.mockResolvedValue({ data: { message: 'added' } });
    phase7Mocks.getComments.mockResolvedValue({
      data: [
        {
          comment_id: 502,
          task_id: 1001,
          user_id: 2,
          user_name: 'Helper',
          task_message: '我來補測試',
          created_at: '2026-04-16T12:00:00Z',
        },
      ],
    });
    phase7Mocks.deleteComment.mockResolvedValue({ data: { message: 'deleted' } });
    phase7Mocks.summarizeComments.mockResolvedValue({
      data: {
        summary: {
          decisions: ['先補 API 文件'],
          risks: ['測試不足'],
          next_actions: ['補上回歸測試'],
        },
        meta: {
          comment_count: 2,
          total_comments: 5,
          used_comments: 2,
          truncated: true,
        },
        message: '摘要使用最近留言',
      },
    });
    phase7Mocks.uploadFile.mockResolvedValue({ data: { message: 'uploaded' } });
    phase7Mocks.getFiles.mockResolvedValue({
      data: [
        {
          id: 702,
          filename: 'updated.pdf',
          original_filename: '更新規格.pdf',
          file_size: 4096,
          uploaded_at: '2026-04-16T12:30:00Z',
        },
      ],
    });
    phase7Mocks.deleteFile.mockResolvedValue({ data: { message: 'deleted' } });
    phase7Mocks.listKnowledgeDocuments.mockResolvedValue({
      data: { message: 'ok', documents: [], meta: { limit: 50, offset: 0, count: 0 } },
    });
    phase7Mocks.listKnowledgeDocumentEvents.mockResolvedValue({
      data: { message: 'ok', events: [], meta: { limit: 10, offset: 0, count: 0 } },
    });
    phase7Mocks.uploadKnowledgeDocument.mockResolvedValue({ data: { message: 'uploaded' } });
    phase7Mocks.batchDeleteKnowledgeDocuments.mockResolvedValue({ data: { message: 'deleted', results: [] } });
    phase7Mocks.batchReindexKnowledgeDocuments.mockResolvedValue({ data: { message: 'reindexed', results: [] } });
    phase7Mocks.downloadKnowledgeDocumentFile.mockResolvedValue({ data: new Blob(['download']) });
    phase7Mocks.previewKnowledgeDocumentFile.mockResolvedValue({ data: new Blob(['preview']) });
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

  it('批次建立任務時若有未帶入前置依賴，會以 toast 顯示受影響任務名稱', async () => {
    phase7Mocks.executeMcp.mockResolvedValue({
      data: {
        result: {
          tasks: [
            { name: '任務1', priority: 2, estimated_days: 1, depends_on_task_refs: [] },
            { name: '任務2', priority: 2, estimated_days: 1, depends_on_task_refs: ['任務1'] },
            { name: '任務4', priority: 2, estimated_days: 1, depends_on_task_refs: ['任務3'] },
          ],
        },
      },
    });
    phase7Mocks.batchCreateTasks.mockResolvedValue({
      data: {
        message: '新增成功',
        kept: 0,
        deleted: 0,
        created: 3,
        ignored_dependency_refs: 1,
        ignored_dependency_ids: 0,
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

    const openAiModalButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('AI 生成任務'));

    expect(openAiModalButton).toBeTruthy();
    if (!openAiModalButton) {
      throw new Error('找不到 AI 生成任務按鈕');
    }
    await openAiModalButton.trigger('click');
    await flushPromises();

    const generateButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('AI 智慧生成'));

    expect(generateButton).toBeTruthy();
    if (!generateButton) {
      throw new Error('找不到 AI 智慧生成按鈕');
    }
    await generateButton.trigger('click');
    await flushPromises();

    const selectAllButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('全部選取'));

    expect(selectAllButton).toBeTruthy();
    if (!selectAllButton) {
      throw new Error('找不到全部選取按鈕');
    }
    await selectAllButton.trigger('click');
    await flushPromises();

    const batchCreateButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('新增選取任務'));

    expect(batchCreateButton).toBeTruthy();
    if (!batchCreateButton) {
      throw new Error('找不到新增選取任務按鈕');
    }
    await batchCreateButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.batchCreateTasks).toHaveBeenCalledTimes(1);
    expect(phase7Mocks.toastInfo).toHaveBeenCalled();
    expect(phase7Mocks.toastInfo).toHaveBeenCalledWith(expect.stringContaining('任務4'));
  });

  it('開啟任務詳情時載入留言、附件、子任務、成員與依賴選項', async () => {
    const wrapper = await mountDialogWithTasks();

    expect(phase7Mocks.loadTaskDetailResourcesWithMembers).toHaveBeenCalledWith(1001);
    expect(phase7Mocks.getMembers).toHaveBeenCalledWith(99);
    expect(wrapper.text()).toContain('完成 API 合約');
    expect(wrapper.text()).toContain('任務備註');
    expect(wrapper.text()).toContain('整理 API 合約');
    expect(wrapper.text()).toContain('規格書.pdf');
    expect(wrapper.text()).toContain('需要補 API 文件');
    expect(wrapper.text()).toContain('快速指派專案成員');
    expect(wrapper.text()).toContain('部署驗證');
  });

  it('可在任務詳情新增、切換、刪除子任務並新增留言與產生摘要', async () => {
    const wrapper = await mountDialogWithTasks();

    const subtaskInput = wrapper.find('input[placeholder="輸入子任務名稱..."]');
    await subtaskInput.setValue('補充錯誤碼');
    await subtaskInput.trigger('keyup.enter');
    await flushPromises();

    expect(phase7Mocks.createSubtask).toHaveBeenCalledWith(1001, { name: '補充錯誤碼' });
    expect(phase7Mocks.getSubtasks).toHaveBeenCalledWith(1001);
    expect(wrapper.text()).toContain('補充錯誤碼');

    const subtaskCheckbox = wrapper.findAll('input[type="checkbox"]').find((input) => {
      const row = input.element.closest('.group');
      return row?.textContent?.includes('整理 API 合約');
    });
    expect(subtaskCheckbox).toBeTruthy();
    if (!subtaskCheckbox) throw new Error('找不到子任務 checkbox');
    await subtaskCheckbox.trigger('change');
    await flushPromises();

    expect(phase7Mocks.toggleSubtask).toHaveBeenCalledWith(1001, 301);

    const subtaskRow = wrapper.findAll('.group').find((row) => row.text().includes('整理 API 合約'));
    const deleteSubtaskButton = subtaskRow?.findAll('button').find((button) => button.text().includes('🗑️'));
    expect(deleteSubtaskButton).toBeTruthy();
    if (!deleteSubtaskButton) throw new Error('找不到刪除子任務按鈕');
    await deleteSubtaskButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.confirm).toHaveBeenCalledWith({ title: '確定要刪除此子任務？', danger: true });
    expect(phase7Mocks.deleteSubtask).toHaveBeenCalledWith(1001, 301);

    const commentInput = wrapper.find('input[placeholder="新增留言..."]');
    await commentInput.setValue('我來補測試');
    await commentInput.trigger('keyup.enter');
    await flushPromises();

    expect(phase7Mocks.addComment).toHaveBeenCalledWith(1001, '我來補測試');
    expect(phase7Mocks.getComments).toHaveBeenCalledWith(1001);
    expect(wrapper.text()).toContain('我來補測試');

    const summarizeButton = wrapper.findAll('button').find((button) => button.text().includes('AI 摘要'));
    expect(summarizeButton).toBeTruthy();
    if (!summarizeButton) throw new Error('找不到 AI 摘要按鈕');
    await summarizeButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.summarizeComments).toHaveBeenCalledWith(1001);
    expect(phase7Mocks.toastInfo).toHaveBeenCalledWith('摘要使用最近留言');
    expect(wrapper.text()).toContain('先補 API 文件');
    expect(wrapper.text()).toContain('已自動截斷較舊留言');
  });

  it('可儲存前置依賴並觸發 refresh-all', async () => {
    const wrapper = await mountDialogWithTasks();

    const dependencySelect = wrapper.find('select[multiple]');
    await dependencySelect.setValue(['1002']);
    await flushPromises();

    const saveButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('儲存前置依賴'));
    expect(saveButton).toBeTruthy();
    if (!saveButton) throw new Error('找不到儲存前置依賴按鈕');
    await saveButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.updateTask).toHaveBeenCalledWith(1001, {
      depends_on_task_ids: [1002],
    });
    expect(phase7Mocks.toastSuccess).toHaveBeenCalledWith('前置依賴已更新');
    expect(wrapper.emitted('refresh-all')).toHaveLength(1);
  });

  it('可處理附件下載、上傳、過大檔案警告與刪除', async () => {
    const wrapper = await mountDialogWithTasks();

    const downloadButton = wrapper.find('button[title="下載"]');
    expect(downloadButton.exists()).toBe(true);
    await downloadButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.downloadFileFromUrl).toHaveBeenCalledWith(
      'http://localhost:5000/api/tasks/files/spec.pdf',
      '規格書.pdf',
    );

    const fileInput = wrapper.findAll('input[type="file"]').at(-1);
    expect(fileInput).toBeTruthy();
    if (!fileInput) throw new Error('找不到任務附件上傳 input');
    const normalFile = new File(['hello'], 'upload.pdf', { type: 'application/pdf' });
    const uploadEvent = new Event('change', { bubbles: true });
    Object.defineProperty(uploadEvent, 'target', {
      value: { files: [normalFile] },
      configurable: true,
    });
    fileInput.element.dispatchEvent(uploadEvent);
    await flushPromises();

    expect(phase7Mocks.uploadFile).toHaveBeenCalledWith(1001, expect.any(FormData));
    expect(phase7Mocks.getFiles).toHaveBeenCalledWith(1001);
    expect(wrapper.text()).toContain('更新規格.pdf');

    const hugeFile = new File([new Uint8Array(10 * 1024 * 1024 + 1)], 'huge.pdf');
    const hugeFileEvent = new Event('change', { bubbles: true });
    Object.defineProperty(hugeFileEvent, 'target', {
      value: { files: [hugeFile] },
      configurable: true,
    });
    fileInput.element.dispatchEvent(hugeFileEvent);
    await flushPromises();

    expect(phase7Mocks.toastWarning).toHaveBeenCalledWith('檔案大小不可超過 10MB');

    const deleteFileButton = wrapper.find('button[title="刪除"]');
    expect(deleteFileButton.exists()).toBe(true);
    await deleteFileButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.confirm).toHaveBeenCalledWith({ title: '確定要刪除此附件？', danger: true });
    expect(phase7Mocks.deleteFile).toHaveBeenCalledWith(1001, 702);
  });

  it('可更新專案備註，失敗時保留編輯內容並顯示錯誤', async () => {
    phase7Mocks.updateRemark.mockResolvedValueOnce({ data: { message: 'updated' } });
    const wrapper = mount(TimelineDetailDialog, {
      props: {
        selectedTimeline: baseTimeline,
        timelineTasks: [],
        apiBaseUrl: 'http://localhost:5000/api',
      },
    });
    await flushPromises();

    const editButton = wrapper.findAll('button').find((button) => button.text().trim() === '✏️');
    expect(editButton).toBeTruthy();
    if (!editButton) throw new Error('找不到編輯備註按鈕');
    await editButton.trigger('click');

    const textarea = wrapper.get('textarea[placeholder="新增備註..."]');
    await textarea.setValue('更新後的專案備註');
    const saveButton = wrapper.findAll('button').find((button) => button.text().trim() === '儲存');
    expect(saveButton).toBeTruthy();
    if (!saveButton) throw new Error('找不到儲存備註按鈕');
    await saveButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.updateRemark).toHaveBeenCalledWith(99, '更新後的專案備註');
    expect(wrapper.text()).toContain('更新後的專案備註');
    expect(wrapper.emitted('refresh-all')).toHaveLength(1);

    phase7Mocks.updateRemark.mockRejectedValueOnce(new Error('failed'));
    const editAgainButton = wrapper.findAll('button').find((button) => button.text().trim() === '✏️');
    expect(editAgainButton).toBeTruthy();
    if (!editAgainButton) throw new Error('找不到再次編輯備註按鈕');
    await editAgainButton.trigger('click');
    await wrapper.get('textarea[placeholder="新增備註..."]').setValue('尚未儲存的備註');
    const saveAgainButton = wrapper.findAll('button').find((button) => button.text().trim() === '儲存');
    expect(saveAgainButton).toBeTruthy();
    if (!saveAgainButton) throw new Error('找不到再次儲存備註按鈕');
    await saveAgainButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.toastError).toHaveBeenCalledWith('更新備註失敗');
    expect((wrapper.get('textarea[placeholder="新增備註..."]').element as HTMLTextAreaElement).value)
      .toBe('尚未儲存的備註');
  });

  it('可產生包含循環邊緣資料的風險依賴圖並重新佈局', async () => {
    phase7Mocks.getRiskAnalysis.mockResolvedValueOnce({
      data: {
        message: '風險分析完成',
        timeline_id: 99,
        timeline_name: 'Phase7 專案',
        generated_at: '2026-06-24T00:00:00Z',
        summary: {
          total_tasks: 2,
          projected_duration_days: 4,
          critical_path_task_count: 2,
          critical_path_duration_days: 4,
          risk_item_count: 2,
          high_risk_count: 1,
          warning_count: 0,
        },
        critical_path: [],
        risk_items: [
          {
            task_id: 1001,
            name: '這是一個很長需要截斷的高風險任務名稱',
            severity: 'high',
            impact_days: 2,
            reasons: ['循環依賴'],
            suggested_actions: ['調整依賴'],
            due_date: '2026-06-25',
            depends_on_task_ids: [1002],
            float_days: 0,
            is_critical: true,
          },
          {
            task_id: 1002,
            name: '中風險任務',
            severity: 'medium',
            impact_days: 1,
            reasons: ['排程緊迫'],
            suggested_actions: ['提早處理'],
            due_date: '2026-06-26',
            depends_on_task_ids: [1001],
            float_days: 0,
            is_critical: false,
          },
        ],
        warnings: [],
        graph: {
          nodes: [
            { task_id: 1001, name: '這是一個很長需要截斷的高風險任務名稱', is_critical: true },
            { task_id: 1002, name: '中風險任務', is_critical: false },
            { task_id: 'invalid', name: '無效節點', is_critical: false },
          ],
          edges: [
            { source_task_id: 1001, target_task_id: 1002, is_critical: true },
            { source_task_id: 1002, target_task_id: 1001, is_critical: false },
            { source_task_id: 1001, target_task_id: 9999, is_critical: false },
          ],
        },
      },
    });

    const wrapper = mount(TimelineDetailDialog, {
      props: {
        selectedTimeline: baseTimeline,
        timelineTasks: [baseTask, dependencyTask],
        apiBaseUrl: 'http://localhost:5000/api',
      },
    });
    await flushPromises();

    const graphButton = wrapper.findAll('button').find((button) => button.text().includes('產生依賴圖'));
    expect(graphButton).toBeTruthy();
    if (!graphButton) throw new Error('找不到產生依賴圖按鈕');
    await graphButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.getRiskAnalysis).toHaveBeenCalledWith(99);
    expect(wrapper.find('svg[aria-label="risk dependency graph"]').exists()).toBe(true);
    expect(wrapper.findAll('line')).toHaveLength(2);
    expect(wrapper.text()).toContain('這是一個很長需要截斷的…');
    expect(wrapper.text()).toContain('中風險任務');

    const rebuildButton = wrapper.findAll('button').find((button) => button.text().includes('重新產生'));
    expect(rebuildButton).toBeTruthy();
    if (!rebuildButton) throw new Error('找不到重新產生依賴圖按鈕');
    await rebuildButton.trigger('click');
    await flushPromises();

    expect(wrapper.find('svg[aria-label="risk dependency graph"]').exists()).toBe(true);
  });

  it('未填截止日期時不送出 AI 衝突建議請求', async () => {
    const wrapper = mount(TimelineDetailDialog, {
      props: {
        selectedTimeline: baseTimeline,
        timelineTasks: [],
        apiBaseUrl: 'http://localhost:5000/api',
      },
    });
    await flushPromises();

    const addTaskButton = wrapper.findAll('button').find((button) => button.text().includes('新增任務'));
    expect(addTaskButton).toBeTruthy();
    if (!addTaskButton) throw new Error('找不到新增任務按鈕');
    await addTaskButton.trigger('click');
    await flushPromises();

    const addTaskModal = wrapper.findComponent({ name: 'TimelineAddTaskModal' });
    expect(addTaskModal.exists()).toBe(true);
    addTaskModal.vm.$emit('request-ai-suggestion', null);
    await flushPromises();

    expect(phase7Mocks.toastWarning).toHaveBeenCalledWith('請先填寫截止日期再產生 AI 衝突建議');
    expect(phase7Mocks.conflictCheck).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('新增任務');
  });

  it('AI 衝突建議失敗時保留衝突預覽並解除 loading', async () => {
    phase7Mocks.confirm.mockResolvedValueOnce(false);
    phase7Mocks.conflictCheck
      .mockResolvedValueOnce({
        data: {
          message: '偵測到衝突',
          timeline_id: 99,
          task_name: '新任務',
          has_conflict: true,
          conflict_count: 1,
          assignee_user_id: null,
          assignee_conflict_count: 1,
          project_conflict_count: 1,
          cross_project_conflict_count: 0,
          workload_overload_count: 0,
          workload_overload_days: [],
          conflicts: [
            {
              task_id: 2001,
              name: '既有任務',
              status: 'in_progress',
              start_date: '2026-06-24',
              end_date: '2026-06-26',
              owner_name: 'Owner',
              same_assignee: true,
              reason: '日期重疊',
            },
          ],
          suggestion: null,
          ai_suggestion: null,
        },
      })
      .mockRejectedValueOnce(new Error('ai suggestion failed'));

    const wrapper = mount(TimelineDetailDialog, {
      props: {
        selectedTimeline: baseTimeline,
        timelineTasks: [],
        apiBaseUrl: 'http://localhost:5000/api',
      },
    });
    await flushPromises();

    const addTaskButton = wrapper.findAll('button').find((button) => button.text().includes('新增任務'));
    expect(addTaskButton).toBeTruthy();
    if (!addTaskButton) throw new Error('找不到新增任務按鈕');
    await addTaskButton.trigger('click');
    await flushPromises();

    const form = wrapper.findAll('form').find((candidate) => candidate.find('input[placeholder="輸入任務名稱"]').exists());
    expect(form).toBeTruthy();
    if (!form) throw new Error('找不到新增任務表單');
    await form.get('input[placeholder="輸入任務名稱"]').setValue('新任務');
    const dateInputs = form.findAll('input[type="date"]');
    await dateInputs[1].setValue('2026-06-25');
    await form.trigger('submit.prevent');
    await flushPromises();

    expect(wrapper.text()).toContain('既有任務');
    const suggestionButton = wrapper.findAll('button').find((button) => button.text().includes('產生 AI 衝突建議'));
    expect(suggestionButton).toBeTruthy();
    if (!suggestionButton) throw new Error('找不到 AI 衝突建議按鈕');
    await suggestionButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.toastError).toHaveBeenCalledWith('取得 AI 衝突建議失敗');
    expect(wrapper.text()).toContain('既有任務');
    expect(suggestionButton.text()).toContain('產生 AI 衝突建議');
    expect(suggestionButton.attributes('disabled')).toBeUndefined();
  });

  it('沒有成員管理權限時不顯示指派入口也不載入成員', async () => {
    const wrapper = mount(TimelineDetailDialog, {
      props: {
        selectedTimeline: { ...baseTimeline, role: 1 as const },
        timelineTasks: [{ ...baseTask, can_manage_members: false, is_owner: false }],
        apiBaseUrl: 'http://localhost:5000/api',
      },
    });
    await flushPromises();

    expect(wrapper.find('button[title="指派成員"]').exists()).toBe(false);
    expect(phase7Mocks.getTaskMembers).not.toHaveBeenCalled();
    expect(phase7Mocks.addTaskMember).not.toHaveBeenCalled();
  });

  it('指派成員的衝突檢查失敗時不新增成員且面板保持開啟', async () => {
    phase7Mocks.getTaskMembers.mockResolvedValueOnce({ data: [ownerMember] });
    phase7Mocks.conflictCheck.mockRejectedValueOnce(new Error('conflict api failed'));
    const wrapper = mount(TimelineDetailDialog, {
      props: {
        selectedTimeline: baseTimeline,
        timelineTasks: [baseTask],
        apiBaseUrl: 'http://localhost:5000/api',
      },
    });
    await flushPromises();

    await wrapper.get('button[title="指派成員"]').trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('任務成員 — 完成 API 合約');
    const assignButton = wrapper.findAll('button').find((button) => button.text().trim() === '指派');
    expect(assignButton).toBeTruthy();
    if (!assignButton) throw new Error('找不到快速指派按鈕');
    await assignButton.trigger('click');
    await flushPromises();

    expect(phase7Mocks.conflictCheck).toHaveBeenCalled();
    expect(phase7Mocks.toastError).toHaveBeenCalledWith('檢查衝突失敗');
    expect(phase7Mocks.addTaskMember).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('任務成員 — 完成 API 合約');
  });
});
