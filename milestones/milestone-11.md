# Milestone 11: Vue 3 Management GUI with Python Backend

> **Planned.** Replaces `reporting-gui/` with a production-quality management GUI: Vue 3 frontend (`tekton-dag-vue-fe`) + Python/Flask backend (`tekton-dag-flask`). Uses the Kubernetes Python client directly (no kubectl dependency), supports multi-team and multi-cluster operation, and can be deployed centrally or per-team from the same codebase and Docker image.

## Goal

Build a **standalone management GUI** for the tekton-dag system that:

1. Replaces the `reporting-gui/frontend` (Vue 3) and `reporting-gui/backend` (Node/Express) with a proper two-repo architecture.
2. Uses the **Python `kubernetes` client** (no `kubectl` subprocess) following the proven pattern from `orchestrator/k8s_client.py`.
3. Supports **multiple teams and clusters** — each team's `team.yaml` specifies a kubeconfig context, and the backend can query any cluster.
4. Deploys in **two modes from one image**: centralized (all teams, team switcher visible) or per-team (`TEAM_NAME=<name>`, switcher hidden).
5. Adds **DAG visualization** of stack app dependencies using Vue Flow.

---

## What already exists (prerequisites)

| Capability | Source | How M11 uses it |
|------------|--------|-----------------|
| Multi-team config with cluster context | `teams/default/team.yaml` (M10) | `team_registry.py` loads all team configs, resolves cluster context per team |
| Stack resolver with PyYAML | `orchestrator/stack_resolver.py` (M10) | Adapted for the management backend with DAG edge extraction |
| Kubernetes Python client pattern | `orchestrator/k8s_client.py` (M10) | Extended with multi-context caching (`config.new_client_from_config(context=...)`) |
| PipelineRun builder | `orchestrator/pipelinerun_builder.py` (M10) | Ported for trigger form — builds pr/bootstrap/merge manifests |
| Vue 3 + Vite scaffold | `tekton-dag-vue-fe/` | Starting point for the frontend (has `App.vue`, `main.js`, `baggage.js`) |
| Flask scaffold | `tekton-dag-flask/` | Starting point for the backend (has `app.py`, `baggage.py`, Dockerfile) |
| Reporting GUI views | `reporting-gui/frontend/src/views/` | Ported and improved with Pinia stores, shared composables, team scoping |
| Baggage library | `libs/baggage-node`, `libs/baggage-python` | Already wired into both repos |

---

## Multi-team / multi-cluster design

The management GUI supports two deployment models from the **same codebase and Docker image**:

- **Mode A (centralized):** Omit `TEAM_NAME` or set `TEAM_NAME=*`. Loads all teams from `teams/`. Frontend shows a team switcher. Backend queries any cluster via kubeconfig contexts.
- **Mode B (per-team):** Set `TEAM_NAME=default`. Loads only that team. Frontend hides the team switcher. All API calls scoped to that team's cluster/namespace.

Each team's `teams/<name>/team.yaml` defines:

```yaml
name: default
namespace: tekton-pipelines
cluster: kind-tekton-stack          # kubeconfig context name
imageRegistry: localhost:5000
cacheRepo: localhost:5000/kaniko-cache
interceptBackend: telepresence
maxConcurrentRuns: 3
maxParallelBuilds: 5
stacks:
  - stacks/stack-one.yaml
```

The backend's `k8s_client.py` caches one `ApiClient` per kubeconfig context, so a single process can talk to N clusters:

```python
_clients = {}  # context_name -> CustomObjectsApi

def get_api(context=None):
    if context not in _clients:
        api_client = config.new_client_from_config(context=context)
        _clients[context] = client.CustomObjectsApi(api_client)
    return _clients[context]
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Vue 3 Frontend  (tekton-dag-vue-fe)                                 │
│  Vue Router · Pinia (teams, runs, stacks) · Vue Flow (DAG)           │
│  TeamSwitcher · useApi composable · 7 views                          │
└────────────────────────────┬─────────────────────────────────────────┘
                             │  fetch /api/teams/<team>/*
┌────────────────────────────▼─────────────────────────────────────────┐
│  Python/Flask Backend  (tekton-dag-flask)                            │
│  team_registry.py · stack_resolver.py · k8s_client.py                │
│  github_client.py · pipelinerun_builder.py                           │
│  Route blueprints: teams, pipelines, stacks, repos, health           │
└──────┬──────────────────┬──────────────────┬─────────────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
  Cluster A          Cluster B          GitHub API
  (context:          (context:          (GITHUB_TOKEN)
   kind-tekton)       staging-east)
```

