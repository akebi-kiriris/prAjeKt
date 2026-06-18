import api from './api';
import type { AxiosResponse } from 'axios';
import type {
  KnowledgeBatchResponse,
  KnowledgeDocumentsResponse,
  KnowledgeDocumentEventsResponse,
  KnowledgeDocumentMutationResponse,
  KnowledgeDocumentReindexResponse,
  KnowledgeDocumentUploadResponse,
} from '../types';

const knowledgeProjectParams = (projectId?: number) => (projectId ? { project_id: projectId } : undefined);

export const knowledgeService = {
  listDocuments: (
    params?: {
      limit?: number;
      offset?: number;
      project_id?: number;
      q?: string;
      sort?: 'created_desc' | 'created_asc' | 'name_asc' | 'name_desc' | 'status_asc';
      status?: string;
    }
  ): Promise<AxiosResponse<KnowledgeDocumentsResponse>> =>
    api.get('/knowledge/documents', { params }),

  uploadDocument: (file: File, projectId?: number): Promise<AxiosResponse<KnowledgeDocumentUploadResponse>> => {
    const form = new FormData();
    form.append('file', file);
    const config: { headers: { 'Content-Type': string }; params?: { project_id: number } } = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };
    const params = knowledgeProjectParams(projectId);
    if (params) config.params = params;
    return api.post('/knowledge/documents', form, config);
  },

  deleteDocument: (documentId: number, projectId?: number): Promise<AxiosResponse<KnowledgeDocumentMutationResponse>> =>
    api.delete(`/knowledge/documents/${documentId}`, { params: knowledgeProjectParams(projectId) }),

  reindexDocument: (documentId: number, projectId?: number): Promise<AxiosResponse<KnowledgeDocumentReindexResponse>> =>
    api.post(`/knowledge/documents/${documentId}/reindex`, null, { params: knowledgeProjectParams(projectId) }),

  batchDeleteDocuments: (projectId: number, documentIds: number[]): Promise<AxiosResponse<KnowledgeBatchResponse>> =>
    api.post('/knowledge/documents/batch-delete', { document_ids: documentIds }, { params: { project_id: projectId } }),

  batchReindexDocuments: (projectId: number, documentIds: number[]): Promise<AxiosResponse<KnowledgeBatchResponse>> =>
    api.post('/knowledge/documents/batch-reindex', { document_ids: documentIds }, { params: { project_id: projectId } }),

  downloadDocumentFile: (documentId: number, projectId: number): Promise<AxiosResponse<Blob>> =>
    api.get(`/knowledge/documents/${documentId}/download`, {
      params: { project_id: projectId },
      responseType: 'blob',
    }),

  previewDocumentFile: (documentId: number, projectId: number): Promise<AxiosResponse<Blob>> =>
    api.get(`/knowledge/documents/${documentId}/preview`, {
      params: { project_id: projectId },
      responseType: 'blob',
    }),

  listDocumentEvents: (
    params: { project_id: number; limit?: number; offset?: number }
  ): Promise<AxiosResponse<KnowledgeDocumentEventsResponse>> =>
    api.get('/knowledge/documents/events', { params }),
};
