<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { createHostGroup, deleteHostGroup, listHostGroups, type HostGroup, type HostGroupPayload } from '../api/hosts'

const { t } = useI18n()
const groups = ref<HostGroup[]>([])
const form = ref<HostGroupPayload>({ name: 'web', description: '' })

async function loadGroups(): Promise<void> {
  groups.value = await listHostGroups()
}

async function submitGroup(): Promise<void> {
  await createHostGroup(form.value)
  ElMessage.success(t('common.success'))
  await loadGroups()
}

async function removeGroup(id: number): Promise<void> {
  await deleteHostGroup(id)
  ElMessage.success(t('common.success'))
  await loadGroups()
}

onMounted(loadGroups)
</script>

<template>
  <main class="space-y-4">
    <section>
      <h1 class="text-2xl font-semibold">{{ t('pages.hostGroups.title') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('pages.hostGroups.description') }}</p>
    </section>

    <el-card>
      <template #header>{{ t('pages.hostGroups.addTitle') }}</template>
      <el-form :model="form" label-width="120px" class="grid gap-2 md:grid-cols-2">
        <el-form-item :label="t('fields.name')"><el-input v-model="form.name" /></el-form-item>
        <el-form-item :label="t('fields.description')"><el-input v-model="form.description" /></el-form-item>
      </el-form>
      <el-button type="primary" @click="submitGroup">{{ t('common.create') }}</el-button>
    </el-card>

    <el-card>
      <template #header>{{ t('nav.hostGroups') }}</template>
      <el-table :data="groups" empty-text="-">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="name" :label="t('fields.name')" />
        <el-table-column prop="description" :label="t('fields.description')" />
        <el-table-column :label="t('pages.hostGroups.members')">
          <template #default="scope">{{ scope.row.host_ids.join(', ') || '-' }}</template>
        </el-table-column>
        <el-table-column :label="t('common.actions')" width="120">
          <template #default="scope">
            <el-button size="small" type="danger" @click="removeGroup(scope.row.id)">{{ t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </main>
</template>
