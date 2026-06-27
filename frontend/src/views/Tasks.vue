<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { listHosts, type Host } from '../api/hosts'
import { listOperationModules, type LocalizedText, type OperationModule } from '../api/operationModules'
import { createTask, createTaskAiAnalysis, getTaskLogs, listTasks, type Task, type TaskLogs, type TaskPayload } from '../api/tasks'
import type { SupportedLocale } from '../i18n'

const { locale, t } = useI18n()
const hosts = ref<Host[]>([])
const modules = ref<OperationModule[]>([])
const tasks = ref<Task[]>([])
const logs = ref<TaskLogs | null>(null)
const logsVisible = ref(false)
const loading = ref(false)
const logsLoading = ref(false)
const analysisLoading = ref(false)
const form = ref<TaskPayload>({
  name: t('defaults.taskName'),
  module_key: 'system_inspection',
  module_task_key: 'check_disk',
  target_type: 'hosts',
  target_ids: [],
  parameters: {},
})

const activeLocale = computed(() => locale.value as SupportedLocale)
const selectedModule = computed(() => modules.value.find((item) => item.module_key === form.value.module_key))

function localize(text: LocalizedText): string {
  // 模块元数据来自后端，同样按当前 locale 展示。
  return text[activeLocale.value] ?? text['zh-CN']
}

function statusTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'success') return 'success'
  if (status === 'partial_success' || status === 'running') return 'warning'
  if (status === 'failed' || status === 'cancelled') return 'danger'
  return 'info'
}

async function loadData(): Promise<void> {
  loading.value = true
  try {
    const [hostList, moduleList, taskList] = await Promise.all([listHosts(), listOperationModules(), listTasks()])
    hosts.value = hostList
    modules.value = moduleList
    tasks.value = taskList
    if (form.value.target_ids.length === 0 && hostList[0]) {
      form.value.target_ids = [hostList[0].id]
    }
  } finally {
    loading.value = false
  }
}

async function submitTask(): Promise<void> {
  await createTask(form.value)
  ElMessage.success(t('common.success'))
  await loadData()
}

async function openLogs(task: Task): Promise<void> {
  logsVisible.value = true
  logsLoading.value = true
  try {
    logs.value = await getTaskLogs(task.id)
  } finally {
    logsLoading.value = false
  }
}