---

## Part 1: Python backend (tekton-dag-flask)

### Files to create/modify

| File | Purpose |
|------|---------|
| `app.py` | Flask app factory with blueprints, CORS, config. Loads `TEAM_NAME` env var. Injects `team_registry` and `stack_resolver` into app config. |
| `k8s_client.py` | Multi-cluster Kubernetes client. Caches `ApiClient` per kubeconfig context. Functions: `get_api(context)`, `list_pipelineruns`, `get_pipelinerun`, `list_taskruns`, `create_pipelinerun` — all accept `context` + `namespace`. |
| `team_registry.py` | Loads `teams/*/team.yaml`. Provides `get_team(name)`, `list_teams()`, `resolve_context(team) -> (context, namespace)`. |
| `stack_resolver.py` | Adapted from `orchestrator/stack_resolver.py`. Parses `stacks/*.yaml` with PyYAML. `list_stacks(team)` filters to allowed stacks. `get_dag(stack_file)` returns `{nodes, edges}` for visualization. |
| `github_client.py` | GitHub API wrapper using `requests` + `GITHUB_TOKEN`. Functions: `list_branches`, `list_tags`, `list_commits`, `list_prs`, `list_prs_all_repos`. |
| `pipelinerun_builder.py` | Builds PipelineRun manifests for pr, bootstrap, merge — ported from `reporting-gui/backend/server.js` trigger logic. |
| `routes/teams.py` | Blueprint: `GET /api/teams` |
| `routes/pipelines.py` | Blueprint: `GET /api/teams/<team>/pipelineruns`, `GET /api/teams/<team>/pipelineruns/<name>`, `GET /api/teams/<team>/taskruns`, `POST /api/teams/<team>/trigger` |
| `routes/stacks.py` | Blueprint: `GET /api/teams/<team>/stacks`, `GET /api/teams/<team>/stacks/<stack>/dag` |
| `routes/repos.py` | Blueprint: `GET /api/repos`, `GET /api/repos/<owner>/<repo>/branches\|tags\|commits\|prs`, `GET /api/prs` |
| `routes/health.py` | Blueprint: `GET /api/health` |
| `requirements.txt` | `flask>=3.0.0`, `flask-cors`, `kubernetes`, `pyyaml`, `requests`, `gunicorn` |
| `tests/` | Tests for each module |

### API design (team-scoped)

All pipeline and stack operations are scoped to a team. The team determines which cluster context and namespace to query.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/teams` | List available teams (or single team if `TEAM_NAME` is set) |
| GET | `/api/teams/<team>/pipelineruns?limit=50` | List runs on that team's cluster/namespace |
| GET | `/api/teams/<team>/pipelineruns/<name>` | Run detail |
| GET | `/api/teams/<team>/taskruns?pipelineRun=<name>` | Task runs for a pipeline run |
| POST | `/api/teams/<team>/trigger` | Create PipelineRun on that team's cluster |
| GET | `/api/teams/<team>/stacks` | Stacks allowed for this team |
| GET | `/api/teams/<team>/stacks/<stack>/dag` | DAG nodes and edges for visualization |
| GET | `/api/repos` | Repos across all stacks (not team-scoped) |
| GET | `/api/repos/<owner>/<repo>/branches\|tags\|commits\|prs` | Git data for a repo |
| GET | `/api/prs?state=open\|closed\|all` | PRs across all repos |
| GET | `/api/health` | Health check |

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEAM_NAME` | `*` | `*` for all teams, or a specific team name for single-team mode |
| `TEAMS_DIR` | `../tekton-dag/teams` | Path to teams directory |
| `STACKS_DIR` | `../tekton-dag/stacks` | Path to stacks directory |
| `GITHUB_TOKEN` | (none) | GitHub API token for repo/PR access |
| `KUBECONFIG` | `~/.kube/config` | Standard kubeconfig (with all cluster contexts) |
| `PORT` | `5000` | Server port |

