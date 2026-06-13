import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick, onMounted } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';

const mocks = vi.hoisted(() => ({
  updateStatus: vi.fn(),
  getSubtasks: vi.fn(),
  createSubtask: vi.fn(),
  toggleSubtask: vi.fn(),
  deleteSubtask: vi.fn(),
  update: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
  ganttCalls: [] as Array<{ element: HTMLElement; tasks: Array<Record<string, unknown>>; options: Record<string, any> }>,
}));

vi.mock('../../../services/taskService', () => ({
  taskService: {
    updateStatus: mocks.updateStatus,
    getSubtasks: mocks.getSubtasks,
    createSubtask: mocks.createSubtask,
    toggleSubtask: mocks.toggleSubtask,
    deleteSubtask: mocks.deleteSubtask,
    update: mocks.update,
  },
}));

vi.mock('vue-sonner', () => ({
  toast: {
    success: mocks.toastSuccess,
    error: mocks.toastError,
  },
}));

vi.mock('frappe-gantt', () => ({
  default: class MockGantt {
    constructor(element: HTMLElement, tasks: Array<Record<string, unknown>>, options: Record<string, any>) {
      mocks.ganttCalls.push({ element, tasks, options });
    }
  },
}));

vi.mock('../TimelineKanbanBoard.vue', () => ({
  default: defineComponent({
    name: 'TimelineKanbanBoardStub',
    props: {
      showFilterPanel: { type: Boolean, required: true },
      pendingTasks: { type: Array, required: true },
      formatDateFn: { type: Function, required: true },
    },
    emits: ['toggle-filter-panel', 'open-task', 'pending-change'],
    setup(props, { emit }) {
      return () => h('div', [
        h('span', { 'data-testid': 'filter-state' }, props.showFilterPanel ? 'open' : 'closed'),
        h('span', { 'data-testid': 'pending-count' }, String(props.pendingTasks.length)),
        h('span', { 'data-testid': 'formatted-date' }, props.formatDateFn('2026-06-10')),
        h('button', { 'data-testid': 'toggle-filter', onClick: () => emit('toggle-filter-panel') }, 'toggle filter'),
        h('button', {
          'data-testid': 'open-task',
          onClick: () => emit('open-task', {
            task_id: 1,
            name: 'Task <img src=x onerror=1>',
            completed: false,
            completed_at: null,
            timeline_id: 1,
            status: 'pending',
            priority: 2,
            tags: 'api',
            estimated_hours: null,
            actual_hours: null,
            members: [],
            start_date: '2026-06-01',
            end_date: '2026-06-03',
            created_at: null,
            updated_at: null,
            task_remark: null,
            isWork: 1,
            is_owner: true,
            depends_on_task_ids: [1, 2, 999],
            subtasks: [],
          }),
        }, 'open task'),
        h('button', {
          'data-testid': 'move-pending',
          onClick: () => emit('pending-change', { added: { element: { task_id: 1 } } }),
        }, 'move pending'),
      ]);
    },
  }),
}));

vi.mock('../TimelineKanbanTaskModal.vue', () => ({
  default: defineComponent({
    name: 'TimelineKanbanTaskModalStub',
    props: {
      show: { type: Boolean, required: true },
      task: { type: Object, default: null },
      newSubtaskName: { type: String, required: true },
    },
    emits: ['close', 'update:new-subtask-name', 'add-subtask', 'toggle-subtask', 'delete-subtask', 'priority-select', 'update-tags'],
    setup(props, { emit }) {
      return () => props.show ? h('div', { 'data-testid': 'kanban-modal' }, [
        h('span', { 'data-testid': 'modal-task-name' }, (props.task as { name?: string } | null)?.name ?? ''),
        h('span', { 'data-testid': 'modal-new-subtask' }, props.newSubtaskName),
        h('button', { 'data-testid': 'close-modal', onClick: () => emit('close') }, 'close'),
        h('button', { 'data-testid': 'set-subtask-name', onClick: () => emit('update:new-subtask-name', 'ship api') }, 'set-subtask-name'),
        h('button', { 'data-testid': 'add-subtask', onClick: () => emit('add-subtask') }, 'add-subtask'),
        h('button', {
          'data-testid': 'toggle-subtask',
          onClick: () => emit('toggle-subtask', (props.task as { subtasks?: Array<Record<string, unknown>> } | null)?.subtasks?.[0]),
        }, 'toggle-subtask'),
        h('button', {
          'data-testid': 'delete-subtask',
          onClick: () => emit('delete-subtask', (props.task as { subtasks?: Array<Record<string, unknown>> } | null)?.subtasks?.[0]),
        }, 'delete-subtask'),
        h('button', {
          'data-testid': 'priority-select',
          onClick: () => emit('priority-select', { target: { value: '1' } }),
        }, 'priority-select'),
        h('button', { 'data-testid': 'update-tags', onClick: () => emit('update-tags') }, 'update-tags'),
      ]) : null;
    },
  }),
}));

