import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Task, CreateTaskPayload, TaskUpdatePayload, Subtask } from '../types';
import { taskService } from '../services/taskService';
import { mapToCreateTaskPayload, mapToUpdateTaskPayload } from '../utils/payloadMappers';

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([]);
  const loading = ref(false);

  async function fetchTasks(): Promise<void> {
    loading.value = true;
    const response = await taskService.getAll();
    tasks.value = response.data;
    loading.value = false;
  }

  async function addTask(data: CreateTaskPayload): Promise<void> {
    const formData = mapToCreateTaskPayload(data);
    await taskService.create(formData);
    await fetchTasks();
  }

  async function updateTask(id: number, data: TaskUpdatePayload): Promise<void> {
    const formData = mapToUpdateTaskPayload(data);

    if (Object.keys(formData).length === 0) {
      return;
    }

    await taskService.update(id, formData);
    await fetchTasks();
  }

  async function removeTask(id: number): Promise<void> {
    await taskService.remove(id);
    await fetchTasks();
  }

  async function toggleTask(id: number): Promise<void> {
    await taskService.toggle(id);
    await fetchTasks();
  }

  async function updateTaskStatus(id: number, status: Task['status']): Promise<void> {
    await taskService.updateStatus(id, status);
    await fetchTasks();
  }

  async function getSubtasks(id: number): Promise<Subtask[]> {
    const response = await taskService.getSubtasks(id);
    return response.data;
  }

  async function addSubtask(taskId: number, data: Pick<Subtask, 'name'>): Promise<void> {
    await taskService.createSubtask(taskId, data);
    await fetchTasks();
  }

  async function toggleSubtask(taskId: number, subtaskId: number): Promise<void> {
    await taskService.toggleSubtask(taskId, subtaskId);
    await fetchTasks();
  }

  async function removeSubtask(taskId: number, subtaskId: number): Promise<void> {
    await taskService.deleteSubtask(taskId, subtaskId);
    await fetchTasks();
  }

  return {
    tasks,
    loading,
    fetchTasks,
    addTask,
    updateTask,
    removeTask,
    toggleTask,
    updateTaskStatus,
    getSubtasks,
    addSubtask,
    toggleSubtask,
    removeSubtask,
  };
});
