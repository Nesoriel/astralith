import { deleteJson, getJson, postJson, putJson } from './client'

export interface ScheduledJobPayload {
  name: string
  module_key: string
  module_task_key: string
  target_type: 'hosts' | 'host_groups'
  target_ids: number[]
  parameters: Record<string, unknown>
  schedule_type: 'cron' | 'interval'
  cron_expression?: string | null
  interval_seconds?: number | null
  enabled: boolean
}

export interface ScheduledJob extends ScheduledJobPayload {
  id: number
  created_at: string
  updated_at: string
  last_run_at?: string | null
  next_run_at?: string | null
}

export interface ScheduledJobTriggerResult {
  scheduled_job_id: number
  task_id: number
}

export function listScheduledJobs() {
  return getJson<ScheduledJob[]>('/scheduled-jobs')
}

export function createScheduledJob(payload: ScheduledJobPayload) {
  return postJson<ScheduledJob>('/scheduled-jobs', payload)
}

export function updateScheduledJob(id: number, payload: ScheduledJobPayload) {
  return putJson<ScheduledJob>(`/scheduled-jobs/${id}`, payload)
}

export function deleteScheduledJob(id: number) {
  return deleteJson(`/scheduled-jobs/${id}`)
}

export function enableScheduledJob(id: number) {
  return postJson<ScheduledJob>(`/scheduled-jobs/${id}/enable`)
}

export function disableScheduledJob(id: number) {
  return postJson<ScheduledJob>(`/scheduled-jobs/${id}/disable`)
}

export function triggerScheduledJob(id: number) {
  return postJson<ScheduledJobTriggerResult>(`/scheduled-jobs/${id}/trigger`)
}
