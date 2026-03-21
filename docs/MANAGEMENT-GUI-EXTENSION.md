# Management GUI — design and extending Tekton interactions

How the **Vue 3** app is structured, how it talks to **Kubernetes/Tekton** (via Flask), and a repeatable pattern for **new features**.

## Stack at a glance

| Layer | Location | Role |
|-------|----------|------|
| **Views** | `management-gui/frontend/src/views/*.vue` | Screens: trigger, monitor, DAG, Git, test results, dashboard embed. |
| **State** | `management-gui/frontend/src/stores/*.js` | Pinia stores (`teams`, `stacks`, `runs`, …). |
| **HTTP** | `management-gui/frontend/src/composables/useApi.js` | `teamUrl()` / `globalUrl()`, `get` / `post` with active team prefix. |
| **Router** | `management-gui/frontend/src/router/index.js` | Vue Router + lazy-loaded views. |
| **API** | `management-gui/backend/routes/*.py` | Flask blueprints: teams, stacks, pipelines (`pipelineruns`, `taskruns`, `trigger`), repos, health. |
| **K8s** | Backend services (`k8s_client`, team registry, stack resolver) | List/watch PipelineRuns, apply triggers, read TaskRuns — **no direct cluster access from the browser**. |

**Security note:** The browser only calls `/api/...`. All `kubectl`-equivalent operations run in the backend with configured credentials.

## How `useApi` scopes work by team

```text
GET /api/teams/{activeTeam}/pipelineruns
```

`useTeamsStore().activeTeam` drives `teamUrl('/pipelineruns')`. Global endpoints (e.g. repo list) use `globalUrl('/repos')`.

Adding a **team-scoped** Tekton read: extend the backend under `/api/teams/<team>/...`, then call `get(teamUrl('/your-path'))` from a store or view.

## Backend route map (extend here first)

| Area | File | Examples |
|------|------|----------|
| Runs & tasks | `backend/routes/pipelines.py` | `pipelineruns`, `pipelineruns/<name>`, `taskruns`, `trigger` POST |
| Stacks / DAG | `backend/routes/stacks.py` | `stacks`, `stacks/.../dag` |
| Teams | `backend/routes/teams.py` | `teams` |
| Git / PRs | `backend/routes/repos.py` | `repos`, branches, PRs |
| Health | `backend/routes/health.py` | `health` |

Register new blueprints in `app.py` (same pattern as existing routes).

## Pattern: add a new Tekton-backed screen

1. **Backend** — Add JSON route(s) that wrap `kubernetes` client calls (list/get CRDs, filter by label, etc.). Return stable JSON shapes `{ items: [...] }` where the UI already expects arrays.  
2. **Tests** — `management-gui/backend/tests/test_routes.py`: Flask client + mocked K8s (follow existing tests).  
3. **Store** (optional) — New Pinia store or extend `runs.js`-style: `useApi()`, `fetch`, error/loading refs, optional polling.  
4. **View** — New `views/YourView.vue`; consume store; use `DataTable` / existing components where possible.  
5. **Router** — Add path in `router/index.js`; **Nav** — Link from `NavSidebar.vue`.  
6. **E2E** — `management-gui/frontend/e2e/*.spec.js`: Playwright against mocked or real API per existing style.

## Ideas for deeper Tekton coverage

- **PipelineRun YAML / spec viewer** — GET detailed run JSON from API; pretty-print in a drawer.  
- **TaskRun logs** — Backend streams or fetches pod logs; frontend shows in modal (watch RBAC).  
- **EventListener / TriggerTemplate** — Read-only list of triggers; link to docs.  
- **Tekton Results** — Proxy read-only Results queries through Flask (reuse patterns from `verify-results-in-db.sh`).  
- **CustomRun / other CRDs** — Same blueprint: backend aggregates, frontend displays.

Keep **orchestrator** vs **raw Tekton** clear: cluster-only operations stay in Flask; cross-team HTTP to the orchestrator service belongs in backend config, not hardcoded in Vue.

## References

- [management-gui/README.md](../management-gui/README.md) — run dev servers, test counts.  
- [M11](../milestones/milestone-11.md) — original GUI milestone.  
- [CUSTOMIZATION.md](CUSTOMIZATION.md) — Helm / team config affecting the GUI.
