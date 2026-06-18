import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../api';
import { knowledgeService } from '../knowledgeService';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('knowledgeService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should map personal and project knowledge document endpoints correctly', () => {
    knowledgeService.listDocuments({ limit: 10, offset: 0 });
    knowledgeService.uploadDocument(new File(['personal'], 'personal.md', { type: 'text/markdown' }));
    knowledgeService.deleteDocument(8);
    knowledgeService.reindexDocument(8);
    knowledgeService.uploadDocument(new File(['hello'], 'doc.md', { type: 'text/markdown' }), 5);
    knowledgeService.deleteDocument(9, 5);
    knowledgeService.reindexDocument(9, 5);
    knowledgeService.batchDeleteDocuments(5, [1, 2]);
    knowledgeService.batchReindexDocuments(5, [1, 2]);
    knowledgeService.downloadDocumentFile(9, 5);
    knowledgeService.previewDocumentFile(9, 5);
    knowledgeService.listDocumentEvents({ project_id: 5, limit: 10, offset: 0 });

    expect(mockedApi.get).toHaveBeenCalledWith('/knowledge/documents', { params: { limit: 10, offset: 0 } });
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/knowledge/documents',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    expect(mockedApi.delete).toHaveBeenCalledWith('/knowledge/documents/8', { params: undefined });
    expect(mockedApi.post).toHaveBeenCalledWith('/knowledge/documents/8/reindex', null, { params: undefined });
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/knowledge/documents',
      expect.any(FormData),
      { params: { project_id: 5 }, headers: { 'Content-Type': 'multipart/form-data' } },
    );
    expect(mockedApi.delete).toHaveBeenCalledWith('/knowledge/documents/9', { params: { project_id: 5 } });
    expect(mockedApi.post).toHaveBeenCalledWith('/knowledge/documents/9/reindex', null, { params: { project_id: 5 } });
    expect(mockedApi.post).toHaveBeenCalledWith('/knowledge/documents/batch-delete', { document_ids: [1, 2] }, { params: { project_id: 5 } });
    expect(mockedApi.post).toHaveBeenCalledWith('/knowledge/documents/batch-reindex', { document_ids: [1, 2] }, { params: { project_id: 5 } });
    expect(mockedApi.get).toHaveBeenCalledWith('/knowledge/documents/9/download', {
      params: { project_id: 5 },
      responseType: 'blob',
    });
    expect(mockedApi.get).toHaveBeenCalledWith('/knowledge/documents/9/preview', {
      params: { project_id: 5 },
      responseType: 'blob',
    });
    expect(mockedApi.get).toHaveBeenCalledWith('/knowledge/documents/events', { params: { project_id: 5, limit: 10, offset: 0 } });
  });
});
