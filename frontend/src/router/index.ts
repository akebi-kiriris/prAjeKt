import { createRouter, createWebHistory } from 'vue-router';
import type { NavigationGuardReturn, RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
  },
  {
    path: '/timelines',
    name: 'Timelines',
    component: () => import('../views/TimelinesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge',
    name: 'KnowledgeBase',
    component: () => import('../views/KnowledgeBaseView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('../views/TasksView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/todos',
    name: 'Todos',
    component: () => import('../views/TodosView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/groups',
    name: 'Groups',
    component: () => import('../views/GroupsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/trash',
    name: 'Trash',
    component: () => import('../views/TrashView.vue'),
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
