import { getJson } from './client'

export interface DashboardSummary {
  hosts: number
  host_groups: number
  operation_modules: number
  operation_tasks: number
  tasks_total: number
  tasks_failed: number
  tasks_success_rate: number
  scheduled_jobs: number
  gitops_repositories: number
  resource_diffs: number
  pending_apply_plans: number
  blocked_policy_results: number
  ai_analyses: number
  pending_ai_proposals: number
  pending_module_proposals: number
}

export function getDashboardSummary() {
  return getJson<DashboardSummary>('/dashboard/summary')
}
