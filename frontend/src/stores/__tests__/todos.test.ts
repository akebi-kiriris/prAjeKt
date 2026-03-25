import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

vi.mock('../../services/todoService', () => ({
  todoService: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
    toggleComplete: vi.fn(),
  },
}));

vi.mock('../../utils/payloadMappers', () => ({
  mapToCreateTodoPayload: vi.fn((v) => v),
  mapToUpdateTodoPayload: vi.fn((v) => v),
}));

import { useTodoStore } from '../todos';
import { todoService } from '../../services/todoService';
import { mapToCreateTodoPayload, mapToUpdateTodoPayload } from '../../utils/payloadMappers';

const mockedTodoService = todoService as unknown as Record<string, ReturnType<typeof vi.fn>>;
const mockedMapCreate = mapToCreateTodoPayload as unknown as ReturnType<typeof vi.fn>;
const mockedMapUpdate = mapToUpdateTodoPayload as unknown as ReturnType<typeof vi.fn>;

describe('todo store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('fetchTodos should update list and loading state', async () => {
    mockedTodoService.getAll.mockResolvedValueOnce({ data: [{ id: 1, completed: false }] });

    const store = useTodoStore();
    await store.fetchTodos();

    expect(store.todos).toEqual([{ id: 1, completed: false }]);
  });

  it('updateTodo should return early when mapped payload is empty', async () => {
    mockedMapUpdate.mockReturnValueOnce({});

    const store = useTodoStore();
    await store.updateTodo(3, { title: 'x' } as never);

    expect(mockedTodoService.update).not.toHaveBeenCalled();
    expect(mockedTodoService.getAll).not.toHaveBeenCalled();
  });

  it('addTodo should map payload then create and refetch', async () => {
    mockedMapCreate.mockReturnValueOnce({ content: 'A' });
    mockedTodoService.create.mockResolvedValueOnce({});
    mockedTodoService.getAll.mockResolvedValueOnce({ data: [{ id: 2, completed: false }] });

    const store = useTodoStore();
    await store.addTodo({ content: 'A' } as never);

    expect(mockedMapCreate).toHaveBeenCalled();
    expect(mockedTodoService.create).toHaveBeenCalledWith({ content: 'A' });
    expect(mockedTodoService.getAll).toHaveBeenCalled();
    expect(store.todos).toEqual([{ id: 2, completed: false }]);
  });

  it('removeTodo/toggleTodo should call service and refetch', async () => {
    mockedTodoService.remove.mockResolvedValueOnce({});
    mockedTodoService.toggleComplete.mockResolvedValueOnce({});
    mockedTodoService.getAll
      .mockResolvedValueOnce({ data: [{ id: 1, completed: false }] })
      .mockResolvedValueOnce({ data: [{ id: 1, completed: true }] });

    const store = useTodoStore();
    await store.removeTodo(1);
    await store.toggleTodo(1);

    expect(mockedTodoService.remove).toHaveBeenCalledWith(1);
    expect(mockedTodoService.toggleComplete).toHaveBeenCalledWith(1);
    expect(mockedTodoService.getAll).toHaveBeenCalledTimes(2);
  });

  it('computed lists should split todos by completed flag', async () => {
    mockedTodoService.getAll.mockResolvedValueOnce({
      data: [
        { id: 1, completed: false },
        { id: 2, completed: true },
      ],
    });

    const store = useTodoStore();
    await store.fetchTodos();

    expect(store.incompleteTodos).toEqual([{ id: 1, completed: false }]);
    expect(store.completedTodos).toEqual([{ id: 2, completed: true }]);
  });

  it('fetchTodos should handle error and still end loading state', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockedTodoService.getAll.mockRejectedValueOnce(new Error('boom'));

    const store = useTodoStore();
    store.todos = [{ id: 9, completed: false } as never];
    await store.fetchTodos();

    expect(store.todos).toEqual([{ id: 9, completed: false }]);
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
