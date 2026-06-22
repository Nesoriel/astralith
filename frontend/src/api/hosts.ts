import { deleteJson, getJson, postJson, putJson } from './client'

export interface HostPayload {
  name: string
  ip_address: string
  ssh_port: number
  ssh_user: string
  private_key_path: string
  description?: string | null
}

export interface Host extends HostPayload {
  id: number
  created_at: string
  updated_at: string
}

export interface HostGroupPayload {
  name: string
  description?: string | null
}

export interface HostGroup extends HostGroupPayload {
  id: number
  host_ids: number[]
  created_at: string
  updated_at: string
}

export interface HostConnectionTestResult {
  host_id: number
  status: string
  message: string
}

export function listHosts() {
  return getJson<Host[]>('/hosts')
}

export function createHost(payload: HostPayload) {
  return postJson<Host>('/hosts', payload)
}

export function updateHost(id: number, payload: HostPayload) {
  return putJson<Host>(`/hosts/${id}`, payload)
}

export function deleteHost(id: number) {
  return deleteJson(`/hosts/${id}`)
}

export function testHostConnection(id: number) {
  return postJson<HostConnectionTestResult>(`/hosts/${id}/test-connection`)
}

export function listHostGroups() {
  return getJson<HostGroup[]>('/host-groups')
}

export function createHostGroup(payload: HostGroupPayload) {
  return postJson<HostGroup>('/host-groups', payload)
}

export function deleteHostGroup(id: number) {
  return deleteJson(`/host-groups/${id}`)
}

export function addHostToGroup(groupId: number, hostId: number) {
  return postJson<HostGroup>(`/host-groups/${groupId}/hosts`, { host_id: hostId })
}

export function removeHostFromGroup(groupId: number, hostId: number) {
  return deleteJson(`/host-groups/${groupId}/hosts/${hostId}`)
}
