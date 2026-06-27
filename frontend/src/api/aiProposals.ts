import { getJson, postJson } from './client'

export interface AiProposalPayload {
  proposal_type: string
  title: string
  summary: string
  content: Record<string, unknown>
  risk_level: string
  source_type?: string | null
  source_id?: number | null
}

export interface AiProposal {
  id: number
  proposal_type: string
  title: string
  summary: string
  content: Record<string, unknown>
  risk_level: string
  status: string
  source_type?: string | null
  source_id?: number | null
  review_comment?: string | null
  reviewed_by?: number | null
  reviewed_at?: string | null
  created_at: string
}

export function listAiProposals() {
  return getJson<AiProposal[]>('/ai-proposals')
}

export function createAiProposal(payload: AiProposalPayload) {
  return postJson<AiProposal>('/ai-proposals', payload)
}

export function approveAiProposal(id: number, review_comment: string) {
  return postJson<AiProposal>(`/ai-proposals/${id}/approve`, { review_comment })
}

export function rejectAiProposal(id: number, review_comment: string) {
  return postJson<AiProposal>(`/ai-proposals/${id}/reject`, { review_comment })
}

export function generateProposalFromApplyPlan(planId: number) {
  return postJson<AiProposal>(`/gitops-repositories/apply-plans/${planId}/ai-proposal`)
}
