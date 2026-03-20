import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTeamsStore = defineStore('teams', () => {
  const teams = ref([])
  const activeTeam = ref('')
  const loading = ref(false)

  const showSwitcher = computed(() => teams.value.length > 1)

  async function fetchTeams() {
    loading.value = true
    try {
      const base = import.meta.env.VITE_API_URL || ''
      const r = await fetch(`${base}/api/teams`)
      if (r.ok) {
        teams.value = await r.json()
        if (teams.value.length && !activeTeam.value) {
          activeTeam.value = teams.value[0].name
        }
      }
    } catch {
      teams.value = []
    } finally {
      loading.value = false
    }
  }

  function setActiveTeam(name) {
    activeTeam.value = name
  }

  return { teams, activeTeam, loading, showSwitcher, fetchTeams, setActiveTeam }
})
