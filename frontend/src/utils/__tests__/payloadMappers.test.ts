import { describe, expect, it } from 'vitest';
import {
  mapToCreateTaskPayload,
  mapToUpdateTaskPayload,
  mapToCreateTodoPayload,
  mapToUpdateTodoPayload,
} from '../payloadMappers';

describe('payloadMappers', () => {
  it('mapToCreateTaskPayload should normalize fields and convert types', () => {
    const payload = mapToCreateTaskPayload({
      name: '  Task A  ',
      start_date: '2026-03-01T10:00:00',
      end_date: '2026-03-03T10:00:00',
      task_remark: null,
      priority: '2',
      tags: ['x'],
      timeline_id: 9,
    } as never);

    expect(payload).toEqual({
      name: 'Task A',
      start_date: '2026-03-01',
      end_date: '2026-03-03',
      task_remark: null,
      priority: 2,
      tags: ['x'],
      timeline_id: 9,
    });
  });

  it('mapToCreateTaskPayload should keep minimal payload when optional keys are absent', () => {
    const payload = mapToCreateTaskPayload({
      name: 'Task B',
    } as never);

    expect(payload).toEqual({ name: 'Task B' });
  });

  it('mapToUpdateTaskPayload should only include owned keys and normalize nullables', () => {
    const payload = mapToUpdateTaskPayload({
      name: '  New Name  ',
      timeline_id: 3,
      priority: '5',
      status: 'done',
      tags: null,
      estimated_hours: 8,
      actual_hours: 6,
      task_remark: undefined,
      isWork: true,
      start_date: '',
      end_date: '2026-03-08T12:00:00',
    } as never);

    expect(payload).toEqual({
      name: 'New Name',
      timeline_id: 3,
      priority: 5,
      status: 'done',
      tags: null,
      estimated_hours: 8,
      actual_hours: 6,
      task_remark: null,
      isWork: true,
      start_date: null,
      end_date: '2026-03-08',
    });
  });

  it('mapToUpdateTaskPayload should preserve explicit invalid priority as undefined when key exists', () => {
    const payload = mapToUpdateTaskPayload({ priority: 'abc' } as never);

    expect(Object.prototype.hasOwnProperty.call(payload, 'priority')).toBe(true);
    expect(payload.priority).toBeUndefined();
  });

  it('mapToCreateTodoPayload should normalize title/deadline/priority', () => {
    const payload = mapToCreateTodoPayload({
      title: '  Todo A  ',
      content: 'detail',
      type: 'study',
      deadline: '2026-03-28T09:30',
      priority: '3',
    } as never);

    expect(payload).toEqual({
      title: 'Todo A',
      content: 'detail',
      type: 'study',
      deadline: '2026-03-28T09:30:00',
      priority: 3,
    });
  });

  it('mapToUpdateTodoPayload should include explicit nullable keys', () => {
    const payload = mapToUpdateTodoPayload({
      title: '  X  ',
      content: 'C',
      type: undefined,
      deadline: '',
      priority: 'bad',
      completed: true,
    } as never);

    expect(payload).toEqual({
      title: 'X',
      content: 'C',
      type: null,
      deadline: null,
      priority: undefined,
      completed: true,
    });
  });
});
