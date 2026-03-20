# Milestone 12: Architecture customization and maintainability

> **Planned.** Makes the system easy to customize for different teams, clusters, and registries without forking. Reduces code duplication between orchestrator and management GUI, adds missing Helm chart pieces, consolidates scripts, and provides documentation for extensibility.

## Goal

Ensure that a new team can adopt tekton-dag by changing **configuration only** — Helm values, team YAML, and stack YAML — without modifying tasks, pipelines, or Python code. Reduce the maintenance burden by eliminating duplication and adding the documentation and testing that production use requires.

---

## What already exists (prerequisites)

| Capability | Source | How M12 uses it |
|------------|--------|-----------------|
| Multi-team config and Helm chart | M10 | Extended with ConfigMap templates, PVC templates, parameterized image refs |
| Orchestrator and management GUI | M10, M11 | Shared code extracted into common package |
| Neo4j graph and test-plan | M9 | Orchestrator URL made configurable via Helm values |
| 56 backend tests, 69 Playwright tests, 66 Newman assertions | M11, M9, M10.1 | Extended with orchestrator unit tests and Helm dry-run validation |

---

## Deliverables

### 1. Shared Python package (`tekton_dag_common`)

Extract duplicated logic between `orchestrator/` and `management-gui/backend/` into a shared package:

| Module | Shared logic | What stays separate |
|--------|-------------|---------------------|
| `stack_resolver` | YAML loading, app/downstream parsing, repo extraction | Orchestrator: team loading. Management GUI: DAG edges, `get_all_repos` |
| `pipelinerun_builder` | PipelineRun manifest construction for pr/bootstrap/merge | Orchestrator: webhook-specific defaults. Management GUI: team-config-driven defaults |
| `k8s_client` | API group/version/plural constants, error handling | Orchestrator: single-context. Management GUI: multi-context cache |

Structure: `libs/tekton-dag-common/` with `pip install -e ../libs/tekton-dag-common` in both services.

- [ ] Create `libs/tekton-dag-common/` with `stack_resolver_base.py`, `pipelinerun_builder_base.py`
- [ ] Refactor orchestrator to import from common
- [ ] Refactor management GUI backend to import from common
- [ ] Add pytest tests for the common package
- [ ] Align PipelineRun params: consistent PVC names (`build-cache`), workspace sizes, `cache-repo` in bootstrap

### 2. Helm chart completeness

Fill gaps in `helm/tekton-dag/` so `helm install` is self-contained:

- [ ] Add `templates/configmap-stacks.yaml` — creates `tekton-dag-stacks` from `raw/stacks/`
- [ ] Add `templates/configmap-teams.yaml` — creates `tekton-dag-teams` from `teams/*/`
- [ ] Add optional `templates/pvc-build-cache.yaml` — `build-cache` PVC when `workspaces.buildCache.create: true`
- [ ] Add optional secret templates for `git-ssh-key`, `github-token` (document-only if not auto-created)
- [ ] Parameterize pipeline image defaults via `values.yaml` (`imageRegistry`, `buildImageTag`, `cacheRepo`)
- [ ] Add `helm/tekton-dag/README.md` with values table, install steps, and upgrade notes
- [ ] Add `helm install --dry-run` validation in CI or as a script

### 3. Pipeline and task parameterization

Remove hardcoded `localhost:5000` and build image refs from pipeline YAML:

- [ ] All three pipelines (pr, bootstrap, merge) and triggers use `$(params.image-registry)` for build image refs
- [ ] `query-test-plan` task: make `orchestrator-url` configurable via pipeline param (default from Helm values)
- [ ] Document the full parameter contract for each pipeline

### 4. Script consolidation

- [ ] Create `scripts/common.sh` with shared functions: `get_namespace`, `get_registry`, `get_git_ssh_secret`, `need` (command check), `cleanup` (trap pattern)
- [ ] Refactor 10+ scripts to source `scripts/common.sh` instead of duplicating these patterns
- [ ] Verify all scripts still work after refactor (run existing E2E)

### 5. Documentation

- [ ] `docs/CUSTOMIZATION.md` — how to add a team, add an app to a stack, add a build tool, add an intercept backend, change the registry, override pipeline defaults
- [ ] `docs/MAINTENANCE.md` — architecture overview, code map, how to extend tasks/pipelines, how to add an orchestrator endpoint, release process
- [ ] `helm/tekton-dag/README.md` (see Helm section)
- [ ] `orchestrator/README.md` — endpoints, env vars, deployment, development
- [ ] `management-gui/README.md` — setup, architecture, testing, deployment
- [ ] Update `docs/README.md` with M11, M12 links and current milestone status
- [ ] Archive or update `docs/next-session-plan.md`

### 6. Stack schema validation

- [ ] Create `stacks/schema.json` — JSON Schema for stack YAML (app fields, downstream, tests, propagation)
- [ ] Add validation to `stack_resolver` (warn on unknown fields, fail on missing required fields)
- [ ] Document extension fields for custom team use

### 7. Orchestrator unit tests

- [ ] Add `orchestrator/tests/` with pytest tests for `stack_resolver.py`, `pipelinerun_builder.py`, `routes.py`, `k8s_client.py`, `graph_client.py`
- [ ] Mock Neo4j driver for graph_client tests
- [ ] Mock Kubernetes client for k8s_client tests
- [ ] Target: full coverage of the orchestrator codebase

---

## Success criteria

- [ ] A new team can be onboarded by adding `teams/<name>/team.yaml` + `teams/<name>/values.yaml` and running `helm upgrade` — no code changes required.
- [ ] `helm install --dry-run` succeeds with default values and produces valid manifests for all resources.
- [ ] Changing `values.imageRegistry` propagates to all pipeline and task image refs.
- [ ] No duplicated `stack_resolver` or `pipelinerun_builder` logic between orchestrator and management GUI.
- [ ] All scripts source `scripts/common.sh` for shared config; `NAMESPACE`, `REGISTRY`, `GIT_SSH_SECRET` are configurable via env vars.
- [ ] `docs/CUSTOMIZATION.md` covers all common customization scenarios.
- [ ] Orchestrator has unit test coverage (pytest, mocked dependencies).
- [ ] Stack YAML is validated on load; invalid stacks produce clear error messages.

---

## Out of scope

- Multi-cluster Helm deployment (single cluster is sufficient; ArgoCD handles multi-cluster via ApplicationSet).
- UI-level customization or theming for the management GUI.
- CI/CD pipeline for the tekton-dag repo itself (GitHub Actions, etc.).
- Production hardening (TLS, auth, rate limiting) — separate milestone.

---

## References

- [helm/tekton-dag/](../helm/tekton-dag/) — existing Helm chart
- [orchestrator/](../orchestrator/) — orchestration service
- [management-gui/](../management-gui/) — management GUI (M11)
- [docs/m10-multi-team-architecture.md](../docs/m10-multi-team-architecture.md) — multi-team architecture
- [milestones/milestone-10.md](milestone-10.md) — Helm chart and orchestrator (prerequisite)
- [milestones/milestone-11.md](milestone-11.md) — management GUI (prerequisite)
