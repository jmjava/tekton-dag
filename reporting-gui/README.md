# Tekton DAG Reporting GUI

Reporting and maintenance GUI for Tekton DAG pipelines: trigger jobs, monitor runs, view test results, explore Git repos, and embed the Tekton Dashboard.

## Structure

- **frontend/** — Vue 3 SPA (Vite). Nav: Trigger, Monitor, Test results, Git, Dashboard.
- **backend/** — Node (Express) API. Uses `kubectl` to list PipelineRuns/TaskRuns and to create PipelineRuns (via `generate-run.sh` or Kubernetes API).

## Prerequisites

- Node 18+
- `kubectl` in PATH, configured for your cluster (e.g. Kind). Backend runs `kubectl get pipelineruns` etc.
- Tekton Pipelines installed in the cluster (e.g. `tekton-pipelines` namespace).
- Optional: Tekton Dashboard for the Dashboard tab and "Open in Dashboard" links. From the repo root: `./scripts/install-tekton-dashboard.sh` (install), `./scripts/port-forward-tekton-dashboard.sh` (then open http://localhost:9097), `./scripts/uninstall-tekton-dashboard.sh` (uninstall). Set `VITE_DASHBOARD_URL=http://localhost:9097` when building or in `.env`.

## Running locally

### Backend

From this directory (or repo root):

```bash
cd reporting-gui/backend
npm install
npm start
```

Listens on `http://localhost:4000`. Environment:

- **PORT** — default 4000
- **KUBECONFIG** — optional; `kubectl` uses default
- **TEKTON_NAMESPACE** — default `tekton-pipelines`
- **REPO_ROOT** — path to tekton-dag repo (for trigger script and **stacks/** for repo list). Default: walk up from backend dir until a `stacks/` folder is found. Set explicitly if the backend runs from a different layout.
- **GITHUB_TOKEN** — optional but **required for private repos**. Used by `GET /api/repos/...` and `GET /api/prs` (branches, tags, commits, PRs). Without it, private app repos are skipped and "Open PRs (all repos)" may show "All repos were skipped" or list only public repos.

### Frontend

```bash
cd reporting-gui/frontend
npm install
npm run dev
```

Opens at `http://localhost:5173`. In dev, Vite proxies `/api` to the backend (see `vite.config.js`). Optional:

- **VITE_API_URL** — if backend is elsewhere, set to full URL (e.g. `http://localhost:4000`). Leave unset when using the dev proxy.
- **VITE_DASHBOARD_URL** — base URL of Tekton Dashboard for the Dashboard tab iframe (e.g. `http://localhost:9097` after port-forward). PipelineRun detail URL: `{base}/#/namespaces/{namespace}/pipelineruns/{name}`.

## API (backend)

- `GET /api/health` — health check
- `GET /api/pipelineruns?limit=50&namespace=tekton-pipelines` — list PipelineRuns
- `GET /api/pipelineruns/:name` — single PipelineRun
- `GET /api/taskruns?pipelineRun=:name` — TaskRuns for a PipelineRun

- `GET /api/stacks` — list stack files and apps (for trigger form)
- `POST /api/trigger` — create a PipelineRun (body: pipelineType, stack, app, prNumber?, gitUrl?, gitRevision?, imageRegistry?, versionOverrides?, buildImages?, storageClass?)
- `GET /api/repos` — list repos (platform + app repos from stacks)
- `GET /api/repos/:owner/:repo/branches` — GitHub branches (requires GITHUB_TOKEN for private repos)
- `GET /api/repos/:owner/:repo/tags` — GitHub tags
- `GET /api/repos/:owner/:repo/commits` — GitHub commits
- `GET /api/repos/:owner/:repo/prs?state=open|closed|all` — GitHub PRs (default open)
- `GET /api/prs?state=open|closed|all` — PRs across all repos (from stacks). Returns `items`, `reposQueried`, `reposSkipped`. Needs **GITHUB_TOKEN** for private repos.

## Debugging "Open PRs (all repos)" / No PRs

- **Restart the backend** after pulling changes. The running process may not have the latest routes (e.g. `GET /api/prs`). Stop the backend (Ctrl+C) and run `npm start` again from `reporting-gui/backend`.
- **Set `GITHUB_TOKEN`** (env or `.env`) if your app repos are private. Without it, GitHub returns 404/401 and those repos are skipped; the GUI shows "Skipped N repo(s)" or "All repos were skipped".
- **Check API directly**: `curl -s http://localhost:4000/api/repos` should list repos from stacks; `curl -s "http://localhost:4000/api/prs?state=open"` should return JSON with `items`, `reposQueried`, `reposSkipped`. If you get HTML "Cannot GET /api/prs", the backend is old — restart it.

## Pointing at Kind

Ensure `kubectl` is configured for your Kind cluster (e.g. `kubectl config use-context kind-kind` or set `KUBECONFIG`). The backend runs in the same environment as your terminal; no in-cluster deployment is required for local dev.

## Production

For production, deploy the backend behind auth (e.g. token, OIDC) and RBAC so only authorized identities can create PipelineRuns. The GUI is intended for dev/Kind; document that production use requires securing the API and frontend.
