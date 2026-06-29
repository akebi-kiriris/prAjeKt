import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { useTimelineStore } from '../../stores/timelines';
import type { Timeline } from '../../types';

const mocks = vi.hoisted(() => ({
  route: { query: {} as Record<string, unknown> },
  confirm: vi.fn(),
  routerReplace: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
  toastInfo: vi.fn(),
  toastWarning: vi.fn(),
}));

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>();
  return {
    ...actual,
    useRoute: () => mocks.route,
    useRouter: () => ({ replace: mocks.routerReplace }),
  };
});

vi.mock('../../composables/useConfirm', () => ({
  useConfirm: () => ({ confirm: mocks.confirm }),
}));

vi.mock('vue-sonner', () => ({
  toast: {
    success: mocks.toastSuccess,
    error: mocks.toastError,
    info: mocks.toastInfo,
    warning: mocks.toastWarning,
  },
}));

import TimelinesView from '../TimelinesView.vue';

const timeline: Timeline = {
  id: 12,
  name: '新人訓練專案',
  startDate: '2026-06-01',
  endDate: '2026-08-31',
  remark: '建立基本交付能力',
  role: 0,
  totalTasks: 4,
  completedTasks: 1,
};

const mountView = (timelines: Timeline[] = []) => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const store = useTimelineStore();
  store.timelines = timelines;
  store.allTasks = [];

  const spies = {
    fetchAll: vi.spyOn(store, 'fetchAll').mockResolvedValue(undefined),
    add: vi.spyOn(store, 'addTimeline').mockResolvedValue(undefined),
    update: vi.spyOn(store, 'updateTimeline').mockResolvedValue(undefined),
    remove: vi.spyOn(store, 'removeTimeline').mockResolvedValue(undefined),
    getTasks: vi.spyOn(store, 'getTimelineTasks').mockResolvedValue([]),
    toggleTask: vi.spyOn(store, 'toggleTask').mockResolvedValue(undefined),
    removeTask: vi.spyOn(store, 'removeTask').mockResolvedValue(undefined),
  };

  const wrapper = mount(TimelinesView, {
    global: {
      plugins: [pinia],
      stubs: {
        TimelineHeader: {
          props: ['timelines', 'urgentCount', 'totalCompletedTasks', 'totalTasks', 'viewMode'],
          emits: ['update:viewMode', 'create-timeline'],
          template: `
            <header>
              <h1>專案時間軸</h1>
              <p>專案數 {{ timelines.length }}</p>
              <button @click="$emit('create-timeline')">新增專案</button>
              <button @click="$emit('update:viewMode', 'list')">清單模式</button>
            </header>
          `,
        },
        TimelineViewModes: {
          props: ['viewMode', 'timelines'],
          emits: ['view-timeline', 'edit-timeline', 'delete-timeline', 'refresh-all'],
          template: `
            <main>
              <p>目前模式 {{ viewMode }}</p>
              <p v-if="timelines.length === 0">目前沒有專案</p>
              <button
                v-for="timeline in timelines"
                :key="timeline.id"
                @click="$emit('view-timeline', timeline)"
              >
                {{ timeline.name }}
              </button>
              <button
                v-if="timelines[0]"
                data-testid="edit-timeline"
                @click="$emit('edit-timeline', timelines[0])"
              >編輯專案</button>
              <button
                v-if="timelines[0]"
                data-testid="delete-timeline"
                @click="$emit('delete-timeline', timelines[0].id)"
              >刪除專案</button>
              <button data-testid="refresh-all" @click="$emit('refresh-all')">重新整理</button>
            </main>
          `,
        },
        TimelineDetailDialog: {
          props: ['selectedTimeline'],
          emits: ['close', 'toggle-task', 'delete-task', 'refresh-all'],
          template: `
            <aside>
              專案詳情 {{ selectedTimeline.name }}
              <button data-testid="close-detail" @click="$emit('close')">關閉詳情</button>
              <button data-testid="toggle-detail-task" @click="$emit('toggle-task', 99)">切換任務</button>
              <button data-testid="delete-detail-task" @click="$emit('delete-task', 99)">刪除任務</button>
              <button data-testid="refresh-detail" @click="$emit('refresh-all')">更新詳情</button>
            </aside>
          `,
        },
      },
    },
  });

  return { wrapper, spies };
};

