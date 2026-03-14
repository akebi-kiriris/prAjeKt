import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Todo, CreateTodoPayload, UpdateTodoPayload } from '../types';
import { todoService } from '../services/todoService';
import { mapToCreateTodoPayload, mapToUpdateTodoPayload } from '../utils/payloadMappers';

export const useTodoStore = defineStore('todos', () => {
  const todos = ref<Todo[]>([]);
  const loading = ref(false);

  const incompleteTodos = computed(() => todos.value.filter(t => !t.completed));
  const completedTodos = computed(() => todos.value.filter(t => t.completed));

  async function fetchTodos(): Promise<void> {
    loading.value = true;
    try {
      const res = await todoService.getAll();
      todos.value = res.data;
    } catch (error) {
      console.error('取得待辦事項失敗:', error);
    } finally {
      loading.value = false;
    }
  }

  async function addTodo(data: CreateTodoPayload): Promise<void> {
    const payload = mapToCreateTodoPayload(data);
    await todoService.create(payload);
    await fetchTodos();
  }

  async function updateTodo(id: number, data: UpdateTodoPayload): Promise<void> {
    const payload = mapToUpdateTodoPayload(data);
    if (Object.keys(payload).length === 0) {
      return;
    }
    await todoService.update(id, payload);
    await fetchTodos();
  }

  async function removeTodo(id: number): Promise<void> {
    await todoService.remove(id);
    await fetchTodos();
  }

  async function toggleTodo(id: number): Promise<void> {
    await todoService.toggleComplete(id);
    await fetchTodos();
  }

  return {
    todos,
    incompleteTodos,
    completedTodos,
    fetchTodos,
    addTodo,
    updateTodo,
    removeTodo,
    toggleTodo,
  };
});
