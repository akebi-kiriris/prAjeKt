import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { defineComponent } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  routerPush: vi.fn(),
  route: { fullPath: '/' },
  getNotifications: vi.fn(),
  getUnreadCount: vi.fn(),
  markAsRead: vi.fn(),
  markAllAsRead: vi.fn(),
  deleteNotification: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  default: {
    get: mocks.apiGet,
    post: mocks.apiPost,
  },
}));

vi.mock('../../services/notificationService', () => ({
  notificationService: {
    getAll: mocks.getNotifications,
    getUnreadCount: mocks.getUnreadCount,
    markAsRead: mocks.markAsRead,
    markAllAsRead: mocks.markAllAsRead,
    delete: mocks.deleteNotification,
  },
}));

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mocks.routerPush }),
  useRoute: () => mocks.route,
}));

import App from '../../App.vue';
import Header from '../Header.vue';
import { useAuthStore } from '../../stores/auth';
import type { Notification } from '../../types';

const HeaderStub = defineComponent({
  name: 'Header',
  emits: ['logout', 'toggle-sidebar'],
  template: `
    <header data-testid="app-header">
      <button data-testid="app-logout" @click="$emit('logout')">登出</button>
      <button data-testid="app-toggle-sidebar" @click="$emit('toggle-sidebar')">切換側欄</button>
    </header>
  `,
});

const mountApp = () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  return mount(App, {
    global: {
      plugins: [pinia],
      stubs: {
        Header: HeaderStub,
        Sidebar: { name: 'Sidebar', template: '<aside data-testid="app-sidebar" />' },
        RouterView: { template: '<div data-testid="router-view" />' },
        CopilotDock: { template: '<div />' },
        Toaster: { template: '<div />' },
        ConfirmDialog: { template: '<div />' },
      },
    },
  });
};

describe('App and Header authentication UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    localStorage.clear();
    setActivePinia(createPinia());
    mocks.route.fullPath = '/';
    mocks.getNotifications.mockResolvedValue({ data: [] });
    mocks.getUnreadCount.mockResolvedValue({ data: { count: 0 } });
    mocks.apiPost.mockResolvedValue({ data: {} });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('Header displays the current user and emits logout and sidebar actions', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const authStore = useAuthStore();
    authStore.user = { id: 1, name: '王小明', email: 'user@example.com' } as never;
    const wrapper = mount(Header, { global: { plugins: [pinia] } });
    await flushPromises();

    const logoutButton = wrapper.findAll('button').find((button) => button.text() === '登出');
    if (!logoutButton) throw new Error('找不到登出按鈕');
    await logoutButton.trigger('click');
    await wrapper.findAll('button')[0].trigger('click');

    expect(wrapper.text()).toContain('王小明');
    expect(wrapper.emitted('logout')).toHaveLength(1);
    expect(wrapper.emitted('toggle-sidebar')).toHaveLength(1);
    expect(mocks.getUnreadCount).toHaveBeenCalledOnce();
    wrapper.unmount();
  });

  it('App waits for logout, clears authentication and redirects to login', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    localStorage.setItem('access_token', 'access-token');
    localStorage.setItem('refresh_token', 'refresh-token');
    const authStore = useAuthStore(pinia);
    authStore.accessToken = 'access-token';
    authStore.refreshToken = 'refresh-token';
    authStore.user = { id: 1, name: '王小明', email: 'user@example.com' } as never;

    const wrapper = mount(App, {
      global: {
        plugins: [pinia],
        stubs: {
          Header: HeaderStub,
          Sidebar: { name: 'Sidebar', template: '<aside data-testid="app-sidebar" />' },
          RouterView: { template: '<div data-testid="router-view" />' },
          CopilotDock: { template: '<div />' },
          Toaster: { template: '<div />' },
          ConfirmDialog: { template: '<div />' },
        },
      },
    });

    expect(wrapper.find('[data-testid="app-header"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="app-sidebar"]').exists()).toBe(true);
    await wrapper.get('[data-testid="app-logout"]').trigger('click');
    await flushPromises();

    expect(mocks.apiPost).toHaveBeenCalledWith('/auth/logout');
    expect(authStore.isAuthenticated).toBe(false);
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(mocks.routerPush).toHaveBeenCalledWith('/login');
    wrapper.unmount();
  });

  it('App hides authenticated navigation for signed-out users', () => {
    const wrapper = mountApp();

    expect(wrapper.find('[data-testid="app-header"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="app-sidebar"]').exists()).toBe(false);
    expect(wrapper.get('main').classes()).toContain('w-full');
    wrapper.unmount();
  });
});

