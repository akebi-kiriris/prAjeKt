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
import { groupService } from '../groupService';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('groupService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getAll should call GET /groups', () => {
    groupService.getAll();
    expect(mockedApi.get).toHaveBeenCalledWith('/groups');
  });

  it('create should call POST /groups with group_name payload', () => {
    groupService.create('Team A');
    expect(mockedApi.post).toHaveBeenCalledWith('/groups', { group_name: 'Team A' });
  });

  it('join should call POST /groups/join with invite_code payload', () => {
    groupService.join('INV123');
    expect(mockedApi.post).toHaveBeenCalledWith('/groups/join', { invite_code: 'INV123' });
  });

  it('leave should call POST /groups/:id/leave', () => {
    groupService.leave(7);
    expect(mockedApi.post).toHaveBeenCalledWith('/groups/7/leave');
  });

  it('getMessages should call GET /groups/:id/messages', () => {
    groupService.getMessages(12);
    expect(mockedApi.get).toHaveBeenCalledWith('/groups/12/messages');
  });

  it('sendMessage should call POST /groups/:id/messages with content payload', () => {
    groupService.sendMessage(12, 'hello');
    expect(mockedApi.post).toHaveBeenCalledWith('/groups/12/messages', { content: 'hello' });
  });
});
