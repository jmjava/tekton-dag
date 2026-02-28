<template>
  <div>
    <h1>Explore Git repos</h1>
    <p>Repos from stacks/registry and stack YAMLs. Read-only: branches, tags, commits, PRs.</p>

    <section class="all-prs-section">
      <h2>Open PRs (all repos)</h2>
      <div class="all-prs-filter">
        <label>Show:</label>
        <select v-model="allPrsState" @change="loadAllPrs">
          <option value="open">Open PRs</option>
          <option value="closed">Closed PRs</option>
          <option value="all">All PRs</option>
        </select>
      </div>
      <p v-if="allPrsLoading">Loading…</p>
      <table v-else-if="allPrs.length" class="all-prs-table">
        <thead>
          <tr>
            <th>Repo</th>
            <th>PR</th>
            <th>Title</th>
            <th>State</th>
            <th>Pipeline run</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in allPrs" :key="row.repoId + '-' + row.pr.number">
            <td><a :href="'https://github.com/' + row.repoId" target="_blank" rel="noopener">{{ row.repoId }}</a></td>
            <td><a v-if="row.pr.url" :href="row.pr.url" target="_blank" rel="noopener">#{{ row.pr.number }}</a><span v-else>#{{ row.pr.number }}</span></td>
            <td>{{ row.pr.title }}</td>
            <td>{{ row.pr.state }}</td>
            <td>
              <a v-if="runLinkForPr(row.apps, row.pr.number)" :href="runLinkForPr(row.apps, row.pr.number)" target="_blank" rel="noopener">{{ runForPr(row.apps, row.pr.number) }}</a>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
      <template v-else>
        <p v-if="allPrsError" class="error">{{ allPrsError }}</p>
        <p v-else-if="reposSkipped.length && reposQueried.length && reposSkipped.length >= reposQueried.length" class="repos-skipped-hint">All {{ reposQueried.length }} repo(s) were skipped (likely private). Set <code>GITHUB_TOKEN</code> on the reporting backend and restart it.</p>
        <p v-else-if="reposSkipped.length" class="repos-skipped-hint">Skipped {{ reposSkipped.length }} repo(s): {{ reposSkipped.map(s => s.id).join(', ') }}. Set <code>GITHUB_TOKEN</code> on the backend for private repos.</p>
        <p v-else-if="reposQueried.length" class="muted">Queried {{ reposQueried.length }} repo(s); no {{ allPrsState }} PRs.</p>
        <p v-else class="muted">No repos found. Backend needs <code>REPO_ROOT</code> pointing at the tekton-dag repo (with <code>stacks/</code>).</p>
      </template>
    </section>

    <div v-if="error" class="error">{{ error }}</div>
    <div v-else>
      <table class="repos-table">
        <thead>
          <tr>
            <th>Repo</th>
            <th>Apps</th>
            <th>Stacks</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in repos" :key="r.id">
            <td><a :href="'https://github.com/' + r.id" target="_blank" rel="noopener">{{ r.id }}</a></td>
            <td>{{ r.apps.join(', ') }}</td>
            <td>{{ r.stacks.join(', ') }}</td>
            <td>
              <button type="button" @click="selectRepo(r)">Browse</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="selected" class="repo-detail">
        <h2>{{ selected.id }}</h2>
        <div class="tabs">
          <button :class="{ active: tab === 'branches' }" @click="tab = 'branches'">Branches</button>
          <button :class="{ active: tab === 'tags' }" @click="tab = 'tags'">Tags</button>
          <button :class="{ active: tab === 'commits' }" @click="tab = 'commits'">Commits</button>
          <button :class="{ active: tab === 'prs' }" @click="tab = 'prs'">PRs</button>
        </div>
        <div v-if="tab === 'branches'" class="tab-content">
          <p v-if="branchesLoading">Loading…</p>
          <ul v-else-if="branches.length">
            <li v-for="b in branches" :key="b.name">{{ b.name }} <code>{{ b.sha ? b.sha.slice(0, 7) : '' }}</code></li>
          </ul>
          <p v-else>No branches or failed to load.</p>
        </div>
        <div v-else-if="tab === 'tags'" class="tab-content">
          <p v-if="tagsLoading">Loading…</p>
          <ul v-else-if="tags.length">
            <li v-for="t in tags" :key="t.name">{{ t.name }} <code>{{ t.sha ? t.sha.slice(0, 7) : '' }}</code></li>
          </ul>
          <p v-else>No tags or failed to load.</p>
        </div>
        <div v-else-if="tab === 'commits'" class="tab-content">
          <p v-if="commitsLoading">Loading…</p>
          <ul v-else-if="commits.length" class="commits-list">
            <li v-for="c in commits" :key="c.sha">
              <a v-if="c.url" :href="c.url" target="_blank" rel="noopener">{{ c.sha.slice(0, 7) }}</a>
              <span v-else>{{ c.sha.slice(0, 7) }}</span>
              {{ c.message }}
              <span class="muted">{{ c.date ? new Date(c.date).toLocaleString() : '' }}</span>
            </li>
          </ul>
          <p v-else>No commits or failed to load.</p>
        </div>
        <div v-else-if="tab === 'prs'" class="tab-content">
          <div class="prs-filter">
            <label>Show:</label>
            <select v-model="prState" @change="loadPrs">
              <option value="open">Open PRs</option>
              <option value="closed">Closed PRs</option>
              <option value="all">All PRs</option>
            </select>
          </div>
          <p v-if="prsLoading">Loading…</p>
          <table v-else-if="prs.length" class="prs-table">
            <thead>
              <tr>
                <th>PR</th>
                <th>Title</th>
                <th>State</th>
                <th>Pipeline run</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in prs" :key="p.number">
                <td><a v-if="p.url" :href="p.url" target="_blank" rel="noopener">#{{ p.number }}</a><span v-else>#{{ p.number }}</span></td>
                <td>{{ p.title }}</td>
                <td>{{ p.state }}</td>
                <td>
                  <a v-if="runLinkForPr(selected?.apps || [], p.number)" :href="runLinkForPr(selected?.apps || [], p.number)" target="_blank" rel="noopener">{{ runForPr(selected?.apps || [], p.number) }}</a>
                  <span v-else class="muted">—</span>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else>No PRs or failed to load.</p>
        </div>
        <p><button type="button" @click="selected = null">Close</button></p>
      </div>
    </div>
    <p v-if="loading">Loading repos…</p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const api = import.meta.env.VITE_API_URL || '';
