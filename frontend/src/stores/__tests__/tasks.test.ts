import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

vi.mock('../../services/taskService', () => ({
  taskService: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
    toggle: vi.fn(),
    updateStatus: vi.fn(),
    getSubtasks: vi.fn(),
    createSubtask: vi.fn(),
    toggleSubtask: vi.fn(),
    deleteSubtask: vi.fn(),
  },
}));

vi.mock('../../utils/payloadMappers', () => ({
  mapToCreateTaskPayload: vi.fn((v) => v),
  mapToUpdateTaskPayload: vi.fn((v) => v),
}));

import { useTaskStore } from '../tasks';
import { taskService } from '../../services/taskService';
import { mapToCreateTaskPayload, mapToUpdateTaskPayload } from '../../utils/payloadMappers';

const mockedTaskService = taskService as unknown as Record<string, ReturnType<typeof vi.fn>>;
const mockedMapCreate = mapToCreateTaskPayload as unknown as ReturnType<typeof vi.fn>;
const mockedMapUpdate = mapToUpdateTaskPayload as unknown as ReturnType<typeof vi.fn>;

describe('task store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('fetchTasks should load tasks and clear loading', async () => {
    mockedTaskService.getAll.mockResolvedValueOnce({ data: [{ id: 1 }] });

    const store = useTaskStore();
    await store.fetchTasks();

    expect(store.tasks).toEqual([{ id: 1 }]);
    expect(store.loading).toBe(false);
  });

  it('updateTask should skip update when payload mapper returns empty object', async () => {
    mockedMapUpdate.mockReturnValueOnce({});

    const store = useTaskStore();
    await store.updateTask(1, { name: 'x' } as never);

    expect(mockedTaskService.update).not.toHaveBeenCalled();
    expect(mockedTaskService.getAll).not.toHaveBeenCalled();
  });

  it('addTask should map payload, create task, then refetch', async () => {
    mockedMapCreate.mockReturnValueOnce({ name: 'A' });
    mockedTaskService.create.mockResolvedValueOnce({});
    mockedTaskService.getAll.mockResolvedValueOnce({ data: [{ id: 2, name: 'A' }] });

    const store = useTaskStore();
    await store.addTask({ name: 'A' } as never);

    expect(mockedTaskService.create).toHaveBeenCalledWith({ name: 'A' });
    expect(mockedTaskService.getAll).toHaveBeenCalled();
    expect(store.tasks).toEqual([{ id: 2, name: 'A' }]);
  });

  it('remove/toggle/updateStatus should call service then refetch', async () => {
    mockedTaskService.remove.mockResolvedValueOnce({});
    mockedTaskService.toggle.mockResolvedValueOnce({});
    mockedTaskService.updateStatus.mockResolvedValueOnce({});
    mockedTaskService.getAll
      .mockResolvedValueOnce({ data: [{ id: 1 }] })
      .mockResolvedValueOnce({ data: [{ id: 1, completed: true }] })
      .mockResolvedValueOnce({ data: [{ id: 1, status: 'done' }] });

    const store = useTaskStore();
    await store.removeTask(1);
    await store.toggleTask(1);
    await store.updateTaskStatus(1, 'done' as never);

    expect(mockedTaskService.remove).toHaveBeenCalledWith(1);
    expect(mockedTaskService.toggle).toHaveBeenCalledWith(1);
    expect(mockedTaskService.updateStatus).toHaveBeenCalledWith(1, 'done');
    expect(mockedTaskService.getAll).toHaveBeenCalledTimes(3);
  });

  it('subtask methods should call corresponding service and refetch tasks', async () => {
    mockedTaskService.getSubtasks.mockResolvedValueOnce({ data: [{ id: 7, name: 's1' }] });
    mockedTaskService.createSubtask.mockResolvedValueOnce({});
    mockedTaskService.toggleSubtask.mockResolvedValueOnce({});
    mockedTaskService.deleteSubtask.mockResolvedValueOnce({});
    mockedTaskService.getAll
      .mockResolvedValueOnce({ data: [{ id: 1, subtasks: [{ id: 7 }] }] })
      .mockResolvedValueOnce({ data: [{ id: 1, subtasks: [{ id: 7, completed: true }] }] })
      .mockResolvedValueOnce({ data: [{ id: 1, subtasks: [] }] });

    const store = useTaskStore();
    const subtasks = await store.getSubtasks(1);
    await store.addSubtask(1, { name: 's1' });
    await store.toggleSubtask(1, 7);
    await store.removeSubtask(1, 7);

    expect(subtasks).toEqual([{ id: 7, name: 's1' }]);
    expect(mockedTaskService.createSubtask).toHaveBeenCalledWith(1, { name: 's1' });
    expect(mockedTaskService.toggleSubtask).toHaveBeenCalledWith(1, 7);
    expect(mockedTaskService.deleteSubtask).toHaveBeenCalledWith(1, 7);
    expect(mockedTaskService.getAll).toHaveBeenCalledTimes(3);
  });
});
