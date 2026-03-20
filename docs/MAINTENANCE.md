# Architecture and maintenance

This document is a map of the **tekton-dag** repository: what each area does, how to change it safely, and how to test and release.

## Architecture overview

The system wires **stack definitions** (YAML) to **Tekton** pipelines, with an in-cluster **orchestrator** that creates `PipelineRun` objects and optional **Neo4j** queries for test planning.

| Area | Role |
|------|------|
| **`stacks/`** | Stack YAML: applications, build tool per app, downstream dependencies, test configuration. Often synced into the cluster via Helm ConfigMaps. |
| **`tasks/`** | Tekton `Task` manifests: resolve stack, clone repos, compile (per tool), containerize, deploy intercepts / full stack, validate propagation, run tests, versioning, cleanup, graph helpers, etc. |
| **`pipeline/`** | Tekton `Pipeline` definitions and trigger bindings. Core flows: PR test, bootstrap deploy, merge/release. Additional pipelines exist for continuation and DAG verification. |
| **`orchestrator/`** | Flask service: `app.py` (config), `routes.py` (HTTP API), `stack_resolver.py` (repo → stack), `pipelinerun_builder.py` (Run YAML), `k8s_client.py`, `graph_client.py` (Neo4j). |
| **`management-gui/`** | Vue 3 (Vite) frontend plus Flask backend for operating and observing pipelines, teams, and repos. |
| **`helm/tekton-dag/`** | Helm chart: orchestrator, management GUI, RBAC, ConfigMaps for stacks/teams, optional PVCs, values for registry and defaults. |
| **`scripts/`** | Bash utilities; new scripts should `source` **`scripts/common.sh`** for shared defaults (`NAMESPACE`, `GIT_URL`, port-forward helpers, etc.). |
| **`build-images/`** | Parameterized Dockerfiles for compile-side images (Maven, Gradle, Node, Python, PHP, mirrord) and scripts to build/push them. |
| **`teams/`** | Per-team metadata (`team.yaml`) and related values; orchestrator discovers teams under mounted paths (e.g. `/teams/<team>/team.yaml`). |

### Primary pipelines (by name)

| Pipeline | File | Purpose |
|----------|------|---------|
| `stack-pr-test` | `pipeline/stack-pr-pipeline.yaml` | PR path: resolve stack, build changed app, intercept deploy, tests, version bump, cleanup. |
| `stack-bootstrap` | `pipeline/stack-bootstrap-pipeline.yaml` | Full stack bring-up / environment bootstrap. |
| `stack-merge-release` | `pipeline/stack-merge-pipeline.yaml` | Post-merge release flow (images, tags, etc.). |

Other pipelines in `pipeline/` include **`stack-pr-continue`**, **`stack-dag-verify`**, and **`triggers.yaml`** (EventListener / bindings / templates) for webhook-style automation.

### Representative tasks

Tasks live under `tasks/` (see filenames for the canonical Tekton `metadata.name`). Examples: `resolve-stack`, `clone-app-repos`, `build-select-tool-apps`, `build-compile-maven` / `gradle` / `npm` / `pip` / `composer`, `build-containerize`, `deploy-intercept` / `deploy-intercept-mirrord`, `deploy-full-stack`, `validate-propagation`, `run-stack-tests`, `query-test-plan`, `cleanup-stack`, `version-bump`, `post-pr-comment`. Example patterns for optional automation are under **`tasks/examples/`**.

---

## Code map: what to change when

### `stacks/`

- **Contains:** Stack YAML files, optional `stacks/schema.json` for validation/documentation.
- **Modify when:** Adding apps, changing `build.tool`, dependencies, or test definitions; pointing apps at new repos or branches.

### `tasks/`

- **Contains:** Reusable Tekton tasks; `examples/` for copy-paste hooks (e.g. Slack, image scan).
- **Modify when:** Changing how a single step behaves (clone, compile, deploy, test). Apply with `kubectl apply -f tasks/...` or your chart/promotion process.

### `pipeline/`

- **Contains:** Pipeline graphs, parameters, workspace wiring, `finally` cleanup, optional hook task refs.
- **Modify when:** Reordering stages, adding parameters, plugging in optional tasks (`pre-build-task`, etc.), or new pipelines.

### `orchestrator/`

- **Contains:** Flask app, K8s and Neo4j clients, PipelineRun construction.
- **Modify when:** New HTTP APIs, different default params on created runs, resolver rules, or graph behavior.

### `management-gui/`

- **Contains:** `frontend/` (Vue 3), `backend/` (Flask API proxying to K8s/orchestrator as configured).
- **Modify when:** UI features, new views, or backend routes the GUI needs.

### `helm/tekton-dag/`

- **Contains:** Templates, `values.yaml`, `Chart.yaml`.
- **Modify when:** Deploying new images, env vars, ConfigMap keys, resource limits, enabling/disabling subcharts or services.

### `scripts/`

