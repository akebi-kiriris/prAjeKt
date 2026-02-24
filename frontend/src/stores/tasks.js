import { defineStore } from 'pinia';
import { ref } from 'vue';
import { taskService } from '../services/taskService';

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref([]);
  const loading = ref(false);

  async function fetchTasks() {
    loading.value = true;
    const response = await taskService.getAll();
    tasks.value = response.data;
    loading.value = false;
  }

  async function addTask(data) {
    const assistantArray = data.assistant 
      ? data.assistant.split(',').map(s => s.trim()).filter(s => s)
      : [];
    
    const formData = {
      ...data,
      assistant: assistantArray,
      start_date: data.start_date || null,
      end_date: data.end_date || null,
    };
    
    await taskService.create(formData);
    await fetchTasks();
  }

  async function updateTask(id, data) {
    const assistantArray = data.assistant 
      ? data.assistant.split(',').map(s => s.trim()).filter(s => s)
      : [];
    
    const formData = {
      ...data,
      assistant: assistantArray,
      start_date: data.start_date || null,
      end_date: data.end_date || null,
    };
    
    await taskService.update(id, formData);
    await fetchTasks();
  }

  async function removeTask(id) {
    await taskService.remove(id);
    await fetchTasks();
  }

  async function toggleTask(id) {
    await taskService.toggle(id);
    await fetchTasks();
  }

  async function updateTaskStatus(id, status) {
    await taskService.updateStatus(id, status);
    await fetchTasks();
  }

  // Subtasks operations
  async function getSubtasks(id) {
    const response = await taskService.getSubtasks(id);
    return response.data;
  }

  async function addSubtask(taskId, data) {
    await taskService.createSubtask(taskId, data);
    await fetchTasks();
  }

  async function toggleSubtask(taskId, subtaskId) {
    await taskService.toggleSubtask(taskId, subtaskId);
    await fetchTasks();
  }

  async function removeSubtask(taskId, subtaskId) {
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
