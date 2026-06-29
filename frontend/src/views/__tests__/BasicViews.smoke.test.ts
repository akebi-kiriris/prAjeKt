import { flushPromises, mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { defineComponent } from 'vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  taskGetAll: vi.fn(),
  taskUpcoming: vi.fn(),
  timelineGetAll: vi.fn(),
  timelineUpcoming: vi.fn(),
  timelineGetMemberStats: vi.fn(),
  groupGetAll: vi.fn(),
  profileGetMe: vi.fn(),
  profileGetChartStats: vi.fn(),
  profileUpdate: vi.fn(),
  todoGetAll: vi.fn(),
  trashGetAll: vi.fn(),
  toastError: vi.fn(),
}));

vi.mock('vue-echarts', () => ({
  default: defineComponent({
    name: 'VChart',
    template: '<div data-testid="v-chart" />',
  }),
}));

vi.mock('echarts/core', () => ({
  use: vi.fn(),
}));

vi.mock('echarts/renderers', () => ({
  CanvasRenderer: {},
}));

vi.mock('echarts/charts', () => ({
  BarChart: {},
  LineChart: {},
  PieChart: {},
}));

vi.mock('echarts/components', () => ({
  GridComponent: {},
  LegendComponent: {},
  TooltipComponent: {},
}));

vi.mock('vue-sonner', () => ({
  toast: {
    error: mocks.toastError,
    success: vi.fn(),
    warning: vi.fn(),
  },
}));

vi.mock('../../services/taskService', () => ({
  taskService: {
    getAll: mocks.taskGetAll,
    upcoming: mocks.taskUpcoming,
  },
}));

vi.mock('../../services/timelineService', () => ({
  timelineService: {
    getAll: mocks.timelineGetAll,
    upcoming: mocks.timelineUpcoming,
    getMemberStats: mocks.timelineGetMemberStats,
  },
}));

vi.mock('../../services/groupService', () => ({
  groupService: {
    getAll: mocks.groupGetAll,
  },
}));

vi.mock('../../services/profileService', () => ({
  profileService: {
    getMe: mocks.profileGetMe,
    getChartStats: mocks.profileGetChartStats,
    update: mocks.profileUpdate,
  },
}));

vi.mock('../../services/todoService', () => ({
  todoService: {
    getAll: mocks.todoGetAll,
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
    toggleComplete: vi.fn(),
  },
}));

vi.mock('../../services/trashService', () => ({
  trashService: {
    getAll: mocks.trashGetAll,
    restoreTask: vi.fn(),
    restoreTimeline: vi.fn(),
    permanentDeleteTask: vi.fn(),
    permanentDeleteTimeline: vi.fn(),
  },
}));

import HomeView from '../HomeView.vue';
import ProfileView from '../ProfileView.vue';
import TodosView from '../TodosView.vue';
import TrashView from '../TrashView.vue';

const RouterLinkStub = defineComponent({
  name: 'RouterLink',
  props: {
    to: {
      type: [String, Object],
      required: true,
    },
  },
  template: '<a :href="typeof to === \'string\' ? to : \'#\'"><slot /></a>',
});

const mountView = (component: unknown) => {
  const pinia = createPinia();
  setActivePinia(pinia);
  return mount(component, {
    global: {
      plugins: [pinia],
      stubs: {
        RouterLink: RouterLinkStub,
      },
    },
  });
};

