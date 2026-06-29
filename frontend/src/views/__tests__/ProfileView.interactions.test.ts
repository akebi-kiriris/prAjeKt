import { beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent } from 'vue';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '../../stores/auth';

const mocks = vi.hoisted(() => ({
  profileGetMe: vi.fn(),
  profileUpdate: vi.fn(),
  profileGetChartStats: vi.fn(),
  taskGetAll: vi.fn(),
  timelineGetAll: vi.fn(),
  timelineGetMemberStats: vi.fn(),
  groupGetAll: vi.fn(),
  fetchCurrentUser: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
  toastWarning: vi.fn(),
}));

vi.mock('vue-echarts', () => ({
  default: defineComponent({
    name: 'VChart',
    props: ['option'],
    template: '<div data-testid="v-chart" />',
  }),
}));
vi.mock('echarts/core', () => ({ use: vi.fn() }));
vi.mock('echarts/renderers', () => ({ CanvasRenderer: {} }));
vi.mock('echarts/charts', () => ({ BarChart: {}, LineChart: {}, PieChart: {} }));
vi.mock('echarts/components', () => ({
  GridComponent: {},
  LegendComponent: {},
  TooltipComponent: {},
}));
vi.mock('../../services/profileService', () => ({
  profileService: {
    getMe: mocks.profileGetMe,
    update: mocks.profileUpdate,
    getChartStats: mocks.profileGetChartStats,
  },
}));
vi.mock('../../services/taskService', () => ({ taskService: { getAll: mocks.taskGetAll } }));
vi.mock('../../services/timelineService', () => ({
  timelineService: {
    getAll: mocks.timelineGetAll,
    getMemberStats: mocks.timelineGetMemberStats,
  },
}));
vi.mock('../../services/groupService', () => ({ groupService: { getAll: mocks.groupGetAll } }));
vi.mock('vue-sonner', () => ({
  toast: {
    success: mocks.toastSuccess,
    error: mocks.toastError,
    warning: mocks.toastWarning,
  },
}));

import ProfileView from '../ProfileView.vue';

const findButton = (wrapper: VueWrapper, label: string) => {
  const button = wrapper.findAll('button').find((candidate) => candidate.text().trim() === label);
  if (!button) throw new Error(`找不到「${label}」按鈕`);
  return button;
};

const mountView = async (withOwnedTimeline = false) => {
  mocks.timelineGetAll.mockResolvedValue({
    data: withOwnedTimeline
      ? [{
          id: 12,
          name: '核心專案',
          startDate: '2026-06-01',
          endDate: '2026-08-01',
          remark: null,
          role: 0,
          totalTasks: 3,
          completedTasks: 1,
        }]
      : [],
  });
  const pinia = createPinia();
  setActivePinia(pinia);
  const authStore = useAuthStore();
  vi.spyOn(authStore, 'fetchCurrentUser').mockImplementation(mocks.fetchCurrentUser);
  const wrapper = mount(ProfileView, { global: { plugins: [pinia] } });
  await flushPromises();
  return wrapper;
};

