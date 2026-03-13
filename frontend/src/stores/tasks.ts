import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Task, CreateTaskPayload, Subtask } from '../types';
import { taskService } from '../services/taskService';

type TaskFormPayload = CreateTaskPayload & Partial<Task>;

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([]);
  const loading = ref(false);

  async function fetchTasks(): Promise<void> {
    loading.value = true;
    const response = await taskService.getAll();
    tasks.value = response.data;
    loading.value = false;
  }

  async function addTask(data: TaskFormPayload): Promise<void> {
    const formData: TaskFormPayload = {
      ...data,
      start_date: data.start_date || null,
      end_date: data.end_date || null,
    };

    await taskService.create(formData);
    await fetchTasks();
  }

  async function updateTask(id: number, data: TaskFormPayload): Promise<void> {
    const formData: TaskFormPayload = {
      ...data,
      start_date: data.start_date || null,
      end_date: data.end_date || null,
    };

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
