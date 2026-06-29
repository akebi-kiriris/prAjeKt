import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { useTodoStore } from '../../stores/todos';
import type { Todo } from '../../types';

const mocks = vi.hoisted(() => ({
  confirm: vi.fn(),
  toastError: vi.fn(),
}));

vi.mock('../../composables/useConfirm', () => ({
  useConfirm: () => ({ confirm: mocks.confirm }),
}));

vi.mock('vue-sonner', () => ({
  toast: { error: mocks.toastError },
}));

import TodosView from '../TodosView.vue';

type TodoFixtureOverrides = {
  [Key in keyof Todo]?: Todo[Key];
};

const makeTodo = (overrides: TodoFixtureOverrides = {}): Todo => ({
  id: 1,
  title: '準備工作日誌',
  content: '整理今天完成的項目',
  type: null,
  deadline: '2026-07-01T09:30:00',
  completed: false,
  priority: 2,
  created_at: '2026-06-24T00:00:00Z',
  updated_at: '2026-06-24T00:00:00Z',
  ...overrides,
});

const findButton = (wrapper: VueWrapper, label: string) => {
  const button = wrapper.findAll('button').find((candidate) => candidate.text().trim() === label);
  if (!button) throw new Error(`找不到「${label}」按鈕`);
  return button;
};

const mountView = (todos: Todo[] = []) => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const store = useTodoStore();
  store.todos = todos;
  const spies = {
    fetch: vi.spyOn(store, 'fetchTodos').mockResolvedValue(undefined),
    add: vi.spyOn(store, 'addTodo').mockResolvedValue(undefined),
    update: vi.spyOn(store, 'updateTodo').mockResolvedValue(undefined),
    toggle: vi.spyOn(store, 'toggleTodo').mockResolvedValue(undefined),
    remove: vi.spyOn(store, 'removeTodo').mockResolvedValue(undefined),
  };
  return {
    wrapper: mount(TodosView, { global: { plugins: [pinia] } }),
    spies,
  };
};

describe('TodosView interactions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.confirm.mockResolvedValue(false);
  });

  it('新增待辦會轉換 deadline，無 deadline 時不送出該欄位', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();

    await findButton(wrapper, '新增待辦').trigger('click');
    const textareas = wrapper.findAll('textarea');
    await textareas[0].setValue('提交週報');
    await textareas[1].setValue('整理本週進度');
    await wrapper.get('input[type="datetime-local"]').setValue('2026-07-03T18:45');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();

    expect(spies.add).toHaveBeenCalledWith({
      title: '提交週報',
      content: '整理本週進度',
      deadline: '2026-07-03T18:45:00',
    });
    expect(wrapper.find('form').exists()).toBe(false);

    await findButton(wrapper, '新增待辦').trigger('click');
    const nextTextareas = wrapper.findAll('textarea');
    await nextTextareas[0].setValue('無期限事項');
    await nextTextareas[1].setValue('之後處理');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();
    expect(spies.add).toHaveBeenLastCalledWith({
      title: '無期限事項',
      content: '之後處理',
      deadline: undefined,
    });
  });

  it('編輯會載入本地日期，更新時可明確清除 deadline，取消則重設表單', async () => {
    const { wrapper, spies } = mountView([makeTodo()]);
    await flushPromises();

    const todoCard = wrapper.findAll('.rounded-xl').find((node) => node.text().includes('準備工作日誌'));
    if (!todoCard) throw new Error('找不到待辦卡片');
    await todoCard.findAll('button')[0].trigger('click');

    expect(wrapper.text()).toContain('編輯待辦事項');
    expect(wrapper.get('input[type="datetime-local"]').element).toHaveProperty('value', '2026-07-01T09:30');
    await wrapper.get('input[type="datetime-local"]').setValue('');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();

    expect(spies.update).toHaveBeenCalledWith(1, {
      title: '準備工作日誌',
      content: '整理今天完成的項目',
      deadline: null,
    });

    await findButton(wrapper, '新增待辦').trigger('click');
    await wrapper.findAll('textarea')[0].setValue('暫存文字');
    await findButton(wrapper, '取消').trigger('click');
    await findButton(wrapper, '新增待辦').trigger('click');
    expect(wrapper.findAll('textarea')[0].element).toHaveProperty('value', '');
  });

  it('可切換狀態，刪除取消不送出、確認後才刪除', async () => {
    const { wrapper, spies } = mountView([makeTodo()]);
    await flushPromises();

    await wrapper.get('input[type="checkbox"]').trigger('change');
    expect(spies.toggle).toHaveBeenCalledWith(1);

    const todoCard = wrapper.findAll('.rounded-xl').find((node) => node.text().includes('準備工作日誌'));
    if (!todoCard) throw new Error('找不到待辦卡片');
    mocks.confirm.mockResolvedValueOnce(false).mockResolvedValueOnce(true);
    await todoCard.findAll('button')[1].trigger('click');
    await flushPromises();
    expect(spies.remove).not.toHaveBeenCalled();

    await todoCard.findAll('button')[1].trigger('click');
    await flushPromises();
    expect(spies.remove).toHaveBeenCalledWith(1);
  });

  it('新增、更新、切換與刪除失敗時顯示錯誤且畫面不崩潰', async () => {
    const { wrapper, spies } = mountView([makeTodo()]);
    await flushPromises();

    spies.add.mockRejectedValueOnce(new Error('add failed'));
    await findButton(wrapper, '新增待辦').trigger('click');
    await wrapper.findAll('textarea')[0].setValue('失敗項目');
    await wrapper.findAll('textarea')[1].setValue('保留表單');
    await wrapper.get('form').trigger('submit.prevent');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('操作失敗');
    expect(wrapper.find('form').exists()).toBe(true);

    await findButton(wrapper, '取消').trigger('click');
    spies.toggle.mockRejectedValueOnce(new Error('toggle failed'));
    await wrapper.get('input[type="checkbox"]').trigger('change');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('更新待辦狀態失敗');

    mocks.confirm.mockResolvedValue(true);
    spies.remove.mockRejectedValueOnce(new Error('remove failed'));
    const todoCard = wrapper.findAll('.rounded-xl').find((node) => node.text().includes('準備工作日誌'));
    if (!todoCard) throw new Error('找不到待辦卡片');
    await todoCard.findAll('button')[1].trigger('click');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('刪除待辦失敗');
    expect(wrapper.text()).toContain('準備工作日誌');
  });
});
