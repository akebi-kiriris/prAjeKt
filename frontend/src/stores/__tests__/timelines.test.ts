import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

vi.mock('../../services/timelineService', () => ({
  timelineService: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
    getTasks: vi.fn(),
  },
}));

vi.mock('../../services/taskService', () => ({
  taskService: {
    getAll: vi.fn(),
    toggle: vi.fn(),
    remove: vi.fn(),
  },
}));

import { useTimelineStore } from '../timelines';
import { timelineService } from '../../services/timelineService';
import { taskService } from '../../services/taskService';

const mockedTimelineService = timelineService as unknown as Record<string, ReturnType<typeof vi.fn>>;
const mockedTaskService = taskService as unknown as Record<string, ReturnType<typeof vi.fn>>;

describe('timeline store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-03-25T10:00:00.000Z'));
  });

  it('getDaysRemaining should return expected buckets', () => {
    const store = useTimelineStore();

    expect(store.getDaysRemaining(null).text).toBe('未設定');
    expect(store.getDaysRemaining('2026-03-24').display).toBe('過期 1 天');
    expect(store.getDaysRemaining('2026-03-25').display).toBe('今天到期');
    expect(store.getDaysRemaining('2026-03-27').colorClass).toBe('text-orange-500');
    expect(store.getDaysRemaining('2026-03-31').colorClass).toBe('text-yellow-600');
    expect(store.getDaysRemaining('2026-04-20').colorClass).toBe('text-blue-500');
    expect(store.getDaysRemaining('2026-05-30').colorClass).toBe('text-green-500');
  });

  it('fetchTimelines should set list and loading', async () => {
    mockedTimelineService.getAll.mockResolvedValueOnce({
      data: [{ timeline_id: 1, name: 'A', endDate: '2026-03-30' }],
    });

    const store = useTimelineStore();
    await store.fetchTimelines();

    expect(store.timelines).toEqual([{ timeline_id: 1, name: 'A', endDate: '2026-03-30' }]);
    expect(store.loading).toBe(false);
  });

  it('fetchTimelines should rethrow on error and clear loading', async () => {
    mockedTimelineService.getAll.mockRejectedValueOnce(new Error('fail'));
    const store = useTimelineStore();

    await expect(store.fetchTimelines()).rejects.toThrow('fail');
    expect(store.loading).toBe(false);
  });

  it('fetchAll should fetch timelines and all tasks', async () => {
    mockedTimelineService.getAll.mockResolvedValueOnce({ data: [{ timeline_id: 1 }] });
    mockedTaskService.getAll.mockResolvedValueOnce({ data: [{ id: 9 }] });

    const store = useTimelineStore();
    await store.fetchAll();

    expect(store.timelines).toEqual([{ timeline_id: 1 }]);
    expect(store.allTasks).toEqual([{ id: 9 }]);
  });

  it('add/update/remove timeline should call service and refetch', async () => {
    mockedTimelineService.create.mockResolvedValueOnce({});
    mockedTimelineService.update.mockResolvedValueOnce({});
    mockedTimelineService.remove.mockResolvedValueOnce({});
    mockedTimelineService.getAll
      .mockResolvedValueOnce({ data: [{ timeline_id: 1, name: 'N1' }] })
      .mockResolvedValueOnce({ data: [{ timeline_id: 1, name: 'N2' }] })
      .mockResolvedValueOnce({ data: [] });

    const store = useTimelineStore();

    await store.addTimeline({
      name: '  Project A  ',
      start_date: '2026-03-01',
      end_date: '2026-03-10',
      remark: 'R',
    } as never);

    await store.updateTimeline(1, {
      name: '  New Name  ',
      start_date: '2026-03-02',
      end_date: '2026-03-11',
      remark: 'new',
    } as never);

    await store.removeTimeline(1);

    expect(mockedTimelineService.create).toHaveBeenCalledWith({
      name: 'Project A',
      start_date: '2026-03-01',
      end_date: '2026-03-10',
      remark: 'R',
    });
    expect(mockedTimelineService.update).toHaveBeenCalledWith(1, {
      name: 'New Name',
      start_date: '2026-03-02',
      end_date: '2026-03-11',
      remark: 'new',
    });
    expect(mockedTimelineService.remove).toHaveBeenCalledWith(1);
    expect(mockedTimelineService.getAll).toHaveBeenCalledTimes(3);
  });

  it('updateTimeline should return early when no valid fields exist', async () => {
    const store = useTimelineStore();
    await store.updateTimeline(5, {} as never);

    expect(mockedTimelineService.update).not.toHaveBeenCalled();
    expect(mockedTimelineService.getAll).not.toHaveBeenCalled();
  });

  it('task operations should call service and refresh as expected', async () => {
    mockedTimelineService.getTasks.mockResolvedValueOnce({ data: [{ id: 100 }] });
    mockedTaskService.toggle.mockResolvedValueOnce({});
    mockedTaskService.remove.mockResolvedValueOnce({});
    mockedTimelineService.getAll
      .mockResolvedValueOnce({ data: [{ timeline_id: 1 }] })
      .mockResolvedValueOnce({ data: [{ timeline_id: 1 }] });
    mockedTaskService.getAll.mockResolvedValueOnce({ data: [{ id: 10 }] });

    const store = useTimelineStore();
    const tasks = await store.getTimelineTasks(1);
    await store.toggleTask(10);
    await store.removeTask(10);

    expect(tasks).toEqual([{ id: 100 }]);
    expect(mockedTaskService.toggle).toHaveBeenCalledWith(10);
    expect(mockedTaskService.remove).toHaveBeenCalledWith(10);
    expect(mockedTaskService.getAll).toHaveBeenCalledTimes(1);
    expect(mockedTimelineService.getAll).toHaveBeenCalledTimes(2);
  });
});
