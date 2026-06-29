import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent } from 'vue';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('@headlessui/vue', () => {
  const passthrough = (name: string) =>
    defineComponent({
      name,
      template: '<div><slot /></div>',
    });

  return {
    TransitionRoot: defineComponent({
      name: 'TransitionRoot',
      props: {
        show: Boolean,
      },
      template: '<div v-if="show"><slot /></div>',
    }),
    TransitionChild: passthrough('TransitionChild'),
    Dialog: passthrough('Dialog'),
    DialogPanel: passthrough('DialogPanel'),
    DialogTitle: passthrough('DialogTitle'),
  };
});

import ConfirmDialog from '../ConfirmDialog.vue';
import { dialogState, useConfirm } from '../../composables/useConfirm';

describe('ConfirmDialog', () => {
  afterEach(() => {
    dialogState.value = null;
  });

  it('is hidden until a confirmation is requested', () => {
    const wrapper = mount(ConfirmDialog);

    expect(wrapper.text()).not.toContain('確認');
  });

  it('renders the requested title and message', async () => {
    const wrapper = mount(ConfirmDialog);
    const { confirm } = useConfirm();

    void confirm({
      title: '確定要刪除嗎？',
      message: '此操作無法復原。',
      danger: true,
    });
    await flushPromises();

    expect(wrapper.text()).toContain('確定要刪除嗎？');
    expect(wrapper.text()).toContain('此操作無法復原。');
    expect(wrapper.text()).toContain('🗑️');
  });

  it('resolves true and clears state when confirmed', async () => {
    const wrapper = mount(ConfirmDialog);
    const { confirm } = useConfirm();
    const result = confirm({ title: '確認執行？' });
    await flushPromises();

    const confirmButton = wrapper.findAll('button').find((button) => button.text() === '確認');
    if (!confirmButton) throw new Error('找不到確認按鈕');
    await confirmButton.trigger('click');

    await expect(result).resolves.toBe(true);
    expect(dialogState.value).toBeNull();
  });

  it('resolves false and clears state when cancelled', async () => {
    const wrapper = mount(ConfirmDialog);
    const { confirm } = useConfirm();
    const result = confirm({ title: '取消測試？' });
    await flushPromises();

    const cancelButton = wrapper.findAll('button').find((button) => button.text() === '取消');
    if (!cancelButton) throw new Error('找不到取消按鈕');
    await cancelButton.trigger('click');

    await expect(result).resolves.toBe(false);
    expect(dialogState.value).toBeNull();
  });

  it('uses the neutral icon and button style for non-danger confirmations', async () => {
    const wrapper = mount(ConfirmDialog);
    const { confirm } = useConfirm();

    void confirm({ title: '一般確認' });
    await flushPromises();

    expect(wrapper.text()).toContain('❓');
    const confirmButton = wrapper.findAll('button').find((button) => button.text() === '確認');
    expect(confirmButton?.classes().join(' ')).toContain('bg-blue-500');
  });
});
