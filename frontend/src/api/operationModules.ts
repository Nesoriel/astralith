import { getJson } from './client'

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

export function listOperationModules() {
  return getJson<OperationModule[]>('/operation-modules')
}
