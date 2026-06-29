import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import type { TaskMember } from '../../../types';
import TimelineSharePanel from '../TimelineSharePanel.vue';
import TimelineTaskMemberPanel from '../TimelineTaskMemberPanel.vue';

const owner: TaskMember = {
  user_id: 1,
  name: '王負責',
  username: 'owner',
  email: 'owner@example.com',
  role: 0,
};

const collaborator: TaskMember = {
  user_id: 2,
  name: '李協作',
  username: null,
  email: 'member@example.com',
  role: 1,
};

describe('Timeline member panels', () => {
  it('TimelineSharePanel 關閉時不渲染，開啟時顯示成員、錯誤與搜尋結果', () => {
    const closed = mount(TimelineSharePanel, {
      props: {
        open: false,
        timelineName: '專案 A',
        timelineMembers: [],
        inputEmail: '',
        searchResult: null,
        searchError: '',
      },
    });
    expect(closed.text()).toBe('');

    const wrapper = mount(TimelineSharePanel, {
      props: {
        open: true,
        timelineName: '專案 A',
        timelineMembers: [owner, collaborator],
        inputEmail: 'new@example.com',
        searchResult: { id: 3, name: '新成員' },
        searchError: '測試錯誤',
      },
    });
    expect(wrapper.text()).toContain('邀請成員加入「專案 A」');
    expect(wrapper.text()).toContain('owner');
    expect(wrapper.text()).toContain('李協作');
    expect(wrapper.text()).toContain('測試錯誤');
    expect(wrapper.text()).toContain('新成員');
    expect(wrapper.findAll('button').filter((button) => button.text().trim() === '×')).toHaveLength(1);
    expect(wrapper.findAll('button').filter((button) => button.text().trim() === '✕')).toHaveLength(1);
  });

  it('TimelineSharePanel 會 emit 關閉、v-model、搜尋、邀請與移除', async () => {
    const wrapper = mount(TimelineSharePanel, {
      props: {
        open: true,
        timelineName: '專案 A',
        timelineMembers: [owner, collaborator],
        inputEmail: '',
        searchResult: { id: 3, name: '新成員' },
        searchError: '',
      },
    });

    await wrapper.get('input[type="email"]').setValue('invite@example.com');
    expect(wrapper.emitted('update:inputEmail')?.[0]).toEqual(['invite@example.com']);
    await wrapper.get('input[type="email"]').trigger('keyup.enter');
    await wrapper.findAll('button').find((button) => button.text().trim() === '搜尋')?.trigger('click');
    await wrapper.findAll('button').find((button) => button.text().trim() === '邀請')?.trigger('click');
    await wrapper.findAll('button').find((button) => button.text().trim() === '✕')?.trigger('click');
    await wrapper.findAll('button').find((button) => button.text().trim() === '×')?.trigger('click');

    expect(wrapper.emitted('search-user')).toHaveLength(2);
    expect(wrapper.emitted('confirm-share')).toHaveLength(1);
    expect(wrapper.emitted('kick-member')?.[0]).toEqual([collaborator]);
    expect(wrapper.emitted('close')).toHaveLength(1);
  });

  it('TimelineTaskMemberPanel 顯示空狀態並過濾已加入成員', () => {
    const empty = mount(TimelineTaskMemberPanel, {
      props: {
        open: true,
        taskName: '任務 A',
        taskMembersForAssign: [],
        timelineMembers: [],
      },
    });
    expect(empty.text()).toContain('尚無指派成員');
    expect(empty.text()).toContain('載入中...');

    const wrapper = mount(TimelineTaskMemberPanel, {
      props: {
        open: true,
        taskName: '任務 A',
        taskMembersForAssign: [owner],
        timelineMembers: [owner, collaborator],
      },
    });
    expect(wrapper.text()).toContain('任務成員 — 任務 A');
    expect(wrapper.text()).toContain('owner');
    expect(wrapper.text()).toContain('李協作');
    expect(wrapper.findAll('button').filter((button) => button.text().trim() === '指派')).toHaveLength(1);
    expect(wrapper.text()).not.toContain('設為主責');
  });

  it('TimelineTaskMemberPanel emit 快速指派、移除、設主責與關閉', async () => {
    const wrapper = mount(TimelineTaskMemberPanel, {
      props: {
        open: true,
        taskName: '任務 A',
        taskMembersForAssign: [owner, collaborator],
        timelineMembers: [owner, collaborator, { ...collaborator, user_id: 3, name: '陳候選' }],
      },
    });

    await wrapper.findAll('button').find((button) => button.text().trim() === '指派')?.trigger('click');
    await wrapper.findAll('button').find((button) => button.text().trim() === '設為主責')?.trigger('click');
    await wrapper.findAll('button').find((button) => button.text().trim() === '✕')?.trigger('click');
    await wrapper.findAll('button').find((button) => button.text().trim() === '×')?.trigger('click');

    expect(wrapper.emitted('quick-assign')?.[0][0]).toMatchObject({ user_id: 3, name: '陳候選' });
    expect(wrapper.emitted('set-owner')?.[0]).toEqual([collaborator]);
    expect(wrapper.emitted('kick-member')?.[0]).toEqual([collaborator]);
    expect(wrapper.emitted('close')).toHaveLength(1);
  });
});
