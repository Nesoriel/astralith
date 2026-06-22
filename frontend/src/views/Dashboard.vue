<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { listHosts } from '../api/hosts'
import { listScheduledJobs } from '../api/scheduledJobs'
import { listTasks } from '../api/tasks'

const { t } = useI18n()
const hostCount = ref(0)
const taskCount = ref(0)
const successCount = ref(0)
const scheduledCount = ref(0)

async function loadSummary(): Promise<void> {
  // v0.1.0 使用轻量列表接口聚合仪表盘数据，后续可替换为专用 summary API。
  const [hosts, tasks, scheduledJobs] = await Promise.all([listHosts(), listTasks(), listScheduledJobs()])
  hostCount.value = hosts.length
  taskCount.value = tasks.length
  successCount.value = tasks.filter((task) => task.status === 'success').length
  scheduledCount.value = scheduledJobs.length
}

onMounted(loadSummary)
</script>

<template>
  <main class="space-y-6">
    <section>
      <h1 class="text-2xl font-semibold text-slate-900">{{ t('dashboard.title') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('dashboard.description') }}</p>
    </section>
    <section class="grid gap-4 md:grid-cols-4">
      <el-card>
        <p class="text-sm text-slate-500">{{ t('dashboard.hosts') }}</p>
        <p class="mt-2 text-2xl font-semibold">{{ hostCount }}</p>
      </el-card>
      <el-card>
        <p class="text-sm text-slate-500">{{ t('dashboard.tasks') }}</p>
        <p class="mt-2 text-2xl font-semibold">{{ taskCount }}</p>
      </el-card>
      <el-card>
        <p class="text-sm text-slate-500">{{ t('dashboard.success') }}</p>
        <p class="mt-2 text-2xl font-semibold">{{ successCount }}</p>
      </el-card>
      <el-card>
        <p class="text-sm text-slate-500">{{ t('dashboard.scheduled') }}</p>
        <p class="mt-2 text-2xl font-semibold">{{ scheduledCount }}</p>
      </el-card>
    </section>
  </main>
</template>