---

## Part 2: Vue 3 frontend (tekton-dag-vue-fe)

### Project structure

```
src/
  main.js                  # Mount app, register router + pinia
  App.vue                  # Layout: sidebar nav + team switcher + router-view
  router/
    index.js               # Routes (lazy-loaded views)
  stores/
    teams.js               # Pinia store: available teams, active team
    runs.js                # Pinia store: pipeline runs (team-scoped polling)
    stacks.js              # Pinia store: stacks + apps (team-scoped)
  composables/
    useApi.js              # Shared fetch wrapper (injects active team into URL)
  views/
    TriggerView.vue        # Pipeline trigger form (team-scoped stacks)
    MonitorView.vue        # Pipeline runs table with 10s polling
    RunDetailView.vue      # Single run detail + task runs
    TestResultsView.vue    # Test results with filters
    GitView.vue            # Repo browser: branches, tags, commits, PRs
    DashboardView.vue      # Tekton Dashboard iframe embed
    DagView.vue            # Stack DAG visualization (Vue Flow + dagre)
  components/
    StatusBadge.vue        # Reusable status indicator (Succeeded/Failed/Running)
    DataTable.vue          # Reusable sortable table
    NavSidebar.vue         # Sidebar navigation
    TeamSwitcher.vue       # Dropdown to switch active team (hidden in single-team mode)
  baggage.js               # Existing: re-exports from @tekton-dag/baggage
```

### Dependencies to add

| Package | Purpose |
|---------|---------|
| `vue-router` | Routing with lazy-loaded views |
| `pinia` | State management (teams, runs, stacks) |
| `@vue-flow/core` | Interactive DAG graph rendering |
| `@vue-flow/dagre-layout` | Automatic DAG layout |

### Team-aware routing and state

- **`stores/teams.js`** — On app init, fetches `GET /api/teams`. Stores `availableTeams` and `activeTeam`. If only one team is returned (single-team mode), `activeTeam` is set automatically and `TeamSwitcher` is hidden.
- **`composables/useApi.js`** — Reads `activeTeam` from the teams store and builds URLs like `/api/teams/${activeTeam}/pipelineruns`. For team-independent endpoints (repos, prs, health), omits the team prefix.
- **`components/TeamSwitcher.vue`** — Dropdown in the sidebar. Changing team clears the runs and stacks stores and re-fetches for the new team's cluster. Only visible when `availableTeams.length > 1`.

### Views (ported from reporting-gui with improvements)

| View | Ported from | Changes |
|------|------------|---------|
| TriggerView | `reporting-gui/frontend/src/views/TriggerView.vue` | Team-scoped stacks, uses Pinia stacks store, shared API composable |
| MonitorView | `reporting-gui/frontend/src/views/MonitorView.vue` | Team-scoped, uses Pinia runs store (shared polling) |
| RunDetailView | `reporting-gui/frontend/src/views/RunDetailView.vue` | Team-scoped, shared API composable, StatusBadge component |
| TestResultsView | `reporting-gui/frontend/src/views/TestResultsView.vue` | Shares Pinia runs store with MonitorView |
| GitView | `reporting-gui/frontend/src/views/GitView.vue` | Not team-scoped (repos shared), cleaner tab structure |
| DashboardView | `reporting-gui/frontend/src/views/DashboardView.vue` | Team-scoped dashboard URL per cluster |
| DagView | **NEW** | Interactive DAG of stack app dependencies using Vue Flow + dagre |

### Key improvements over reporting-gui

