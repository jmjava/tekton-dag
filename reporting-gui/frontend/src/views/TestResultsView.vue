<template>
  <div>
    <h1>Test results</h1>
    <p>View test summary and pass/fail per run. Canned views below.</p>

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

    <div v-if="error" class="error">{{ error }}</div>
    <table v-else-if="filteredRuns.length">
      <thead>
        <tr>
          <th>Run</th>
          <th>Pipeline</th>
          <th>Status</th>
          <th>Start</th>
          <th>Test summary</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="run in filteredRuns" :key="run.name">
          <td>{{ run.name }}</td>
          <td>{{ run.pipeline }}</td>
          <td :class="'status-' + run.status">{{ run.status }}</td>
          <td>{{ formatTime(run.startTime) }}</td>
          <td class="summary-cell">{{ summaryPreview(run.testSummary) }}</td>
          <td><router-link :to="'/monitor/' + run.name">Detail</router-link></td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading">No runs match the filter.</p>
    <p v-if="loading">Loading…</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const api = import.meta.env.VITE_API_URL || '';
const runs = ref([]);
const loading = ref(true);
const error = ref('');
const filter = ref('last');

const filteredRuns = computed(() => {
  let list = [...runs.value];
  const now = Date.now();
  const day = 24 * 60 * 60 * 1000;
  if (filter.value === 'failed24') {
    list = list.filter((r) => r.status === 'Failed' && r.startTime && (now - new Date(r.startTime).getTime()) < day);
  } else if (filter.value === 'succeeded') {
    list = list.filter((r) => r.status === 'Succeeded').slice(0, 20);
  } else {
    list = list.slice(0, 50);
  }
  return list;
});

function formatTime(iso) {
  if (!iso) return '-';
  return new Date(iso).toLocaleString();
}
function summaryPreview(val) {
  if (!val) return '—';
  try {
    const o = typeof val === 'string' ? JSON.parse(val) : val;
    return typeof o === 'object' ? JSON.stringify(o).slice(0, 80) + (JSON.stringify(o).length > 80 ? '…' : '') : String(o);
  } catch {
    return String(val).slice(0, 60);
  }
}

onMounted(async () => {
  try {
    const r = await fetch(`${api}/api/pipelineruns?limit=100`);
    if (!r.ok) throw new Error(await r.text());
    const data = await r.json();
    runs.value = data.items || [];
    error.value = '';
  } catch (e) {
    error.value = e.message || 'Failed to load runs';
    runs.value = [];
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
  .filters { margin-bottom: 1rem; }
  .error { color: #c00; margin: 1rem 0; }
  .summary-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; font-size: 0.85rem; }
</style>