describe('ProfileView interactions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.profileGetMe.mockResolvedValue({
      data: { name: '王小明', username: 'ming', email: 'ming@example.com', phone: '0912345678' },
    });
    mocks.profileUpdate.mockResolvedValue({ data: {} });
    mocks.profileGetChartStats.mockResolvedValue({
      data: {
        daily_completions: [{ date: '2026-06-24', count: 2 }],
        status_distribution: { pending: 2, completed: 1, unknown: 9 },
        tasks_by_project: [{ name: '核心專案', count: 3 }],
      },
    });
    mocks.taskGetAll.mockResolvedValue({ data: [] });
    mocks.timelineGetAll.mockResolvedValue({ data: [] });
    mocks.timelineGetMemberStats.mockResolvedValue({
      data: {
        total_tasks: 3,
        members: [{ name: '王小明', total_tasks: 3, completed_tasks: 1 }],
        status_distribution: { in_progress: 2, completed: 1, unknown: 4 },
      },
    });
    mocks.groupGetAll.mockResolvedValue({ data: [] });
    mocks.fetchCurrentUser.mockResolvedValue({ success: true });
  });

  it('取消編輯會還原原始資料並清空密碼欄位', async () => {
    const wrapper = await mountView();
    await findButton(wrapper, '編輯資料').trigger('click');

    const textInputs = wrapper.findAll('input[type="text"]');
    await textInputs[0].setValue('被修改的名字');
    await wrapper.get('input[placeholder="請輸入新密碼"]').setValue('secret1');
    await findButton(wrapper, '取消').trigger('click');

    expect(textInputs[0].element).toHaveProperty('value', '王小明');
    expect(wrapper.text()).not.toContain('變更密碼（選填）');
  });

  it('一般資料更新成功後同步 auth user 並離開編輯模式', async () => {
    const wrapper = await mountView();
    await findButton(wrapper, '編輯資料').trigger('click');
    const textInputs = wrapper.findAll('input[type="text"]');
    await textInputs[0].setValue('王大明');
    await wrapper.get('input[type="email"]').setValue('new@example.com');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();

    expect(mocks.profileUpdate).toHaveBeenCalledWith({
      name: '王大明',
      username: 'ming',
      email: 'new@example.com',
      phone: '0912345678',
    });
    expect(mocks.fetchCurrentUser).toHaveBeenCalledOnce();
    expect(mocks.toastSuccess).toHaveBeenCalledWith('個人資料更新成功');
    expect(wrapper.text()).not.toContain('儲存變更');
  });

  it('密碼更新會依序阻擋缺少目前密碼、不一致與長度不足', async () => {
    const wrapper = await mountView();
    await findButton(wrapper, '編輯資料').trigger('click');
    const current = wrapper.get('input[placeholder="如要變更密碼，請輸入目前密碼"]');
    const next = wrapper.get('input[placeholder="請輸入新密碼"]');
    const confirm = wrapper.get('input[placeholder="再次輸入新密碼"]');

    await next.setValue('secret1');
    await confirm.setValue('secret1');
    await wrapper.get('form').trigger('submit.prevent');
    expect(mocks.toastWarning).toHaveBeenLastCalledWith('請輸入目前密碼');

    await current.setValue('old-password');
    await confirm.setValue('different');
    await wrapper.get('form').trigger('submit.prevent');
    expect(mocks.toastWarning).toHaveBeenLastCalledWith('新密碼與確認密碼不一致');

    await next.setValue('12345');
    await confirm.setValue('12345');
    await wrapper.get('form').trigger('submit.prevent');
    expect(mocks.toastWarning).toHaveBeenLastCalledWith('新密碼至少需要 6 個字元');
    expect(mocks.profileUpdate).not.toHaveBeenCalled();
  });

  it('更新失敗時顯示錯誤並保留編輯模式', async () => {
    mocks.profileUpdate.mockRejectedValueOnce(new Error('update failed'));
    const wrapper = await mountView();
    await findButton(wrapper, '編輯資料').trigger('click');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();

    expect(mocks.toastError).toHaveBeenCalledWith('更新失敗');
    expect(wrapper.text()).toContain('儲存變更');
  });

  it('會載入負責專案統計，並過濾未知或零筆狀態', async () => {
    const wrapper = await mountView(true);

    expect(mocks.timelineGetMemberStats).toHaveBeenCalledWith(12);
    expect(wrapper.text()).toContain('核心專案');
    const charts = wrapper.findAllComponents({ name: 'VChart' });
    const pieOptions = charts
      .map((chart) => chart.props('option') as { series?: Array<{ type?: string; data?: Array<{ name: string }> }> })
      .filter((option) => option.series?.[0]?.type === 'pie');
    expect(pieOptions.some((option) =>
      option.series?.[0]?.data?.some((item) => item.name === '待辦'),
    )).toBe(true);
    expect(pieOptions.some((option) =>
      option.series?.[0]?.data?.some((item) => item.name === 'unknown'),
    )).toBe(false);
  });

  it('專案統計載入失敗時顯示錯誤且結束 loading', async () => {
    mocks.timelineGetMemberStats.mockRejectedValueOnce(new Error('stats failed'));
    const wrapper = await mountView(true);

    expect(mocks.toastError).toHaveBeenCalledWith('載入專案統計失敗');
    expect(wrapper.text()).not.toContain('載入專案統計...');
  });
});