const dashboardUrl = (import.meta.env.VITE_DASHBOARD_URL || '').replace(/\/$/, '');
const repos = ref([]);
const loading = ref(true);
const error = ref('');
const selected = ref(null);
const tab = ref('branches');
const branches = ref([]);
const branchesLoading = ref(false);
const tags = ref([]);
const tagsLoading = ref(false);
const commits = ref([]);
const commitsLoading = ref(false);
const prs = ref([]);
const prsLoading = ref(false);
const prState = ref('open');
const allPrs = ref([]);
const allPrsLoading = ref(false);
const allPrsState = ref('open');
const reposQueried = ref([]);
const reposSkipped = ref([]);
const allPrsError = ref('');
const pipelineRuns = ref([]);

async function loadRepos() {
  try {
    const r = await fetch(`${api}/api/repos`);
    if (!r.ok) throw new Error(await r.text());
    const data = await r.json();
    repos.value = data.items || [];
    error.value = '';
  } catch (e) {
    error.value = e.message || 'Failed to load repos';
    repos.value = [];
  } finally {
    loading.value = false;
  }
}

function selectRepo(r) {
  selected.value = r;
  tab.value = 'branches';
  branches.value = [];
  tags.value = [];
  commits.value = [];
  prs.value = [];
}

async function loadPipelineRuns() {
  try {
    const r = await fetch(`${api}/api/pipelineruns?limit=100`);
    const data = r.ok ? await r.json() : { items: [] };
    pipelineRuns.value = (data.items || []).filter((run) => run.prNumber != null || run.changedApp != null);
  } catch {
    pipelineRuns.value = [];
  }
}

function runForPr(apps, prNumber) {
  const prNum = String(prNumber);
  const run = pipelineRuns.value.find(
    (r) => r.prNumber === prNum && r.changedApp && apps.includes(r.changedApp)
  );
  return run ? run.name : null;
}

function runLinkForPr(apps, prNumber) {
  const name = runForPr(apps, prNumber);
  if (!name || !dashboardUrl) return '';
  return `${dashboardUrl}/#/namespaces/tekton-pipelines/pipelineruns/${name}`;
}

