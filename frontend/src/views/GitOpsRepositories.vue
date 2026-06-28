<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import {
  createGitOpsRepository,
  listDesiredResources,
  listGitOpsRepositories,
  listGitOpsSyncRuns,
  syncGitOpsRepository,
  type DesiredResource,
  type GitOpsRepository,
  type GitOpsRepositoryPayload,
  type GitOpsSyncRun,
} from '../api/gitops'
import { statusTagType } from '../utils/status'

const { t } = useI18n()
const repositories = ref<GitOpsRepository[]>([])
const selectedRepositoryId = ref<number | null>(null)
const desiredResources = ref<DesiredResource[]>([])
const syncRuns = ref<GitOpsSyncRun[]>([])
const loading = ref(false)
const syncLoading = ref<number | null>(null)
const form = ref<GitOpsRepositoryPayload>({
  name: t('defaults.gitOpsRepositoryName'),
  repo_url: '',
  branch: 'main',
  local_path: 'backend/.gitops/default',
  auth_type: 'none',
  enabled: true,
})

const selectedRepository = computed(() => repositories.value.find((item) => item.id === selectedRepositoryId.value))

async function loadRepositories(): Promise<void> {
  loading.value = true
  try {
    repositories.value = await listGitOpsRepositories()
    if (selectedRepositoryId.value === null && repositories.value[0]) {
      selectedRepositoryId.value = repositories.value[0].id
      await loadRepositoryDetails(repositories.value[0])
    }
  } finally {
    loading.value = false
  }
}

async function loadRepositoryDetails(repository: GitOpsRepository): Promise<void> {
  selectedRepositoryId.value = repository.id
  const [resources, runs] = await Promise.all([
    listDesiredResources(repository.id),
    listGitOpsSyncRuns(repository.id),
  ])
  desiredResources.value = resources
  syncRuns.value = runs
}

async function submitRepository(): Promise<void> {
  const repository = await createGitOpsRepository(form.value)
  ElMessage.success(t('common.success'))
  await loadRepositories()
  await loadRepositoryDetails(repository)
}

async function syncRepository(repository: GitOpsRepository): Promise<void> {
  syncLoading.value = repository.id
  try {
    const result = await syncGitOpsRepository(repository.id)
    ElMessage.success(result.status === 'success' ? t('pages.gitops.syncSuccess') : t('pages.gitops.syncFailed'))
    await loadRepositories()
    await loadRepositoryDetails(repository)
  } finally {
    syncLoading.value = null
  }
}

function formatContent(content: Record<string, unknown>): string {
  return JSON.stringify(content, null, 2)
}

onMounted(loadRepositories)
</script>

<template>
  <main class="space-y-4">
    <section>
      <h1 class="text-2xl font-semibold">{{ t('pages.gitops.title') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('pages.gitops.description') }}</p>
    </section>

    <el-card>
      <template #header>{{ t('pages.gitops.createTitle') }}</template>
      <el-form :model="form" label-width="140px" class="grid gap-2 md:grid-cols-2">
        <el-form-item :label="t('fields.name')"><el-input v-model="form.name" /></el-form-item>
        <el-form-item :label="t('fields.repoUrl')"><el-input v-model="form.repo_url" /></el-form-item>
        <el-form-item :label="t('fields.branch')"><el-input v-model="form.branch" /></el-form-item>
        <el-form-item :label="t('fields.localPath')"><el-input v-model="form.local_path" /></el-form-item>
        <el-form-item :label="t('fields.enabled')"><el-switch v-model="form.enabled" /></el-form-item>
      </el-form>
      <el-button type="primary" @click="submitRepository">{{ t('common.create') }}</el-button>
    </el-card>

    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <span>{{ t('pages.gitops.repositories') }}</span>
          <el-button size="small" :loading="loading" @click="loadRepositories">{{ t('common.refresh') }}</el-button>
        </div>
      </template>
      <el-table v-loading="loading" :data="repositories" empty-text="-" @row-click="loadRepositoryDetails">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="name" :label="t('fields.name')" />
        <el-table-column prop="repo_url" :label="t('fields.repoUrl')" min-width="220" />
        <el-table-column prop="branch" :label="t('fields.branch')" width="120" />
        <el-table-column prop="last_commit_sha" :label="t('fields.commitSha')" min-width="160">
          <template #default="scope">{{ scope.row.last_commit_sha?.slice(0, 12) ?? '-' }}</template>
        </el-table-column>
        <el-table-column :label="t('common.actions')" width="140">
          <template #default="scope">
            <el-button size="small" type="primary" :loading="syncLoading === scope.row.id" @click.stop="syncRepository(scope.row)">
              {{ t('common.sync') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="selectedRepository">
      <template #header>
        <div class="flex items-center justify-between">
          <span>{{ t('pages.gitops.desiredResources') }} · {{ selectedRepository.name }}</span>
          <span class="text-xs text-slate-500">{{ selectedRepository.last_sync_at ?? '-' }}</span>
        </div>
      </template>
      <el-table :data="desiredResources" empty-text="-">
        <el-table-column prop="resource_type" :label="t('fields.resourceType')" width="120" />
        <el-table-column prop="resource_key" :label="t('fields.resourceKey')" width="180" />
        <el-table-column prop="file_path" :label="t('fields.filePath')" min-width="220" />
        <el-table-column :label="t('fields.content')" min-width="260">
          <template #default="scope">
            <pre class="max-h-40 overflow-auto rounded bg-slate-100 p-2 text-xs text-slate-800">{{ formatContent(scope.row.content) }}</pre>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="selectedRepository">
      <template #header>{{ t('pages.gitops.syncRuns') }}</template>
      <el-table :data="syncRuns" empty-text="-">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="status" :label="t('fields.status')" width="120">
          <template #default="scope"><el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="commit_sha" :label="t('fields.commitSha')" min-width="180">
          <template #default="scope">{{ scope.row.commit_sha?.slice(0, 12) ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="started_at" :label="t('fields.startedAt')" min-width="180" />
        <el-table-column prop="stderr" :label="t('fields.stderr')" min-width="220">
          <template #default="scope">{{ scope.row.stderr || '-' }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </main>
</template>
