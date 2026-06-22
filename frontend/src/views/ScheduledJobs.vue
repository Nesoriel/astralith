<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <main class="space-y-4">
    <h1 class="text-2xl font-semibold">{{ t('pages.scheduledJobs.title') }}</h1>
    <el-card>{{ t('pages.scheduledJobs.description') }}</el-card>
  </main>
</template>
