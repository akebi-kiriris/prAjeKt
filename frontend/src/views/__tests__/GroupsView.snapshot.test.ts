import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { GroupSnapshotResponse } from '../../types';

vi.mock('../../services/groupService', () => ({
  groupService: {
    getAll: vi.fn(),
    create: vi.fn(),
    join: vi.fn(),
    leave: vi.fn(),
    getMessages: vi.fn(),
    sendMessage: vi.fn(),
    generateSnapshot: vi.fn(),
    getLatestSnapshot: vi.fn(),
    getSnapshotJobStatus: vi.fn(),
  },
}));

vi.mock('../../services/socketService', () => ({
  socketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    isConnected: vi.fn(() => false),
    getSocket: vi.fn(() => null),
    joinGroup: vi.fn(),
    leaveGroup: vi.fn(),
    sendMessage: vi.fn(),
    onConnect: vi.fn(),
    onDisconnect: vi.fn(),
    onReady: vi.fn(),
    onGroupMessage: vi.fn(),
    onGroupError: vi.fn(),
    offConnect: vi.fn(),
    offDisconnect: vi.fn(),
    offReady: vi.fn(),
    offGroupMessage: vi.fn(),
    offGroupError: vi.fn(),
  },
}));

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock('vue-sonner', () => ({
  toast: {
    info: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('../../composables/useConfirm', () => ({
  useConfirm: () => ({ confirm: vi.fn(async () => true) }),
}));

import GroupsView from '../GroupsView.vue';
import { groupService } from '../../services/groupService';
import { toast } from 'vue-sonner';

const mockedGroupService = groupService as unknown as Record<string, ReturnType<typeof vi.fn>>;
const mockedToast = toast as unknown as Record<string, ReturnType<typeof vi.fn>>;

const snapshot: GroupSnapshotResponse = {
  snapshot_id: 101,
  group_id: 1,
  summary: {
    topics: [],
    decisions: [],
    action_items: [],
    blockers: [],
    notable_quotes: [],
    digest: {
      overview: '已整理本週開發重點',
      todo_for_user: [],
      watch_out: [],
      decisions_brief: [],
    },
  },
  created_by: 1,
  created_at: '2026-06-23T00:00:00Z',
  source_count: 3,
  model: null,
  provider: null,
  metadata: {},
};

const mountView = async (): Promise<VueWrapper> => {
  const pinia = createPinia();
  setActivePinia(pinia);
  mockedGroupService.getAll.mockResolvedValue({
    data: [{ group_id: 1, group_name: '測試群組', invite_code: 'ABC123', created_at: '2026-06-23T00:00:00Z' }],
  });

  const wrapper = mount(GroupsView, {
    global: { plugins: [pinia] },
  });
  await flushPromises();
  return wrapper;
};

const clickGenerateSnapshot = async (wrapper: VueWrapper): Promise<void> => {
  const button = wrapper.findAll('button').find((candidate) => candidate.text() === '生成快照');
  if (!button) throw new Error('找不到生成快照按鈕');
  await button.trigger('click');
  await flushPromises();
};

const clickLatestSnapshot = async (wrapper: VueWrapper): Promise<void> => {
  const button = wrapper.findAll('button').find((candidate) => candidate.text() === '最新快照');
  if (!button) throw new Error('找不到最新快照按鈕');
  await button.trigger('click');
  await flushPromises();
};

describe('GroupsView snapshot generation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('opens the snapshot modal when synchronous generation succeeds', async () => {
    mockedGroupService.generateSnapshot.mockResolvedValueOnce({ data: snapshot });
    const wrapper = await mountView();

    await clickGenerateSnapshot(wrapper);

    expect(mockedGroupService.generateSnapshot).toHaveBeenCalledWith(1, { window_days: 30, async: false });
    expect(wrapper.text()).toContain('群組知識快照');
    expect(wrapper.text()).toContain('已整理本週開發重點');
    expect(mockedToast.success).toHaveBeenCalledWith('群組快照生成完成');
    wrapper.unmount();
  });

  it('polls a queued job and opens the returned snapshot', async () => {
    mockedGroupService.generateSnapshot.mockResolvedValueOnce({
      data: { job_id: 'snapshot-job-1', status: 'queued' },
    });
    mockedGroupService.getSnapshotJobStatus.mockResolvedValueOnce({
      data: { job_id: 'snapshot-job-1', status: 'completed', snapshot },
    });
    const wrapper = await mountView();

    await clickGenerateSnapshot(wrapper);

    expect(mockedToast.info).toHaveBeenCalledWith('群組快照已進入背景工作，正在等待完成...');
    expect(mockedGroupService.getSnapshotJobStatus).toHaveBeenCalledWith('snapshot-job-1');
    expect(wrapper.text()).toContain('已整理本週開發重點');
    expect(mockedToast.success).toHaveBeenCalledWith('群組快照生成完成');
    wrapper.unmount();
  });

  it('shows an error when the background job fails', async () => {
    mockedGroupService.generateSnapshot.mockResolvedValueOnce({
      data: { job_id: 'snapshot-job-2', status: 'queued' },
    });
    mockedGroupService.getSnapshotJobStatus.mockResolvedValueOnce({
      data: { job_id: 'snapshot-job-2', status: 'failed', error: '模型暫時不可用' },
    });
    const wrapper = await mountView();

    await clickGenerateSnapshot(wrapper);

    expect(wrapper.text()).not.toContain('群組知識快照');
    expect(mockedToast.error).toHaveBeenCalledWith('模型暫時不可用');
    wrapper.unmount();
  });

  it('keeps using the shared API error mapping when generation request fails', async () => {
    mockedGroupService.generateSnapshot.mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { error_code: 'SERVICE_UNAVAILABLE' } },
    });
    const wrapper = await mountView();

    await clickGenerateSnapshot(wrapper);

    expect(mockedToast.error).toHaveBeenCalledWith('服務暫時不可用，請稍後再試');
    expect(wrapper.text()).not.toContain('群組知識快照');
    wrapper.unmount();
  });

  it('stops polling and shows an error after 15 unsuccessful attempts', async () => {
    const wrapper = await mountView();
    vi.useFakeTimers();
    mockedGroupService.generateSnapshot.mockResolvedValueOnce({
      data: { job_id: 'snapshot-job-timeout', status: 'queued' },
    });
    mockedGroupService.getSnapshotJobStatus.mockResolvedValue({
      data: { job_id: 'snapshot-job-timeout', status: 'running' },
    });

    const button = wrapper.findAll('button').find((candidate) => candidate.text() === '生成快照');
    if (!button) throw new Error('找不到生成快照按鈕');
    await button.trigger('click');
    await vi.runAllTimersAsync();
    await flushPromises();

    expect(mockedGroupService.getSnapshotJobStatus).toHaveBeenCalledTimes(15);
    expect(mockedToast.error).toHaveBeenCalledWith('群組快照背景工作逾時，請稍後再查詢');
    expect(wrapper.text()).not.toContain('群組知識快照');
    wrapper.unmount();
  });

  it('shows an explicit error when a completed job has no snapshot', async () => {
    mockedGroupService.generateSnapshot.mockResolvedValueOnce({
      data: { job_id: 'snapshot-job-empty', status: 'queued' },
    });
    mockedGroupService.getSnapshotJobStatus.mockResolvedValueOnce({
      data: { job_id: 'snapshot-job-empty', status: 'completed', snapshot: null },
    });
    const wrapper = await mountView();

    await clickGenerateSnapshot(wrapper);

    expect(wrapper.text()).not.toContain('群組知識快照');
    expect(mockedToast.success).not.toHaveBeenCalled();
    expect(mockedToast.error).toHaveBeenCalledWith('群組快照背景工作已完成，但沒有可顯示的快照');
    wrapper.unmount();
  });

  it('opens the modal when the latest snapshot is loaded', async () => {
    mockedGroupService.getLatestSnapshot.mockResolvedValueOnce({ data: snapshot });
    const wrapper = await mountView();

    await clickLatestSnapshot(wrapper);

    expect(mockedGroupService.getLatestSnapshot).toHaveBeenCalledWith(1);
    expect(wrapper.text()).toContain('群組知識快照');
    expect(wrapper.text()).toContain('已整理本週開發重點');
    wrapper.unmount();
  });

  it('maps API errors when the latest snapshot request fails', async () => {
    mockedGroupService.getLatestSnapshot.mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { error_code: 'NOT_FOUND' } },
    });
    const wrapper = await mountView();

    await clickLatestSnapshot(wrapper);

    expect(mockedToast.error).toHaveBeenCalledWith('找不到指定資源');
    expect(wrapper.text()).not.toContain('群組知識快照');
    wrapper.unmount();
  });
});
