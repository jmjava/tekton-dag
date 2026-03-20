<template>
  <div>
    <h1>Test results</h1>
    <p>View test summary and pass/fail per run.</p>

    <div class="filters">
      <label>
        View:
        <select v-model="filter">
          <option value="last">Last 50 runs</option>
          <option value="failed24">Failed in last 24h</option>
          <option value="succeeded">Last 20 succeeded</option>
        </select>
      </label>
    </div>

    <div v-if="store.error" class="error">{{ store.error }}</div>
    <DataTable v-else :columns="columns" :rows="filteredRuns" empty-text="No runs match the filter.">
      <template #status="{ value }">
        <StatusBadge :status="value" />
      </template>
      <template #startTime="{ value }">{{ formatTime(value) }}</template>
      <template #testSummary="{ value }">
        <span class="summary-cell">{{ summaryPreview(value) }}</span>
      </template>
      <template #name="{ row }">
        <router-link :to="'/monitor/' + row.name">{{ row.name }}</router-link>
      </template>
    </DataTable>
    <p v-if="store.loading">Loading...</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRunsStore } from '../stores/runs'
import { useTeamsStore } from '../stores/teams'
import DataTable from '../components/DataTable.vue'
import StatusBadge from '../components/StatusBadge.vue'

const store = useRunsStore()
const teams = useTeamsStore()
const filter = ref('last')

const columns = [
  { key: 'name', label: 'Run' },
  { key: 'pipeline', label: 'Pipeline' },
  { key: 'status', label: 'Status' },
  { key: 'startTime', label: 'Start' },
  { key: 'testSummary', label: 'Test summary' },
]

const filteredRuns = computed(() => {
  let list = [...store.runs]
  const now = Date.now()
  const day = 24 * 60 * 60 * 1000
  if (filter.value === 'failed24') {
    list = list.filter(r => r.status === 'Failed' && r.startTime && (now - new Date(r.startTime).getTime()) < day)
  } else if (filter.value === 'succeeded') {
    list = list.filter(r => r.status === 'Succeeded').slice(0, 20)
  } else {
    list = list.slice(0, 50)
  }
  return list
})

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString()
}

function summaryPreview(val) {
  if (!val) return '—'
  try {
    const o = typeof val === 'string' ? JSON.parse(val) : val
    const s = typeof o === 'object' ? JSON.stringify(o) : String(o)
    return s.length > 80 ? s.slice(0, 80) + '...' : s
  } catch {
    return String(val).slice(0, 60)
  }
}

watch(() => teams.activeTeam, () => { if (teams.activeTeam) store.fetchRuns() })
onMounted(() => { if (teams.activeTeam && !store.runs.length) store.fetchRuns() })
</script>

<style scoped>
.filters { margin-bottom: 1rem; }
.error { color: #c00; margin: 1rem 0; }
.summary-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; font-size: 0.85rem; }
</style>
