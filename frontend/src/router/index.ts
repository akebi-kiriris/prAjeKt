import { createRouter, createWebHistory } from 'vue-router';
import type { NavigationGuardReturn, RouteRecordRaw } from 'vue-router';

import GroupsView from '../views/GroupsView.vue';
import HomeView from '../views/HomeView.vue';
import KnowledgeBaseView from '../views/KnowledgeBaseView.vue';
import LoginView from '../views/LoginView.vue';
import ProfileView from '../views/ProfileView.vue';
import RegisterView from '../views/RegisterView.vue';
import TasksView from '../views/TasksView.vue';
import TimelinesView from '../views/TimelinesView.vue';
import TodosView from '../views/TodosView.vue';
import TrashView from '../views/TrashView.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
  },
  {
    path: '/timelines',
    name: 'Timelines',
    component: TimelinesView,
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge',
    name: 'KnowledgeBase',
    component: KnowledgeBaseView,
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: TasksView,
    meta: { requiresAuth: true },
  },
  {
    path: '/todos',
    name: 'Todos',
    component: TodosView,
    meta: { requiresAuth: true },
  },
  {
    path: '/groups',
    name: 'Groups',
    component: GroupsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    meta: { requiresAuth: true },
  },
  {
    path: '/trash',
    name: 'Trash',
    component: TrashView,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to): NavigationGuardReturn => {
  const token = localStorage.getItem('access_token');

  if (to.meta.requiresAuth && !token) {
    return '/login';
  }

  if (to.path === '/login' && token) {
    return '/';
  }

  return true;
});

export default router;
