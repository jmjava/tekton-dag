import { useTeamsStore } from '../stores/teams'

const BASE = import.meta.env.VITE_API_URL || ''

export function useApi() {
  function teamUrl(path) {
    const teams = useTeamsStore()
    return `${BASE}/api/teams/${teams.activeTeam}${path}`
  }

  function globalUrl(path) {
    return `${BASE}/api${path}`
  }

  async function get(url) {
    const r = await fetch(url)
    if (!r.ok) throw new Error(await r.text())
    return r.json()
  }

  function mutationHeaders() {
    const token = sessionStorage.getItem('tektonDagApiToken') || import.meta.env.VITE_API_MUTATION_TOKEN
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }
  }

  async function post(url, body) {
    const r = await fetch(url, {
      method: 'POST',
      headers: mutationHeaders(),
      body: JSON.stringify(body),
    })
    const data = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(data.error || r.statusText)
    return data
  }

  async function patch(url, body) {
    const r = await fetch(url, {
      method: 'PATCH',
      headers: mutationHeaders(),
      body: JSON.stringify(body),
    })
    const data = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(data.error || r.statusText)
    return data
  }

  return { teamUrl, globalUrl, get, post, patch }
}