vi.mock('../TimelineGanttView.vue', () => ({
  default: defineComponent({
    name: 'TimelineGanttViewStub',
    props: {
      ganttRenderableTaskCount: { type: Number, required: true },
      missingGanttTaskDates: { type: Number, required: true },
      setGanttContainerRef: { type: Function, required: true },
    },
    setup(props) {
      const el = document.createElement('div');
      onMounted(() => {
        props.setGanttContainerRef(el);
      });
      return () => h('div', [
        h('span', { 'data-testid': 'gantt-renderable-count' }, String(props.ganttRenderableTaskCount)),
        h('span', { 'data-testid': 'gantt-missing-count' }, String(props.missingGanttTaskDates)),
      ]);
    },
  }),
}));

vi.mock('../TimelineCalendarView.vue', () => ({
  default: defineComponent({ name: 'TimelineCalendarViewStub', setup: () => () => h('div') }),
}));

vi.mock('../TimelineListView.vue', () => ({
  default: defineComponent({ name: 'TimelineListViewStub', setup: () => () => h('div') }),
}));

vi.mock('../TimelineCardView.vue', () => ({
  default: defineComponent({ name: 'TimelineCardViewStub', setup: () => () => h('div') }),
}));

import TimelineViewModes from '../TimelineViewModes.vue';
import type { Task, Timeline } from '../../../types';

const baseTimelines: Timeline[] = [
  {
    id: 1,
    name: 'Timeline <b>One</b>',
    startDate: '2026-06-01',
    endDate: '2026-06-10',
    remark: null,
    role: 0,
    totalTasks: 2,
    completedTasks: 0,
  },
];

const baseTasks: Task[] = [
  {
    task_id: 1,
    name: 'Task <img src=x onerror=1>',
    completed: false,
    completed_at: null,
    timeline_id: 1,
    status: 'pending',
    priority: 2,
    tags: 'api',
    estimated_hours: null,
    actual_hours: null,
    members: [],
    start_date: '2026-06-01',
    end_date: '2026-06-03',
    created_at: null,
    updated_at: null,
    task_remark: null,
    isWork: 1,
    is_owner: true,
    depends_on_task_ids: [1, 2, 999],
    subtasks: [],
  },
  {
    task_id: 2,
    name: 'Second Task',
    completed: false,
    completed_at: null,
    timeline_id: 1,
    status: 'in_progress',
    priority: 1,
    tags: 'backend',
    estimated_hours: null,
    actual_hours: null,
    members: [],
    start_date: '2026-06-05',
    end_date: '2026-06-04',
    created_at: null,
    updated_at: null,
    task_remark: null,
    isWork: 1,
    is_owner: true,
    depends_on_task_ids: [],
    subtasks: [],
  },
  {
    task_id: 3,
    name: 'No Date',
    completed: false,
    completed_at: null,
    timeline_id: 1,
    status: 'pending',
    priority: 3,
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
    is_owner: true,
    depends_on_task_ids: [],
    subtasks: [],
  },
];

