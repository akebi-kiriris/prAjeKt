import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

vi.mock('../../services/profileService', () => ({
  profileService: {
    getMe: vi.fn(),
    update: vi.fn(),
    getChartStats: vi.fn(),
  },
}));

vi.mock('../../services/taskService', () => ({
  taskService: {
    getAll: vi.fn(),
  },
}));

vi.mock('../../services/timelineService', () => ({
  timelineService: {
    getAll: vi.fn(),
  },
}));

vi.mock('../../services/groupService', () => ({
  groupService: {
    getAll: vi.fn(),
  },
}));

import { useProfileStore } from '../profile';
import { profileService } from '../../services/profileService';
import { taskService } from '../../services/taskService';
import { timelineService } from '../../services/timelineService';
import { groupService } from '../../services/groupService';

const mockedProfileService = profileService as unknown as Record<string, ReturnType<typeof vi.fn>>;
const mockedTaskService = taskService as unknown as Record<string, ReturnType<typeof vi.fn>>;
const mockedTimelineService = timelineService as unknown as Record<string, ReturnType<typeof vi.fn>>;
const mockedGroupService = groupService as unknown as Record<string, ReturnType<typeof vi.fn>>;

describe('profile store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('fetchProfile should map response and clear loading', async () => {
    mockedProfileService.getMe.mockResolvedValueOnce({
      data: { name: 'A', username: 'aa', email: 'a@a.com', phone: '0912' },
    });

    const store = useProfileStore();
    await store.fetchProfile();

    expect(store.profile).toEqual({
      name: 'A',
      username: 'aa',
      email: 'a@a.com',
      phone: '0912',
    });
    expect(store.loading).toBe(false);
  });

  it('fetchProfile should throw on error and clear loading', async () => {
    mockedProfileService.getMe.mockRejectedValueOnce(new Error('profile fail'));

    const store = useProfileStore();
    await expect(store.fetchProfile()).rejects.toThrow('profile fail');
    expect(store.loading).toBe(false);
  });

  it('updateProfile should include password fields when new_password exists', async () => {
    mockedProfileService.update.mockResolvedValueOnce({});

    const store = useProfileStore();
    await store.updateProfile({
      name: 'B',
      username: 'bb',
      email: 'b@b.com',
      phone: '0922',
      current_password: 'old',
      new_password: 'new',
    } as never);

    expect(mockedProfileService.update).toHaveBeenCalledWith({
      name: 'B',
      username: 'bb',
      email: 'b@b.com',
      phone: '0922',
      current_password: 'old',
      new_password: 'new',
    });
    expect(store.profile.name).toBe('B');
  });

  it('fetchStats should compute stats and owned timelines', async () => {
    mockedTaskService.getAll.mockResolvedValueOnce({
      data: [
        { id: 1, completed: true },
        { id: 2, completed: false },
      ],
    });
    mockedTimelineService.getAll.mockResolvedValueOnce({
      data: [
        { timeline_id: 1, role: 0 },
        { timeline_id: 2, role: 1 },
      ],
    });
    mockedGroupService.getAll.mockResolvedValueOnce({ data: [{ group_id: 1 }, { group_id: 2 }] });

    const store = useProfileStore();
    await store.fetchStats();

    expect(store.stats).toEqual({
      totalTasks: 2,
      completedTasks: 1,
      totalProjects: 2,
      totalGroups: 2,
    });
    expect(store.ownedTimelines).toEqual([{ timeline_id: 1, role: 0 }]);
    expect(store.statCards.length).toBe(4);
  });

  it('fetchChartStats should set data and reset loading in both paths', async () => {
    mockedProfileService.getChartStats.mockResolvedValueOnce({ data: { done: 3 } });

    const store = useProfileStore();
    await store.fetchChartStats();

    expect(store.chartStats).toEqual({ done: 3 });
    expect(store.chartLoading).toBe(false);

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockedProfileService.getChartStats.mockRejectedValueOnce(new Error('chart fail'));
    await store.fetchChartStats();

    expect(store.chartLoading).toBe(false);
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
