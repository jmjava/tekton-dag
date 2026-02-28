<template>
  <div>
    <h1>Run: {{ name }}</h1>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="run">
      <p><strong>Pipeline:</strong> {{ run.pipeline }} · <span :class="'status-' + run.status">{{ run.status }}</span></p>
      <p v-if="run.startTime">Start: {{ formatTime(run.startTime) }}</p>
      <p v-if="run.completionTime">Completion: {{ formatTime(run.completionTime) }}</p>
      <section v-if="run.testSummary" class="test-results">
        <h2>Test results</h2>
        <pre class="test-summary">{{ formatTestSummary(run.testSummary) }}</pre>
      </section>
      <h2>TaskRuns</h2>
      <table v-if="taskruns.length">
        <thead>
          <tr>
            <th>Name</th>
            <th>Task</th>
            <th>Status</th>
            <th>Start</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tr in taskruns" :key="tr.name">
            <td>{{ tr.name }}</td>
            <td>{{ tr.task }}</td>
            <td :class="'status-' + tr.status">{{ tr.status }}</td>
            <td>{{ formatTime(tr.startTime) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else>No task runs or still loading.</p>
      <p v-if="dashboardUrl" class="dashboard-link">
        <a :href="dashboardRunUrl" target="_blank" rel="noopener">Open in Tekton Dashboard</a>
        <span class="sep">·</span>
        <router-link :to="'/dashboard?run=' + encodeURIComponent(run.name) + '&namespace=' + encodeURIComponent(run.namespace || 'tekton-pipelines')">Embed in Dashboard tab</router-link>
      </p>
    </div>
    <p v-else>Loading…</p>
    <p><router-link to="/monitor">← Back to Monitor</router-link></p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const name = computed(() => route.params.name);

const run = ref(null);
const taskruns = ref([]);
const error = ref('');

const api = import.meta.env.VITE_API_URL || '';
const dashboardUrl = computed(() => import.meta.env.VITE_DASHBOARD_URL || '');
const dashboardRunUrl = computed(() => {
  if (!dashboardUrl.value || !run.value) return '';
  const ns = run.value.namespace || 'tekton-pipelines';
  const base = dashboardUrl.value.replace(/\/$/, '');
  return `${base}/#/namespaces/${ns}/pipelineruns/${run.value.name}`;
});

function formatTime(iso) {
  if (!iso) return '-';
  return new Date(iso).toLocaleString();
}
function formatTestSummary(val) {
  if (!val) return '';
  try {
    const o = typeof val === 'string' ? JSON.parse(val) : val;
    return JSON.stringify(o, null, 2);
  } catch {
    return val;
  }
}

onMounted(async () => {
  try {
    const r = await fetch(`${api}/api/pipelineruns/${name.value}`);
    if (!r.ok) throw new Error(await r.text());
    run.value = await r.json();
  } catch (e) {
    error.value = e.message || 'Failed to load run';
    return;
  }
  try {
    const tr = await fetch(`${api}/api/taskruns?pipelineRun=${name.value}`);
    if (tr.ok) {
      const data = await tr.json();
      taskruns.value = data.items || [];
    }
  } catch {
    taskruns.value = [];
  }
});
</script>

<style scoped>
  .error { color: #c00; margin: 1rem 0; }
  .dashboard-link { margin-top: 1rem; }
  .sep { margin: 0 0.5rem; color: #666; }
  .test-results { margin: 1rem 0; }
  .test-summary { background: #f5f5f5; padding: 0.75rem; overflow: auto; font-size: 0.9rem; }
</style>
