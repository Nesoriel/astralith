<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import {
  approveOperationModuleProposal,
  createOperationModuleProposal,
  exportOperationModuleProposal,
  implementOperationModuleProposal,
  listOperationModuleProposals,
  rejectOperationModuleProposal,
  type OperationModuleProposal,
  type OperationModuleProposalPayload,
} from '../api/operationModuleProposals'
import { parseJsonObject, riskTagType, statusTagType } from '../utils/status'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const proposals = ref<OperationModuleProposal[]>([])
const statusFilter = ref('all')
const loading = ref(false)
const reviewComment = ref('')
const exportText = ref('')

const selectedProposalId = computed(() => Number(route.query.id) || null)
const selectedProposal = computed(() => proposals.value.find((item) => item.id === selectedProposalId.value) ?? null)
const filteredProposals = computed(() => statusFilter.value === 'all' ? proposals.value : proposals.value.filter((item) => item.status === statusFilter.value))
const form = ref<OperationModuleProposalPayload>({
  title: t('defaults.moduleProposalTitle'),
  problem_summary: t('pages.operationModuleProposals.defaultProblem'),
  module_key: 'docker_compose_restart',
  task_key: 'restart_service',
  risk_level: 'medium',
  parameter_schema: { service_name: { type: 'string', pattern: '^[a-zA-Z0-9_.@-]+$' } },
  runbook: '1. Validate compose config\n2. Restart service\n3. Check service status',
  playbook: { tasks: [{ 'ansible.builtin.command': 'docker compose restart {{ service_name }}' }] },
  test_plan: ['syntax-check', 'manual review'],
  rollback_notes: 'Run docker compose up -d with the previous compose content.',
})
const parameterSchemaText = ref(JSON.stringify(form.value.parameter_schema, null, 2))
const playbookText = ref(JSON.stringify(form.value.playbook, null, 2))
const testPlanText = ref(form.value.test_plan.join('\n'))

function isHighRisk(proposal: OperationModuleProposal): boolean {
  return ['high', 'critical'].includes(proposal.risk_level)
    || proposal.dangerous_command_detected
    || ['blocked', 'failed'].includes(proposal.validation_status)
}

async function loadData(): Promise<void> {
  loading.value = true
  try {
    proposals.value = await listOperationModuleProposals()
  } finally {
    loading.value = false
  }
}

async function submitProposal(): Promise<void> {
  try {
    form.value.parameter_schema = parseJsonObject(parameterSchemaText.value)
    form.value.playbook = parseJsonObject(playbookText.value)
    form.value.test_plan = testPlanText.value.split('\n').map((item) => item.trim()).filter(Boolean)
    const proposal = await createOperationModuleProposal(form.value)
    ElMessage.success(t('common.success'))
    await loadData()
    await openProposal(proposal)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : t('common.failed'))
  }
}

async function approveProposal(proposal: OperationModuleProposal): Promise<void> {
  await approveOperationModuleProposal(proposal.id, reviewComment.value || t('pages.operationModuleProposals.defaultApproveComment'))
  ElMessage.success(t('pages.operationModuleProposals.approved'))
  await loadData()
}

async function rejectProposal(proposal: OperationModuleProposal): Promise<void> {
  await rejectOperationModuleProposal(proposal.id, reviewComment.value || t('pages.operationModuleProposals.defaultRejectComment'))
  ElMessage.success(t('pages.operationModuleProposals.rejected'))
  await loadData()
}

async function implementProposal(proposal: OperationModuleProposal): Promise<void> {
  await implementOperationModuleProposal(proposal.id, reviewComment.value || t('pages.operationModuleProposals.defaultImplementComment'))
  ElMessage.success(t('pages.operationModuleProposals.implemented'))
  await loadData()
}

async function exportProposal(proposal: OperationModuleProposal): Promise<void> {
  exportText.value = JSON.stringify(await exportOperationModuleProposal(proposal.id), null, 2)
}

async function openProposal(proposal: OperationModuleProposal): Promise<void> {
  await router.push(`/operation-module-proposals?id=${proposal.id}`)
}

async function closeProposal(): Promise<void> {
  await router.push('/operation-module-proposals')
}

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2)
}

onMounted(loadData)
</script>

