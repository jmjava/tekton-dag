import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '../composables/useApi'

export const useRunsStore = defineStore('runs', () => {
  const runs = ref([])
  const loading = ref(false)
  const error = ref('')
  let intervalId = null

  async function fetchRuns() {
    const { teamUrl, get } = useApi()
    try {
      const data = await get(teamUrl('/pipelineruns?limit=50'))
      runs.value = data.items || []
      error.value = ''
    } catch (e) {
      error.value = e.message || 'Failed to load pipeline runs'
      runs.value = []
    } finally {
      loading.value = false
    }
  }

  function startPolling(intervalMs = 10000) {
    stopPolling()
    loading.value = true
    fetchRuns()
    intervalId = setInterval(fetchRuns, intervalMs)
  }

  function stopPolling() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  function reset() {
    stopPolling()
    runs.value = []
    error.value = ''
  }

  return { runs, loading, error, fetchRuns, startPolling, stopPolling, reset }
})
