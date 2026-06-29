import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { useGroupStore } from '../../stores/groups';
import type { Group } from '../../types';

const mocks = vi.hoisted(() => ({
  route: { query: {} as Record<string, unknown> },
  routerReplace: vi.fn(),
  confirm: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
  toastWarning: vi.fn(),
  toastInfo: vi.fn(),
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
    warning: mocks.toastWarning,
    info: mocks.toastInfo,
  },
}));

vi.mock('../../services/groupService', () => ({
  groupService: {
    getAll: vi.fn(),
    create: vi.fn(),
    join: vi.fn(),
    leave: vi.fn(),
    getMessages: vi.fn(),
    sendMessage: vi.fn(),
    generateSnapshot: vi.fn(),
    getLatestSnapshot: vi.fn(),
    getSnapshotJobStatus: vi.fn(),
  },
}));

vi.mock('../../services/socketService', () => ({
  socketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    isConnected: vi.fn(() => false),
    getSocket: vi.fn(() => null),
    joinGroup: vi.fn(),
    leaveGroup: vi.fn(),
    sendMessage: vi.fn(),
    onConnect: vi.fn(),
    onDisconnect: vi.fn(),
    onReady: vi.fn(),
    onGroupMessage: vi.fn(),
    onGroupError: vi.fn(),
    offConnect: vi.fn(),
    offDisconnect: vi.fn(),
    offReady: vi.fn(),
    offGroupMessage: vi.fn(),
    offGroupError: vi.fn(),
  },
}));

import GroupsView from '../GroupsView.vue';

const group: Group = {
  group_id: 1,
  group_name: '前端小組',
  invite_code: 'ABC123',
  created_at: '2026-06-24T00:00:00Z',
};

const findButton = (wrapper: VueWrapper, label: string) => {
  const button = wrapper.findAll('button').find((candidate) => candidate.text().trim() === label);
  if (!button) throw new Error(`找不到「${label}」按鈕`);
  return button;
};

const mountView = () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const store = useGroupStore();
  store.groups = [group];

  const spies = {
    fetch: vi.spyOn(store, 'fetchGroups').mockResolvedValue(undefined),
    create: vi.spyOn(store, 'createGroup').mockResolvedValue({
      message: '建立成功',
      group_id: 2,
      invite_code: 'NEW123',
    }),
    join: vi.spyOn(store, 'joinGroup').mockResolvedValue(undefined),
    openChat: vi.spyOn(store, 'openChat').mockImplementation(async (selected) => {
      store.currentGroup = selected;
    }),
    closeChat: vi.spyOn(store, 'closeChat').mockImplementation(() => {
      store.currentGroup = null;
      store.messages = [];
    }),
    send: vi.spyOn(store, 'sendMessage').mockResolvedValue(undefined),
    leave: vi.spyOn(store, 'leaveGroup').mockResolvedValue(undefined),
    destroy: vi.spyOn(store, 'destroySocket').mockImplementation(() => undefined),
  };

  const wrapper = mount(GroupsView, { global: { plugins: [pinia] } });
  return { wrapper, store, spies };
};