<template>
  <main class="space-y-4">
    <section>
      <h1 class="text-2xl font-semibold">{{ t('pages.operationModuleProposals.title') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('pages.operationModuleProposals.description') }}</p>
    </section>

    <el-card>
      <template #header>{{ t('pages.operationModuleProposals.createTitle') }}</template>
      <el-form :model="form" label-width="150px" class="grid gap-2 md:grid-cols-2">
        <el-form-item :label="t('fields.title')"><el-input v-model="form.title" /></el-form-item>
        <el-form-item :label="t('fields.riskLevel')"><el-input v-model="form.risk_level" /></el-form-item>
        <el-form-item :label="t('fields.module')"><el-input v-model="form.module_key" /></el-form-item>
        <el-form-item :label="t('fields.moduleTask')"><el-input v-model="form.task_key" /></el-form-item>
        <el-form-item :label="t('fields.problemSummary')" class="md:col-span-2"><el-input v-model="form.problem_summary" /></el-form-item>
        <el-form-item :label="t('fields.parameterSchema')" class="md:col-span-2"><el-input v-model="parameterSchemaText" type="textarea" :rows="4" /></el-form-item>
        <el-form-item :label="t('fields.playbook')" class="md:col-span-2"><el-input v-model="playbookText" type="textarea" :rows="5" /></el-form-item>
        <el-form-item :label="t('fields.runbook')" class="md:col-span-2"><el-input v-model="form.runbook" type="textarea" :rows="4" /></el-form-item>
        <el-form-item :label="t('fields.testPlan')" class="md:col-span-2"><el-input v-model="testPlanText" type="textarea" :rows="3" /></el-form-item>
        <el-form-item :label="t('fields.rollbackNotes')" class="md:col-span-2"><el-input v-model="form.rollback_notes" /></el-form-item>
      </el-form>
      <el-button type="primary" @click="submitProposal">{{ t('common.create') }}</el-button>
    </el-card>

    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <span>{{ t('pages.operationModuleProposals.proposals') }}</span>
          <div class="flex items-center gap-2">
            <el-select v-model="statusFilter" class="w-36">
              <el-option label="all" value="all" />
              <el-option label="draft" value="draft" />
              <el-option label="reviewing" value="reviewing" />
              <el-option label="approved" value="approved" />
              <el-option label="rejected" value="rejected" />
              <el-option label="implemented" value="implemented" />
              <el-option label="blocked" value="blocked" />
            </el-select>
            <el-input v-model="reviewComment" class="w-72" :placeholder="t('pages.aiProposals.reviewComment')" />
            <el-button size="small" :loading="loading" @click="loadData">{{ t('common.refresh') }}</el-button>
          </div>
        </div>
      </template>
      <el-table v-loading="loading" :data="filteredProposals" empty-text="-" @row-click="openProposal">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="title" :label="t('fields.title')" min-width="220" />
        <el-table-column prop="module_key" :label="t('fields.module')" width="190" />
        <el-table-column prop="task_key" :label="t('fields.moduleTask')" width="160" />
        <el-table-column prop="status" :label="t('fields.status')" width="120">
          <template #default="scope"><el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="risk_level" :label="t('fields.riskLevel')" width="120">
          <template #default="scope"><el-tag :type="riskTagType(scope.row.risk_level)">{{ scope.row.risk_level }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="validation_status" :label="t('fields.validationStatus')" width="140">
          <template #default="scope"><el-tag :type="statusTagType(scope.row.validation_status)">{{ scope.row.validation_status }}</el-tag></template>
        </el-table-column>
        <el-table-column :label="t('common.actions')" width="360">
          <template #default="scope">
            <el-button size="small" @click.stop="openProposal(scope.row)">{{ t('common.detail') }}</el-button>
            <el-button size="small" @click.stop="approveProposal(scope.row)">{{ t('common.approve') }}</el-button>
            <el-button size="small" type="danger" @click.stop="rejectProposal(scope.row)">{{ t('common.reject') }}</el-button>
            <el-button size="small" type="success" @click.stop="implementProposal(scope.row)">{{ t('common.implement') }}</el-button>
            <el-button size="small" @click.stop="exportProposal(scope.row)">{{ t('common.export') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer :model-value="selectedProposal !== null" :title="selectedProposal?.title" size="60%" @close="closeProposal">
      <div v-if="selectedProposal" class="space-y-4">
        <el-alert v-if="isHighRisk(selectedProposal)" :title="t('pages.operationModuleProposals.highRiskNotice')" type="error" :closable="false" show-icon />

        <el-card shadow="never">
          <template #header>{{ t('pages.operationModuleProposals.basicInfo') }}</template>
          <el-descriptions border :column="2">
            <el-descriptions-item :label="t('fields.title')">{{ selectedProposal.title }}</el-descriptions-item>
            <el-descriptions-item :label="t('fields.module')">{{ selectedProposal.module_key }}</el-descriptions-item>
            <el-descriptions-item :label="t('fields.moduleTask')">{{ selectedProposal.task_key }}</el-descriptions-item>
            <el-descriptions-item :label="t('fields.status')"><el-tag :type="statusTagType(selectedProposal.status)">{{ selectedProposal.status }}</el-tag></el-descriptions-item>
            <el-descriptions-item :label="t('fields.riskLevel')"><el-tag :type="riskTagType(selectedProposal.risk_level)">{{ selectedProposal.risk_level }}</el-tag></el-descriptions-item>
            <el-descriptions-item :label="t('fields.validationStatus')"><el-tag :type="statusTagType(selectedProposal.validation_status)">{{ selectedProposal.validation_status }}</el-tag></el-descriptions-item>
            <el-descriptions-item :label="t('fields.dangerousCommandDetected')"><el-tag :type="selectedProposal.dangerous_command_detected ? 'danger' : 'success'">{{ selectedProposal.dangerous_command_detected }}</el-tag></el-descriptions-item>
            <el-descriptions-item :label="t('fields.createdAt')">{{ selectedProposal.created_at }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never">
          <template #header>{{ t('fields.content') }}</template>
          <div class="space-y-3">
            <section>
              <p class="font-medium">{{ t('fields.problemSummary') }}</p>
              <p class="text-sm text-slate-700">{{ selectedProposal.problem_summary }}</p>
            </section>
            <section>
              <p class="font-medium">{{ t('fields.parameterSchema') }}</p>
              <pre class="max-h-48 overflow-auto rounded bg-slate-100 p-3 text-xs">{{ formatJson(selectedProposal.parameter_schema) }}</pre>
            </section>
            <section>
              <p class="font-medium">{{ t('fields.runbook') }}</p>
              <pre class="whitespace-pre-wrap rounded bg-slate-50 p-3 text-sm">{{ selectedProposal.runbook }}</pre>
            </section>
            <section>
              <p class="font-medium">{{ t('fields.playbook') }}</p>
              <pre class="max-h-64 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-100">{{ formatJson(selectedProposal.playbook) }}</pre>
            </section>
            <section>
              <p class="font-medium">{{ t('fields.testPlan') }}</p>
              <ul class="list-disc pl-5 text-sm text-slate-700">
                <li v-for="item in selectedProposal.test_plan" :key="item">{{ item }}</li>
              </ul>
            </section>
            <section>
              <p class="font-medium">{{ t('fields.rollbackNotes') }}</p>
              <p class="text-sm text-slate-700">{{ selectedProposal.rollback_notes }}</p>
            </section>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header>{{ t('pages.operationModuleProposals.review') }}</template>
          <el-descriptions border :column="1" class="mb-3">
            <el-descriptions-item :label="t('fields.reviewComment')">{{ selectedProposal.review_comment ?? '-' }}</el-descriptions-item>
            <el-descriptions-item :label="t('fields.reviewedBy')">{{ selectedProposal.reviewed_by ?? '-' }}</el-descriptions-item>
            <el-descriptions-item :label="t('fields.reviewedAt')">{{ selectedProposal.reviewed_at ?? '-' }}</el-descriptions-item>
          </el-descriptions>
          <div class="mb-3 flex items-center gap-2">
            <el-input v-model="reviewComment" :placeholder="t('pages.aiProposals.reviewComment')" />
          </div>
          <div class="flex flex-wrap gap-2">
            <el-button @click="approveProposal(selectedProposal)">{{ t('common.approve') }}</el-button>
            <el-button type="danger" @click="rejectProposal(selectedProposal)">{{ t('common.reject') }}</el-button>
            <el-button type="success" @click="implementProposal(selectedProposal)">{{ t('common.implement') }}</el-button>
            <el-button @click="exportProposal(selectedProposal)">{{ t('common.export') }}</el-button>
          </div>
        </el-card>
      </div>
    </el-drawer>

    <el-card v-if="exportText">
      <template #header>{{ t('pages.operationModuleProposals.exportDraft') }}</template>
      <pre class="max-h-96 overflow-auto rounded bg-slate-100 p-3 text-xs">{{ exportText }}</pre>
    </el-card>
  </main>
</template>
