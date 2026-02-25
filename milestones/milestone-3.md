# Milestone 3: Reporting GUI — trigger jobs, monitor jobs, view test results

## Goal

Deliver a **reporting GUI** that allows users to:

1. **Trigger jobs** — start pipeline runs (e.g. PR test, bootstrap, merge) with chosen stack, app, and params (registry, git revision, etc.) without running `generate-run.sh` and `kubectl create` from the CLI.
2. **Monitor jobs** — watch running PipelineRuns and TaskRuns (status, progress, duration) and see when they complete or fail.
3. **View test results** — see test outcomes (e.g. from `run-tests` task, validation propagation, E2E summary) and link to Tekton Results DB for history and details.
4. **Explore Git repos** — browse and explore Git repositories used by the DAG (platform repo, app repos) for related info such as branches, tags, recent commits, PRs, and which repo maps to which stack/app.
5. **Post job results to GitHub PR and link to Tekton Dashboard** — when a PR pipeline run completes, post a comment on the GitHub PR with the run result (passed/failed, summary) and a direct link to the **Tekton Dashboard** for that PipelineRun. Use the official Tekton Dashboard (installed in-cluster), not the reporting GUI, as the destination for the link.
6. **Embed Tekton Dashboard in the maintenance GUI via iframe** — allow users to view the main areas of the Tekton Dashboard (PipelineRuns list, run detail, task logs, etc.) inside the reporting/maintenance GUI using an **iframe**, so they can stay in one place instead of opening the Dashboard in a separate tab.

The GUI should integrate with the existing Tekton setup (Kind cluster, `stack-pr-test` / `stack-bootstrap` / `stack-merge-release` pipelines, Tekton Results + Postgres) and feel like a single control plane for the DAG pipelines.

## Scope

### 1. Trigger jobs

- **Inputs**: pipeline choice (PR test, bootstrap, merge), stack file, app (changed-app), PR number (for PR), optional overrides (git revision, registry, version-overrides, build-images flag). Optionally: SSH key / secret selection if multiple are configured.
- **Mechanism**: create a PipelineRun resource in the cluster (same YAML shape as produced by `scripts/generate-run.sh`). Options: (a) GUI backend that runs `generate-run.sh` and `kubectl create`, (b) GUI backend that builds PipelineRun JSON/YAML from parameters and submits via Kubernetes API, (c) Tekton Triggers EventListener already used for webhooks — extend or add a simple “manual run” endpoint that creates PipelineRuns from form payload.
- **Validation**: ensure required params (e.g. `--pr` for PR mode, stack, app) are present; show errors before submit. Optional: dry-run to show the PipelineRun YAML without applying.
- **Security**: only allow triggering from trusted users/environments; if the GUI is exposed, consider auth (e.g. token, OIDC) and RBAC so only authorized identities can create PipelineRuns.

### 2. Monitor jobs

- **Data source**: Kubernetes API (PipelineRuns, TaskRuns) and/or Tekton Results API (if exposed). Prefer Results API for consistent, queryable history; use Kubernetes watch for live “running” state.
- **UI**: list of recent runs (e.g. last 50 or filter by time range), with columns: name, pipeline, status (Running / Succeeded / Failed), start time, duration, triggered-by (e.g. “manual”, “webhook”). Click a run to see TaskRun-level status and step progress.
- **Live updates**: use watch or polling so the list and detail views update when runs complete or fail. Optionally show logs link (e.g. to Tekton Dashboard or `kubectl logs` instructions).
- **Failure drill-down**: for failed runs, show which task/step failed and, if available, a short failure message or link to logs.

### 3. View test results

- **Source of truth**: Tekton Results DB (Postgres) stores pipeline/task run records; `run-tests` (and validate-propagation) task results are recorded there. Optionally, task results (e.g. `test-summary`) are exposed as PipelineRun/TaskRun results in the cluster.
- **UI**: for a given PipelineRun, show “Test results” section: overall pass/fail, test summary (if stored in Results or in task result), and link to full run in Results or Tekton Dashboard. Canned views: “last N runs with test summary”, “failed runs in last 24h”, “runs for stack X”.
- **Queries**: reuse or extend the “canned queries” idea from Milestone 2 (Results GUI): recent runs, by stack/app, failures, duration. Ensure test result fields (e.g. `test-summary` result, `run-tests` task status) are surfaced.
- **Export / share**: optional export (e.g. CSV) or deep link to a run for sharing or CI dashboards.

### 4. Explore Git repos

