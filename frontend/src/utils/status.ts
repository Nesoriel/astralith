export type TagType = 'success' | 'warning' | 'danger' | 'info'

export function statusTagType(status: string): TagType {
  if (['success', 'approved', 'implemented', 'passed'].includes(status)) return 'success'
  if (['failed', 'cancelled', 'rejected', 'blocked'].includes(status)) return 'danger'
  if (['running', 'pending', 'partial_success', 'pending_review', 'reviewing', 'draft'].includes(status)) return 'warning'
  return 'info'
}

export function riskTagType(risk: string): TagType {
  if (['high', 'critical'].includes(risk)) return 'danger'
  if (risk === 'medium') return 'warning'
  if (risk === 'low') return 'success'
  return 'info'
}

export function parseJsonObject(text: string): Record<string, unknown> {
  const parsed = JSON.parse(text) as unknown
  if (parsed === null || Array.isArray(parsed) || typeof parsed !== 'object') {
    throw new Error('JSON must be an object')
  }
  return parsed as Record<string, unknown>
}