describe('TimelinesView smoke', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.route.query = {};
    mocks.confirm.mockResolvedValue(false);
  });

  it('可掛載空狀態、顯示主要入口並載入初始資料', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();

    expect(spies.fetchAll).toHaveBeenCalledOnce();
    expect(wrapper.text()).toContain('專案時間軸');
    expect(wrapper.text()).toContain('專案數 0');
    expect(wrapper.text()).toContain('目前沒有專案');
    expect(wrapper.text()).toContain('目前模式 card');

    await wrapper.get('button:nth-of-type(2)').trigger('click');
    expect(wrapper.text()).toContain('目前模式 list');
  });

  it('可從主要入口開啟新增 modal 並建立專案', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();

    await wrapper.get('header button').trigger('click');
    expect(wrapper.text()).toContain('新增專案');
    expect(wrapper.text()).toContain('建立專案');

    await wrapper.get('input[placeholder="例如：Q1 產品開發計畫"]').setValue('新專案');
    const dates = wrapper.findAll('input[type="date"]');
    await dates[0].setValue('2026-07-01');
    await dates[1].setValue('2026-07-31');
    await wrapper.get('textarea').setValue('Smoke test');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();

    expect(spies.add).toHaveBeenCalledWith({
      name: '新專案',
      start_date: '2026-07-01',
      end_date: '2026-07-31',
      remark: 'Smoke test',
    });
    expect(mocks.toastSuccess).toHaveBeenCalledWith('專案新增成功');
    expect(wrapper.find('form').exists()).toBe(false);
  });

  it('點擊專案可載入任務並顯示詳情入口', async () => {
    const { wrapper, spies } = mountView([timeline]);
    await flushPromises();

    await wrapper.findAll('main button')[0].trigger('click');
    await flushPromises();

    expect(spies.getTasks).toHaveBeenCalledWith(12);
    expect(mocks.routerReplace).toHaveBeenCalledWith({ query: { timeline_id: '12' } });
    expect(wrapper.text()).toContain('專案詳情 新人訓練專案');
  });

  it('編輯專案只送出變更欄位，沒有變更時不呼叫 API', async () => {
    const { wrapper, spies } = mountView([timeline]);
    await flushPromises();

    await wrapper.get('[data-testid="edit-timeline"]').trigger('click');
    expect(wrapper.text()).toContain('編輯專案');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();
    expect(spies.update).not.toHaveBeenCalled();
    expect(mocks.toastInfo).toHaveBeenCalledWith('沒有變更內容');

    await wrapper.get('[data-testid="edit-timeline"]').trigger('click');
    await wrapper.get('input[placeholder="例如：Q1 產品開發計畫"]').setValue('新人訓練計畫');
    await wrapper.get('textarea').setValue('更新備註');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();
    expect(spies.update).toHaveBeenCalledWith(12, {
      name: '新人訓練計畫',
      remark: '更新備註',
    });
    expect(mocks.toastSuccess).toHaveBeenCalledWith('專案更新成功');
  });

  it('建立或更新失敗時顯示錯誤並保留 modal，空名稱顯示警告', async () => {
    const { wrapper, spies } = mountView([timeline]);
    await flushPromises();

    await wrapper.get('header button').trigger('click');
    await wrapper.get('form').trigger('submit.prevent');
    expect(mocks.toastWarning).toHaveBeenCalledWith('請輸入專案名稱');

    spies.add.mockRejectedValueOnce(new Error('add failed'));
    await wrapper.get('input[placeholder="例如：Q1 產品開發計畫"]').setValue('失敗專案');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('操作失敗');
    expect(wrapper.find('form').exists()).toBe(true);
  });

  it('刪除專案會處理取消、成功與失敗', async () => {
    const { wrapper, spies } = mountView([timeline]);
    await flushPromises();
    mocks.confirm.mockResolvedValueOnce(false).mockResolvedValueOnce(true).mockResolvedValueOnce(true);

    await wrapper.get('[data-testid="delete-timeline"]').trigger('click');
    await flushPromises();
    expect(spies.remove).not.toHaveBeenCalled();

    await wrapper.get('[data-testid="delete-timeline"]').trigger('click');
    await flushPromises();
    expect(spies.remove).toHaveBeenCalledWith(12);
    expect(mocks.toastSuccess).toHaveBeenCalledWith('專案刪除成功');

    spies.remove.mockRejectedValueOnce(new Error('remove failed'));
    await wrapper.get('[data-testid="delete-timeline"]').trigger('click');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('刪除失敗');
  });

  it('詳情任務事件、重新整理與關閉時會更新資料及 query', async () => {
    mocks.route.query = { keep: 'yes' };
    const { wrapper, spies } = mountView([timeline]);
    await flushPromises();
    await wrapper.findAll('main button')[0].trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="toggle-detail-task"]').trigger('click');
    await flushPromises();
    expect(spies.toggleTask).toHaveBeenCalledWith(99);
    expect(spies.getTasks).toHaveBeenCalledTimes(2);

    mocks.confirm.mockResolvedValue(true);
    await wrapper.get('[data-testid="delete-detail-task"]').trigger('click');
    await flushPromises();
    expect(spies.removeTask).toHaveBeenCalledWith(99);
    expect(mocks.toastSuccess).toHaveBeenCalledWith('任務刪除成功');

    await wrapper.get('[data-testid="refresh-detail"]').trigger('click');
    await flushPromises();
    expect(spies.fetchAll).toHaveBeenCalledTimes(2);

    await wrapper.get('[data-testid="close-detail"]').trigger('click');
    await flushPromises();
    expect(mocks.routerReplace).toHaveBeenLastCalledWith({ query: { keep: 'yes' } });
  });
});