async function loadAllPrs() {
  allPrsLoading.value = true;
  allPrsError.value = '';
  try {
    const [prsRes, runsRes] = await Promise.all([
      fetch(`${api}/api/prs?state=${allPrsState.value}`),
      fetch(`${api}/api/pipelineruns?limit=100`),
    ]);
    if (!prsRes.ok) {
      const text = await prsRes.text();
      allPrsError.value = `Could not load PRs: ${prsRes.status} ${prsRes.statusText}${text ? ' — ' + text.slice(0, 200) : ''}`;
      allPrs.value = [];
      reposQueried.value = [];
      reposSkipped.value = [];
    } else {
      const prsData = await prsRes.json();
      allPrs.value = prsData.items || [];
      reposQueried.value = prsData.reposQueried || [];
      reposSkipped.value = prsData.reposSkipped || [];
    }
    const runsData = runsRes.ok ? await runsRes.json() : { items: [] };
    pipelineRuns.value = (runsData.items || []).filter((r) => r.prNumber != null || r.changedApp != null);
  } catch (e) {
    allPrsError.value = `Could not load PRs: ${e.message || 'Network error'}. Is the reporting backend running at ${api || 'same origin'}?`;
    allPrs.value = [];
    reposQueried.value = [];
    reposSkipped.value = [];
  }
  allPrsLoading.value = false;
}

async function loadPrs() {
  if (!selected.value) return;
  const path = `${selected.value.owner}/${selected.value.repo}`;
  prsLoading.value = true;
  try {
    const [prsRes, runsRes] = await Promise.all([
      fetch(`${api}/api/repos/${path}/prs?state=${prState.value}`),
      fetch(`${api}/api/pipelineruns?limit=100`),
    ]);
    const prsData = prsRes.ok ? await prsRes.json() : { items: [] };
    prs.value = prsData.items || [];
    const runsData = runsRes.ok ? await runsRes.json() : { items: [] };
    pipelineRuns.value = (runsData.items || []).filter((r) => r.prNumber != null || r.changedApp != null);
  } catch {
    prs.value = [];
  }
  prsLoading.value = false;
}

watch([selected, tab], async () => {
  if (!selected.value) return;
  const { owner, repo } = selected.value;
  const path = `${owner}/${repo}`;
  if (tab.value === 'branches') {
    branchesLoading.value = true;
    try {
      const r = await fetch(`${api}/api/repos/${path}/branches`);
      const data = r.ok ? await r.json() : { items: [] };
      branches.value = data.items || [];
    } catch {
      branches.value = [];
    }
    branchesLoading.value = false;
  } else if (tab.value === 'tags') {
    tagsLoading.value = true;
    try {
      const r = await fetch(`${api}/api/repos/${path}/tags`);
      const data = r.ok ? await r.json() : { items: [] };
      tags.value = data.items || [];
    } catch {
      tags.value = [];
    }
    tagsLoading.value = false;
  } else if (tab.value === 'commits') {
    commitsLoading.value = true;
    try {
      const r = await fetch(`${api}/api/repos/${path}/commits`);
      const data = r.ok ? await r.json() : { items: [] };
      commits.value = data.items || [];
    } catch {
      commits.value = [];
    }
    commitsLoading.value = false;
  } else if (tab.value === 'prs') {
    loadPrs();
  }
}, { immediate: true });

loadAllPrs();

watch(prState, () => {
  if (tab.value === 'prs' && selected.value) loadPrs();
});

loadRepos();
</script>

<style scoped>
  .error { color: #c00; margin: 1rem 0; }
  .repos-table { margin-top: 1rem; }
  .repo-detail { margin-top: 1.5rem; padding: 1rem; border: 1px solid #ccc; border-radius: 4px; }
  .tabs { margin: 0.5rem 0; }
  .tabs button { margin-right: 0.5rem; padding: 0.25rem 0.5rem; cursor: pointer; }
  .tabs button.active { font-weight: bold; }
  .tab-content ul { list-style: none; padding-left: 0; }
  .tab-content li { margin: 0.25rem 0; }
  .tab-content code { font-size: 0.85em; }
  .commits-list li { margin: 0.5rem 0; }
  .muted { color: #666; font-size: 0.9em; }
  .prs-filter { margin-bottom: 0.75rem; }
  .prs-filter select { margin-left: 0.5rem; padding: 0.25rem; }
  .all-prs-section { margin: 2rem 0; padding: 1rem; border: 1px solid #ddd; border-radius: 4px; }
  .all-prs-section h2 { margin-top: 0; }
  .all-prs-filter { margin-bottom: 0.75rem; }
  .all-prs-filter select { margin-left: 0.5rem; padding: 0.25rem; }
  .all-prs-table, .prs-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
  .all-prs-table th, .all-prs-table td, .prs-table th, .prs-table td { padding: 0.35rem 0.5rem; text-align: left; border-bottom: 1px solid #eee; }
  .all-prs-table th, .prs-table th { font-weight: 600; }
  .repos-skipped-hint { font-size: 0.9em; color: #666; margin-top: 0.5rem; }
</style>
