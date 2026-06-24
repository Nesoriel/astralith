<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { login } from '../api/auth'

const { t } = useI18n()
const router = useRouter()
const loading = ref(false)
const form = ref({
  username: 'admin',
  password: 'admin123',
})

async function submitLogin(): Promise<void> {
  loading.value = true
  try {
    await login(form.value)
    ElMessage.success(t('auth.loginSuccess'))
    await router.push('/dashboard')
  } catch {
    ElMessage.error(t('auth.loginFailed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-slate-100 px-4">
    <el-card class="w-full max-w-md">
      <template #header>
        <div>
          <h1 class="text-xl font-semibold text-slate-900">{{ t('auth.title') }}</h1>
          <p class="mt-1 text-sm text-slate-500">{{ t('auth.description') }}</p>
        </div>
      </template>

      <el-form :model="form" label-width="100px" @submit.prevent="submitLogin">
        <el-form-item :label="t('auth.username')">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item :label="t('auth.password')">
          <el-input
            v-model="form.password"
            autocomplete="current-password"
            show-password
            type="password"
            @keyup.enter="submitLogin"
          />
        </el-form-item>
        <el-button type="primary" class="w-full" :loading="loading" @click="submitLogin">
          {{ t('auth.login') }}
        </el-button>
      </el-form>
    </el-card>
  </main>
</template>
