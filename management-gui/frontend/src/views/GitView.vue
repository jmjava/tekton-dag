<template>
  <div>
    <h1>Explore Git repos</h1>
    <p>Repos from stack YAMLs. Browse branches, tags, commits, PRs.</p>

    <section class="all-prs-section">
      <h2>Open PRs (all repos)</h2>
      <div class="prs-filter">
        <label>Show: <select v-model="allPrsState" @change="loadAllPrs"><option value="open">Open</option><option value="closed">Closed</option><option value="all">All</option></select></label>
      </div>
      <p v-if="allPrsLoading">Loading...</p>
      <DataTable v-else-if="allPrs.length" :columns="allPrsColumns" :rows="allPrs">
        <template #repoId="{ value }"><a :href="'https://github.com/' + value" target="_blank" rel="noopener">{{ value }}</a></template>
        <template #pr="{ value }"><a v-if="value.url" :href="value.url" target="_blank" rel="noopener">#{{ value.number }}</a><span v-else>#{{ value.number }}</span> {{ value.title }}</template>
      </DataTable>
      <p v-else class="muted">No PRs found.</p>
    </section>

    <div v-if="error" class="error">{{ error }}</div>
    <DataTable v-else :columns="repoColumns" :rows="repos">
      <template #id="{ row }"><a :href="'https://github.com/' + row.id" target="_blank" rel="noopener">{{ row.id }}</a></template>
      <template #apps="{ value }">{{ value.join(', ') }}</template>
      <template #stacks="{ value }">{{ value.join(', ') }}</template>
      <template #actions="{ row }"><button type="button" @click="selectRepo(row)">Browse</button></template>
    </DataTable>

    <div v-if="selected" class="repo-detail">
      <h2>{{ selected.id }}</h2>
      <div class="tabs">
        <button v-for="t in ['branches','tags','commits','prs']" :key="t" :class="{ active: tab === t }" @click="tab = t">{{ t }}</button>
      </div>
      <div class="tab-content">
        <p v-if="tabLoading">Loading...</p>
        <ul v-else-if="tabData.length && tab !== 'prs'">
          <li v-for="item in tabData" :key="item.name || item.sha">
            <template v-if="tab === 'commits'"><a v-if="item.url" :href="item.url" target="_blank" rel="noopener">{{ item.sha?.slice(0,7) }}</a> {{ item.message }} <span class="muted">{{ item.date ? new Date(item.date).toLocaleString() : '' }}</span></template>
            <template v-else>{{ item.name }} <code>{{ item.sha?.slice(0,7) || '' }}</code></template>
          </li>
        </ul>
        <DataTable v-else-if="tab === 'prs' && tabData.length" :columns="[{key:'number',label:'PR'},{key:'title',label:'Title'},{key:'state',label:'State'}]" :rows="tabData">
          <template #number="{ row }"><a v-if="row.url" :href="row.url" target="_blank" rel="noopener">#{{ row.number }}</a></template>
        </DataTable>
        <p v-else>No data.</p>
      </div>
      <p><button @click="selected = null">Close</button></p>
    </div>
    <p v-if="loading">Loading repos...</p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useApi } from '../composables/useApi'
import DataTable from '../components/DataTable.vue'

const { globalUrl, get } = useApi()

const repos = ref([])
const loading = ref(true)
const error = ref('')
const selected = ref(null)
const tab = ref('branches')
const tabData = ref([])
const tabLoading = ref(false)
const allPrs = ref([])
const allPrsLoading = ref(false)
const allPrsState = ref('open')

const repoColumns = [
  { key: 'id', label: 'Repo' },
  { key: 'apps', label: 'Apps' },
  { key: 'stacks', label: 'Stacks' },
  { key: 'actions', label: '' },
]
const allPrsColumns = [
  { key: 'repoId', label: 'Repo' },
  { key: 'pr', label: 'PR' },
]

async function loadRepos() {
  try {
    const data = await get(globalUrl('/repos'))
    repos.value = data.items || []
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadAllPrs() {
  allPrsLoading.value = true
  try {
    const data = await get(globalUrl(`/prs?state=${allPrsState.value}`))
    allPrs.value = data.items || []
  } catch {
    allPrs.value = []
  }
  allPrsLoading.value = false
}

function selectRepo(r) {
  selected.value = r
  tab.value = 'branches'
}

watch([() => selected.value, tab], async () => {
  if (!selected.value) return
  const path = `${selected.value.owner}/${selected.value.repo}`
  tabLoading.value = true
  tabData.value = []
  try {
    let endpoint
    if (tab.value === 'prs') endpoint = `/repos/${path}/prs?state=open`
    else endpoint = `/repos/${path}/${tab.value}`
    const data = await get(globalUrl(endpoint))
    tabData.value = data.items || []
  } catch {
    tabData.value = []
  }
  tabLoading.value = false
}, { immediate: true })

loadRepos()
loadAllPrs()
</script>

<style scoped>
.error { color: #c00; margin: 1rem 0; }
.muted { color: #888; }
.all-prs-section { margin: 1.5rem 0; padding: 1rem; border: 1px solid #ddd; border-radius: 4px; }
.all-prs-section h2 { margin-top: 0; }
.prs-filter { margin-bottom: 0.75rem; }
.prs-filter select { margin-left: 0.5rem; padding: 0.25rem; }
.repo-detail { margin-top: 1.5rem; padding: 1rem; border: 1px solid #ccc; border-radius: 4px; }
.tabs { margin: 0.5rem 0; display: flex; gap: 0.5rem; }
.tabs button { padding: 0.3rem 0.6rem; cursor: pointer; border: 1px solid #ccc; border-radius: 4px; background: #fff; }
.tabs button.active { font-weight: bold; background: #f0f0f0; }
.tab-content ul { list-style: none; padding-left: 0; }
.tab-content li { margin: 0.3rem 0; }
.tab-content code { font-size: 0.85em; color: #555; }
</style>
