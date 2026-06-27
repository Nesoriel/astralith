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
