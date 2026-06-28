<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

import {
  approveAiProposal,
  createAiProposal,
  listAiProposals,
  rejectAiProposal,
  type AiProposal,
  type AiProposalPayload,
} from '../api/aiProposals'
import { generateOperationModuleProposalFromAi as generateModuleProposal } from '../api/operationModuleProposals'

const { t } = useI18n()
const proposals = ref<AiProposal[]>([])
const statusFilter = ref('all')
const loading = ref(false)
const reviewComment = ref('')

const filteredProposals = computed(() => statusFilter.value === 'all' ? proposals.value : proposals.value.filter((item) => item.status === statusFilter.value))
const form = ref<AiProposalPayload>({
  proposal_type: 'runbook',
  title: t('defaults.aiProposalTitle'),
  summary: t('pages.aiProposals.defaultSummary'),
  content: { steps: ['review evidence', 'generate controlled GitOps change'], rollback_plan: 'restore previous commit' },
  risk_level: 'low',
})
const contentText = ref(JSON.stringify(form.value.content, null, 2))

function statusTagType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'approved') return 'success'
  if (status === 'rejected') return 'danger'
  if (status === 'draft') return 'warning'
  return 'info'
}

async function loadData(): Promise<void> {
  loading.value = true
  try {
    proposals.value = await listAiProposals()
  } finally {
    loading.value = false
  }
}

async function submitProposal(): Promise<void> {
  form.value.content = JSON.parse(contentText.value) as Record<string, unknown>
  await createAiProposal(form.value)
  ElMessage.success(t('common.success'))
  await loadData()
}

async function approveProposal(proposal: AiProposal): Promise<void> {
  await approveAiProposal(proposal.id, reviewComment.value || t('pages.aiProposals.defaultApproveComment'))
  ElMessage.success(t('pages.aiProposals.approved'))
  await loadData()
}

async function rejectProposal(proposal: AiProposal): Promise<void> {
  await rejectAiProposal(proposal.id, reviewComment.value || t('pages.aiProposals.defaultRejectComment'))
  ElMessage.success(t('pages.aiProposals.rejected'))
  await loadData()
}

async function generateModule(proposal: AiProposal): Promise<void> {
  await generateModuleProposal(proposal.id)
  ElMessage.success(t('pages.aiProposals.moduleProposalGenerated'))
}

function formatJson(value: Record<string, unknown>): string {
  return JSON.stringify(value, null, 2)
}

onMounted(loadData)
</script>

<template>
  <main class="space-y-4">
    <section>
      <h1 class="text-2xl font-semibold">{{ t('pages.aiProposals.title') }}</h1>
      <p class="mt-2 text-slate-600">{{ t('pages.aiProposals.description') }}</p>
    </section>

    <el-card>
      <template #header>{{ t('pages.aiProposals.createTitle') }}</template>
      <el-form :model="form" label-width="140px" class="grid gap-2 md:grid-cols-2">
        <el-form-item :label="t('fields.proposalType')"><el-input v-model="form.proposal_type" /></el-form-item>
        <el-form-item :label="t('fields.riskLevel')"><el-input v-model="form.risk_level" /></el-form-item>
        <el-form-item :label="t('fields.title')"><el-input v-model="form.title" /></el-form-item>
        <el-form-item :label="t('fields.summary')"><el-input v-model="form.summary" /></el-form-item>
        <el-form-item :label="t('fields.content')" class="md:col-span-2">
          <el-input v-model="contentText" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <el-button type="primary" @click="submitProposal">{{ t('common.create') }}</el-button>
    </el-card>

    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <span>{{ t('pages.aiProposals.proposals') }}</span>
          <div class="flex items-center gap-2">
            <el-select v-model="statusFilter" class="w-36">
              <el-option label="all" value="all" />
              <el-option label="draft" value="draft" />
              <el-option label="approved" value="approved" />
              <el-option label="rejected" value="rejected" />
            </el-select>
            <el-input v-model="reviewComment" class="w-72" :placeholder="t('pages.aiProposals.reviewComment')" />
            <el-button size="small" :loading="loading" @click="loadData">{{ t('common.refresh') }}</el-button>
          </div>
        </div>
      </template>
      <el-table v-loading="loading" :data="filteredProposals" empty-text="-">
        <el-table-column prop="id" :label="t('fields.id')" width="80" />
        <el-table-column prop="proposal_type" :label="t('fields.proposalType')" width="140" />
        <el-table-column prop="title" :label="t('fields.title')" min-width="220" />
        <el-table-column prop="status" :label="t('fields.status')" width="120">
          <template #default="scope"><el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="risk_level" :label="t('fields.riskLevel')" width="120" />
        <el-table-column :label="t('fields.content')" min-width="300">
          <template #default="scope"><pre class="max-h-40 overflow-auto rounded bg-slate-100 p-2 text-xs">{{ formatJson(scope.row.content) }}</pre></template>
        </el-table-column>
        <el-table-column :label="t('common.actions')" width="180">
          <template #default="scope">
            <el-button size="small" @click="approveProposal(scope.row)">{{ t('common.approve') }}</el-button>
            <el-button size="small" type="danger" @click="rejectProposal(scope.row)">{{ t('common.reject') }}</el-button>
            <el-button size="small" type="success" @click="generateModule(scope.row)">{{ t('pages.aiProposals.generateModuleProposal') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </main>
</template>
