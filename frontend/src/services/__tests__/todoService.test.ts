import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../api';
import { todoService } from '../todoService';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('todoService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should map todo endpoints correctly', () => {
    todoService.getAll();
    todoService.create({ title: 'A' } as never);
    todoService.update(2, { title: 'B' } as never);
    todoService.remove(2);
    todoService.toggleComplete(2);

    expect(mockedApi.get).toHaveBeenCalledWith('/todos');
    expect(mockedApi.post).toHaveBeenCalledWith('/todos', { title: 'A' });
    expect(mockedApi.put).toHaveBeenCalledWith('/todos/2', { title: 'B' });
    expect(mockedApi.delete).toHaveBeenCalledWith('/todos/2');
    expect(mockedApi.patch).toHaveBeenCalledWith('/todos/2/toggle');
  });
});
