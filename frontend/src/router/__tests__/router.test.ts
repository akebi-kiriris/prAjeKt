import { beforeEach, describe, expect, it, vi } from 'vitest';

const viewStub = { default: { template: '<div />' } };

vi.mock('../../views/HomeView.vue', () => viewStub);
vi.mock('../../views/LoginView.vue', () => viewStub);
vi.mock('../../views/RegisterView.vue', () => viewStub);
vi.mock('../../views/TimelinesView.vue', () => viewStub);
vi.mock('../../views/KnowledgeBaseView.vue', () => viewStub);
vi.mock('../../views/TasksView.vue', () => viewStub);
vi.mock('../../views/TodosView.vue', () => viewStub);
vi.mock('../../views/GroupsView.vue', () => viewStub);
vi.mock('../../views/ProfileView.vue', () => viewStub);
vi.mock('../../views/TrashView.vue', () => viewStub);

const loadRouter = async () => {
  vi.resetModules();
  window.history.replaceState({}, '', '/');
  return (await import('../index')).default;
};

describe('router authentication guard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it.each(['/', '/timelines', '/tasks'])(
    'redirects unauthenticated navigation from %s to /login',
    async (path) => {
      const router = await loadRouter();

      await router.push(path);
      await router.isReady();

      expect(router.currentRoute.value.path).toBe('/login');
    },
  );

  it('redirects an authenticated user away from /login', async () => {
    localStorage.setItem('access_token', 'test-token');
    const router = await loadRouter();

    await router.push('/login');
    await router.isReady();

    expect(router.currentRoute.value.path).toBe('/');
  });

  it('allows an unauthenticated user to open /register', async () => {
    const router = await loadRouter();

    await router.push('/register');
    await router.isReady();

    expect(router.currentRoute.value.path).toBe('/register');
  });
});
