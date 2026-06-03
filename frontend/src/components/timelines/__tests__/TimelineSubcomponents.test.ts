import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';

vi.mock('@fullcalendar/vue3', () => ({
  default: defineComponent({
    name: 'FullCalendarStub',
    template: '<div data-testid="full-calendar-stub" />',
  }),
}));

import TimelineKanbanBoard from '../TimelineKanbanBoard.vue';
import TimelineCalendarView from '../TimelineCalendarView.vue';
import TimelineCardView from '../TimelineCardView.vue';
import TimelineHeader from '../TimelineHeader.vue';
import TimelineKanbanTaskModal from '../TimelineKanbanTaskModal.vue';
import TimelineListView from '../TimelineListView.vue';
import TaskDetailPanel from '../TaskDetailPanel.vue';
import AiTaskGeneratePanel from '../AiTaskGeneratePanel.vue';
import ProjectKnowledgePanel from '../ProjectKnowledgePanel.vue';
import type { Task, Timeline } from '../../../types';

const baseTimeline: Timeline = {
  id: 1,
  name: 'Alpha',
  startDate: '2026-05-01',
  endDate: '2026-05-20',
  remark: null,
  role: 0,
  totalTasks: 4,
  completedTasks: 2,
};

describe('Timeline subcomponents (phase 8.4 split)', () => {
  it('TimelineHeader emits update:viewMode and create-timeline', async () => {
    const wrapper = mount(TimelineHeader, {
      props: {
        todayFormatted: '2026-05-27',
        timelines: [baseTimeline],
        urgentCount: 1,
        totalCompletedTasks: 2,
        totalTasks: 4,
        viewMode: 'card',
      },
    });

    const buttons = wrapper.findAll('button');
    await buttons[1].trigger('click');
    await buttons[5].trigger('click');

    expect(wrapper.emitted('update:viewMode')?.[0]).toEqual(['kanban']);
    expect(wrapper.emitted('create-timeline')).toBeTruthy();
  });

  it('TimelineHeader renders stats and emits all view modes', async () => {
    const wrapper = mount(TimelineHeader, {
      props: {
        todayFormatted: '2026-06-03',
        timelines: [baseTimeline, { ...baseTimeline, id: 2, name: 'Beta' }],
        urgentCount: 3,
        totalCompletedTasks: 8,
        totalTasks: 12,
        viewMode: 'gantt',
      },
    });

    const buttons = wrapper.findAll('button');
    await buttons[0].trigger('click');
    await buttons[2].trigger('click');
    await buttons[3].trigger('click');
    await buttons[4].trigger('click');

    expect(wrapper.text()).toContain('2');
    expect(wrapper.text()).toContain('3');
    expect(wrapper.text()).toContain('8');
    expect(wrapper.text()).toContain('12');
    expect(wrapper.emitted('update:viewMode')).toEqual([['card'], ['timeline'], ['calendar'], ['gantt']]);
    expect(buttons[4].classes()).toContain('bg-primary');
  });

  it('TimelineListView emits view/edit/delete actions', async () => {
    const wrapper = mount(TimelineListView, {
      props: {
        sortedTimelines: [baseTimeline],
        timelinesCount: 1,
        getTimelineStatus: () => ({
          label: '進行中',
          bgClass: 'bg-blue-100',
          textClass: 'text-blue-700',
          badgeClass: 'bg-blue-100 text-blue-700',
        }),
        getDaysRemaining: () => ({ text: '3 天' }),
        getProgressBarColor: () => 'bg-green-500',
        getTaskProgress: () => 50,
      },
    });

    await wrapper.find('.cursor-pointer').trigger('click');
    const actionButtons = wrapper.findAll('.shrink-0 button');
    await actionButtons[0].trigger('click');
    await actionButtons[1].trigger('click');

    expect(wrapper.emitted('view-timeline')?.length).toBe(1);
    expect(wrapper.emitted('edit-timeline')?.[0][0]).toMatchObject({ id: 1 });
    expect(wrapper.emitted('delete-timeline')?.[0]).toEqual([1]);
  });

  it('TimelineCardView emits view/edit/delete and create actions', async () => {
    const wrapper = mount(TimelineCardView, {
      props: {
        sortedTimelines: [baseTimeline],
        timelinesCount: 1,
        getTimelineStatus: () => ({
          label: '進行中',
          icon: '📋',
          badgeClass: 'badge',
          borderClass: 'border-blue-200',
          barClass: 'bar-blue',
        }),
        getDaysRemaining: () => ({ display: '剩 3 天', colorClass: 'text-orange-500' }),
        getTimeProgress: () => 50,
        getProgressTextColor: () => 'text-blue-600',
        getProgressBarColor: () => 'bg-blue-500',
        getTaskProgress: () => 50,
      },
    });

    await wrapper.find('.group').trigger('click');
    const actionButtons = wrapper.findAll('.group-hover\\:opacity-100 button');
    await actionButtons[0].trigger('click');
    await actionButtons[1].trigger('click');

    expect(wrapper.text()).toContain('時程進度 50%');
    expect(wrapper.text()).toContain('查看詳情');
    expect(wrapper.emitted('view-timeline')?.[0][0]).toMatchObject({ id: 1 });
    expect(wrapper.emitted('edit-timeline')?.[0][0]).toMatchObject({ id: 1 });
    expect(wrapper.emitted('delete-timeline')?.[0]).toEqual([1]);
  });

  it('TimelineCardView hides owner actions for collaborator and supports empty state CTA', async () => {
    const collaboratorTimeline: Timeline = { ...baseTimeline, id: 2, role: 1, name: 'Gamma', startDate: null, endDate: null };
    const wrapper = mount(TimelineCardView, {
      props: {
        sortedTimelines: [collaboratorTimeline],
        timelinesCount: 1,
        getTimelineStatus: () => ({
          label: '進行中',
          icon: '📋',
          badgeClass: 'badge',
          borderClass: 'border-slate-200',
          barClass: 'bar-slate',
        }),
        getDaysRemaining: () => ({ display: '未設定', colorClass: 'text-slate-500' }),
        getTimeProgress: () => 0,
        getProgressTextColor: () => 'text-slate-600',
        getProgressBarColor: () => 'bg-slate-400',
        getTaskProgress: () => 0,
      },
    });

    expect(wrapper.findAll('.group-hover\\:opacity-100 button')).toHaveLength(0);

    const emptyWrapper = mount(TimelineCardView, {
      props: {
        sortedTimelines: [],
        timelinesCount: 0,
        getTimelineStatus: () => ({
          label: '進行中',
          icon: '📋',
          badgeClass: 'badge',
          borderClass: 'border-slate-200',
          barClass: 'bar-slate',
        }),
        getDaysRemaining: () => ({ display: '未設定', colorClass: 'text-slate-500' }),
        getTimeProgress: () => 0,
        getProgressTextColor: () => 'text-slate-600',
        getProgressBarColor: () => 'bg-slate-400',
        getTaskProgress: () => 0,
      },
    });

    await emptyWrapper.find('button').trigger('click');
    expect(emptyWrapper.text()).toContain('目前尚無專案');
    expect(emptyWrapper.emitted('create-timeline')).toBeTruthy();
  });

  it('TimelineCalendarView emits view-timeline from summary lists and shows empty states', async () => {
    const wrapper = mount(TimelineCalendarView, {
      props: {
        calendarOptions: { initialView: 'dayGridMonth' },
        thisWeekTimelines: [baseTimeline],
        overdueTimelines: [{ ...baseTimeline, id: 2, name: 'Overdue' }],
        completedTimelines: [{ ...baseTimeline, id: 3, name: 'Done' }],
        getDaysRemaining: () => ({ text: '剩 3 天' }),
      },
      global: {
        stubs: {
          FullCalendar: {
            template: '<div data-testid="full-calendar-stub" />',
          },
        },
      },
    });

    const clickableCards = wrapper.findAll('.cursor-pointer');
    await clickableCards[0].trigger('click');
    await clickableCards[1].trigger('click');
    await clickableCards[2].trigger('click');

    expect(wrapper.find('[data-testid="full-calendar-stub"]').exists()).toBe(true);
    const emittedTimelines = (wrapper.emitted('view-timeline') ?? []).map(
      (entry) => (entry[0] as Timeline).id,
    );
    expect(emittedTimelines).toEqual([1, 2, 3]);

    const emptyWrapper = mount(TimelineCalendarView, {
      props: {
        calendarOptions: { initialView: 'dayGridMonth' },
        thisWeekTimelines: [],
        overdueTimelines: [],
        completedTimelines: [],
        getDaysRemaining: () => ({ text: '剩 0 天' }),
      },
      global: {
        stubs: {
          FullCalendar: {
            template: '<div data-testid="full-calendar-stub" />',
          },
        },
      },
    });

    expect(emptyWrapper.text()).toContain('無專案');
    expect(emptyWrapper.text()).toContain('無過期專案');
    expect(emptyWrapper.text()).toContain('尚無完成專案');
  });

  it('TaskDetailPanel emits dependency, member, file and comment actions', async () => {
    const selectedTask: Task = {
      task_id: 77,
      name: 'Task Detail',
      completed: false,
      completed_at: null,
      timeline_id: 1,
      status: 'in_progress',
      priority: 2,
      tags: 'api',
      estimated_hours: null,
      actual_hours: null,
      members: [],
      start_date: '2026-06-01',
      end_date: '2026-06-03',
      created_at: null,
      updated_at: null,
      task_remark: 'remark',
      isWork: 1,
      is_owner: true,
      subtasks: [],
    };

    const wrapper = mount(TaskDetailPanel, {
      props: {
        selectedTask,
        selectedTaskDependencyIds: [11],
        selectedTaskDependencyOptions: [
          { task_id: 11, name: 'Setup DB' },
          { task_id: 12, name: 'Build API' },
        ],
        isSavingTaskDependencies: false,
        getTaskNameById: (id: number) => ({ 11: 'Setup DB', 12: 'Build API' }[id] || `Task ${id}`),
        canManageTaskMembers: () => true,
        taskMembersForAssign: [
          { user_id: 1, name: 'Owner', username: 'owner', role: 0 },
          { user_id: 2, name: 'Pair', username: 'pair', role: 1 },
        ] as any,
        timelineMembers: [
          { user_id: 1, name: 'Owner', username: 'owner', role: 0 },
          { user_id: 2, name: 'Pair', username: 'pair', role: 1 },
          { user_id: 3, name: 'Newbie', username: 'newbie', role: 1 },
        ] as any,
        taskSubtasks: [
          { id: 9, task_id: 77, name: 'child', completed: false, sort_order: 1, created_at: null },
        ],
        subtaskProgress: 25,
        newSubtaskName: '',
        taskFiles: [
          {
            id: 5,
            filename: 'a.png',
            original_filename: 'design.png',
            file_size: 1024,
            uploaded_at: '2026-06-03T00:00:00Z',
          },
        ] as any,
        apiBaseUrl: 'http://localhost:5000/api',
        taskComments: [
          {
            comment_id: 100,
            user_name: 'Alice',
            created_at: '2026-06-03T01:00:00Z',
            task_message: 'Need review',
          },
        ] as any,
        isSummarizingComments: false,
        commentSummary: {
          decisions: ['Keep API stable'],
          risks: ['Schedule slip'],
          next_actions: ['Ship tests'],
        },
        commentSummaryMeta: {
          total_comments: 10,
          used_comments: 5,
          truncated: true,
        },
        newComment: 'hello',
      },
    });

    const dependencySelect = wrapper.find('select[multiple]');
    const dependencyElement = dependencySelect.element as HTMLSelectElement;
    Array.from(dependencyElement.options).forEach((option) => {
      option.selected = option.value === '11' || option.value === '12';
    });
    await dependencySelect.trigger('change');

    const allButtons = wrapper.findAll('button');
    const saveDependenciesButton = allButtons.find((button) => button.text().includes('儲存前置依賴'));
    const setOwnerButton = allButtons.find((button) => button.text().includes('主責'));
    const quickAssignButton = allButtons.find((button) => button.text().includes('newbie'));
    const summarizeButton = allButtons.find((button) => button.text().includes('AI 摘要'));
    const sendButton = allButtons.find((button) => button.text().includes('傳送'));

    expect(saveDependenciesButton).toBeTruthy();
    expect(setOwnerButton).toBeTruthy();
    expect(quickAssignButton).toBeTruthy();
    expect(summarizeButton).toBeTruthy();
    expect(sendButton).toBeTruthy();
    if (!saveDependenciesButton || !setOwnerButton || !quickAssignButton || !summarizeButton || !sendButton) {
      throw new Error('missing expected TaskDetailPanel action buttons');
    }

    await saveDependenciesButton.trigger('click');
    await setOwnerButton.trigger('click');
    await quickAssignButton.trigger('click');
    await wrapper.find('input[type="file"]').trigger('change');
    await wrapper.find('button[title="下載"]').trigger('click');
    await wrapper.find('button[title="刪除"]').trigger('click');
    await summarizeButton.trigger('click');
    await wrapper.find('button[title="刪除留言"]').trigger('click');
    await wrapper.find('input[placeholder="新增留言..."]').setValue('ship it');
    await sendButton.trigger('click');

    expect(wrapper.text()).toContain('Setup DB');
    expect(wrapper.text()).toContain('快速指派專案成員');
    expect(wrapper.text()).toContain('已自動截斷較舊留言');
    expect(wrapper.emitted('update:selected-task-dependency-ids')?.[0]).toEqual([[11, 12]]);
    expect(wrapper.emitted('save-dependencies')).toBeTruthy();
    expect(wrapper.emitted('set-owner')?.[0][0]).toMatchObject({ user_id: 2 });
    expect(wrapper.emitted('quick-assign')?.[0][0]).toMatchObject({ user_id: 3 });
    expect(wrapper.emitted('file-upload')).toBeTruthy();
    expect(wrapper.emitted('download-file')?.[0][0]).toMatchObject({ id: 5 });
    expect(wrapper.emitted('delete-file')?.[0]).toEqual([5]);
    expect(wrapper.emitted('summarize-comments')).toBeTruthy();
    expect(wrapper.emitted('delete-comment')?.[0]).toEqual([100]);
    expect(wrapper.emitted('update:new-comment')?.at(-1)).toEqual(['ship it']);
    expect(wrapper.emitted('add-comment')).toBeTruthy();
  });

  it('TaskDetailPanel hides member tools and disables save states when needed', async () => {
    const selectedTask: Task = {
      task_id: 88,
      name: 'Read only',
      completed: false,
      completed_at: null,
      timeline_id: 1,
      status: 'pending',
      priority: 2,
      tags: null,
      estimated_hours: null,
      actual_hours: null,
      members: [],
      start_date: null,
      end_date: null,
      created_at: null,
      updated_at: null,
      task_remark: null,
      isWork: 1,
      is_owner: false,
      subtasks: [],
    };

    const wrapper = mount(TaskDetailPanel, {
      props: {
        selectedTask,
        selectedTaskDependencyIds: [],
        selectedTaskDependencyOptions: [],
        isSavingTaskDependencies: true,
        getTaskNameById: () => '',
        canManageTaskMembers: () => false,
        taskMembersForAssign: [],
        timelineMembers: [],
        taskSubtasks: [],
        subtaskProgress: 0,
        newSubtaskName: '',
        taskFiles: [],
        apiBaseUrl: 'http://localhost:5000/api',
        taskComments: [],
        isSummarizingComments: true,
        commentSummary: null,
        commentSummaryMeta: null,
        newComment: '   ',
      },
    });

    expect(wrapper.text()).toContain('尚無子任務');
    expect(wrapper.text()).toContain('尚無附件');
    expect(wrapper.text()).toContain('尚無留言');
    expect(wrapper.text()).not.toContain('指派成員');
    expect(wrapper.text()).toContain('儲存中...');
    expect(wrapper.text()).toContain('摘要中...');
    expect(wrapper.findAll('button').some((button) => button.text().includes('傳送') && button.attributes('disabled') !== undefined)).toBe(true);
  });

  it('AiTaskGeneratePanel covers generating, prompt options and generated-task actions', async () => {
    const generatingWrapper = mount(AiTaskGeneratePanel, {
      props: {
        isGeneratingAi: true,
        aiGeneratedTasks: [],
        selectedAiTasks: [],
        aiPrompt: '',
        useRagPlanning: false,
        useCopilotMcp: false,
        usePersonalKnowledge: false,
        useProjectKnowledge: false,
        autoCreateAfterGenerate: false,
        ragErrorMessage: '',
        ragSourceReferences: [],
        ragSummary: '',
      },
    });
    expect(generatingWrapper.text()).toContain('AI 正在生成任務建議');

    const emptyWrapper = mount(AiTaskGeneratePanel, {
      props: {
        isGeneratingAi: false,
        aiGeneratedTasks: [],
        selectedAiTasks: [],
        aiPrompt: '',
        useRagPlanning: true,
        useCopilotMcp: false,
        usePersonalKnowledge: true,
        useProjectKnowledge: false,
        autoCreateAfterGenerate: true,
        ragErrorMessage: 'rag failed',
        ragSourceReferences: [],
        ragSummary: '',
      },
    });

    await emptyWrapper.find('textarea').setValue('拆任務');
    const emptyChecks = emptyWrapper.findAll('input[type="checkbox"]');
    await emptyChecks[0].setValue(false);
    await emptyChecks[1].setValue(false);
    await emptyChecks[2].setValue(true);
    await emptyChecks[3].setValue(false);
    await emptyWrapper.find('button').trigger('click');

    expect(emptyWrapper.text()).toContain('rag failed');
    expect(emptyWrapper.emitted('update:ai-prompt')?.[0]).toEqual(['拆任務']);
    expect(emptyWrapper.emitted('update:use-rag-planning')?.[0]).toEqual([false]);
    expect(emptyWrapper.emitted('update:use-personal-knowledge')?.[0]).toEqual([false]);
    expect(emptyWrapper.emitted('touch-project-knowledge')).toBeTruthy();
    expect(emptyWrapper.emitted('update:use-project-knowledge')?.[0]).toEqual([true]);
    expect(emptyWrapper.emitted('update:auto-create-after-generate')?.[0]).toEqual([false]);
    expect(emptyWrapper.emitted('generate')).toBeTruthy();

    const generatedWrapper = mount(AiTaskGeneratePanel, {
      props: {
        isGeneratingAi: false,
        aiGeneratedTasks: [
          {
            name: 'Task A',
            priority: 1,
            start_date: '2026-06-01',
            end_date: '2026-06-02',
            tags: 'api',
            depends_on_task_refs: ['Task X'],
            remark: 'note',
          },
          {
            name: 'Task B',
            priority: 2,
            start_date: '2026-06-03',
            end_date: '2026-06-04',
            tags: '',
            depends_on_task_refs: [],
            remark: '',
          },
        ] as any,
        selectedAiTasks: [0],
        aiPrompt: '拆任務',
        useRagPlanning: false,
        useCopilotMcp: true,
        usePersonalKnowledge: false,
        useProjectKnowledge: false,
        autoCreateAfterGenerate: false,
        ragErrorMessage: '',
        ragSourceReferences: [
          {
            source_type: 'knowledge_chunk',
            source_id: 'k1',
            title: 'KB Ref',
            snippet: 'snippet',
            score: 0.91,
          },
        ] as any,
        ragSummary: 'summary',
      },
    });

    const generatedButtons = generatedWrapper.findAll('button');
    await generatedButtons.find((button) => button.text().includes('全部選取'))?.trigger('click');
    await generatedButtons.find((button) => button.text().includes('重新生成'))?.trigger('click');
    await generatedWrapper.findAll('.cursor-pointer')[0].trigger('click');
    await generatedButtons.find((button) => button.text().includes('取消'))?.trigger('click');
    await generatedButtons.find((button) => button.text().includes('新增選取任務'))?.trigger('click');

    expect(generatedWrapper.text()).toContain('來源依據（1）');
    expect(generatedWrapper.text()).toContain('前置：Task X');
    expect(generatedWrapper.emitted('toggle-all')).toBeTruthy();
    expect(generatedWrapper.emitted('reset-generated')).toBeTruthy();
    expect(generatedWrapper.emitted('toggle-task')?.[0]).toEqual([0]);
    expect(generatedWrapper.emitted('close')).toBeTruthy();
    expect(generatedWrapper.emitted('batch-create')).toBeTruthy();
  });

  it('ProjectKnowledgePanel emits upload, filters and document actions', async () => {
    const wrapper = mount(ProjectKnowledgePanel, {
      props: {
        documents: [
          {
            id: 31,
            filename: 'architecture.pdf',
            original_filename: '系統架構.pdf',
            status: 'ready',
            chunk_count: 12,
            error_message: '',
          },
          {
            id: 32,
            filename: 'broken.txt',
            original_filename: 'broken.txt',
            status: 'failed',
            chunk_count: null,
            error_message: '解析失敗',
          },
        ] as any,
        events: [
          {
            id: 8,
            document_id: 31,
            event_type: 'download',
            created_at: '2026-06-03T10:00:00Z',
          },
        ] as any,
        loading: false,
        uploading: false,
        selectedIds: [31],
        query: '',
        sort: 'created_desc',
        status: '',
        error: '同步中斷',
        formatDateTime: () => '2026/06/03 18:00',
      },
    });

    await wrapper.find('input[type="file"]').trigger('change');
    await wrapper.find('input[placeholder="搜尋檔名"]').setValue('架構');

    const selects = wrapper.findAll('select');
    await selects[0].setValue('name_asc');
    await selects[1].setValue('ready');

    const buttons = wrapper.findAll('button');
    await buttons.find((button) => button.text().includes('刷新'))?.trigger('click');
    await buttons.find((button) => button.text().includes('批次刪除'))?.trigger('click');
    await buttons.find((button) => button.text().includes('批次重建'))?.trigger('click');
    await buttons.find((button) => button.text().includes('套用篩選'))?.trigger('click');
    await wrapper.find('input[type="checkbox"]').trigger('change');
    await buttons.find((button) => button.text().includes('下載'))?.trigger('click');
    await buttons.find((button) => button.text().includes('預覽'))?.trigger('click');

    expect(wrapper.text()).toContain('系統架構.pdf');
    expect(wrapper.text()).toContain('12 chunks');
    expect(wrapper.text()).toContain('索引數未知');
    expect(wrapper.text()).toContain('解析失敗');
    expect(wrapper.text()).toContain('同步中斷');
    expect(wrapper.text()).toContain('download · #31 · 2026/06/03 18:00');
    expect(wrapper.emitted('upload')).toBeTruthy();
    expect(wrapper.emitted('update:query')?.[0]).toEqual(['架構']);
    expect(wrapper.emitted('update:sort')?.[0]).toEqual(['name_asc']);
    expect(wrapper.emitted('update:status')?.[0]).toEqual(['ready']);
    expect(wrapper.emitted('refresh')).toHaveLength(2);
    expect(wrapper.emitted('batch-delete')).toBeTruthy();
    expect(wrapper.emitted('batch-reindex')).toBeTruthy();
    expect(wrapper.emitted('toggle-selection')?.[0]).toEqual([31]);
    expect(wrapper.emitted('download')?.[0][0]).toMatchObject({ id: 31 });
    expect(wrapper.emitted('preview')?.[0][0]).toMatchObject({ id: 31 });
  });

  it('ProjectKnowledgePanel renders loading and empty states with disabled batch actions', async () => {
    const loadingWrapper = mount(ProjectKnowledgePanel, {
      props: {
        documents: [],
        events: [],
        loading: true,
        uploading: true,
        selectedIds: [],
        query: '',
        sort: 'created_desc',
        status: '',
        error: '',
        formatDateTime: () => '',
      },
    });

    expect(loadingWrapper.text()).toContain('上傳中...');
    expect(loadingWrapper.text()).toContain('載入中...');
    const loadingButtons = loadingWrapper.findAll('button');
    expect(loadingButtons.find((button) => button.text().includes('批次刪除'))?.attributes('disabled')).toBeDefined();
    expect(loadingButtons.find((button) => button.text().includes('批次重建'))?.attributes('disabled')).toBeDefined();

    const emptyWrapper = mount(ProjectKnowledgePanel, {
      props: {
        documents: [],
        events: [],
        loading: false,
        uploading: false,
        selectedIds: [],
        query: '',
        sort: 'created_desc',
        status: '',
        error: '',
        formatDateTime: () => '',
      },
    });

    expect(emptyWrapper.text()).toContain('目前沒有檔案');
    expect(emptyWrapper.text()).toContain('尚無紀錄');
  });

  it('TimelineKanbanTaskModal emits form events', async () => {
    const task: Task = {
      task_id: 10,
      name: 'Kanban Task',
      completed: false,
      completed_at: null,
      timeline_id: 1,
      status: 'pending',
      priority: 2,
      tags: 'api,backend',
      estimated_hours: null,
      actual_hours: null,
      members: [],
      start_date: '2026-05-10',
      end_date: '2026-05-12',
      created_at: null,
      updated_at: null,
      task_remark: 'remark',
      isWork: 1,
      is_owner: true,
      subtasks: [
        {
          id: 1,
          task_id: 10,
          name: 'child',
          completed: false,
          sort_order: 1,
          created_at: null,
        },
      ],
    };

    const wrapper = mount(TimelineKanbanTaskModal, {
      props: {
        show: true,
        task,
        newSubtaskName: '',
        getSubtaskProgress: () => 0,
        getCompletedSubtaskCount: () => 0,
      },
    });

    await wrapper.find('select').trigger('change');
    await wrapper.find('input[type="text"]').setValue('tag-a,tag-b');
    await wrapper.find('input[type="checkbox"]').trigger('change');
    await wrapper.find('button').trigger('click');

    expect(wrapper.emitted('priority-select')).toBeTruthy();
    expect(wrapper.emitted('update:tags')?.[0]).toEqual(['tag-a,tag-b']);
    expect(wrapper.emitted('toggle-subtask')).toBeTruthy();
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('TimelineKanbanTaskModal emits tag save, subtask input, add and delete events', async () => {
    const task: Task = {
      task_id: 10,
      name: 'Kanban Task',
      completed: false,
      completed_at: null,
      timeline_id: 1,
      status: 'pending',
      priority: 2,
      tags: 'api,backend',
      estimated_hours: null,
      actual_hours: null,
      members: [],
      start_date: null,
      end_date: null,
      created_at: null,
      updated_at: null,
      task_remark: null,
      isWork: 1,
      is_owner: true,
      subtasks: [
        {
          id: 1,
          task_id: 10,
          name: 'child',
          completed: false,
          sort_order: 1,
          created_at: null,
        },
      ],
    };

    const wrapper = mount(TimelineKanbanTaskModal, {
      props: {
        show: true,
        task,
        newSubtaskName: '',
        getSubtaskProgress: () => 25,
        getCompletedSubtaskCount: () => 0,
      },
    });

    const textInputs = wrapper.findAll('input[type="text"]');
    await textInputs[1].setValue('ship api');
    await textInputs[1].trigger('keyup', { key: 'Enter' });
    const buttons = wrapper.findAll('button');
    await buttons[2].trigger('click');
    await buttons[1].trigger('click');

    expect(wrapper.emitted('update:new-subtask-name')?.[0]).toEqual(['ship api']);
    expect(wrapper.emitted('add-subtask')).toBeTruthy();
    expect(wrapper.emitted('update-tags')).toBeTruthy();
    expect(wrapper.emitted('delete-subtask')?.[0][0]).toMatchObject({ id: 1 });
  });

  it('TimelineKanbanBoard emits filters, search and task open actions', async () => {
    const task: Task = {
      task_id: 10,
      name: 'Kanban Task',
      completed: false,
      completed_at: null,
      timeline_id: 1,
      status: 'pending',
      priority: 2,
      tags: 'api,backend,urgent,frontend',
      estimated_hours: null,
      actual_hours: null,
      members: [],
      start_date: '2026-05-10',
      end_date: '2026-05-12',
      created_at: null,
      updated_at: null,
      task_remark: null,
      isWork: 1,
      is_owner: true,
      subtasks: [
        {
          id: 1,
          task_id: 10,
          name: 'child',
          completed: false,
          sort_order: 1,
          created_at: null,
        },
      ],
    };

    const wrapper = mount(TimelineKanbanBoard, {
      props: {
        timelines: [baseTimeline],
        selectedKanbanTimeline: null,
        searchQuery: '',
        showFilterPanel: true,
        hasActiveFilters: true,
        activeFilterCount: 2,
        filterPriority: null,
        filterTag: '',
        pendingTasks: [task],
        inProgressTasks: [],
        completedTasks: [],
        isDragging: false,
        getPriorityBadgeClass: () => 'badge',
        getPriorityLabel: () => '中優先',
        getSubtaskProgress: () => 50,
        getCompletedSubtaskCount: () => 0,
        getTaskTimelineName: () => 'Alpha',
        formatDateFn: () => '2026/05/12',
      },
      global: {
        stubs: {
          draggable: {
            template: '<div><template v-if="list.length"><slot name="item" :element="list[0]" /></template></div>',
            props: ['list'],
          },
        },
      },
    });

    const selects = wrapper.findAll('select');
    await selects[0].setValue('1');
    await wrapper.find('input[placeholder="輸入任務名稱..."]').setValue('kanban');
    await wrapper.find('input[placeholder="輸入標籤關鍵字..."]').setValue('api');
    await selects[1].setValue('2');
    await wrapper.find('button').trigger('click');
    await wrapper.find('.kanban-card').trigger('click');

    expect(wrapper.text()).toContain('+1');
    expect(wrapper.text()).toContain('2026/05/12');
    expect(wrapper.emitted('update:selected-kanban-timeline')?.[0]).toEqual([1]);
    expect(wrapper.emitted('update:search-query')?.[0]).toEqual(['kanban']);
    expect(wrapper.emitted('update:filter-tag')?.[0]).toEqual(['api']);
    expect(wrapper.emitted('update:filter-priority')?.[0]).toEqual([2]);
    expect(wrapper.emitted('toggle-filter-panel')).toBeTruthy();
    expect(wrapper.emitted('open-task')?.[0][0]).toMatchObject({ task_id: 10 });
  });

  it('TimelineKanbanBoard handles nullable selects and empty states', async () => {
    const wrapper = mount(TimelineKanbanBoard, {
      props: {
        timelines: [baseTimeline],
        selectedKanbanTimeline: 1,
        searchQuery: '',
        showFilterPanel: true,
        hasActiveFilters: false,
        activeFilterCount: 0,
        filterPriority: 1,
        filterTag: '',
        pendingTasks: [],
        inProgressTasks: [],
        completedTasks: [],
        isDragging: false,
        getPriorityBadgeClass: () => 'badge',
        getPriorityLabel: () => '中優先',
        getSubtaskProgress: () => 0,
        getCompletedSubtaskCount: () => 0,
        getTaskTimelineName: () => '',
        formatDateFn: () => 'unknown',
      },
      global: {
        stubs: {
          draggable: {
            template: '<div />',
            props: ['list'],
          },
        },
      },
    });

    const selects = wrapper.findAll('select');
    await selects[0].setValue('null');
    await selects[1].setValue('null');
    await wrapper.find('button[class*="text-slate-500"]').trigger('click');

    expect(wrapper.text()).toContain('拖曳任務到這裡');
    expect(wrapper.text()).toContain('完成的任務會出現在這裡');
    expect(wrapper.emitted('update:selected-kanban-timeline')?.[0]).toEqual([null]);
    expect(wrapper.emitted('update:filter-priority')?.[0]).toEqual([null]);
    expect(wrapper.emitted('clear-filters')).toBeTruthy();
  });
});
