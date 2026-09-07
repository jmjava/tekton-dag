<template>
  <div>
    <h1>Run: {{ name }}</h1>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="run">
      <p>
        <strong>Mode:</strong> {{ run.mode || run.pipeline }}
        · <StatusBadge :status="run.status" />
      </p>
      <p v-if="run.stackRef || run.stackFile">
        <strong>Stack:</strong> {{ run.stackRef || run.stackFile }}
      </p>
      <p v-if="run.changedApp"><strong>Changed app:</strong> {{ run.changedApp }}</p>
      <p v-if="run.prNumber"><strong>PR:</strong> {{ run.prNumber }}</p>
      <p v-if="run.pipelineRunName">
        <strong>PipelineRun:</strong> {{ run.pipelineRunName }}
      </p>
      <p v-if="run.startTime">Start: {{ formatTime(run.startTime) }}</p>
      <p v-if="run.completionTime">Completion: {{ formatTime(run.completionTime) }}</p>
      <p v-if="run.message" class="muted">{{ run.message }}</p>

      <section v-if="showApprove" class="approve">
        <h2>Promote approval</h2>
        <p>This StackRun is waiting for <code>spec.approvedBy</code> before the operator creates a PipelineRun.</p>
        <form @submit.prevent="approve" class="approve-form">
          <label>
            Approved by
            <input v-model="approver" type="text" required placeholder="your name" />
          </label>
          <button type="submit" :disabled="approving">Approve</button>
        </form>
        <p v-if="approveError" class="error">{{ approveError }}</p>
      </section>
      <p v-else-if="run.approvedBy" class="muted">Approved by {{ run.approvedBy }}</p>

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
const { teamUrl, get, patch } = useApi()

const run = ref(null)
const taskruns = ref([])
const error = ref('')
const approver = ref('')
const approving = ref(false)
const approveError = ref('')

const showApprove = computed(() => {
  const r = run.value
  if (!r) return false
  return r.mode === 'promote' && r.requireApproval && !r.approvedBy
})

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

async function loadTaskruns(pipelineRunName) {
  if (!pipelineRunName) {
    taskruns.value = []
    return
  }
  try {
    const data = await get(teamUrl(`/taskruns?pipelineRun=${encodeURIComponent(pipelineRunName)}`))
    taskruns.value = data.items || []
  } catch {
    taskruns.value = []
  }
}

async function loadRun() {
  run.value = await get(teamUrl(`/stackruns/${name.value}`))
  await loadTaskruns(run.value.pipelineRunName)
}

async function approve() {
  approveError.value = ''
  approving.value = true
  try {
    run.value = await patch(teamUrl(`/stackruns/${name.value}`), { approvedBy: approver.value })
    await loadTaskruns(run.value.pipelineRunName)
  } catch (e) {
    approveError.value = e.message || 'Approve failed'
  } finally {
    approving.value = false
  }
}

onMounted(async () => {
  try {
    await loadRun()
  } catch (e) {
    error.value = e.message || 'Failed to load run'
  }
})
</script>

<style scoped>
.error { color: #c00; margin: 1rem 0; }
.muted { color: #555; }
.test-results { margin: 1rem 0; }
.test-summary { background: #f5f5f5; padding: 0.75rem; overflow: auto; font-size: 0.9rem; border-radius: 4px; }
.approve { margin: 1.25rem 0; padding: 1rem; border: 1px solid #c9a227; border-radius: 6px; background: #fff8e1; }
.approve-form { display: flex; gap: 0.5rem; align-items: flex-end; flex-wrap: wrap; }
.approve-form label { display: flex; flex-direction: column; font-size: 0.9rem; font-weight: 500; }
.approve-form input { padding: 0.4rem; border: 1px solid #ccc; border-radius: 4px; min-width: 12rem; }
.approve-form button { padding: 0.45rem 0.9rem; background: #1a1a2e; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
.approve-form button:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
