import { getJson, postJson, putJson } from './client'

export interface GitOpsRepositoryPayload {
  name: string
  repo_url: string
  branch: string
  local_path: string
  auth_type: string
  enabled: boolean
}

export interface GitOpsRepository extends GitOpsRepositoryPayload {
  id: number
  last_sync_at?: string | null
  last_commit_sha?: string | null
  created_at: string
  updated_at: string
}

export interface GitOpsSyncRun {
  id: number
  repository_id: number
  commit_sha?: string | null
  status: string
  stdout?: string | null
  stderr?: string | null
  started_at: string
  finished_at?: string | null
}

export interface DesiredResource {
  id: number
  repository_id: number
  commit_sha: string
  resource_type: string
  resource_key: string
  file_path: string
  content: Record<string, unknown>
  content_hash: string
}

export interface ActualResourcePayload {
  resource_type: string
  resource_key: string
  source: string
  content: Record<string, unknown>
}

export interface ActualResource extends ActualResourcePayload {
  id: number
  content_hash: string
  scanned_at: string
}

export interface ResourceDiff {
  id: number
  repository_id: number
  resource_type: string
  resource_key: string
  diff_type: string
  before?: Record<string, unknown> | null
  after?: Record<string, unknown> | null
  risk_level: string
  created_at: string
}

export interface ApplyPlan {
  id: number
  repository_id: number
  diff_id: number
  plan: {
    resource_type: string
    resource_key: string
    diff_type: string
    steps: string[]
    rollback: string
  }
  status: string
  policy_status: string
  ai_summary?: string | null
  approved_by?: number | null
  approved_at?: string | null
  created_at: string
}

export interface PolicyResult {
  id: number
  repository_id: number
  plan_id: number
  rule_key: string
  severity: string
  passed: boolean
  message: string
  created_at: string
}

export interface GitOpsApplyRun {
  id: number
  repository_id: number
  plan_id: number
  stack_name: string
  target_path: string
  commit_sha?: string | null
  status: string
  stdout?: string | null
  stderr?: string | null
  raw_event_data?: string | null
  rollback_json: string
  started_at: string
  finished_at?: string | null
}
export function listGitOpsRepositories() {
  return getJson<GitOpsRepository[]>('/gitops-repositories')
}

export function createGitOpsRepository(payload: GitOpsRepositoryPayload) {
  return postJson<GitOpsRepository>('/gitops-repositories', payload)
}

export function updateGitOpsRepository(id: number, payload: GitOpsRepositoryPayload) {
  return putJson<GitOpsRepository>(`/gitops-repositories/${id}`, payload)
}

export function syncGitOpsRepository(id: number) {
  return postJson<GitOpsSyncRun>(`/gitops-repositories/${id}/sync`)
}

export function listGitOpsSyncRuns(id: number) {
  return getJson<GitOpsSyncRun[]>(`/gitops-repositories/${id}/sync-runs`)
}

export function listDesiredResources(id: number) {
  return getJson<DesiredResource[]>(`/gitops-repositories/${id}/desired-resources`)
}

export function upsertActualResource(payload: ActualResourcePayload) {
  return postJson<ActualResource>('/gitops-repositories/actual-resources', payload)
}

export function listActualResources() {
  return getJson<ActualResource[]>('/gitops-repositories/actual-resources')
}

export function generateDiffs(id: number) {
  return postJson<ResourceDiff[]>(`/gitops-repositories/${id}/diff`)
}

export function listDiffs(id: number) {
  return getJson<ResourceDiff[]>(`/gitops-repositories/${id}/diffs`)
}

export function listApplyPlans(id: number) {
  return getJson<ApplyPlan[]>(`/gitops-repositories/${id}/apply-plans`)
}

export function listPolicyResults(id: number) {
  return getJson<PolicyResult[]>(`/gitops-repositories/${id}/policy-results`)
}

export function approveApplyPlan(id: number) {
  return postJson<ApplyPlan>(`/gitops-repositories/apply-plans/${id}/approve`)
}

export function executeApplyPlan(id: number) {
  return postJson<GitOpsApplyRun>(`/gitops-repositories/apply-plans/${id}/execute`)
}

export function listApplyRuns(repositoryId: number) {
  return getJson<GitOpsApplyRun[]>(`/gitops-repositories/${repositoryId}/apply-runs`)
}
