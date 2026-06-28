<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { listHosts, type Host } from '../api/hosts'
import {
  createOperationModuleTask,
  listOperationModuleRecentTasks,
  listOperationModules,
  previewOperationTaskPlaybook,
  type LocalizedText,
  type OperationModule,
  type OperationTask,
  type PlaybookPreview,
} from '../api/operationModules'
import type { Task } from '../api/tasks'
import type { SupportedLocale } from '../i18n'

const { locale, t } = useI18n()
const modules = ref<OperationModule[]>([])
const hosts = ref<Host[]>([])
const recentTasks = ref<Task[]>([])
const selectedModuleKey = ref('')
const selectedTaskKey = ref('')
const targetIds = ref<number[]>([])
const taskName = ref('')
const parameterText = ref('{}')
const preview = ref<PlaybookPreview | null>(null)
const loading = ref(false)
const previewLoading = ref(false)

const activeLocale = computed(() => locale.value as SupportedLocale)
const selectedModule = computed(() => modules.value.find((item) => item.module_key === selectedModuleKey.value) ?? null)
const selectedTask = computed(() => selectedModule.value?.tasks.find((item) => item.task_key === selectedTaskKey.value) ?? null)

function localize(text: LocalizedText): string {
  return text[activeLocale.value] ?? text['zh-CN']
}

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2)
}

function exampleParameters(task: OperationTask | null): Record<string, unknown> {
  if (!task) return {}
  const result: Record<string, unknown> = {}
  for (const key of Object.keys(task.parameters ?? {})) {
    result[key] = key === 'service_name' ? 'nginx' : ''
  }
  return result
}

async function loadRecentTasks(): Promise<void> {
  if (!selectedModuleKey.value) return
  recentTasks.value = await listOperationModuleRecentTasks(selectedModuleKey.value)
}

function selectModule(moduleKey: string): void {
  selectedModuleKey.value = moduleKey
  selectedTaskKey.value = modules.value.find((item) => item.module_key === moduleKey)?.tasks[0]?.task_key ?? ''
}

async function loadData(): Promise<void> {
  loading.value = true
  try {
    const [moduleList, hostList] = await Promise.all([listOperationModules(), listHosts()])
    modules.value = moduleList
    hosts.value = hostList
    if (!selectedModuleKey.value && moduleList[0]) selectModule(moduleList[0].module_key)
    if (targetIds.value.length === 0 && hostList[0]) targetIds.value = [hostList[0].id]
    await loadRecentTasks()
  } finally {
    loading.value = false
  }
}

async function runPreview(): Promise<void> {
  if (!selectedModule.value || !selectedTask.value) return
  previewLoading.value = true
  try {
    const parameters = JSON.parse(parameterText.value) as Record<string, unknown>
    preview.value = await previewOperationTaskPlaybook(selectedModule.value.module_key, selectedTask.value.task_key, parameters)
  } finally {
    previewLoading.value = false
  }
}

async function submitQuickTask(): Promise<void> {
  if (!selectedModule.value || !selectedTask.value) return
  const parameters = JSON.parse(parameterText.value) as Record<string, unknown>
  await createOperationModuleTask(selectedModule.value.module_key, selectedTask.value.task_key, {
    name: taskName.value || localize(selectedTask.value.name),
    target_type: 'hosts',
    target_ids: targetIds.value,
    parameters,
  })
  ElMessage.success(t('pages.operationModules.taskCreated'))
  await loadRecentTasks()
}

watch(selectedTask, (task) => {
  parameterText.value = JSON.stringify(exampleParameters(task), null, 2)
  taskName.value = task ? localize(task.name) : ''
  preview.value = null
}, { immediate: true })

watch(selectedModuleKey, loadRecentTasks)

onMounted(loadData)
</script>