- **Purpose**: help users choose revisions, verify repo URLs, and understand the relationship between repos and stacks before triggering a run or when debugging.
- **Data sources**: (a) GitHub/GitLab API (or similar) for branches, tags, commits, PRs; (b) stack YAML and `stacks/registry.yaml` in the platform repo for “which repos belong to which stack/app”; (c) optional: shallow clone or backend `git ls-remote` for refs without full provider API.
- **UI**: “Repos” or “Git” section that:
  - Lists **repos** referenced by the system: platform repo (e.g. tekton-dag) and app repos from stack definitions (e.g. from `stack-one.yaml` → `apps[].repo`). Show repo URL (SSH/HTTPS), default branch, and which stack(s) or app(s) use it.
  - Per repo: **browse branches** (e.g. `main`, `feature/one-image-per-build`), **tags** (e.g. `v0.1.0`), and **recent commits** (message, sha, date). Optional: link to provider’s UI (e.g. GitHub commit page).
  - **PRs**: for app repos, show open PRs or recent PRs (if provider API supports it) so users can pick a PR number for the trigger form.
  - **Search**: optional filter by branch/tag name or commit message to quickly find a revision to use for “git revision” when triggering.
- **Backend**: backend (or serverless) calls Git provider API with optional token for higher rate limits; or runs `git ls-remote` against repo URLs. For private repos, backend must have credentials or token; document that the GUI’s “explore” feature is best-effort and may be read-only (no push).
- **Scope**: read-only exploration; no creating branches or PRs from the GUI. Focus on info needed for “trigger a run” (revision, PR number) and “what repos does this stack use”.

### 5. Tekton Dashboard + post results to GitHub PR

- **Tekton Dashboard**: Install the **official Tekton Dashboard** in the cluster (e.g. via `kubectl apply` from upstream or a script in this repo). Expose it via Ingress or port-forward so users can open it at a stable base URL (e.g. `https://tekton-dashboard.ingress.example.com` or documented local URL). The Dashboard provides the canonical UI for viewing PipelineRun/TaskRun details and logs; the “link back” from GitHub will point here, not to the reporting GUI.
- **Post results to PR**: When a **PR pipeline** run (e.g. `stack-pr-test`) completes (success or failure), post a **comment on the GitHub PR** that triggered (or is associated with) the run. The comment should include:
  - **Status**: e.g. “Pipeline succeeded” or “Pipeline failed”.
  - **Summary**: optional one-line or short summary (e.g. test result summary if available from task results).
  - **Link to Tekton Dashboard**: direct URL to the Dashboard page for this PipelineRun (e.g. Dashboard’s PipelineRun detail view for the run name/namespace). This lets developers click from the PR to see full logs and task details in the Dashboard.
- **Mechanism**: Add a **final task** to the PR pipeline (or a separate pipeline/task triggered on completion) that: (a) has access to the pipeline run name and namespace, (b) knows the repo and PR number (from params), (c) calls the **GitHub API** to create an issue comment on the PR with the status and dashboard URL. The task needs a **GitHub token** (secret) with `repo` or `public_repo` and write access to the repo. Construct the dashboard URL from a configurable base (e.g. `DASHBOARD_URL`) + path to the PipelineRun (Dashboard’s URL pattern for a run is documented in Tekton Dashboard docs).
- **Optional**: Only post on failure, or post on both success and failure; optionally edit/update a single “status” comment per PR instead of appending many. Document how to obtain and store the GitHub token (e.g. `repo:owner/repo` scope).

### 6. Embed Tekton Dashboard in the maintenance GUI (iframe)

- **Purpose**: provide a single pane of glass: the maintenance (reporting) GUI hosts both its own views (trigger, monitor list, test results, Git explore) and the **Tekton Dashboard** for deep inspection of runs and logs, without leaving the GUI.
- **Mechanism**: embed the **Tekton Dashboard** (or specific Dashboard views) in the reporting GUI using an **iframe**. The GUI has a configurable **Dashboard base URL** (same as used for “link to Dashboard” in PR comments). Main areas to expose:
  - **PipelineRuns list** — Dashboard’s PipelineRuns list view (optionally scoped to namespace), e.g. `{DASHBOARD_BASE}/#/namespaces/{namespace}/pipelineruns`.
  - **PipelineRun detail** — single run view with task/step tree and status, e.g. `{DASHBOARD_BASE}/#/namespaces/{namespace}/pipelineruns/{name}`. The GUI can open this when user clicks a run in its own monitor list (either in iframe or new tab).
  - **TaskRun / logs** — Dashboard’s TaskRun detail or log viewer for a specific task/step; deep link from GUI “view logs” for a run.
  - **Pipelines / Tasks list** (optional) — Dashboard’s Pipelines and Tasks overview if useful for operators.
- **UI**: add a section or tab in the maintenance GUI such as “Dashboard” or “Run details” that contains an iframe whose `src` is the Dashboard base URL or a specific Dashboard path. Optionally: tabs or dropdown to switch iframe content between “PipelineRuns”, “Run detail” (with run name/namespace from context), “Logs”. If the GUI’s monitor list has a selected run, the iframe can auto-navigate to that run’s detail URL.
- **Framing and security**: the Tekton Dashboard may send **X-Frame-Options** or **Content-Security-Policy frame-ancestors** that block embedding. Options: (a) deploy Dashboard with configuration that allows framing from the reporting GUI’s origin (e.g. `frame-ancestors https://reporting-gui.example.com` or same-origin); (b) serve the reporting GUI and the Dashboard under the same origin (e.g. reverse proxy so both are on one host); (c) document that iframe embedding is optional and if blocked, “open in new tab” is used instead. Same-origin or proxy approach avoids cross-origin restrictions and preserves Dashboard auth (e.g. kubeconfig-backed login) within the iframe.
- **Outcome**: users can open the maintenance GUI and use it to trigger runs, see the monitor list and test results, and use the same page to drill into Dashboard views (runs, logs) via the embedded iframe without switching apps.

