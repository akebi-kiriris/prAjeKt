import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';

import TimelineHeader from '../TimelineHeader.vue';
import TimelineKanbanTaskModal from '../TimelineKanbanTaskModal.vue';
import TimelineListView from '../TimelineListView.vue';
import type { Task, Timeline } from '../../../types';

const baseTimeline: Timeline = {
  id: 1,
  name: 'Alpha',
  startDate: '2026-05-01',
  endDate: '2026-05-20',
  remark: null,
  role: 0,
  totalTasks: 4,
  completedTasks: 2,
};

describe('Timeline subcomponents (phase 8.4 split)', () => {
  it('TimelineHeader emits update:viewMode and create-timeline', async () => {
    const wrapper = mount(TimelineHeader, {
      props: {
        todayFormatted: '2026-05-27',
        timelines: [baseTimeline],
        urgentCount: 1,
        totalCompletedTasks: 2,
        totalTasks: 4,
        viewMode: 'card',
      },
    });

    const buttons = wrapper.findAll('button');
    await buttons[1].trigger('click');
    await buttons[5].trigger('click');

    expect(wrapper.emitted('update:viewMode')?.[0]).toEqual(['kanban']);
    expect(wrapper.emitted('create-timeline')).toBeTruthy();
  });

  it('TimelineListView emits view/edit/delete actions', async () => {
    const wrapper = mount(TimelineListView, {
      props: {
        sortedTimelines: [baseTimeline],
        timelinesCount: 1,
        getTimelineStatus: () => ({
          label: '進行中',
          bgClass: 'bg-blue-100',
          textClass: 'text-blue-700',
          badgeClass: 'bg-blue-100 text-blue-700',
        }),
        getDaysRemaining: () => ({ text: '3 天' }),
        getProgressBarColor: () => 'bg-green-500',
        getTaskProgress: () => 50,
      },
    });

    await wrapper.find('.cursor-pointer').trigger('click');
    const actionButtons = wrapper.findAll('.shrink-0 button');
    await actionButtons[0].trigger('click');
    await actionButtons[1].trigger('click');

    expect(wrapper.emitted('view-timeline')?.length).toBe(1);
    expect(wrapper.emitted('edit-timeline')?.[0][0]).toMatchObject({ id: 1 });
    expect(wrapper.emitted('delete-timeline')?.[0]).toEqual([1]);
  });

  it('TimelineKanbanTaskModal emits form events', async () => {
    const task: Task = {
      task_id: 10,
      name: 'Kanban Task',
      completed: false,
      completed_at: null,
      timeline_id: 1,
      status: 'pending',
      priority: 2,
      tags: 'api,backend',
      estimated_hours: null,
      actual_hours: null,
      members: [],
      start_date: '2026-05-10',
      end_date: '2026-05-12',
      created_at: null,
      updated_at: null,
      task_remark: 'remark',
      isWork: 1,
      is_owner: true,
      subtasks: [
        {
          id: 1,
          task_id: 10,
          name: 'child',
          completed: false,
          sort_order: 1,
          created_at: null,
        },
      ],
    };

    const wrapper = mount(TimelineKanbanTaskModal, {
      props: {
        show: true,
        task,
        newSubtaskName: '',
        getSubtaskProgress: () => 0,
        getCompletedSubtaskCount: () => 0,
      },
    });

    await wrapper.find('select').trigger('change');
    await wrapper.find('input[type="text"]').setValue('tag-a,tag-b');
    await wrapper.find('input[type="checkbox"]').trigger('change');
    await wrapper.find('button').trigger('click');

    expect(wrapper.emitted('priority-select')).toBeTruthy();
    expect(wrapper.emitted('update:tags')?.[0]).toEqual(['tag-a,tag-b']);
    expect(wrapper.emitted('toggle-subtask')).toBeTruthy();
    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
