<template>
  <div>
    <h1>Tekton Dashboard</h1>
    <p>Embedded Tekton Dashboard (iframe). Set base URL below or use <code>VITE_DASHBOARD_URL</code>.</p>
    <div class="dashboard-controls">
      <label>
        Dashboard base URL
        <input v-model="baseUrl" type="text" placeholder="http://localhost:9097" />
      </label>
      <label class="view-select">
        View
        <select v-model="view">
          <option value="list">PipelineRuns list</option>
          <option value="detail">Run detail</option>
        </select>
      </label>
      <template v-if="view === 'detail'">
        <label>
          Namespace
          <input v-model="runNamespace" type="text" placeholder="tekton-pipelines" />
        </label>
        <label>
          PipelineRun name
          <input v-model="runName" type="text" placeholder="stack-pr-1-abc12" />
        </label>
      </template>
    </div>
    <p class="muted">If the Dashboard blocks embedding (X-Frame-Options), use "Open in new tab" or serve both under the same origin.</p>
    <div v-if="iframeSrc" class="iframe-wrap">
      <iframe :src="iframeSrc" title="Tekton Dashboard" class="dashboard-iframe" />
    </div>
    <p v-else>Enter Dashboard base URL (e.g. http://localhost:9097) to load.</p>
    <p v-if="baseUrl">
      <a :href="iframeSrc" target="_blank" rel="noopener">Open in new tab</a>
    </p>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const baseUrl = ref(import.meta.env.VITE_DASHBOARD_URL || '');
const view = ref('list');
const runNamespace = ref('tekton-pipelines');
const runName = ref('');

// When navigating from Monitor with ?run=name&namespace=ns, prefill and show detail
watch(() => route.query.run, (run) => {
  if (run) {
    runName.value = run;
    view.value = 'detail';
  }
}, { immediate: true });
watch(() => route.query.namespace, (ns) => {
  if (ns) runNamespace.value = ns;
}, { immediate: true });

const iframeSrc = computed(() => {
  const base = (baseUrl.value || '').replace(/\/$/, '');
  if (!base) return '';
  if (view.value === 'detail' && runName.value) {
    return `${base}/#/namespaces/${runNamespace.value || 'tekton-pipelines'}/pipelineruns/${runName.value}`;
  }
  return `${base}/#/namespaces/${runNamespace.value || 'tekton-pipelines'}/pipelineruns`;
});
</script>

<style scoped>
  .muted { color: #666; }
  .dashboard-controls { display: flex; flex-wrap: wrap; gap: 1rem; align-items: flex-end; margin: 1rem 0; }
  .dashboard-controls label { display: flex; flex-direction: column; gap: 0.25rem; }
  .dashboard-controls input, .dashboard-controls select { padding: 0.35rem; min-width: 180px; }
  .iframe-wrap { margin-top: 1rem; border: 1px solid #ccc; border-radius: 4px; overflow: hidden; min-height: 600px; }
  .dashboard-iframe { width: 100%; height: 80vh; min-height: 600px; border: 0; }
  code { font-size: 0.9em; }
</style>
