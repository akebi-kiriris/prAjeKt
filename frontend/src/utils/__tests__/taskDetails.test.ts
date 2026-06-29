import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/taskService', () => ({
  taskService: {
    getComments: vi.fn(),
    getFiles: vi.fn(),
    getSubtasks: vi.fn(),
    getMembers: vi.fn(),
  },
}));

import { taskService } from '../../services/taskService';
import {
  downloadFileFromUrl,
  loadTaskDetailResources,
  loadTaskDetailResourcesWithMembers,
} from '../taskDetails';

const mockedTaskService = taskService as unknown as Record<string, ReturnType<typeof vi.fn>>;

describe('taskDetails utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('loads comments, files and subtasks in parallel', async () => {
    const comments = [{ comment_id: 1, content: '完成 API 串接' }];
    const files = [{ file_id: 2, original_filename: 'spec.pdf' }];
    const subtasks = [{ subtask_id: 3, name: '補測試' }];
    mockedTaskService.getComments.mockResolvedValueOnce({ data: comments });
    mockedTaskService.getFiles.mockResolvedValueOnce({ data: files });
    mockedTaskService.getSubtasks.mockResolvedValueOnce({ data: subtasks });

    const result = await loadTaskDetailResources(8);

    expect(mockedTaskService.getComments).toHaveBeenCalledWith(8);
    expect(mockedTaskService.getFiles).toHaveBeenCalledWith(8);
    expect(mockedTaskService.getSubtasks).toHaveBeenCalledWith(8);
    expect(result).toEqual({ comments, files, subtasks });
  });

  it('falls back only failed or empty resources to empty arrays', async () => {
    const subtasks = [{ subtask_id: 3, name: '保留成功資料' }];
    mockedTaskService.getComments.mockRejectedValueOnce(new Error('comments unavailable'));
    mockedTaskService.getFiles.mockResolvedValueOnce({ data: undefined });
    mockedTaskService.getSubtasks.mockResolvedValueOnce({ data: subtasks });

    const result = await loadTaskDetailResources(9);

    expect(result).toEqual({ comments: [], files: [], subtasks });
  });

  it('adds members while preserving the loaded task resources', async () => {
    const comments = [{ comment_id: 1, content: '討論內容' }];
    const files = [{ file_id: 2, original_filename: 'notes.txt' }];
    const subtasks = [{ subtask_id: 3, name: '下一步' }];
    const members = [{ user_id: 4, name: '王小明' }];
    mockedTaskService.getComments.mockResolvedValueOnce({ data: comments });
    mockedTaskService.getFiles.mockResolvedValueOnce({ data: files });
    mockedTaskService.getSubtasks.mockResolvedValueOnce({ data: subtasks });
    mockedTaskService.getMembers.mockResolvedValueOnce({ data: members });

    const result = await loadTaskDetailResourcesWithMembers(10);

    expect(mockedTaskService.getMembers).toHaveBeenCalledWith(10);
    expect(result).toEqual({ comments, files, subtasks, members });
  });

  it('falls back to an empty member list without discarding other resources', async () => {
    const comments = [{ comment_id: 1, content: '仍應保留' }];
    mockedTaskService.getComments.mockResolvedValueOnce({ data: comments });
    mockedTaskService.getFiles.mockResolvedValueOnce({ data: null });
    mockedTaskService.getSubtasks.mockResolvedValueOnce({ data: null });
    mockedTaskService.getMembers.mockRejectedValueOnce(new Error('members unavailable'));

    const result = await loadTaskDetailResourcesWithMembers(11);

    expect(result).toEqual({ comments, files: [], subtasks: [], members: [] });
  });

  it('downloads a file and always removes the temporary DOM resources', async () => {
    const blob = new Blob(['file-content'], { type: 'text/plain' });
    const blobMethod = vi.fn(async () => blob);
    const fetchMock = vi.fn(async () => ({ ok: true, blob: blobMethod }));
    const createObjectURL = vi.fn(() => 'blob:task-file');
    const revokeObjectURL = vi.fn();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    vi.stubGlobal('fetch', fetchMock);
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL });

    await downloadFileFromUrl('/files/12', 'spec.txt');

    expect(fetchMock).toHaveBeenCalledWith('/files/12');
    expect(blobMethod).toHaveBeenCalledOnce();
    expect(createObjectURL).toHaveBeenCalledWith(blob);
    expect(click).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:task-file');
    expect(document.querySelector('a[download="spec.txt"]')).toBeNull();
  });

  it('throws without creating a download link when the request fails', async () => {
    const createObjectURL = vi.fn();
    const revokeObjectURL = vi.fn();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false })));
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL });

    await expect(downloadFileFromUrl('/files/missing', '')).rejects.toThrow('download failed');

    expect(createObjectURL).not.toHaveBeenCalled();
    expect(click).not.toHaveBeenCalled();
    expect(revokeObjectURL).not.toHaveBeenCalled();
  });
});
