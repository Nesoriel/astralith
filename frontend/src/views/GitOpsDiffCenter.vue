<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import {
  generateDiffs,
  listActualResources,
  listApplyPlans,
  listDiffs,
  listGitOpsRepositories,
  listPolicyResults,
  upsertActualResource,
  type ActualResource,
  type ActualResourcePayload,
  type ApplyPlan,
  type GitOpsRepository,
  type PolicyResult,
  type ResourceDiff,
} from '../api/gitops'

const { t } = useI18n()
const repositories = ref<GitOpsRepository[]>([])
const selectedRepositoryId = ref<number | null>(null)
const actualResources = ref<ActualResource[]>([])
const diffs = ref<ResourceDiff[]>([])
const applyPlans = ref<ApplyPlan[]>([])
const policyResults = ref<PolicyResult[]>([])
const loading = ref(false)
const diffLoading = ref(false)
const actualForm = ref<ActualResourcePayload>({
  resource_type: 'stack',
  resource_key: 'uptime-kuma',
  source: 'manual',
  content: { name: 'uptime-kuma', host: 'monitoring-01', image: 'old/image:1' },
})
const contentText = ref(JSON.stringify(actualForm.value.content, null, 2))

function statusTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'passed' || status === 'success') return 'success'
  if (status === 'blocked' || status === 'failed') return 'danger'
  if (status === 'pending' || status === 'pending_review') return 'warning'
  return 'info'
}

function riskTagType(risk: string): 'success' | 'warning' | 'danger' | 'info' {
  if (risk === 'high') return 'danger'
  if (risk === 'medium') return 'warning'
  if (risk === 'low') return 'success'
  return 'info'
}

async function loadData(): Promise<void> {
  loading.value = true
  try {
    const [repositoryList, actualList] = await Promise.all([listGitOpsRepositories(), listActualResources()])
    repositories.value = repositoryList
    actualResources.value = actualList
    if (selectedRepositoryId.value === null && repositoryList[0]) {
      selectedRepositoryId.value = repositoryList[0].id
    }
    if (selectedRepositoryId.value !== null) {
      await loadDiffData(selectedRepositoryId.value)
    }
  } finally {
    loading.value = false
  }
}

async function loadDiffData(repositoryId: number): Promise<void> {
  selectedRepositoryId.value = repositoryId
  const [diffList, planList, policyList] = await Promise.all([
    listDiffs(repositoryId),
    listApplyPlans(repositoryId),
    listPolicyResults(repositoryId),
  ])
  diffs.value = diffList
  applyPlans.value = planList
  policyResults.value = policyList
}

async function submitActualResource(): Promise<void> {
  actualForm.value.content = JSON.parse(contentText.value) as Record<string, unknown>
  await upsertActualResource(actualForm.value)
  ElMessage.success(t('common.success'))
  await loadData()
}

async function runDiff(): Promise<void> {
  if (selectedRepositoryId.value === null) return
  diffLoading.value = true
  try {
    diffs.value = await generateDiffs(selectedRepositoryId.value)
    await loadDiffData(selectedRepositoryId.value)
    ElMessage.success(t('pages.gitops.diffGenerated'))
  } finally {
    diffLoading.value = false
  }
}

function formatJson(value: Record<string, unknown> | null | undefined): string {
  return value ? JSON.stringify(value, null, 2) : '-'
}

onMounted(loadData)
</script>

<template>
  <main class="space-y-4">
    <section>
      <h1 class="text-2xl font-semibold">{{ t('pages.gitops.diffCenter') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('pages.gitops.diffDescription') }}</p>
    </section>

    <el-card>
      <template #header>{{ t('pages.gitops.actualResource') }}</template>
      <el-form :model="actualForm" label-width="140px" class="grid gap-2 md:grid-cols-2">
        <el-form-item :label="t('fields.resourceType')"><el-input v-model="actualForm.resource_type" /></el-form-item>
        <el-form-item :label="t('fields.resourceKey')"><el-input v-model="actualForm.resource_key" /></el-form-item>
        <el-form-item :label="t('fields.source')"><el-input v-model="actualForm.source" /></el-form-item>
        <el-form-item :label="t('fields.content')" class="md:col-span-2">
          <el-input v-model="contentText" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <el-button type="primary" @click="submitActualResource">{{ t('common.save') }}</el-button>
    </el-card>

    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <span>{{ t('pages.gitops.diffCenter') }}</span>
          <div class="flex items-center gap-2">
            <el-select v-model="selectedRepositoryId" class="w-64" @change="loadDiffData">
              <el-option v-for="repo in repositories" :key="repo.id" :label="repo.name" :value="repo.id" />
            </el-select>
            <el-button size="small" :loading="loading" @click="loadData">{{ t('common.refresh') }}</el-button>
            <el-button size="small" type="primary" :loading="diffLoading" @click="runDiff">{{ t('pages.gitops.generateDiff') }}</el-button>
          </div>
        </div>
      </template>
      <el-table :data="diffs" empty-text="-">
        <el-table-column prop="resource_type" :label="t('fields.resourceType')" width="120" />
        <el-table-column prop="resource_key" :label="t('fields.resourceKey')" width="180" />
        <el-table-column prop="diff_type" :label="t('fields.diffType')" width="120" />
        <el-table-column prop="risk_level" :label="t('fields.riskLevel')" width="120">
          <template #default="scope"><el-tag :type="riskTagType(scope.row.risk_level)">{{ scope.row.risk_level }}</el-tag></template>
        </el-table-column>
        <el-table-column :label="t('fields.before')" min-width="220">
          <template #default="scope"><pre class="max-h-32 overflow-auto rounded bg-slate-100 p-2 text-xs">{{ formatJson(scope.row.before) }}</pre></template>
        </el-table-column>
        <el-table-column :label="t('fields.after')" min-width="220">
          <template #default="scope"><pre class="max-h-32 overflow-auto rounded bg-slate-100 p-2 text-xs">{{ formatJson(scope.row.after) }}</pre></template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header>{{ t('pages.gitops.applyPlans') }}</template>
      <el-table :data="applyPlans" empty-text="-">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="status" :label="t('fields.status')" width="140">
          <template #default="scope"><el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="policy_status" :label="t('fields.policyStatus')" width="140">
          <template #default="scope"><el-tag :type="statusTagType(scope.row.policy_status)">{{ scope.row.policy_status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="ai_summary" :label="t('fields.summary')" min-width="220" />
        <el-table-column :label="t('fields.steps')" min-width="260">
          <template #default="scope">
            <ol class="list-decimal pl-5 text-sm">
              <li v-for="step in scope.row.plan.steps" :key="step">{{ step }}</li>
            </ol>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card>
      <template #header>{{ t('pages.gitops.policyResults') }}</template>
      <el-table :data="policyResults" empty-text="-">
        <el-table-column prop="rule_key" :label="t('fields.ruleKey')" min-width="180" />
        <el-table-column prop="severity" :label="t('fields.severity')" width="120" />
        <el-table-column prop="passed" :label="t('fields.passed')" width="120">
          <template #default="scope"><el-tag :type="scope.row.passed ? 'success' : 'danger'">{{ scope.row.passed }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="message" :label="t('fields.message')" min-width="260" />
      </el-table>
    </el-card>
  </main>
</template>
