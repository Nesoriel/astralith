<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { listOperationModules, type LocalizedText, type OperationModule } from '../api/operationModules'
import type { SupportedLocale } from '../i18n'

const { locale, t } = useI18n()
const modules = ref<OperationModule[]>([])
const activeLocale = computed(() => locale.value as SupportedLocale)

function localize(text: LocalizedText): string {
  // 后端模块元数据也按同一套 locale 展示，避免中英文混杂。
  return text[activeLocale.value] ?? text['zh-CN']
}

onMounted(async () => {
  modules.value = await listOperationModules()
})
</script>

<template>
  <main class="space-y-4">
    <h1 class="text-2xl font-semibold">{{ t('pages.operationModules.title') }}</h1>
    <el-empty v-if="modules.length === 0" :description="t('pages.operationModules.empty')" />
    <el-card v-for="module in modules" :key="module.module_key" class="mb-4">
      <template #header>{{ localize(module.name) }}</template>
      <p class="mb-3 text-slate-600">{{ localize(module.description) }}</p>
      <el-tag v-for="task in module.tasks" :key="task.task_key" class="mb-2 mr-2">
        {{ localize(task.name) }}
      </el-tag>
    </el-card>
  </main>
</template>