### 7. Technology and deployment

- **Stack**: Vue SPA (or similar) with a thin backend (Node or small service) that:
  - Creates PipelineRuns (Kubernetes API or shell out to `generate-run.sh` + `kubectl`).
  - Proxies or queries Tekton Results API (or read-only Postgres) for history and test results.
  - Optionally streams or polls Kubernetes API for live run status.
- **Deployment**: run the GUI in-cluster (e.g. behind Ingress) or locally (e.g. `npm run dev` with `kubectl proxy` or kubeconfig so the backend can talk to the cluster and Results). Document how to point the GUI at the same Kind cluster and Postgres used by Tekton Results.
- **Consistency**: align with existing patterns (e.g. `tekton-dag-vue-fe` if present, or sample-repos structure); keep the GUI focused on “trigger, monitor, view results” rather than duplicating full Tekton Dashboard.

## Outcomes

- **Reporting GUI app** (in this repo under e.g. `reporting-gui/` or a dedicated repo) with:
  - **Trigger**: form or wizard to select pipeline type, stack, app, PR number, overrides; submit creates a PipelineRun.
  - **Monitor**: list of recent PipelineRuns with status and duration; detail view per run with task/step progress; live or polling updates.
  - **Test results**: view test summary and pass/fail per run; canned queries (recent runs, failures, by stack/app); optional export or deep links.
  - **Explore Git repos**: list of platform and app repos (from stack definitions); per-repo view of branches, tags, recent commits, and optional PR list; support picking a revision or PR for the trigger form.
  - **Embed Tekton Dashboard**: section or tab with iframe(s) pointing at main Tekton Dashboard areas (PipelineRuns list, PipelineRun detail, task logs); configurable Dashboard base URL; handle framing (same-origin or Dashboard config) so embedding works.
- **Backend** (or serverless/API layer) that creates PipelineRuns and reads from Kubernetes and/or Tekton Results API (or Postgres).
- **Documentation**: README for running the GUI locally and against Kind + Tekton Results; how to configure registry, git URL, and SSH so triggered runs succeed.
- **Optional**: integration with Tekton Triggers (e.g. “manual run” EventListener) so the same webhook path can be used by the GUI and by external callers.
- **Tekton Dashboard**: install script or manifest (e.g. `scripts/install-tekton-dashboard.sh` or doc pointing to upstream); document base URL and how to construct a link to a specific PipelineRun.
- **Post to GitHub PR**: task or step that posts a comment with run status and dashboard link; requires GitHub token in a Kubernetes secret; document token scope and security.

## Notes

- **Trigger**: use SSH and the same `generate-run.sh` parameter set (e.g. `--git-revision`, `--registry`, `--storage-class`) so triggered runs behave like CLI-triggered runs. Do not use HTTPS for push if the project standard is SSH.
- **Results DB**: Tekton Results is required for persistent history and test results; the GUI should assume Postgres + Tekton Results are installed (e.g. `install-postgres-kind.sh`, `install-tekton-results.sh`) and that the backend can reach the Results API or DB.
- **Pipeline names**: `stack-pr-test`, `stack-bootstrap`, `stack-merge-release`; ensure the GUI uses the same pipeline and param names as defined in `pipeline/` and `scripts/generate-run.sh`.
- **Security**: in production, the GUI and backend must be secured (auth, RBAC, network policy); for local/Kind, document that the GUI is for dev and that kubeconfig or in-cluster auth is sufficient.
- **Git explore**: for private repos, the backend needs a Git provider token or SSH key with read access; for public repos, provider API or `git ls-remote` may be enough. Keep exploration read-only and rate-limit friendly.
- **Tekton Dashboard**: use the official Dashboard as the target for “view run details” links from GitHub and optionally from the reporting GUI; avoid duplicating its run/log views. Dashboard URL for a PipelineRun is typically something like `{DASHBOARD_BASE}/#/namespaces/{namespace}/pipelineruns/{name}` (confirm from Tekton Dashboard docs).
- **GitHub PR comment**: token must have permission to create issue/PR comments; use a dedicated bot or app token with minimal scope. For multiple runs per PR, consider updating a single comment (e.g. “Latest run: …”) to avoid comment spam.
- **Dashboard iframe**: Tekton Dashboard may need to allow framing from the reporting GUI origin (CSP `frame-ancestors` or X-Frame-Options). Alternatively, serve both under one origin (e.g. reverse proxy) so the iframe is same-origin and auth/cookies work. Document the chosen approach in install/setup docs.
