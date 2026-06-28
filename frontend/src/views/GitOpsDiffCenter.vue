<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { generateProposalFromApplyPlan } from '../api/aiProposals'
import {
  approveApplyPlan,
  executeApplyPlan,
  generateDiffs,
  listActualResources,
  listApplyRuns,
  listApplyPlans,
  listDiffs,
  listGitOpsRepositories,
  listPolicyResults,
  upsertActualResource,
  type ActualResource,
  type ActualResourcePayload,
  type ApplyPlan,
  type GitOpsApplyRun,
  type GitOpsRepository,
  type PolicyResult,
  type ResourceDiff,
} from '../api/gitops'
import { parseJsonObject, riskTagType, statusTagType } from '../utils/status'

const { t } = useI18n()
const repositories = ref<GitOpsRepository[]>([])
const selectedRepositoryId = ref<number | null>(null)
const activeStep = ref('actual')
const actualResources = ref<ActualResource[]>([])
const diffs = ref<ResourceDiff[]>([])
const applyPlans = ref<ApplyPlan[]>([])
const applyRuns = ref<GitOpsApplyRun[]>([])
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

const steps = ['actual', 'diff', 'plan', 'policy', 'run']

async function loadData(): Promise<void> {
  loading.value = true
  try {
    const [repositoryList, actualList] = await Promise.all([listGitOpsRepositories(), listActualResources()])
    repositories.value = repositoryList
    actualResources.value = actualList
    if (selectedRepositoryId.value === null && repositoryList[0]) selectedRepositoryId.value = repositoryList[0].id
    if (selectedRepositoryId.value !== null) await loadDiffData(selectedRepositoryId.value)
  } finally {
    loading.value = false
  }
}

async function loadDiffData(repositoryId: number): Promise<void> {
  selectedRepositoryId.value = repositoryId
  const [diffList, planList, policyList, runList] = await Promise.all([
    listDiffs(repositoryId),
    listApplyPlans(repositoryId),
    listPolicyResults(repositoryId),
    listApplyRuns(repositoryId),
  ])
  diffs.value = diffList
  applyPlans.value = planList
  policyResults.value = policyList
  applyRuns.value = runList
}

async function submitActualResource(): Promise<void> {
  try {
    actualForm.value.content = parseJsonObject(contentText.value)
    await upsertActualResource(actualForm.value)
    ElMessage.success(t('common.success'))
    activeStep.value = 'diff'
    await loadData()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : t('common.failed'))
  }
}

async function runDiff(): Promise<void> {
  if (selectedRepositoryId.value === null) return
  diffLoading.value = true
  try {
    diffs.value = await generateDiffs(selectedRepositoryId.value)
    await loadDiffData(selectedRepositoryId.value)
    activeStep.value = 'plan'
    ElMessage.success(t('pages.gitops.diffGenerated'))
  } finally {
    diffLoading.value = false
  }
}

async function approvePlan(plan: ApplyPlan): Promise<void> {
  await approveApplyPlan(plan.id)
  ElMessage.success(t('pages.gitops.planApproved'))
  activeStep.value = 'policy'
  if (selectedRepositoryId.value !== null) await loadDiffData(selectedRepositoryId.value)
}

async function executePlan(plan: ApplyPlan): Promise<void> {
  await ElMessageBox.confirm(t('pages.gitops.executeConfirm'), t('common.execute'), { type: 'warning' })
  await executeApplyPlan(plan.id)
  ElMessage.success(t('pages.gitops.planExecuted'))
  activeStep.value = 'run'
  if (selectedRepositoryId.value !== null) await loadDiffData(selectedRepositoryId.value)
}

async function generateProposal(plan: ApplyPlan): Promise<void> {
  await generateProposalFromApplyPlan(plan.id)
  ElMessage.success(t('pages.gitops.proposalGenerated'))
}

function formatJson(value: Record<string, unknown> | null | undefined): string {
  return value ? JSON.stringify(value, null, 2) : '-'
}

onMounted(loadData)
</script>

