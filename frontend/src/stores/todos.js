import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { todoService } from '../services/todoService';

export const useTodoStore = defineStore('todos', () => {
  const todos = ref([]);
  const loading = ref(false);

  const incompleteTodos = computed(() => todos.value.filter(t => !t.completed));
  const completedTodos = computed(() => todos.value.filter(t => t.completed));

  async function fetchTodos() {
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

  async function addTodo(data) {
    await todoService.create(data);
    await fetchTodos();
  }

  async function updateTodo(id, data) {
    await todoService.update(id, data);
    await fetchTodos();
  }

  async function removeTodo(id) {
    await todoService.remove(id);
    await fetchTodos();
  }

  async function toggleTodo(id) {
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