<template>
  <main class="space-y-4">
    <section class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold">{{ t('pages.operationModules.title') }}</h1>
        <p class="mt-2 text-slate-600">{{ t('pages.operationModules.description') }}</p>
      </div>
      <el-button :loading="loading" @click="loadData">{{ t('common.refresh') }}</el-button>
    </section>

    <section class="grid gap-4 lg:grid-cols-[300px_1fr]">
      <el-card>
        <template #header>{{ t('pages.operationModules.catalog') }}</template>
        <div class="space-y-2">
          <button
            v-for="module in modules"
            :key="module.module_key"
            class="w-full rounded border p-3 text-left hover:bg-slate-50"
            :class="module.module_key === selectedModuleKey ? 'border-blue-500 bg-blue-50' : 'border-slate-200'"
            @click="selectModule(module.module_key)"
          >
            <p class="font-medium">{{ localize(module.name) }}</p>
            <p class="text-xs text-slate-500">{{ module.module_key }} · {{ module.tasks.length }} {{ t('dashboard.operationTasks') }}</p>
          </button>
        </div>
      </el-card>

      <div class="space-y-4">
        <el-card v-if="selectedModule">
          <template #header>{{ localize(selectedModule.name) }}</template>
          <p class="mb-4 text-slate-600">{{ localize(selectedModule.description) }}</p>
          <el-tabs v-model="selectedTaskKey">
            <el-tab-pane v-for="task in selectedModule.tasks" :key="task.task_key" :name="task.task_key" :label="localize(task.name)" />
          </el-tabs>
          <div v-if="selectedTask" class="grid gap-4 lg:grid-cols-2">
            <el-card shadow="never">
              <template #header>{{ t('pages.operationModules.taskDetail') }}</template>
              <el-descriptions border :column="1">
                <el-descriptions-item label="task_key">{{ selectedTask.task_key }}</el-descriptions-item>
                <el-descriptions-item :label="t('fields.description')">{{ localize(selectedTask.description) }}</el-descriptions-item>
              </el-descriptions>
              <p class="mt-4 font-medium">{{ t('fields.parameterSchema') }}</p>
              <pre class="mt-2 max-h-56 overflow-auto rounded bg-slate-100 p-3 text-xs">{{ formatJson(selectedTask.parameters) }}</pre>
            </el-card>

            <el-card shadow="never">
              <template #header>{{ t('pages.operationModules.quickExecute') }}</template>
              <el-form label-width="120px">
                <el-form-item :label="t('fields.name')"><el-input v-model="taskName" /></el-form-item>
                <el-form-item :label="t('fields.targets')">
                  <el-select v-model="targetIds" multiple class="w-full">
                    <el-option v-for="host in hosts" :key="host.id" :label="host.name" :value="host.id" />
                  </el-select>
                </el-form-item>
                <el-form-item :label="t('fields.parameters')"><el-input v-model="parameterText" type="textarea" :rows="5" /></el-form-item>
              </el-form>
              <div class="flex gap-2">
                <el-button :loading="previewLoading" @click="runPreview">{{ t('pages.operationModules.previewPlaybook') }}</el-button>
                <el-button type="primary" @click="submitQuickTask">{{ t('common.execute') }}</el-button>
              </div>
            </el-card>
          </div>
        </el-card>

        <el-card v-if="preview">
          <template #header>{{ t('pages.operationModules.playbookPreview') }}</template>
          <pre class="max-h-80 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">{{ formatJson(preview.playbook) }}</pre>
        </el-card>

        <el-card>
          <template #header>{{ t('pages.operationModules.recentTasks') }}</template>
          <el-table :data="recentTasks" empty-text="-">
            <el-table-column prop="id" :label="t('fields.id')" width="80" />
            <el-table-column prop="name" :label="t('fields.name')" />
            <el-table-column prop="module_task_key" :label="t('fields.moduleTask')" />
            <el-table-column prop="status" :label="t('fields.status')" />
            <el-table-column prop="created_at" :label="t('fields.createdAt')" />
          </el-table>
        </el-card>
      </div>
    </section>
  </main>
</template>
