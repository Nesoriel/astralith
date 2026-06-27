import { getJson, postJson } from './client'

export interface OperationModuleProposalPayload {
  source_ai_proposal_id?: number | null
  title: string
  problem_summary: string
  module_key: string
  task_key: string
  risk_level: string
  parameter_schema: Record<string, unknown>
  runbook: string
  playbook: Record<string, unknown>
  test_plan: string[]
  rollback_notes: string
}

export interface OperationModuleProposal extends OperationModuleProposalPayload {
  id: number
  status: string
  validation_status: string
  validation_output?: string | null
  dangerous_command_detected: boolean
  review_comment?: string | null
  reviewed_by?: number | null
  reviewed_at?: string | null
  created_at: string
}

export interface OperationModuleProposalExport {
  module_key: string
  task_key: string
  metadata: Record<string, unknown>
  playbook: Record<string, unknown>
  runbook: string
  tests: string[]
  rollback_notes: string
}

export function listOperationModuleProposals() {
  return getJson<OperationModuleProposal[]>('/operation-module-proposals')
}

export function createOperationModuleProposal(payload: OperationModuleProposalPayload) {
  return postJson<OperationModuleProposal>('/operation-module-proposals', payload)
}

export function generateOperationModuleProposalFromAi(aiProposalId: number) {
  return postJson<OperationModuleProposal>(`/operation-module-proposals/from-ai-proposals/${aiProposalId}`)
}

export function approveOperationModuleProposal(id: number, review_comment: string) {
  return postJson<OperationModuleProposal>(`/operation-module-proposals/${id}/approve`, { review_comment })
}

export function rejectOperationModuleProposal(id: number, review_comment: string) {
  return postJson<OperationModuleProposal>(`/operation-module-proposals/${id}/reject`, { review_comment })
}

export function implementOperationModuleProposal(id: number, review_comment: string) {
  return postJson<OperationModuleProposal>(`/operation-module-proposals/${id}/implement`, { review_comment })
}

export function exportOperationModuleProposal(id: number) {
  return getJson<OperationModuleProposalExport>(`/operation-module-proposals/${id}/export`)
}
