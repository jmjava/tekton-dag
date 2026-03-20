<template>
  <div>
    <h1>Run: {{ name }}</h1>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="run">
      <p><strong>Pipeline:</strong> {{ run.pipeline }} · <StatusBadge :status="run.status" /></p>
      <p v-if="run.startTime">Start: {{ formatTime(run.startTime) }}</p>
      <p v-if="run.completionTime">Completion: {{ formatTime(run.completionTime) }}</p>

      <section v-if="run.testSummary" class="test-results">
        <h2>Test results</h2>
        <pre class="test-summary">{{ formatTestSummary(run.testSummary) }}</pre>
      </section>

      <h2>TaskRuns</h2>
      <DataTable :columns="taskColumns" :rows="taskruns" empty-text="No task runs or still loading.">
        <template #status="{ value }">
          <StatusBadge :status="value" />
        </template>
        <template #startTime="{ value }">{{ formatTime(value) }}</template>
      </DataTable>
    </div>
    <p v-else>Loading...</p>
    <p><router-link to="/monitor">← Back to Monitor</router-link></p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useApi } from '../composables/useApi'
import DataTable from '../components/DataTable.vue'
import StatusBadge from '../components/StatusBadge.vue'

const route = useRoute()
const name = computed(() => route.params.name)
const { teamUrl, get } = useApi()

const run = ref(null)
const taskruns = ref([])
const error = ref('')

const taskColumns = [
  { key: 'name', label: 'Name' },
  { key: 'task', label: 'Task' },
  { key: 'status', label: 'Status' },
  { key: 'startTime', label: 'Start' },
]

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString()
}

function formatTestSummary(val) {
  if (!val) return ''
  try {
    const o = typeof val === 'string' ? JSON.parse(val) : val
    return JSON.stringify(o, null, 2)
  } catch {
    return val
  }
}

onMounted(async () => {
  try {
    run.value = await get(teamUrl(`/pipelineruns/${name.value}`))
  } catch (e) {
    error.value = e.message || 'Failed to load run'
    return
  }
  try {
    const data = await get(teamUrl(`/taskruns?pipelineRun=${name.value}`))
    taskruns.value = data.items || []
  } catch {
    taskruns.value = []
  }
})
</script>

<style scoped>
.error { color: #c00; margin: 1rem 0; }
.test-results { margin: 1rem 0; }
.test-summary { background: #f5f5f5; padding: 0.75rem; overflow: auto; font-size: 0.9rem; border-radius: 4px; }
</style>
