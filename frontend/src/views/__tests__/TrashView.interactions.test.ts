import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';

const mocks = vi.hoisted(() => ({
  confirm: vi.fn(),
  getAll: vi.fn(),
  restoreTask: vi.fn(),
  restoreTimeline: vi.fn(),
  permanentDeleteTask: vi.fn(),
  permanentDeleteTimeline: vi.fn(),
  toastError: vi.fn(),
}));

vi.mock('../../composables/useConfirm', () => ({
  useConfirm: () => ({ confirm: mocks.confirm }),
}));
vi.mock('../../services/trashService', () => ({
  trashService: {
    getAll: mocks.getAll,
    restoreTask: mocks.restoreTask,
    restoreTimeline: mocks.restoreTimeline,
    permanentDeleteTask: mocks.permanentDeleteTask,
    permanentDeleteTimeline: mocks.permanentDeleteTimeline,
  },
}));
vi.mock('vue-sonner', () => ({
  toast: { error: mocks.toastError },
}));

import TrashView from '../TrashView.vue';

const payload = {
  tasks: [{
    task_id: 10,
    name: '已刪任務',
    deleted_at: '2026-06-02T12:00:00Z',
    end_date: '2026-06-10',
    priority: 1,
    is_owner: true,
  }],
  timelines: [{
    id: 1,
    name: '已刪專案',
    deleted_at: '2026-06-01T12:00:00Z',
    start_date: '2026-05-01',
    end_date: '2026-05-31',
    is_owner: true,
  }],
};

const findArticle = (wrapper: VueWrapper, text: string) => {
  const article = wrapper.findAll('article').find((candidate) => candidate.text().includes(text));
  if (!article) throw new Error(`找不到「${text}」項目`);
  return article;
};

const hasArticle = (wrapper: VueWrapper, text: string) =>
  wrapper.findAll('article').some((candidate) => candidate.text().includes(text));

describe('TrashView interactions', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mocks.confirm.mockResolvedValue(false);
    mocks.getAll.mockResolvedValue({ data: structuredClone(payload) });
    mocks.restoreTask.mockResolvedValue({ data: {} });
    mocks.restoreTimeline.mockResolvedValue({ data: {} });
    mocks.permanentDeleteTask.mockResolvedValue({ data: {} });
    mocks.permanentDeleteTimeline.mockResolvedValue({ data: {} });
  });

  it('可還原任務與專案，成功後立即從畫面移除', async () => {
    const wrapper = mount(TrashView);
    await flushPromises();

    await findArticle(wrapper, '已刪任務').findAll('button')[0].trigger('click');
    await flushPromises();
    expect(mocks.restoreTask).toHaveBeenCalledWith(10);
    expect(hasArticle(wrapper, '已刪任務')).toBe(false);

    await findArticle(wrapper, '已刪專案').findAll('button')[0].trigger('click');
    await flushPromises();
    expect(mocks.restoreTimeline).toHaveBeenCalledWith(1);
    expect(hasArticle(wrapper, '已刪專案')).toBe(false);
    expect(wrapper.text()).toContain('垃圾桶目前是空的');
  });

  it('永久刪除任務取消時不送出，確認後刪除並更新畫面', async () => {
    const wrapper = mount(TrashView);
    await flushPromises();
    mocks.confirm.mockResolvedValueOnce(false).mockResolvedValueOnce(true);

    await findArticle(wrapper, '已刪任務').findAll('button')[1].trigger('click');
    await flushPromises();
    expect(mocks.permanentDeleteTask).not.toHaveBeenCalled();

    await findArticle(wrapper, '已刪任務').findAll('button')[1].trigger('click');
    await flushPromises();
    expect(mocks.confirm).toHaveBeenLastCalledWith({
      title: '確定要永久刪除「已刪任務」？',
      message: '此操作無法復原，所有附件也會一併刪除。',
      danger: true,
    });
    expect(mocks.permanentDeleteTask).toHaveBeenCalledWith(10);
    expect(hasArticle(wrapper, '已刪任務')).toBe(false);
  });

  it('永久刪除專案確認後重新載入垃圾桶', async () => {
    const wrapper = mount(TrashView);
    await flushPromises();
    mocks.confirm.mockResolvedValue(true);
    mocks.getAll.mockResolvedValueOnce({
      data: { tasks: payload.tasks, timelines: [] },
    });

    await findArticle(wrapper, '已刪專案').findAll('button')[1].trigger('click');
    await flushPromises();

    expect(mocks.permanentDeleteTimeline).toHaveBeenCalledWith(1);
    expect(mocks.getAll).toHaveBeenCalledTimes(2);
    expect(hasArticle(wrapper, '已刪專案')).toBe(false);
  });

  it('初始載入與各操作失敗時顯示錯誤且結束 loading', async () => {
    mocks.getAll.mockRejectedValueOnce(new Error('load failed'));
    const loadWrapper = mount(TrashView);
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('無法載入垃圾桶內容');
    expect(loadWrapper.text()).toContain('垃圾桶目前是空的');

    mocks.getAll.mockResolvedValueOnce({ data: structuredClone(payload) });
    const wrapper = mount(TrashView);
    await flushPromises();

    mocks.restoreTask.mockRejectedValueOnce(new Error('restore failed'));
    await findArticle(wrapper, '已刪任務').findAll('button')[0].trigger('click');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('還原失敗');
    expect(wrapper.text()).toContain('已刪任務');

    mocks.confirm.mockResolvedValue(true);
    mocks.permanentDeleteTimeline.mockRejectedValueOnce(new Error('delete failed'));
    await findArticle(wrapper, '已刪專案').findAll('button')[1].trigger('click');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('永久刪除失敗');
    expect(wrapper.text()).toContain('已刪專案');
  });
});
