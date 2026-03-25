import { beforeEach, describe, expect, it } from 'vitest';
import { dialogState, useConfirm } from '../useConfirm';

describe('useConfirm', () => {
  beforeEach(() => {
    dialogState.value = null;
  });

  it('confirm 會建立 dialog 狀態並套用預設值', () => {
    const { confirm } = useConfirm();

    void confirm({ title: '刪除任務？' });

    expect(dialogState.value).not.toBeNull();
    expect(dialogState.value?.title).toBe('刪除任務？');
    expect(dialogState.value?.message).toBe('');
    expect(dialogState.value?.danger).toBe(false);
    expect(typeof dialogState.value?.resolve).toBe('function');
  });

  it('confirm 在 danger=true 時應保留旗標', () => {
    const { confirm } = useConfirm();

    void confirm({
      title: '永久刪除？',
      message: '這個操作無法復原。',
      danger: true,
    });

    expect(dialogState.value?.danger).toBe(true);
    expect(dialogState.value?.message).toBe('這個操作無法復原。');
  });

  it('使用者確認時 Promise 應 resolve true', async () => {
    const { confirm } = useConfirm();

    const pending = confirm({ title: '確認送出？' });
    dialogState.value?.resolve(true);

    await expect(pending).resolves.toBe(true);
  });

  it('使用者取消時 Promise 應 resolve false', async () => {
    const { confirm } = useConfirm();

    const pending = confirm({ title: '取消變更？' });
    dialogState.value?.resolve(false);

    await expect(pending).resolves.toBe(false);
  });
});
