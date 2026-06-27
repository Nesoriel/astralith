import { createRouter, createWebHistory } from 'vue-router'

import { isAuthenticated } from '../api/auth'

// 路由先覆盖毕业设计主演示链路，后续再逐页补齐业务功能。
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', component: () => import('../views/Login.vue'), meta: { public: true } },
    { path: '/dashboard', component: () => import('../views/Dashboard.vue') },
    { path: '/hosts', component: () => import('../views/Hosts.vue') },
    { path: '/host-groups', component: () => import('../views/HostGroups.vue') },
    { path: '/operation-modules', component: () => import('../views/OperationModules.vue') },
    { path: '/tasks', component: () => import('../views/Tasks.vue') },
    { path: '/scheduled-jobs', component: () => import('../views/ScheduledJobs.vue') },
    { path: '/gitops-repositories', component: () => import('../views/GitOpsRepositories.vue') },
    { path: '/gitops-diff', component: () => import('../views/GitOpsDiffCenter.vue') },
    { path: '/ai-proposals', component: () => import('../views/AiProposals.vue') },
  ],
})

router.beforeEach((to) => {
  // v0.3.0 先用轻量前端守卫保护主演示页面；后端写接口会继续补 JWT 依赖。
  if (to.meta.public === true) {
    return isAuthenticated() ? '/dashboard' : true
  }
  return isAuthenticated() ? true : { path: '/login', query: { redirect: to.fullPath } }
})