describe('basic view smoke tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
    mocks.taskGetAll.mockResolvedValue({ data: [] });
    mocks.taskUpcoming.mockResolvedValue({ data: [] });
    mocks.timelineGetAll.mockResolvedValue({ data: [] });
    mocks.timelineUpcoming.mockResolvedValue({ data: [] });
    mocks.timelineGetMemberStats.mockResolvedValue({ data: null });
    mocks.groupGetAll.mockResolvedValue({ data: [] });
    mocks.profileGetMe.mockResolvedValue({
      data: {
        name: '王小明',
        username: 'ming',
        email: 'ming@example.com',
        phone: '0912345678',
      },
    });
    mocks.profileGetChartStats.mockResolvedValue({
      data: {
        daily_completions: [],
        status_distribution: {},
        tasks_by_project: [],
      },
    });
    mocks.todoGetAll.mockResolvedValue({ data: [] });
    mocks.trashGetAll.mockResolvedValue({ data: { tasks: [], timelines: [] } });
  });

  it('renders HomeView navigation cards and upcoming empty state', async () => {
    const wrapper = mountView(HomeView);
    await flushPromises();

    expect(mocks.taskUpcoming).toHaveBeenCalledOnce();
    expect(mocks.timelineUpcoming).toHaveBeenCalledOnce();
    expect(wrapper.text()).toContain('PrAjeKt 專案管理');
    expect(wrapper.text()).toContain('專案管理');
    expect(wrapper.text()).toContain('目前沒有即將到期的項目');
    wrapper.unmount();
  });

  it('keeps HomeView usable when one upcoming request fails', async () => {
    mocks.taskUpcoming.mockRejectedValueOnce(new Error('task api failed'));
    mocks.timelineUpcoming.mockResolvedValueOnce({
      data: [
        {
          id: 2,
          type: 'timeline',
          name: '即將到期專案',
          end_date: '2026-07-01',
          is_overdue: false,
        },
      ],
    });

    const wrapper = mountView(HomeView);
    await flushPromises();

    expect(wrapper.text()).toContain('即將到期專案');
    wrapper.unmount();
  });

  it('sorts overdue items first and keeps invalid deadlines at the end', async () => {
    mocks.taskUpcoming.mockResolvedValueOnce({
      data: [
        {
          task_id: 10,
          type: 'task',
          name: '日期格式錯誤任務',
          end_date: 'not-a-date',
          is_overdue: false,
        },
        {
          task_id: 11,
          type: 'task',
          name: '較早到期任務',
          end_date: '2026-06-26',
          is_overdue: false,
        },
      ],
    });
    mocks.timelineUpcoming.mockResolvedValueOnce({
      data: [
        {
          id: 2,
          type: 'timeline',
          name: '已逾期專案',
          end_date: '2026-06-20',
          is_overdue: true,
        },
        {
          id: 3,
          type: 'timeline',
          name: '較晚到期專案',
          end_date: '2026-06-30',
          is_overdue: false,
        },
      ],
    });

    const wrapper = mountView(HomeView);
    await flushPromises();

    const text = wrapper.text();
    expect(text.indexOf('已逾期專案')).toBeLessThan(text.indexOf('較早到期任務'));
    expect(text.indexOf('較早到期任務')).toBeLessThan(text.indexOf('較晚到期專案'));
    expect(text.indexOf('較晚到期專案')).toBeLessThan(text.indexOf('日期格式錯誤任務'));
    expect(wrapper.findAll('a[href="/tasks"]')).toHaveLength(3);
    expect(wrapper.findAll('a[href="/timelines"]')).toHaveLength(3);
    wrapper.unmount();
  });

  it('renders ProfileView, loads profile data and opens edit mode', async () => {
    const wrapper = mountView(ProfileView);
    await flushPromises();

    expect(mocks.profileGetMe).toHaveBeenCalledOnce();
    expect(mocks.taskGetAll).toHaveBeenCalledOnce();
    expect(mocks.timelineGetAll).toHaveBeenCalledOnce();
    expect(mocks.groupGetAll).toHaveBeenCalledOnce();
    expect(wrapper.text()).toContain('個人資料');
    expect(wrapper.text()).toContain('基本資料');

    const editButton = wrapper.findAll('button').find((button) => button.text() === '編輯資料');
    if (!editButton) throw new Error('找不到編輯資料按鈕');
    await editButton.trigger('click');

    expect(wrapper.text()).toContain('儲存變更');
    expect(wrapper.text()).toContain('變更密碼（選填）');
    wrapper.unmount();
  });

  it('renders TodosView, loads todos and opens the add modal', async () => {
    const wrapper = mountView(TodosView);
    await flushPromises();

    expect(mocks.todoGetAll).toHaveBeenCalledOnce();
    expect(wrapper.text()).toContain('待辦事項');
    expect(wrapper.text()).toContain('未完成');
    expect(wrapper.text()).toContain('已完成');

    const addButton = wrapper.findAll('button').find((button) => button.text().includes('新增待辦'));
    if (!addButton) throw new Error('找不到新增待辦按鈕');
    await addButton.trigger('click');

    expect(wrapper.text()).toContain('新增待辦事項');
    expect(wrapper.text()).toContain('待辦事項名稱');
    wrapper.unmount();
  });

  it('renders TrashView empty state after loading trash data', async () => {
    const wrapper = mountView(TrashView);
    await flushPromises();

    expect(mocks.trashGetAll).toHaveBeenCalledOnce();
    expect(wrapper.text()).toContain('垃圾桶');
    expect(wrapper.text()).toContain('垃圾桶目前是空的');
    wrapper.unmount();
  });

  it('renders TrashView deleted task and timeline counts', async () => {
    mocks.trashGetAll.mockResolvedValueOnce({
      data: {
        timelines: [
          {
            id: 1,
            name: '已刪專案',
            deleted_at: '2026-06-01T12:00:00Z',
            start_date: '2026-05-01',
            end_date: '2026-05-31',
            is_owner: true,
          },
        ],
        tasks: [
          {
            task_id: 10,
            name: '已刪任務',
            priority: 1,
            deleted_at: '2026-06-02T12:00:00Z',
            end_date: '2026-06-10',
            is_owner: true,
          },
        ],
      },
    });

    const wrapper = mountView(TrashView);
    await flushPromises();

    expect(wrapper.text()).toContain('已刪專案');
    expect(wrapper.text()).toContain('已刪任務');
    expect(wrapper.text()).toContain('高優先');
    wrapper.unmount();
  });
});
