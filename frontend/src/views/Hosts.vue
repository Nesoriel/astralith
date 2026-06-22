<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { createHost, deleteHost, listHosts, testHostConnection, type Host, type HostPayload } from '../api/hosts'

const { t } = useI18n()
const hosts = ref<Host[]>([])
const form = ref<HostPayload>({
  name: t('defaults.hostName'),
  ip_address: '192.0.2.10',
  ssh_port: 22,
  ssh_user: 'root',
  private_key_path: '/home/demo/.ssh/id_rsa',
  description: '',
})

async function loadHosts(): Promise<void> {
  hosts.value = await listHosts()
}

async function submitHost(): Promise<void> {
  // v0.1.0 先提供新增入口；编辑可以复用后端 PUT 接口在后续页面细化。
  await createHost(form.value)
  ElMessage.success(t('common.success'))
  await loadHosts()
}

async function removeHost(id: number): Promise<void> {
  await deleteHost(id)
  ElMessage.success(t('common.success'))
  await loadHosts()
}

async function runConnectionTest(id: number): Promise<void> {
  const result = await testHostConnection(id)
  ElMessage.info(result.message || t('pages.hosts.testPending'))
}

onMounted(loadHosts)
</script>

<template>
  <main class="space-y-4">
    <section>
      <h1 class="text-2xl font-semibold">{{ t('pages.hosts.title') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('pages.hosts.description') }}</p>
    </section>

    <el-card>
      <template #header>{{ t('pages.hosts.addTitle') }}</template>
      <el-form :model="form" label-width="140px" class="grid gap-2 md:grid-cols-2">
        <el-form-item :label="t('fields.name')"><el-input v-model="form.name" /></el-form-item>
        <el-form-item :label="t('fields.ipAddress')"><el-input v-model="form.ip_address" /></el-form-item>
        <el-form-item :label="t('fields.sshPort')"><el-input-number v-model="form.ssh_port" :min="1" :max="65535" class="w-full" /></el-form-item>
        <el-form-item :label="t('fields.sshUser')"><el-input v-model="form.ssh_user" /></el-form-item>
        <el-form-item :label="t('fields.privateKeyPath')" class="md:col-span-2"><el-input v-model="form.private_key_path" /></el-form-item>
        <el-form-item :label="t('fields.description')" class="md:col-span-2"><el-input v-model="form.description" /></el-form-item>
      </el-form>
      <el-button type="primary" @click="submitHost">{{ t('common.create') }}</el-button>
    </el-card>

    <el-card>
      <template #header>{{ t('nav.hosts') }}</template>
      <el-table :data="hosts" empty-text="-">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="name" :label="t('fields.name')" />
        <el-table-column prop="ip_address" :label="t('fields.ipAddress')" />
        <el-table-column prop="ssh_user" :label="t('fields.sshUser')" />
        <el-table-column :label="t('common.actions')" width="220">
          <template #default="scope">
            <el-button size="small" @click="runConnectionTest(scope.row.id)">{{ t('common.test') }}</el-button>
            <el-button size="small" type="danger" @click="removeHost(scope.row.id)">{{ t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </main>
</template>
