import { getJson, postJson } from './client'
import type { Task, TaskPayload } from './tasks'

export interface LocalizedText {
  'zh-CN': string
  'en-US': string
}

export interface OperationTask {
  task_key: string
  name: LocalizedText
  description: LocalizedText
  parameters: Record<string, unknown>
}

export interface OperationModule {
  module_key: string
  name: LocalizedText
  description: LocalizedText
  tasks: OperationTask[]
}

export interface PlaybookPreview {
  module_key: string
  task_key: string
  parameters: Record<string, unknown>
  playbook: Record<string, unknown>[]
}

export function listOperationModules() {
  return getJson<OperationModule[]>('/operation-modules')
}

export function getOperationModule(moduleKey: string) {
  return getJson<OperationModule>(`/operation-modules/${moduleKey}`)
}

export function previewOperationTaskPlaybook(moduleKey: string, taskKey: string, parameters: Record<string, unknown>) {
  return postJson<PlaybookPreview>(`/operation-modules/${moduleKey}/tasks/${taskKey}/preview-playbook`, { parameters })
}

export function listOperationModuleRecentTasks(moduleKey: string) {
  return getJson<Task[]>(`/operation-modules/${moduleKey}/recent-tasks`)
}

export function createOperationModuleTask(moduleKey: string, taskKey: string, payload: Omit<TaskPayload, 'module_key' | 'module_task_key'>) {
  return postJson<Task>(`/operation-modules/${moduleKey}/tasks/${taskKey}/create-task`, payload)
}
