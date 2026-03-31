import { taskService } from '../services/taskService';
import type { TaskComment, TaskFile, TaskMember, Subtask } from '../types';

export interface TaskDetailResources {
  comments: TaskComment[];
  files: TaskFile[];
  subtasks: Subtask[];
}

export interface TaskDetailResourcesWithMembers extends TaskDetailResources {
  members: TaskMember[];
}

export const loadTaskDetailResources = async (taskId: number): Promise<TaskDetailResources> => {
  const [commentsRes, filesRes, subtasksRes] = await Promise.allSettled([
    taskService.getComments(taskId),
    taskService.getFiles(taskId),
    taskService.getSubtasks(taskId),
  ]);

  return {
    comments: commentsRes.status === 'fulfilled' ? commentsRes.value.data || [] : [],
    files: filesRes.status === 'fulfilled' ? filesRes.value.data || [] : [],
    subtasks: subtasksRes.status === 'fulfilled' ? subtasksRes.value.data || [] : [],
  };
};

export const loadTaskDetailResourcesWithMembers = async (taskId: number): Promise<TaskDetailResourcesWithMembers> => {
  const [resourcesRes, membersRes] = await Promise.allSettled([
    loadTaskDetailResources(taskId),
    taskService.getMembers(taskId),
  ]);

  const resources: TaskDetailResources = resourcesRes.status === 'fulfilled'
    ? resourcesRes.value
    : { comments: [], files: [], subtasks: [] };

  return {
    ...resources,
    members: membersRes.status === 'fulfilled' ? membersRes.value.data || [] : [],
  };
};

export const downloadFileFromUrl = async (url: string, originalFilename: string): Promise<void> => {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error('download failed');
  }

  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = originalFilename || 'download';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(blobUrl);
};
