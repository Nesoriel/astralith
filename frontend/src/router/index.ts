import { createRouter, createWebHistory } from 'vue-router'

// 路由先覆盖毕业设计主演示链路，后续再逐页补齐业务功能。
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: () => import('../views/Dashboard.vue') },
    { path: '/hosts', component: () => import('../views/Hosts.vue') },
    { path: '/host-groups', component: () => import('../views/HostGroups.vue') },
    { path: '/operation-modules', component: () => import('../views/OperationModules.vue') },
    { path: '/tasks', component: () => import('../views/Tasks.vue') },
    { path: '/scheduled-jobs', component: () => import('../views/ScheduledJobs.vue') },
  ],
})
