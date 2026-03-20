<template>
  <div>
    <h1>Stack DAG</h1>
    <div class="controls">
      <label>
        Stack:
        <select v-model="selectedStack" @change="loadDag">
          <option value="">— select —</option>
          <option v-for="s in stacksStore.stacks" :key="s.stack_file" :value="s.stack_file">
            {{ s.name || s.stack_file }}
          </option>
        </select>
      </label>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="nodes.length" class="dag-container">
      <VueFlow :nodes="flowNodes" :edges="flowEdges" :default-viewport="{ zoom: 1 }" fit-view-on-init>
        <template #node-custom="{ data }">
          <div class="dag-node" :class="'role-' + data.propagationRole">
            <div class="node-name">{{ data.label }}</div>
            <div class="node-meta">{{ data.role }} · {{ data.runtime || data.build }}</div>
          </div>
        </template>
      </VueFlow>
    </div>
    <p v-else-if="selectedStack && !loading" class="muted">No apps in this stack.</p>
    <p v-else-if="!selectedStack" class="muted">Select a stack to view its application dependency graph.</p>
    <p v-if="loading">Loading DAG...</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { VueFlow } from '@vue-flow/core'
import dagre from '@dagrejs/dagre'
import { useStacksStore } from '../stores/stacks'
import { useTeamsStore } from '../stores/teams'
import { useApi } from '../composables/useApi'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const stacksStore = useStacksStore()
const teamsStore = useTeamsStore()
const { teamUrl, get } = useApi()

const selectedStack = ref('')
const nodes = ref([])
const edges = ref([])
const loading = ref(false)
const error = ref('')

function layoutDag(rawNodes, rawEdges) {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'LR', nodesep: 60, ranksep: 120 })

  for (const n of rawNodes) {
    g.setNode(n.id, { width: 180, height: 70 })
  }
  for (const e of rawEdges) {
    g.setEdge(e.source, e.target)
  }
  dagre.layout(g)

  return rawNodes.map(n => {
    const pos = g.node(n.id)
    return {
      id: n.id,
      type: 'custom',
      position: { x: pos.x - 90, y: pos.y - 35 },
      data: { label: n.id, role: n.role, propagationRole: n.propagationRole, build: n.build, runtime: n.runtime },
    }
  })
}

const flowNodes = computed(() => layoutDag(nodes.value, edges.value))
const flowEdges = computed(() => edges.value.map(e => ({
  id: `${e.source}-${e.target}`,
  source: e.source,
  target: e.target,
  animated: true,
})))

async function loadDag() {
  if (!selectedStack.value) { nodes.value = []; edges.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const data = await get(teamUrl(`/stacks/${selectedStack.value}/dag`))
    nodes.value = data.nodes || []
    edges.value = data.edges || []
  } catch (e) {
    error.value = e.message || 'Failed to load DAG'
    nodes.value = []
    edges.value = []
  } finally {
    loading.value = false
  }
}

watch(() => teamsStore.activeTeam, () => {
  if (teamsStore.activeTeam) {
    stacksStore.fetchStacks()
    selectedStack.value = ''
    nodes.value = []
    edges.value = []
  }
})
onMounted(() => { if (teamsStore.activeTeam) stacksStore.fetchStacks() })
</script>

<style scoped>
.controls { margin-bottom: 1rem; }
.controls select { padding: 0.35rem; min-width: 250px; border: 1px solid #ccc; border-radius: 4px; }
.dag-container { width: 100%; height: 500px; border: 1px solid #ddd; border-radius: 4px; }
.error { color: #c00; margin: 1rem 0; }
.muted { color: #888; }

.dag-node {
  background: #fff;
  border: 2px solid #1a1a2e;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  min-width: 160px;
  text-align: center;
}
.dag-node .node-name { font-weight: 600; font-size: 0.95rem; }
.dag-node .node-meta { font-size: 0.75rem; color: #666; margin-top: 0.2rem; }
.role-originator { border-color: #28a745; }
.role-forwarder { border-color: #007bff; }
.role-terminal { border-color: #6f42c1; }
</style>
