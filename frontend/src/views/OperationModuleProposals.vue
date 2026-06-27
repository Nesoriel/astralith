<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
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

const { t } = useI18n()
const proposals = ref<OperationModuleProposal[]>([])
const loading = ref(false)
const reviewComment = ref('')
const exportText = ref('')
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

function statusTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'approved' || status === 'implemented') return 'success'
  if (status === 'rejected' || status === 'blocked') return 'danger'
  if (status === 'draft' || status === 'reviewing') return 'warning'
  return 'info'
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
  form.value.parameter_schema = JSON.parse(parameterSchemaText.value) as Record<string, unknown>
  form.value.playbook = JSON.parse(playbookText.value) as Record<string, unknown>
  form.value.test_plan = testPlanText.value.split('\n').map((item) => item.trim()).filter(Boolean)
  await createOperationModuleProposal(form.value)
  ElMessage.success(t('common.success'))
  await loadData()
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

function formatJson(value: Record<string, unknown>): string {
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
            <el-input v-model="reviewComment" class="w-72" :placeholder="t('pages.aiProposals.reviewComment')" />
            <el-button size="small" :loading="loading" @click="loadData">{{ t('common.refresh') }}</el-button>
          </div>
        </div>
      </template>
      <el-table v-loading="loading" :data="proposals" empty-text="-">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="module_key" :label="t('fields.module')" width="190" />
        <el-table-column prop="task_key" :label="t('fields.moduleTask')" width="160" />
        <el-table-column prop="status" :label="t('fields.status')" width="120">
          <template #default="scope"><el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="validation_status" :label="t('fields.validationStatus')" width="140" />
        <el-table-column :label="t('fields.playbook')" min-width="260">
          <template #default="scope"><pre class="max-h-36 overflow-auto rounded bg-slate-100 p-2 text-xs">{{ formatJson(scope.row.playbook) }}</pre></template>
        </el-table-column>
        <el-table-column :label="t('common.actions')" width="300">
          <template #default="scope">
            <el-button size="small" @click="approveProposal(scope.row)">{{ t('common.approve') }}</el-button>
            <el-button size="small" type="danger" @click="rejectProposal(scope.row)">{{ t('common.reject') }}</el-button>
            <el-button size="small" type="success" @click="implementProposal(scope.row)">{{ t('common.implement') }}</el-button>
            <el-button size="small" @click="exportProposal(scope.row)">{{ t('common.export') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="exportText">
      <template #header>{{ t('pages.operationModuleProposals.exportDraft') }}</template>
      <pre class="max-h-96 overflow-auto rounded bg-slate-100 p-3 text-xs">{{ exportText }}</pre>
    </el-card>
  </main>
</template>
