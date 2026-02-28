<template>
  <div>
    <h1>Monitor jobs</h1>
    <p>Recent PipelineRuns (polling every 10s).</p>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Pipeline</th>
            <th>Status</th>
            <th>Start</th>
            <th>Duration</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in runs" :key="run.name">
            <td>{{ run.name }}</td>
            <td>{{ run.pipeline }}</td>
            <td :class="'status-' + run.status">{{ run.status }}</td>
            <td>{{ formatTime(run.startTime) }}</td>
            <td>{{ run.durationSeconds != null ? run.durationSeconds + 's' : '-' }}</td>
            <td>
              <router-link :to="'/monitor/' + run.name">Detail</router-link>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="runs.length === 0 && !loading">No pipeline runs found.</p>
      <p v-if="loading">Loading…</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const runs = ref([]);
const loading = ref(true);
const error = ref('');

const api = import.meta.env.VITE_API_URL || '';

async function fetchRuns() {
  try {
    const r = await fetch(`${api}/api/pipelineruns?limit=50`);
    if (!r.ok) throw new Error(await r.text());
    const data = await r.json();
    runs.value = data.items || [];
    error.value = '';
  } catch (e) {
    error.value = e.message || 'Failed to load pipeline runs';
    runs.value = [];
  } finally {
    loading.value = false;
  }
}

function formatTime(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleString();
}

let interval;
onMounted(() => {
  fetchRuns();
  interval = setInterval(fetchRuns, 10000);
});
onUnmounted(() => clearInterval(interval));
</script>

<style scoped>
  .error { color: #c00; margin: 1rem 0; }
</style>
