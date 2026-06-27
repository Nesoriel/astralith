<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { getDashboardSummary, type DashboardSummary } from '../api/dashboard'

const { t } = useI18n()
const router = useRouter()
const loading = ref(false)
const summary = ref<DashboardSummary>({
  hosts: 0,
  host_groups: 0,
  operation_modules: 0,
  operation_tasks: 0,
  tasks_total: 0,
  tasks_failed: 0,
  tasks_success_rate: 0,
  scheduled_jobs: 0,
  gitops_repositories: 0,
  resource_diffs: 0,
  pending_apply_plans: 0,
  blocked_policy_results: 0,
  ai_analyses: 0,
  pending_ai_proposals: 0,
  pending_module_proposals: 0,
})

interface MetricCard {
  label: string
  value: number | string
  route: string
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function go(route: string): void {
  void router.push(route)
}

async function loadSummary(): Promise<void> {
  loading.value = true
  try {
    summary.value = await getDashboardSummary()
  } finally {
    loading.value = false
  }
}

function operationsCards(): MetricCard[] {
  return [
    { label: t('dashboard.hosts'), value: summary.value.hosts, route: '/hosts' },
    { label: t('dashboard.hostGroups'), value: summary.value.host_groups, route: '/host-groups' },
    { label: t('dashboard.operationModules'), value: summary.value.operation_modules, route: '/operation-modules' },
    { label: t('dashboard.operationTasks'), value: summary.value.operation_tasks, route: '/operation-modules' },
    { label: t('dashboard.tasks'), value: summary.value.tasks_total, route: '/tasks' },
    { label: t('dashboard.taskSuccessRate'), value: percent(summary.value.tasks_success_rate), route: '/tasks' },
    { label: t('dashboard.failedTasks'), value: summary.value.tasks_failed, route: '/tasks' },
    { label: t('dashboard.scheduled'), value: summary.value.scheduled_jobs, route: '/scheduled-jobs' },
  ]
}

function gitopsCards(): MetricCard[] {
  return [
    { label: t('dashboard.gitopsRepositories'), value: summary.value.gitops_repositories, route: '/gitops-repositories' },
    { label: t('dashboard.resourceDiffs'), value: summary.value.resource_diffs, route: '/gitops-diff' },
    { label: t('dashboard.pendingApplyPlans'), value: summary.value.pending_apply_plans, route: '/gitops-diff' },
    { label: t('dashboard.blockedPolicies'), value: summary.value.blocked_policy_results, route: '/gitops-diff' },
  ]
}

function proposalCards(): MetricCard[] {
  return [
    { label: t('dashboard.aiAnalyses'), value: summary.value.ai_analyses, route: '/tasks' },
    { label: t('dashboard.pendingAiProposals'), value: summary.value.pending_ai_proposals, route: '/ai-proposals' },
    { label: t('dashboard.pendingModuleProposals'), value: summary.value.pending_module_proposals, route: '/operation-module-proposals' },
  ]
}

onMounted(loadSummary)
</script>

<template>
  <main class="space-y-6">
    <section class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-slate-900">{{ t('dashboard.title') }}</h1>
        <p class="mt-2 text-slate-600">{{ t('dashboard.description') }}</p>
      </div>
      <el-button :loading="loading" @click="loadSummary">{{ t('common.refresh') }}</el-button>
    </section>

    <el-card>
      <template #header>{{ t('dashboard.operationsSection') }}</template>
      <section class="grid gap-4 md:grid-cols-4">
        <el-card v-for="card in operationsCards()" :key="card.label" shadow="hover" class="cursor-pointer" @click="go(card.route)">
          <p class="text-sm text-slate-500">{{ card.label }}</p>
          <p class="mt-2 text-2xl font-semibold">{{ card.value }}</p>
        </el-card>
      </section>
    </el-card>

    <el-card>
      <template #header>{{ t('dashboard.gitopsSection') }}</template>
      <section class="grid gap-4 md:grid-cols-4">
        <el-card v-for="card in gitopsCards()" :key="card.label" shadow="hover" class="cursor-pointer" @click="go(card.route)">
          <p class="text-sm text-slate-500">{{ card.label }}</p>
          <p class="mt-2 text-2xl font-semibold">{{ card.value }}</p>
        </el-card>
      </section>
    </el-card>

    <el-card>
      <template #header>{{ t('dashboard.aiSection') }}</template>
      <section class="grid gap-4 md:grid-cols-3">
        <el-card v-for="card in proposalCards()" :key="card.label" shadow="hover" class="cursor-pointer" @click="go(card.route)">
          <p class="text-sm text-slate-500">{{ card.label }}</p>
          <p class="mt-2 text-2xl font-semibold">{{ card.value }}</p>
        </el-card>
      </section>
    </el-card>
  </main>
</template>