const notifications: Notification[] = [
  {
    id: 1,
    title: '任務指派',
    content: '你有新的任務',
    type: 'task_assigned',
    is_read: false,
    link: '/tasks',
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    title: '已讀通知',
    content: '這是一則已讀通知',
    type: 'comment',
    is_read: true,
    link: null,
    created_at: new Date(Date.now() - 3600 * 1000).toISOString(),
  },
] as Notification[];

const mountHeader = async (notificationList: Notification[] = notifications, unread = 1) => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const authStore = useAuthStore();
  authStore.user = { id: 1, name: '王小明', email: 'user@example.com' } as never;
  mocks.getNotifications.mockResolvedValue({ data: notificationList.map((item) => ({ ...item })) });
  mocks.getUnreadCount.mockResolvedValue({ data: { count: unread } });
  mocks.markAsRead.mockResolvedValue({ data: {} });
  mocks.markAllAsRead.mockResolvedValue({ data: {} });
  mocks.deleteNotification.mockResolvedValue({ data: {} });

  const wrapper = mount(Header, {
    attachTo: document.body,
    global: { plugins: [pinia] },
  });
  await flushPromises();
  return wrapper;
};

const openNotificationPanel = async (wrapper: VueWrapper) => {
  const bellButton = wrapper.findAll('button')[1];
  await bellButton.trigger('click');
  await flushPromises();
};

describe('Header notification center', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    setActivePinia(createPinia());
    mocks.getNotifications.mockResolvedValue({ data: [] });
    mocks.getUnreadCount.mockResolvedValue({ data: { count: 0 } });
    mocks.markAsRead.mockResolvedValue({ data: {} });
    mocks.markAllAsRead.mockResolvedValue({ data: {} });
    mocks.deleteNotification.mockResolvedValue({ data: {} });
  });

  afterEach(() => {
    document.body.innerHTML = '';
    vi.useRealTimers();
  });

  it('opens the panel, refreshes notifications and displays unread state', async () => {
    const wrapper = await mountHeader();

    await openNotificationPanel(wrapper);

    expect(mocks.getUnreadCount).toHaveBeenCalledTimes(2);
    expect(mocks.getNotifications).toHaveBeenCalledOnce();
    expect(wrapper.text()).toContain('通知中心');
    expect(wrapper.text()).toContain('未讀 1');
    expect(wrapper.text()).toContain('任務指派');
    expect(wrapper.text()).toContain('NEW');
    wrapper.unmount();
  });

  it('filters unread notifications from the panel', async () => {
    const wrapper = await mountHeader();
    await openNotificationPanel(wrapper);

    const unreadFilter = wrapper.findAll('button').find((button) => button.text() === '未讀');
    if (!unreadFilter) throw new Error('找不到未讀篩選按鈕');
    await unreadFilter.trigger('click');

    expect(wrapper.text()).toContain('任務指派');
    expect(wrapper.text()).not.toContain('已讀通知');
    wrapper.unmount();
  });

  it('marks an unread linked notification as read, navigates and closes the panel', async () => {
    const wrapper = await mountHeader();
    await openNotificationPanel(wrapper);

    const notificationTitle = wrapper.findAll('p').find((node) => node.text() === '任務指派');
    const notificationRow = notificationTitle?.element.closest('.group') as HTMLElement | null;
    if (!notificationRow) throw new Error('找不到通知列');
    notificationRow.click();
    await flushPromises();

    expect(mocks.markAsRead).toHaveBeenCalledWith(1);
    expect(mocks.routerPush).toHaveBeenCalledWith('/tasks');
    expect(wrapper.text()).not.toContain('通知中心');
    wrapper.unmount();
  });

  it('marks all as read and clears read notifications from the panel', async () => {
    const wrapper = await mountHeader();
    await openNotificationPanel(wrapper);

    const markAllButton = wrapper.findAll('button').find((button) => button.text() === '全部已讀');
    if (!markAllButton) throw new Error('找不到全部已讀按鈕');
    await markAllButton.trigger('click');
    await flushPromises();

    expect(mocks.markAllAsRead).toHaveBeenCalledOnce();

    const clearReadButton = wrapper.findAll('button').find((button) => button.text() === '清除已讀');
    if (!clearReadButton) throw new Error('找不到清除已讀按鈕');
    await clearReadButton.trigger('click');
    await flushPromises();

    expect(mocks.deleteNotification).toHaveBeenCalledWith(1);
    expect(mocks.deleteNotification).toHaveBeenCalledWith(2);
    wrapper.unmount();
  });

  it('closes the notification panel when clicking outside', async () => {
    const wrapper = await mountHeader();
    await openNotificationPanel(wrapper);

    document.body.click();
    await flushPromises();

    expect(wrapper.text()).not.toContain('通知中心');
    wrapper.unmount();
  });
});
