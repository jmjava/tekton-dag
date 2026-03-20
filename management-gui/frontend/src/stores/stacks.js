import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useApi } from '../composables/useApi'

export const useStacksStore = defineStore('stacks', () => {
  const stacks = ref([])
  const loading = ref(false)

  async function fetchStacks() {
    const { teamUrl, get } = useApi()
    loading.value = true
    try {
      stacks.value = await get(teamUrl('/stacks'))
    } catch {
      stacks.value = []
    } finally {
      loading.value = false
    }
  }

  function reset() {
    stacks.value = []
  }

  return { stacks, loading, fetchStacks, reset }
})
