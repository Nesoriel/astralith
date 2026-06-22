<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { listHosts, type Host } from '../api/hosts'
import {
  createScheduledJob,
  disableScheduledJob,
  enableScheduledJob,
  listScheduledJobs,
  triggerScheduledJob,
  type ScheduledJob,
  type ScheduledJobPayload,
} from '../api/scheduledJobs'

const { t } = useI18n()
const hosts = ref<Host[]>([])
const jobs = ref<ScheduledJob[]>([])
const form = ref<ScheduledJobPayload>({
  name: t('defaults.scheduledJobName'),
  module_key: 'system_inspection',
  module_task_key: 'check_disk',
  target_type: 'hosts',
  target_ids: [],
  parameters: {},
  schedule_type: 'interval',
  interval_seconds: 3600,
  cron_expression: null,
  enabled: true,
})

async function loadData(): Promise<void> {
  const [hostList, jobList] = await Promise.all([listHosts(), listScheduledJobs()])
  hosts.value = hostList
  jobs.value = jobList
  if (form.value.target_ids.length === 0 && hostList[0]) {
    form.value.target_ids = [hostList[0].id]
  }
}

async function submitJob(): Promise<void> {
  await createScheduledJob(form.value)
  ElMessage.success(t('common.success'))
  await loadData()
}

async function setEnabled(job: ScheduledJob, enabled: boolean): Promise<void> {
  if (enabled) {
    await enableScheduledJob(job.id)
  } else {
    await disableScheduledJob(job.id)
  }
  ElMessage.success(t('common.success'))
  await loadData()
}

async function triggerJob(job: ScheduledJob): Promise<void> {
  const result = await triggerScheduledJob(job.id)
  ElMessage.success(t('pages.tasks.triggerCreated', { id: result.task_id }))
  await loadData()
}

onMounted(loadData)
</script>

<template>
  <main class="space-y-4">
    <section>
      <h1 class="text-2xl font-semibold">{{ t('pages.scheduledJobs.title') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('pages.scheduledJobs.description') }}</p>
    </section>

    <el-card>
      <template #header>{{ t('pages.scheduledJobs.createTitle') }}</template>
      <el-form :model="form" label-width="140px" class="grid gap-2 md:grid-cols-2">
        <el-form-item :label="t('fields.name')"><el-input v-model="form.name" /></el-form-item>
        <el-form-item :label="t('fields.targets')">
          <el-select v-model="form.target_ids" multiple class="w-full">
            <el-option v-for="host in hosts" :key="host.id" :label="host.name" :value="host.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('fields.scheduleType')">
          <el-select v-model="form.schedule_type" class="w-full">
            <el-option label="interval" value="interval" />
            <el-option label="cron" value="cron" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.schedule_type === 'interval'" :label="t('fields.intervalSeconds')">
          <el-input-number v-model="form.interval_seconds" :min="1" class="w-full" />
        </el-form-item>
        <el-form-item v-else :label="t('fields.cronExpression')">
          <el-input v-model="form.cron_expression" placeholder="0 2 * * *" />
        </el-form-item>
      </el-form>
      <el-button type="primary" @click="submitJob">{{ t('common.create') }}</el-button>
    </el-card>

    <el-card>
      <template #header>{{ t('nav.scheduledJobs') }}</template>
      <el-table :data="jobs" empty-text="-">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="name" :label="t('fields.name')" />
        <el-table-column prop="schedule_type" :label="t('fields.scheduleType')" />
        <el-table-column :label="t('fields.enabled')">
          <template #default="scope">{{ scope.row.enabled ? t('common.enabled') : t('common.disabled') }}</template>
        </el-table-column>
        <el-table-column :label="t('common.actions')" width="260">
          <template #default="scope">
            <el-button size="small" @click="triggerJob(scope.row)">{{ t('common.trigger') }}</el-button>
            <el-button v-if="scope.row.enabled" size="small" @click="setEnabled(scope.row, false)">{{ t('common.disable') }}</el-button>
            <el-button v-else size="small" @click="setEnabled(scope.row, true)">{{ t('common.enable') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </main>
</template>