describe('GroupsView interactions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.route.query = { keep: 'yes' };
    mocks.confirm.mockResolvedValue(false);
  });

  it('建立群組會驗證空名稱，成功後清空並關閉 modal', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();

    await findButton(wrapper, '建立群組').trigger('click');
    await findButton(wrapper, '建立').trigger('click');
    expect(mocks.toastWarning).toHaveBeenCalledWith('請輸入群組名稱');
    expect(spies.create).not.toHaveBeenCalled();

    await wrapper.get('input[placeholder="請輸入群組名稱"]').setValue('新工作群組');
    await findButton(wrapper, '建立').trigger('click');
    await flushPromises();

    expect(spies.create).toHaveBeenCalledWith('新工作群組');
    expect(mocks.toastSuccess).toHaveBeenCalledWith('群組建立成功！邀請碼: NEW123');
    expect(wrapper.text()).not.toContain('建立新群組');
  });

  it('建立與加入群組失敗時顯示錯誤並保留 modal', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();

    spies.create.mockRejectedValueOnce(new Error('create failed'));
    await findButton(wrapper, '建立群組').trigger('click');
    await wrapper.get('input[placeholder="請輸入群組名稱"]').setValue('失敗群組');
    await findButton(wrapper, '建立').trigger('click');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('建立群組失敗');
    expect(wrapper.text()).toContain('建立新群組');

    await findButton(wrapper, '取消').trigger('click');
    spies.join.mockRejectedValueOnce(new Error('join failed'));
    await findButton(wrapper, '加入群組').trigger('click');
    await findButton(wrapper, '加入').trigger('click');
    expect(mocks.toastWarning).toHaveBeenCalledWith('請輸入邀請碼');

    await wrapper.get('input[placeholder="請輸入六位數邀請碼"]').setValue('BAD123');
    await findButton(wrapper, '加入').trigger('click');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('加入群組失敗');
    expect(wrapper.text()).toContain('加入群組');
  });

  it('加入群組成功後清空邀請碼並關閉 modal', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();

    await findButton(wrapper, '加入群組').trigger('click');
    await wrapper.get('input[placeholder="請輸入六位數邀請碼"]').setValue('ABC123');
    await findButton(wrapper, '加入').trigger('click');
    await flushPromises();

    expect(spies.join).toHaveBeenCalledWith('ABC123');
    expect(mocks.toastSuccess).toHaveBeenCalledWith('成功加入群組');
    expect(wrapper.find('input[placeholder="請輸入六位數邀請碼"]').exists()).toBe(false);
  });

  it('開啟與關閉聊天會同步 group_id query', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();

    await findButton(wrapper, '開啟聊天').trigger('click');
    await flushPromises();
    expect(spies.openChat).toHaveBeenCalledWith(group, expect.any(Function));
    expect(mocks.routerReplace).toHaveBeenCalledWith({ query: { keep: 'yes', group_id: '1' } });
    expect(wrapper.text()).toContain('目前沒有訊息');

    await findButton(wrapper, '✕').trigger('click');
    expect(spies.closeChat).toHaveBeenCalled();
    expect(mocks.routerReplace).toHaveBeenLastCalledWith({ query: { keep: 'yes' } });
  });

  it('空訊息不送出，成功後清空，失敗時保留內容', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();
    await findButton(wrapper, '開啟聊天').trigger('click');
    await flushPromises();

    const input = wrapper.get('input[placeholder="輸入訊息..."]');
    await input.setValue('   ');
    await findButton(wrapper, '送出').trigger('click');
    expect(spies.send).not.toHaveBeenCalled();

    await input.setValue('大家好');
    await findButton(wrapper, '送出').trigger('click');
    await flushPromises();
    expect(spies.send).toHaveBeenCalledWith('大家好', expect.any(Function));
    expect(wrapper.get('input[placeholder="輸入訊息..."]').element).toHaveProperty('value', '');

    spies.send.mockRejectedValueOnce(new Error('send failed'));
    await wrapper.get('input[placeholder="輸入訊息..."]').setValue('請重試');
    await findButton(wrapper, '送出').trigger('click');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('發送訊息失敗');
    expect(wrapper.get('input[placeholder="輸入訊息..."]').element).toHaveProperty('value', '請重試');
  });

  it('離開群組取消時不送出，成功與失敗皆有回饋', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();

    mocks.confirm.mockResolvedValueOnce(false).mockResolvedValueOnce(true).mockResolvedValueOnce(true);
    await findButton(wrapper, '離開').trigger('click');
    await flushPromises();
    expect(spies.leave).not.toHaveBeenCalled();

    await findButton(wrapper, '離開').trigger('click');
    await flushPromises();
    expect(spies.leave).toHaveBeenCalledWith(1);
    expect(mocks.toastSuccess).toHaveBeenCalledWith('已離開群組');

    spies.leave.mockRejectedValueOnce(new Error('leave failed'));
    await findButton(wrapper, '離開').trigger('click');
    await flushPromises();
    expect(mocks.toastError).toHaveBeenCalledWith('離開群組失敗');
  });

  it('mount 載入群組，unmount 時清理 socket', async () => {
    const { wrapper, spies } = mountView();
    await flushPromises();
    expect(spies.fetch).toHaveBeenCalledOnce();

    wrapper.unmount();
    expect(spies.destroy).toHaveBeenCalledOnce();
  });
});
