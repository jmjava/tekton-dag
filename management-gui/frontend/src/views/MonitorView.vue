<template>
  <div>
    <h1>Monitor jobs</h1>
    <p>Recent PipelineRuns (polling every 10s).</p>
    <div v-if="store.error" class="error">{{ store.error }}</div>
    <DataTable v-else :columns="columns" :rows="store.runs" empty-text="No pipeline runs found.">
      <template #status="{ value }">
        <StatusBadge :status="value" />
      </template>
      <template #startTime="{ value }">{{ formatTime(value) }}</template>
      <template #durationSeconds="{ value }">{{ value != null ? value + 's' : '-' }}</template>
      <template #name="{ row }">
        <router-link :to="'/monitor/' + row.name">{{ row.name }}</router-link>
      </template>
    </DataTable>
    <p v-if="store.loading">Loading...</p>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { useRunsStore } from '../stores/runs'
import { useTeamsStore } from '../stores/teams'
import DataTable from '../components/DataTable.vue'
import StatusBadge from '../components/StatusBadge.vue'

const store = useRunsStore()
const teams = useTeamsStore()

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'pipeline', label: 'Pipeline' },
  { key: 'status', label: 'Status' },
  { key: 'startTime', label: 'Start' },
  { key: 'durationSeconds', label: 'Duration' },
]

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString()
}

watch(() => teams.activeTeam, () => { if (teams.activeTeam) store.startPolling() })
onMounted(() => { if (teams.activeTeam) store.startPolling() })
onUnmounted(() => store.stopPolling())
</script>

<style scoped>
.error { color: #c00; margin: 1rem 0; }
</style>