1. **Multi-team / multi-cluster** — team switcher, all data scoped to active team's cluster/namespace.
2. **Same codebase, two modes** — centralized (all teams visible) or per-team (single team, switcher hidden).
3. **Python backend with Kubernetes client** — no `kubectl` subprocess, direct API via `kubernetes` library.
4. **Shared API layer** (`composables/useApi.js`) — single fetch wrapper with automatic team scoping instead of duplicated `fetch()` in every view.
5. **Pinia stores** — pipeline runs polled once and shared across Monitor, TestResults, and Git views.
6. **Reusable components** — `StatusBadge`, `DataTable`, `TeamSwitcher` extracted from repeated patterns.
7. **DAG visualization** — interactive directed graph of stack app dependencies.
8. **Modern styling** — clean sidebar layout, responsive design.

---

## Deliverables

### Python backend (tekton-dag-flask)

- [ ] `app.py` — Flask app factory with blueprints, CORS, team/stack config
- [ ] `k8s_client.py` — Multi-cluster Kubernetes client (context-per-team caching)
- [ ] `team_registry.py` — Load and resolve `teams/*/team.yaml`
- [ ] `stack_resolver.py` — Parse `stacks/*.yaml`, extract DAG structure
- [ ] `github_client.py` — GitHub API wrapper (branches, tags, commits, PRs)
- [ ] `pipelinerun_builder.py` — Build PipelineRun manifests for pr/bootstrap/merge
- [ ] `routes/` — Blueprints: teams, pipelines, stacks, repos, health
- [ ] `requirements.txt` — Production dependencies
- [ ] `tests/` — Unit tests for all modules
- [ ] `Dockerfile` — Updated for management GUI backend

### Vue 3 frontend (tekton-dag-vue-fe)

- [ ] Project setup: vue-router, pinia, @vue-flow/core, @vue-flow/dagre-layout
- [ ] `stores/` — teams.js, runs.js, stacks.js
- [ ] `composables/useApi.js` — Shared fetch wrapper with team scoping
- [ ] `components/` — StatusBadge, DataTable, NavSidebar, TeamSwitcher
- [ ] `views/` — TriggerView, MonitorView, RunDetailView, TestResultsView, GitView, DashboardView, DagView
- [ ] `App.vue` — Sidebar nav layout with team switcher
- [ ] `vite.config.js` — Proxy `/api` to Flask backend (localhost:5000)

---

## Success criteria

- [ ] All 7 views functional with team-scoped data.
- [ ] Backend connects to Kubernetes via Python client (no `kubectl` dependency).
- [ ] Multi-team mode: team switcher shows all teams, switching re-fetches data from correct cluster.
- [ ] Single-team mode: `TEAM_NAME=default` hides switcher, scopes all queries.
- [ ] DAG view renders stack app dependencies as interactive graph with correct edges.
- [ ] Trigger form creates PipelineRuns on the correct team's cluster/namespace.
- [ ] All reporting-gui functionality preserved (trigger, monitor, run detail, test results, git, dashboard).
- [ ] Backend tests pass for k8s_client, team_registry, stack_resolver, github_client, and route blueprints.

---

## Dependencies

```
# Python backend
pip install flask flask-cors kubernetes pyyaml requests gunicorn

# Vue frontend
npm install vue-router pinia @vue-flow/core @vue-flow/dagre-layout
```

---

## References

- [orchestrator/k8s_client.py](../orchestrator/k8s_client.py) — Kubernetes client pattern (single-cluster)
- [orchestrator/stack_resolver.py](../orchestrator/stack_resolver.py) — Stack resolver with team loading
- [orchestrator/routes.py](../orchestrator/routes.py) — Flask route patterns
- [reporting-gui/backend/server.js](../reporting-gui/backend/server.js) — Node backend being replaced
- [reporting-gui/frontend/](../reporting-gui/frontend/) — Vue 3 frontend being replaced
- [teams/default/team.yaml](../teams/default/team.yaml) — Team config example
- [stacks/stack-one.yaml](../stacks/stack-one.yaml) — Stack definition with DAG edges
- [Vue Flow](https://vueflow.dev/) — DAG visualization library