<template>
  <main class="space-y-4">
    <section>
      <h1 class="text-2xl font-semibold">{{ t('pages.gitops.workbench') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('pages.gitops.workbenchDescription') }}</p>
    </section>

    <el-card>
      <div class="flex flex-wrap items-center gap-2">
        <el-select v-model="selectedRepositoryId" class="w-72" @change="loadDiffData">
          <el-option v-for="repo in repositories" :key="repo.id" :label="repo.name" :value="repo.id" />
        </el-select>
        <el-button :loading="loading" @click="loadData">{{ t('common.refresh') }}</el-button>
        <el-button type="primary" :loading="diffLoading" @click="runDiff">{{ t('pages.gitops.generateDiff') }}</el-button>
      </div>
    </el-card>

    <el-steps :active="steps.indexOf(activeStep)" finish-status="success" simple>
      <el-step :title="t('pages.gitops.actualResource')" />
      <el-step :title="t('pages.gitops.diffCenter')" />
      <el-step :title="t('pages.gitops.applyPlans')" />
      <el-step :title="t('pages.gitops.policyResults')" />
      <el-step :title="t('pages.gitops.applyRuns')" />
    </el-steps>

    <el-tabs v-model="activeStep">
      <el-tab-pane :label="t('pages.gitops.actualResource')" name="actual">
        <el-card>
          <template #header>{{ t('pages.gitops.actualResource') }}</template>
          <el-alert class="mb-4" :title="t('pages.gitops.manualActualNotice')" type="warning" :closable="false" show-icon />
          <el-form :model="actualForm" label-width="140px" class="grid gap-2 md:grid-cols-2">
            <el-form-item :label="t('fields.resourceType')"><el-input v-model="actualForm.resource_type" /></el-form-item>
            <el-form-item :label="t('fields.resourceKey')"><el-input v-model="actualForm.resource_key" /></el-form-item>
            <el-form-item :label="t('fields.source')"><el-input v-model="actualForm.source" /></el-form-item>
            <el-form-item :label="t('fields.content')" class="md:col-span-2">
              <el-input v-model="contentText" type="textarea" :rows="6" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="submitActualResource">{{ t('common.save') }}</el-button>
          <el-table class="mt-4" :data="actualResources" empty-text="-">
            <el-table-column prop="resource_type" :label="t('fields.resourceType')" />
            <el-table-column prop="resource_key" :label="t('fields.resourceKey')" />
            <el-table-column prop="source" :label="t('fields.source')" />
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="t('pages.gitops.diffCenter')" name="diff">
        <el-card>
          <el-table :data="diffs" empty-text="-">
            <el-table-column prop="resource_type" :label="t('fields.resourceType')" width="120" />
            <el-table-column prop="resource_key" :label="t('fields.resourceKey')" width="180" />
            <el-table-column prop="diff_type" :label="t('fields.diffType')" width="120" />
            <el-table-column prop="risk_level" :label="t('fields.riskLevel')" width="120">
              <template #default="scope"><el-tag :type="riskTagType(scope.row.risk_level)">{{ scope.row.risk_level }}</el-tag></template>
            </el-table-column>
            <el-table-column :label="t('fields.after')" min-width="260">
              <template #default="scope"><pre class="max-h-40 overflow-auto rounded bg-slate-100 p-2 text-xs">{{ formatJson(scope.row.after) }}</pre></template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="t('pages.gitops.applyPlans')" name="plan">
        <el-card>
          <el-table :data="applyPlans" empty-text="-">
            <el-table-column prop="id" :label="t('fields.id')" width="80" />
            <el-table-column prop="status" :label="t('fields.status')" width="140">
              <template #default="scope"><el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="policy_status" :label="t('fields.policyStatus')" width="140" />
            <el-table-column prop="ai_summary" :label="t('fields.summary')" min-width="220" />
            <el-table-column :label="t('common.actions')" width="260">
              <template #default="scope">
                <el-button size="small" @click="approvePlan(scope.row)">{{ t('common.approve') }}</el-button>
                <el-button size="small" type="primary" @click="executePlan(scope.row)">{{ t('common.execute') }}</el-button>
                <el-button size="small" @click="generateProposal(scope.row)">{{ t('common.propose') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="t('pages.gitops.policyResults')" name="policy">
        <el-card>
          <el-table :data="policyResults" empty-text="-">
            <el-table-column prop="rule_key" :label="t('fields.ruleKey')" />
            <el-table-column prop="severity" :label="t('fields.severity')" />
            <el-table-column prop="passed" :label="t('fields.passed')">
              <template #default="scope"><el-tag :type="scope.row.passed ? 'success' : 'danger'">{{ scope.row.passed }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="message" :label="t('fields.message')" />
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane :label="t('pages.gitops.applyRuns')" name="run">
        <el-card>
          <el-table :data="applyRuns" empty-text="-">
            <el-table-column prop="stack_name" :label="t('fields.stackName')" />
            <el-table-column prop="status" :label="t('fields.status')">
              <template #default="scope"><el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="target_path" :label="t('fields.targetPath')" />
            <el-table-column prop="stdout" :label="t('fields.stdout')" />
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </main>
</template>