async function analyzeTask(): Promise<void> {
  if (!logs.value) return
  analysisLoading.value = true
  try {
    await createTaskAiAnalysis(logs.value.task.id)
    logs.value = await getTaskLogs(logs.value.task.id)
    ElMessage.success(t('pages.tasks.analysisCreated'))
  } finally {
    analysisLoading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <main class="space-y-4">
    <section>
      <h1 class="text-2xl font-semibold">{{ t('pages.tasks.title') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('pages.tasks.description') }}</p>
    </section>

    <el-card>
      <template #header>{{ t('pages.tasks.createTitle') }}</template>
      <el-form :model="form" label-width="130px" class="grid gap-2 md:grid-cols-2">
        <el-form-item :label="t('fields.name')"><el-input v-model="form.name" /></el-form-item>
        <el-form-item :label="t('fields.module')">
          <el-select v-model="form.module_key" class="w-full">
            <el-option v-for="item in modules" :key="item.module_key" :label="localize(item.name)" :value="item.module_key" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('fields.moduleTask')">
          <el-select v-model="form.module_task_key" class="w-full">
            <el-option v-for="item in selectedModule?.tasks ?? []" :key="item.task_key" :label="localize(item.name)" :value="item.task_key" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('fields.targets')">
          <el-select v-model="form.target_ids" multiple class="w-full">
            <el-option v-for="host in hosts" :key="host.id" :label="host.name" :value="host.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-button type="primary" @click="submitTask">{{ t('common.create') }}</el-button>
    </el-card>

    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <span>{{ t('nav.tasks') }}</span>
          <el-button size="small" :loading="loading" @click="loadData">{{ t('common.refresh') }}</el-button>
        </div>
      </template>
      <el-table v-loading="loading" :data="tasks" empty-text="-">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="name" :label="t('fields.name')" />
        <el-table-column prop="module_key" :label="t('fields.module')" />
        <el-table-column prop="module_task_key" :label="t('fields.moduleTask')" />
        <el-table-column prop="status" :label="t('fields.status')">
          <template #default="scope">
            <el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('fields.targets')">
          <template #default="scope">{{ scope.row.target_ids.join(', ') }}</template>
        </el-table-column>
        <el-table-column :label="t('common.actions')" width="120">
          <template #default="scope">
            <el-button size="small" @click="openLogs(scope.row)">{{ t('pages.tasks.logs') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="logsVisible" :title="t('pages.tasks.logs')" size="60%">
      <div v-loading="logsLoading" class="min-h-40">
        <div v-if="logs" class="space-y-4">
          <el-descriptions border :column="2">
            <el-descriptions-item :label="t('fields.id')">{{ logs.task.id }}</el-descriptions-item>
            <el-descriptions-item :label="t('fields.status')">
              <el-tag :type="statusTagType(logs.task.status)">{{ logs.task.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="t('fields.module')">{{ logs.task.module_key }}</el-descriptions-item>
            <el-descriptions-item :label="t('fields.moduleTask')">{{ logs.task.module_task_key }}</el-descriptions-item>
            <el-descriptions-item :label="t('fields.startedAt')">{{ logs.task.started_at ?? '-' }}</el-descriptions-item>
            <el-descriptions-item :label="t('fields.finishedAt')">{{ logs.task.finished_at ?? '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-card shadow="never">
            <template #header>
              <div class="flex items-center justify-between">
                <span>{{ t('pages.tasks.aiAnalysis') }}</span>
                <el-button size="small" type="primary" :loading="analysisLoading" @click="analyzeTask">
                  {{ t('pages.tasks.runAnalysis') }}
                </el-button>
              </div>
            </template>
            <el-empty v-if="logs.ai_analyses.length === 0" :description="t('pages.tasks.noAnalysis')" />
            <div v-for="analysis in logs.ai_analyses" :key="analysis.id" class="space-y-3 rounded border border-slate-200 p-3">
              <div class="flex items-center justify-between gap-3">
                <p class="font-medium">{{ analysis.summary }}</p>
                <el-tag type="warning">{{ analysis.content.risk_level }}</el-tag>
              </div>
              <p class="text-xs text-slate-500">
                {{ analysis.model_name ?? '-' }} / {{ analysis.created_at }}
              </p>
              <div>
                <p class="font-medium">{{ t('pages.tasks.keyEvidence') }}</p>
                <ul class="list-disc pl-5 text-sm text-slate-700">
                  <li v-for="item in analysis.content.key_evidence" :key="item">{{ item }}</li>
                </ul>
              </div>
              <div>
                <p class="font-medium">{{ t('pages.tasks.possibleCauses') }}</p>
                <ul class="list-disc pl-5 text-sm text-slate-700">
                  <li v-for="item in analysis.content.possible_causes" :key="item">{{ item }}</li>
                </ul>
              </div>
              <div>
                <p class="font-medium">{{ t('pages.tasks.recommendedSteps') }}</p>
                <ol class="list-decimal pl-5 text-sm text-slate-700">
                  <li v-for="item in analysis.content.recommended_steps" :key="item">{{ item }}</li>
                </ol>
              </div>
              <el-alert
                v-for="note in analysis.content.review_notes"
                :key="note"
                :title="note"
                type="warning"
                :closable="false"
                show-icon
              />
            </div>
          </el-card>

          <el-empty v-if="logs.results.length === 0" :description="t('common.empty')" />
          <el-card v-for="result in logs.results" :key="result.id" shadow="never">
            <template #header>
              <div class="flex items-center justify-between">
                <span>{{ t('fields.host') }} #{{ result.host_id ?? '-' }}</span>
                <el-tag :type="statusTagType(result.status)">{{ result.status }}</el-tag>
              </div>
            </template>
            <div class="mb-3 text-sm text-slate-500">
              {{ t('fields.startedAt') }}: {{ result.started_at ?? '-' }} / {{ t('fields.finishedAt') }}: {{ result.finished_at ?? '-' }}
            </div>
            <p class="font-medium">{{ t('fields.stdout') }}</p>
            <pre class="overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">{{ result.stdout || '-' }}</pre>
            <p class="mt-3 font-medium">{{ t('fields.stderr') }}</p>
            <pre class="overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">{{ result.stderr || '-' }}</pre>
            <p class="mt-3 font-medium">{{ t('fields.rawEventData') }}</p>
            <pre class="overflow-auto rounded bg-slate-100 p-3 text-xs text-slate-800">{{ result.raw_event_data || '-' }}</pre>
          </el-card>
        </div>
      </div>
    </el-drawer>
  </main>
</template>