const createTimelines = (): Timeline[] => structuredClone(baseTimelines);
const createTasks = (): Task[] => structuredClone(baseTasks);

const createWrapper = (viewMode: 'kanban' | 'gantt' | 'card' = 'kanban') => mount(TimelineViewModes, {
  props: {
    viewMode,
    timelines: createTimelines(),
    sortedTimelines: createTimelines(),
    allTasks: createTasks(),
  },
});

describe('TimelineViewModes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.ganttCalls.length = 0;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('emits refresh-all and error toast when kanban move fails', async () => {
    mocks.updateStatus.mockRejectedValueOnce(new Error('fail'));
    const wrapper = createWrapper('kanban');

    await wrapper.get('[data-testid="move-pending"]').trigger('click');
    await flushPromises();

    expect(mocks.updateStatus).toHaveBeenCalledWith(1, 'pending');
    expect(wrapper.emitted('refresh-all')).toHaveLength(1);
    expect(mocks.toastError).toHaveBeenCalledWith('更新狀態失敗');
  });

  it('opens kanban modal and resets transient state after view switch', async () => {
    mocks.getSubtasks.mockResolvedValueOnce({ data: [{ id: 9, task_id: 1, name: 'child', completed: false, sort_order: 1, created_at: null }] });
    const wrapper = createWrapper('kanban');

    expect(wrapper.get('[data-testid="filter-state"]').text()).toBe('closed');
    await wrapper.get('[data-testid="toggle-filter"]').trigger('click');
    expect(wrapper.get('[data-testid="filter-state"]').text()).toBe('open');

    await wrapper.get('[data-testid="open-task"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="kanban-modal"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="modal-task-name"]').text()).toContain('Task <img src=x onerror=1>');

    await wrapper.setProps({ viewMode: 'card' });
    await nextTick();
    expect(wrapper.find('[data-testid="kanban-modal"]').exists()).toBe(false);

    await wrapper.setProps({ viewMode: 'kanban' });
    await nextTick();
    expect(wrapper.get('[data-testid="filter-state"]').text()).toBe('closed');
  });

  it('renders gantt task metrics and sanitizes popup content', async () => {
    const wrapper = createWrapper('gantt');
    await flushPromises();

    expect(wrapper.get('[data-testid="gantt-renderable-count"]').text()).toBe('2');
    expect(wrapper.get('[data-testid="gantt-missing-count"]').text()).toBe('0');
    expect(mocks.ganttCalls).toHaveLength(1);

    const firstCall = mocks.ganttCalls[0];
    expect(firstCall.tasks[0].dependencies).toBe('2');
    expect(firstCall.tasks[1].end).toBe('2026-06-05');

    const popupHtml = firstCall.options.custom_popup_html({
      id: '1',
      name: 'Task <img src=x onerror=1>',
      start: '2026-06-01',
      end: '2026-06-03',
      progress: 50,
    });

    expect(popupHtml).toContain('&lt;img src=x onerror=1&gt;');
    expect(popupHtml).not.toContain('<img');
  });

  it('debounces gantt date change success and refreshes data', async () => {
    vi.useFakeTimers();
    mocks.update.mockResolvedValueOnce({ data: {} });
    const wrapper = createWrapper('gantt');
    await flushPromises();

    const firstCall = mocks.ganttCalls[0];
    await firstCall.options.on_date_change(
      { id: '1' },
      new Date(2026, 5, 2),
      new Date(2026, 5, 6),
    );

    vi.advanceTimersByTime(649);
    await flushPromises();
    expect(mocks.update).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    await flushPromises();
    await flushPromises();

    expect(mocks.update).toHaveBeenCalledWith(1, {
      start_date: '2026-06-02',
      end_date: '2026-06-06',
    });
    expect(wrapper.emitted('refresh-all')).toHaveLength(1);
    expect(mocks.toastSuccess).toHaveBeenCalledWith('任務時程已更新');
    expect((wrapper.props('allTasks') as Task[])[0].start_date).toBe('2026-06-02');
    expect((wrapper.props('allTasks') as Task[])[0].end_date).toBe('2026-06-06');
  });

  it('handles gantt date change failure and emits refresh-all', async () => {
    vi.useFakeTimers();
    mocks.update.mockRejectedValueOnce(new Error('fail'));
    const wrapper = createWrapper('gantt');
    await flushPromises();

    const firstCall = mocks.ganttCalls[0];
    await firstCall.options.on_date_change(
      { id: '1' },
      new Date(2026, 5, 4),
      new Date(2026, 5, 8),
    );

    vi.advanceTimersByTime(650);
    await flushPromises();
    await flushPromises();

    expect(wrapper.emitted('refresh-all')).toHaveLength(1);
    expect(mocks.toastError).toHaveBeenCalledWith('更新任務時程失敗，已重新整理');
  });

  it('emits view-timeline when gantt bar is clicked', async () => {
    const wrapper = createWrapper('gantt');
    await flushPromises();

    const firstCall = mocks.ganttCalls[0];
    firstCall.options.on_click({ id: '1' });

    expect(wrapper.emitted('view-timeline')?.[0][0]).toMatchObject({ id: 1, name: 'Timeline <b>One</b>' });
  });

  it('adds subtask and emits refresh-all', async () => {
    mocks.getSubtasks.mockResolvedValueOnce({ data: [] });
    mocks.createSubtask.mockResolvedValueOnce({
      data: {
        message: '子任務新增成功',
        subtask: { id: 9, task_id: 1, name: 'ship api', completed: false, sort_order: 1, created_at: null },
      },
    });
    const wrapper = createWrapper('kanban');

    await wrapper.get('[data-testid="open-task"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="set-subtask-name"]').trigger('click');
    await nextTick();
    expect(wrapper.get('[data-testid="modal-new-subtask"]').text()).toBe('ship api');

    await wrapper.get('[data-testid="add-subtask"]').trigger('click');
    await flushPromises();

    expect(mocks.createSubtask).toHaveBeenCalledWith(1, { name: 'ship api' });
    expect(wrapper.emitted('refresh-all')).toHaveLength(1);
    expect(wrapper.get('[data-testid="modal-new-subtask"]').text()).toBe('');
  });

  it('handles subtask toggle failure and delete success', async () => {
    mocks.getSubtasks.mockResolvedValueOnce({
      data: [{ id: 9, task_id: 1, name: 'child', completed: false, sort_order: 1, created_at: null }],
    });
    mocks.toggleSubtask.mockRejectedValueOnce(new Error('fail'));
    mocks.deleteSubtask.mockResolvedValueOnce({ data: {} });
    const wrapper = createWrapper('kanban');

    await wrapper.get('[data-testid="open-task"]').trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="toggle-subtask"]').trigger('click');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('更新子任務失敗');

    await wrapper.get('[data-testid="delete-subtask"]').trigger('click');
    await flushPromises();
    expect(mocks.deleteSubtask).toHaveBeenCalledWith(1, 9);
    expect(wrapper.emitted('refresh-all')).toHaveLength(1);
  });

  it('updates priority and tags from modal actions', async () => {
    mocks.getSubtasks.mockResolvedValueOnce({ data: [] });
    mocks.update.mockResolvedValue({ data: {} });
    const wrapper = createWrapper('kanban');

    await wrapper.get('[data-testid="open-task"]').trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="priority-select"]').trigger('click');
    await flushPromises();
    expect(mocks.update).toHaveBeenCalledWith(1, { priority: 1 });

    const modalVm = wrapper.findComponent({ name: 'TimelineKanbanTaskModalStub' }).vm as {
      task: { tags?: string };
    };
    modalVm.task.tags = 'backend,urgent';
    await nextTick();

    await wrapper.get('[data-testid="update-tags"]').trigger('click');
    await flushPromises();

    expect(mocks.update).toHaveBeenCalledWith(1, { tags: 'backend,urgent' });
    expect(wrapper.emitted('refresh-all')).toHaveLength(2);
  });
});
