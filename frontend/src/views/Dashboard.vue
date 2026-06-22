<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
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
        <p class="mt-2 text-2xl font-semibold">0</p>
      </el-card>
      <el-card>
        <p class="text-sm text-slate-500">{{ t('dashboard.tasks') }}</p>
        <p class="mt-2 text-2xl font-semibold">0</p>
      </el-card>
      <el-card>
        <p class="text-sm text-slate-500">{{ t('dashboard.success') }}</p>
        <p class="mt-2 text-2xl font-semibold">0</p>
      </el-card>
      <el-card>
        <p class="text-sm text-slate-500">{{ t('dashboard.scheduled') }}</p>
        <p class="mt-2 text-2xl font-semibold">0</p>
      </el-card>
    </section>
  </main>
</template>
