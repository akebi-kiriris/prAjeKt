import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import KnowledgeBaseView from '../KnowledgeBaseView.vue';
import { timelineService } from '../../services/timelineService';

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

vi.mock('../../services/timelineService', () => ({
  timelineService: {
    listKnowledgeDocuments: vi.fn(),
    uploadKnowledgeDocument: vi.fn(),
    deleteKnowledgeDocument: vi.fn(),
    reindexKnowledgeDocument: vi.fn(),
  },
}));

const mockedTimelineService = timelineService as unknown as {
  listKnowledgeDocuments: ReturnType<typeof vi.fn>;
  uploadKnowledgeDocument: ReturnType<typeof vi.fn>;
  deleteKnowledgeDocument: ReturnType<typeof vi.fn>;
  reindexKnowledgeDocument: ReturnType<typeof vi.fn>;
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
    mockedTimelineService.listKnowledgeDocuments.mockResolvedValue({ data: documentPayload });
    mockedTimelineService.uploadKnowledgeDocument.mockResolvedValue({ data: { message: 'uploaded' } });
    mockedTimelineService.deleteKnowledgeDocument.mockResolvedValue({ data: { message: 'deleted' } });
    mockedTimelineService.reindexKnowledgeDocument.mockResolvedValue({ data: { message: 'reindexed' } });
  });

  it('renders personal knowledge documents', async () => {
    const wrapper = mount(KnowledgeBaseView);
    await flushPromises();

    expect(mockedTimelineService.listKnowledgeDocuments).toHaveBeenCalledWith({
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
    mockedTimelineService.listKnowledgeDocuments.mockResolvedValueOnce({
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

    expect(mockedTimelineService.uploadKnowledgeDocument).toHaveBeenCalledWith(expect.any(File));
    expect(mockedTimelineService.listKnowledgeDocuments).toHaveBeenCalledTimes(2);
  });

  it('deletes and reindexes one document without project_id', async () => {
    const wrapper = mount(KnowledgeBaseView);
    await flushPromises();

    await wrapper.findAll('button').find(button => button.text() === '重建索引')!.trigger('click');
    await flushPromises();
    await wrapper.findAll('button').find(button => button.text() === '刪除')!.trigger('click');
    await flushPromises();

    expect(mockedTimelineService.reindexKnowledgeDocument).toHaveBeenCalledWith(7);
    expect(mockedTimelineService.deleteKnowledgeDocument).toHaveBeenCalledWith(7);
  });

  it('shows load errors', async () => {
    mockedTimelineService.listKnowledgeDocuments.mockRejectedValueOnce({
      response: { data: { error: '讀取失敗' } },
      isAxiosError: true,
    });

    const wrapper = mount(KnowledgeBaseView);
    await flushPromises();

    expect(wrapper.text()).toContain('讀取失敗');
  });
});
