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
import { taskService } from '../taskService';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('taskService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should map task CRUD and status endpoints correctly', () => {
    taskService.getAll();
    taskService.create({ name: 'Task' } as never);
    taskService.update(2, { name: 'Task 2' } as never);
    taskService.remove(2);
    taskService.toggle(2);
    taskService.updateStatus(2, 'todo' as never);
    taskService.upcoming();

    expect(mockedApi.get).toHaveBeenCalledWith('/tasks');
    expect(mockedApi.post).toHaveBeenCalledWith('/tasks', { name: 'Task' });
    expect(mockedApi.put).toHaveBeenCalledWith('/tasks/2', { name: 'Task 2' });
    expect(mockedApi.delete).toHaveBeenCalledWith('/tasks/2');
    expect(mockedApi.patch).toHaveBeenCalledWith('/tasks/2/toggle');
    expect(mockedApi.patch).toHaveBeenCalledWith('/tasks/2/status', { status: 'todo' });
    expect(mockedApi.get).toHaveBeenCalledWith('/tasks/upcoming');
  });

  it('should map subtask/member/comment/file endpoints correctly', () => {
    const formData = new FormData();
    formData.append('file', new Blob(['abc'], { type: 'text/plain' }), 'a.txt');

    taskService.getSubtasks(3);
    taskService.createSubtask(3, { name: 'Sub' });
    taskService.toggleSubtask(3, 4);
    taskService.deleteSubtask(3, 4);

    taskService.getMembers(3);
    taskService.addMember(3, 10);
    taskService.updateMemberRole(3, 10, 1);
    taskService.removeMember(3, 10);
    taskService.searchUser('u@example.com');

    taskService.getComments(3);
    taskService.addComment(3, 'msg');
    taskService.deleteComment(3, 11);

    taskService.getFiles(3);
    taskService.uploadFile(3, formData);
    taskService.deleteFile(3, 20);

    expect(mockedApi.get).toHaveBeenCalledWith('/tasks/3/subtasks');
    expect(mockedApi.post).toHaveBeenCalledWith('/tasks/3/subtasks', { name: 'Sub' });
    expect(mockedApi.patch).toHaveBeenCalledWith('/tasks/3/subtasks/4/toggle');
    expect(mockedApi.delete).toHaveBeenCalledWith('/tasks/3/subtasks/4');

    expect(mockedApi.get).toHaveBeenCalledWith('/tasks/3/members');
    expect(mockedApi.post).toHaveBeenCalledWith('/tasks/3/members', { user_id: 10 });
    expect(mockedApi.patch).toHaveBeenCalledWith('/tasks/3/members/10', { role: 1 });
    expect(mockedApi.delete).toHaveBeenCalledWith('/tasks/3/members/10');
    expect(mockedApi.post).toHaveBeenCalledWith('/timelines/search_user', { email: 'u@example.com' });

    expect(mockedApi.get).toHaveBeenCalledWith('/tasks/3/comments');
    expect(mockedApi.post).toHaveBeenCalledWith('/tasks/3/comments', { task_message: 'msg' });
    expect(mockedApi.delete).toHaveBeenCalledWith('/tasks/3/comments/11');

    expect(mockedApi.get).toHaveBeenCalledWith('/tasks/3/files');
    expect(mockedApi.post).toHaveBeenCalledWith('/tasks/3/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    expect(mockedApi.delete).toHaveBeenCalledWith('/tasks/3/files/20');
  });
});
