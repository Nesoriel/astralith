<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <main class="space-y-4">
    <h1 class="text-2xl font-semibold">{{ t('pages.hostGroups.title') }}</h1>
    <el-card>{{ t('pages.hostGroups.description') }}</el-card>
  </main>
</template>
