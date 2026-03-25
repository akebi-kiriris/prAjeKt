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
import { timelineService } from '../timelineService';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('timelineService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should map timeline CRUD endpoints correctly', () => {
    timelineService.getAll();
    timelineService.create({ name: 'T1' } as never);
    timelineService.update(3, { name: 'T2' } as never);
    timelineService.remove(3);

    expect(mockedApi.get).toHaveBeenCalledWith('/timelines');
    expect(mockedApi.post).toHaveBeenCalledWith('/timelines', { name: 'T1' });
    expect(mockedApi.put).toHaveBeenCalledWith('/timelines/3', { name: 'T2' });
    expect(mockedApi.delete).toHaveBeenCalledWith('/timelines/3');
  });

  it('should map task/member related endpoints correctly', () => {
    timelineService.getTasks(5);
    timelineService.getMembers(5);
    timelineService.addMember(5, 9);
    timelineService.removeMember(5, 9);
    timelineService.batchCreateTasks(5, [{ name: 'A' } as never]);

    expect(mockedApi.get).toHaveBeenCalledWith('/timelines/5/tasks');
    expect(mockedApi.get).toHaveBeenCalledWith('/timelines/5/members');
    expect(mockedApi.post).toHaveBeenCalledWith('/timelines/5/members', { user_id: 9, role: 1 });
    expect(mockedApi.delete).toHaveBeenCalledWith('/timelines/5/members/9');
    expect(mockedApi.post).toHaveBeenCalledWith('/timelines/5/batch-create-tasks', { tasks: [{ name: 'A' }] });
  });

  it('should map utility endpoints correctly', () => {
    timelineService.updateRemark(5, 'memo');
    timelineService.searchUser('u@example.com');
    timelineService.generateTasks(5);
    timelineService.upcoming();
    timelineService.getMemberStats(5);

    expect(mockedApi.put).toHaveBeenCalledWith('/timelines/5/remark', { remark: 'memo' });
    expect(mockedApi.post).toHaveBeenCalledWith('/timelines/search_user', { email: 'u@example.com' });
    expect(mockedApi.post).toHaveBeenCalledWith('/timelines/5/generate-tasks', {});
    expect(mockedApi.get).toHaveBeenCalledWith('/timelines/upcoming');
    expect(mockedApi.get).toHaveBeenCalledWith('/timelines/5/member-stats');
  });
});