- **Contains:** Local/kind setup, E2E runners, image publish helpers.
- **Modify when:** Automating cluster setup or CI glue; prefer extending **`common.sh`** for shared env defaults.

### `build-images/`

- **Contains:** Dockerfiles and build scripts for compile and tooling images.
- **Modify when:** Toolchain versions, OS packages, or adding a new compile image type.

### `teams/`

- **Contains:** `team.yaml` (and related) per team.
- **Modify when:** Registering stacks per team, documenting team-level defaults (keep aligned with Helm env where both apply).

### `docs/`, `milestones/`, `tests/postman/`

- **Contains:** Human docs, milestone notes, Newman collections for orchestrator/graph APIs.
- **Modify when:** Documenting behavior or extending API contract tests.

---

## How to extend

### Add a new Tekton Task

1. Add `tasks/<your-task>.yaml` with `apiVersion: tekton.dev/v1`, `kind: Task`, and a unique `metadata.name`.
2. Ensure workspaces and params match how the pipeline will call it.
3. Apply to the cluster (or bake into your install path).
4. Reference it from the relevant `pipeline/*.yaml` via `taskRef.name` or a `pipeline` task with `taskSpec` inline (existing pattern in repo).

### Add an orchestrator endpoint

1. Implement the handler in **`orchestrator/routes.py`** inside `register_routes(app)` (or a small module imported there if it grows).
2. Read config from `current_app.config` or env via `create_app()` in **`orchestrator/app.py`** if new settings are needed.
3. Add unit tests under **`orchestrator/tests/`**.
4. Optionally extend **`tests/postman/`** and **`scripts/run-orchestrator-tests.sh`** flows for integration checks.

### Add a pipeline parameter

1. Add a `spec.params` entry in the **`Pipeline`** manifest (`pipeline/stack-*-pipeline.yaml`).
2. Thread `$(params.your-param)` into the tasks that need it.
3. If the orchestrator must set it, extend **`orchestrator/pipelinerun_builder.py`** for each mode (`build_pr_pipelinerun`, `build_bootstrap_pipelinerun`, `build_merge_pipelinerun`) and any callers (`routes.py`).
4. Re-apply pipelines to the cluster; bump Helm/app version if you version the chart with the change.

### Add a compile tool (e.g. Rust, Go)

1. **Stack schema / YAML:** Allow the new `build.tool` value on apps (see existing tools: `npm`, `maven`, `gradle`, `pip`, `composer`).
2. **`build-images/`:** Add a Dockerfile (and publish script if you follow the existing pattern).
3. **`tasks/`:** Add `build-compile-<tool>.yaml` analogous to `build-compile-maven.yaml` (workspace layout, params for image override).
4. **`tasks/build-select-tool-apps.yaml`:** Extend the shell `case` so the tool maps into `.tool-apps.json`.
5. **`pipeline/stack-pr-pipeline.yaml` (and bootstrap/merge if they compile):** Add a `compile-image-<tool>` param, a compile task with `when` expressions keyed off `.tool-apps.json`, and wire results into later tasks (same pattern as existing compile tasks).

### Add a custom hook task

The PR pipeline exposes optional hook parameters (see `stack-pr-test`):

- **`pre-build-task`** — after clone, before compile  
- **`post-build-task`** — after containerize, before deploy  
- **`pre-test-task`** — after deploy, before tests  
- **`post-test-task`** — in `finally` after tests  

Implement a Tekton `Task`, install it in the cluster, then set the pipeline param to that task’s `metadata.name`. See **`tasks/examples/`** for starting points.

---

## Testing

| Scope | Command | Notes |
|-------|---------|--------|
| Orchestrator unit tests | `cd orchestrator && python3 -m pytest tests/ -v` | **62** tests (collector count). |
| Management GUI backend | `cd management-gui/backend && python3 -m pytest tests/ -v` | **56** tests. |
| Management GUI frontend (E2E) | `cd management-gui/frontend && npx playwright test` | **69** tests. |
| Newman / Postman (cluster) | `./scripts/run-orchestrator-tests.sh --all` | Requires running orchestrator (and Neo4j for graph collection); see script header for prerequisites. |

---

## Release process

1. **Chart version:** Bump **`helm/tekton-dag/Chart.yaml`** `version` (and `appVersion` if you track app release separately).
2. **Images:** Rebuild and push orchestrator, management GUI, compile images, and any other images referenced by `values.yaml` / pipelines (use **`build-images/`** and repo scripts such as `scripts/publish-*.sh` as appropriate).
3. **Deploy:** `helm upgrade` the release with updated `values.yaml` image tags and any new parameters.
4. **Tekton definitions:** Re-apply or promote updated `tasks/` and `pipeline/` YAML if they are not fully chart-managed.

For cluster-specific customization (teams, stacks, registries), see **`docs/CUSTOMIZATION.md`** and **`helm/tekton-dag/README.md`** when present.
