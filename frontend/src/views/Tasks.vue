<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { listHosts, type Host } from '../api/hosts'
import { listOperationModules, type LocalizedText, type OperationModule } from '../api/operationModules'
import { createTask, listTasks, type Task, type TaskPayload } from '../api/tasks'
import type { SupportedLocale } from '../i18n'

const { locale, t } = useI18n()
const hosts = ref<Host[]>([])
const modules = ref<OperationModule[]>([])
const tasks = ref<Task[]>([])
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

async function loadData(): Promise<void> {
  const [hostList, moduleList, taskList] = await Promise.all([listHosts(), listOperationModules(), listTasks()])
  hosts.value = hostList
  modules.value = moduleList
  tasks.value = taskList
  if (form.value.target_ids.length === 0 && hostList[0]) {
    form.value.target_ids = [hostList[0].id]
  }
}

async function submitTask(): Promise<void> {
  await createTask(form.value)
  ElMessage.success(t('common.success'))
  await loadData()
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
      <template #header>{{ t('nav.tasks') }}</template>
      <el-table :data="tasks" empty-text="-">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="name" :label="t('fields.name')" />
        <el-table-column prop="module_key" :label="t('fields.module')" />
        <el-table-column prop="module_task_key" :label="t('fields.moduleTask')" />
        <el-table-column prop="status" :label="t('fields.status')" />
        <el-table-column :label="t('fields.targets')">
          <template #default="scope">{{ scope.row.target_ids.join(', ') }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </main>
</template>
