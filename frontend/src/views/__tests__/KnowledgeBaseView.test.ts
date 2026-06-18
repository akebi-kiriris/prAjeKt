import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import KnowledgeBaseView from '../KnowledgeBaseView.vue';
import { knowledgeService } from '../../services/knowledgeService';

vi.mock('vue-sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('../../composables/useConfirm', () => ({
  useConfirm: () => ({
    confirm: vi.fn().mockResolvedValue(true),
  }),
}));

vi.mock('../../services/knowledgeService', () => ({
  knowledgeService: {
    listDocuments: vi.fn(),
    uploadDocument: vi.fn(),
    deleteDocument: vi.fn(),
    reindexDocument: vi.fn(),
  },
}));

const mockedKnowledgeService = knowledgeService as unknown as {
  listDocuments: ReturnType<typeof vi.fn>;
  uploadDocument: ReturnType<typeof vi.fn>;
  deleteDocument: ReturnType<typeof vi.fn>;
  reindexDocument: ReturnType<typeof vi.fn>;
};

const documentPayload = {
  message: 'ok',
  documents: [
    {
      id: 7,
      filename: 'phase7.md',
      original_filename: 'phase7.md',
      status: 'ready',
      size_bytes: 2048,
      created_at: '2026-05-07T10:00:00Z',
    },
  ],
  meta: { limit: 20, offset: 0, count: 1 },
};

describe('KnowledgeBaseView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedKnowledgeService.listDocuments.mockResolvedValue({ data: documentPayload });
    mockedKnowledgeService.uploadDocument.mockResolvedValue({ data: { message: 'uploaded' } });
    mockedKnowledgeService.deleteDocument.mockResolvedValue({ data: { message: 'deleted' } });
    mockedKnowledgeService.reindexDocument.mockResolvedValue({ data: { message: 'reindexed' } });
  });

  it('renders personal knowledge documents', async () => {
    const wrapper = mount(KnowledgeBaseView);
    await flushPromises();

    expect(mockedKnowledgeService.listDocuments).toHaveBeenCalledWith({
      limit: 20,
      offset: 0,
      q: undefined,
      status: undefined,
      sort: 'created_desc',
    });
    expect(wrapper.text()).toContain('個人知識庫');
    expect(wrapper.text()).toContain('phase7.md');
    expect(wrapper.text()).toContain('ready');
  });

  it('renders an empty state', async () => {
    mockedKnowledgeService.listDocuments.mockResolvedValueOnce({
      data: { message: 'ok', documents: [], meta: { limit: 20, offset: 0, count: 0 } },
    });

    const wrapper = mount(KnowledgeBaseView);
    await flushPromises();

    expect(wrapper.text()).toContain('目前沒有文件');
  });

  it('uploads a personal document without project_id', async () => {
    const wrapper = mount(KnowledgeBaseView);
    await flushPromises();

    const input = wrapper.find('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
      value: [new File(['hello'], 'hello.md', { type: 'text/markdown' })],
      configurable: true,
    });
    await input.trigger('change');
    await flushPromises();

    expect(mockedKnowledgeService.uploadDocument).toHaveBeenCalledWith(expect.any(File));
    expect(mockedKnowledgeService.listDocuments).toHaveBeenCalledTimes(2);
  });

  it('deletes and reindexes one document without project_id', async () => {
    const wrapper = mount(KnowledgeBaseView);
    await flushPromises();

    await wrapper.findAll('button').find(button => button.text() === '重建索引')!.trigger('click');
    await flushPromises();
    await wrapper.findAll('button').find(button => button.text() === '刪除')!.trigger('click');
    await flushPromises();

    expect(mockedKnowledgeService.reindexDocument).toHaveBeenCalledWith(7);
    expect(mockedKnowledgeService.deleteDocument).toHaveBeenCalledWith(7);
  });

  it('shows load errors', async () => {
    mockedKnowledgeService.listDocuments.mockRejectedValueOnce({
      response: { data: { error: '讀取失敗' } },
      isAxiosError: true,
    });

    const wrapper = mount(KnowledgeBaseView);
    await flushPromises();

    expect(wrapper.text()).toContain('讀取失敗');
  });
});
