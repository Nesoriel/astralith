<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { localeLabels, persistLocale, supportedLocales, type SupportedLocale } from './i18n'

const { locale, t } = useI18n()

const activeLocale = computed({
  get: () => locale.value as SupportedLocale,
  set: (value: SupportedLocale) => {
    // 语言切换只影响前端展示文案，后续 API 错误信息再接入同一套 locale。
    locale.value = value
    persistLocale(value)
  },
})
</script>

<template>
  <!-- 主布局：左侧导航 + 右侧页面内容，先服务毕业设计演示路径。 -->
  <el-container class="min-h-screen">
    <el-aside width="220px" class="border-r border-slate-200 bg-white">
      <div class="px-5 py-4 text-lg font-semibold text-slate-900">{{ t('app.name') }}</div>
      <!-- Element Plus 菜单直接使用 vue-router 路由跳转。 -->
      <el-menu router default-active="/dashboard">
        <el-menu-item index="/dashboard">{{ t('nav.dashboard') }}</el-menu-item>
        <el-menu-item index="/hosts">{{ t('nav.hosts') }}</el-menu-item>
        <el-menu-item index="/host-groups">{{ t('nav.hostGroups') }}</el-menu-item>
        <el-menu-item index="/operation-modules">{{ t('nav.operationModules') }}</el-menu-item>
        <el-menu-item index="/tasks">{{ t('nav.tasks') }}</el-menu-item>
        <el-menu-item index="/scheduled-jobs">{{ t('nav.scheduledJobs') }}</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="flex items-center justify-end border-b border-slate-200 bg-white">
        <el-select v-model="activeLocale" class="w-36" size="small">
          <el-option
            v-for="item in supportedLocales"
            :key="item"
            :label="localeLabels[item]"
            :value="item"
          />
        </el-select>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
