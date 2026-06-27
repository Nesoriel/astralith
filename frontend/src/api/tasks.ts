import { getJson, postJson } from './client'

export interface TaskPayload {
  name: string
  module_key: string
  module_task_key: string
  target_type: 'hosts' | 'host_groups'
  target_ids: number[]
  parameters: Record<string, unknown>
}

export interface Task extends TaskPayload {
  id: number
  status: 'pending' | 'running' | 'success' | 'partial_success' | 'failed' | 'cancelled'
  created_at: string
  updated_at: string
  started_at?: string | null
  finished_at?: string | null
}

export interface TaskResult {
  id: number
  task_id: number
  host_id?: number | null
  status: string
  stdout?: string | null
  stderr?: string | null
  raw_event_data?: string | null
  started_at?: string | null
  finished_at?: string | null
}

export interface TaskLogs {
  task: Task
  results: TaskResult[]
  ai_analyses: AiAnalysisResult[]
}

export interface AiAnalysisResult {
  id: number
  evidence_pack_id: number
  summary: string
  content: {
    risk_level: string
    key_evidence: string[]
    possible_causes: string[]
    recommended_steps: string[]
    review_notes: string[]
    source: Record<string, unknown>
  }
  model_name?: string | null
  created_at: string
}

export function listTasks() {
  return getJson<Task[]>('/tasks')
}

export function createTask(payload: TaskPayload) {
  return postJson<Task>('/tasks', payload)
}

export function getTaskLogs(id: number) {
  return getJson<TaskLogs>(`/tasks/${id}/logs`)
}

export function createTaskAiAnalysis(id: number) {
  return postJson<AiAnalysisResult>(`/tasks/${id}/ai-analysis`)
}
