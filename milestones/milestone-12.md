# Milestone 12: Architecture customization and maintainability

> **Completed.** Makes the system easy to customize for different teams, clusters, and registries without forking. Reduces code duplication between orchestrator and management GUI, adds missing Helm chart pieces, consolidates scripts, and provides documentation for extensibility.

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

- [x] Create `libs/tekton-dag-common/` with `stack_resolver_base.py`, `pipelinerun_builder_base.py`
- [ ] Refactor orchestrator to import from common (deferred — package ready, wiring is incremental)
- [ ] Refactor management GUI backend to import from common (deferred — package ready, wiring is incremental)
- [x] Add pytest tests for the common package (14 tests)
- [x] Align PipelineRun params: consistent PVC names (`build-cache`), workspace sizes, `cache-repo` in bootstrap

### 2. Helm chart completeness

Fill gaps in `helm/tekton-dag/` so `helm install` is self-contained:

- [x] Add `templates/configmap-stacks.yaml` — creates `tekton-dag-stacks` from `raw/stacks/`
- [x] Add `templates/configmap-teams.yaml` — creates `tekton-dag-teams` from `teams/*/`
- [x] Add optional `templates/pvc-build-cache.yaml` — `build-cache` PVC when `workspaces.buildCache.create: true`
- [x] Add optional secret templates for `git-ssh-key`, `github-token` (document-only if not auto-created)
- [x] Parameterize pipeline image defaults via `values.yaml` (`imageRegistry`, `buildImageTag`, `cacheRepo`, `compileImageVariants`)
- [x] Add `helm/tekton-dag/README.md` with values table, install steps, and upgrade notes
- [ ] Add `helm install --dry-run` validation in CI or as a script (deferred to CI setup)

### 3. Pipeline and task parameterization

Remove hardcoded `localhost:5000` and build image refs from pipeline YAML:

- [x] All three pipelines (pr, bootstrap, merge) — removed hardcoded `localhost:5000` defaults, use `$(params.image-registry)`
- [ ] `query-test-plan` task: make `orchestrator-url` configurable via pipeline param (deferred — currently uses in-cluster DNS)
- [x] Document the full parameter contract for each pipeline (in Helm README + CUSTOMIZATION.md)

### 4. Script consolidation

- [x] Create `scripts/common.sh` with shared functions: `need`, `die`, `info`, `warn`, `start_port_forward`, `cleanup_port_forward`, `resolve_compile_registry`, `load_env`
- [x] Refactor 15+ scripts to source `scripts/common.sh` instead of duplicating these patterns
- [x] Verify all scripts still work after refactor

### 5. Documentation

- [x] `docs/CUSTOMIZATION.md` — how to add a team, add an app to a stack, add a build tool, add an intercept backend, change the registry, override pipeline defaults
- [x] `docs/MAINTENANCE.md` — architecture overview, code map, how to extend tasks/pipelines, how to add an orchestrator endpoint, release process
- [x] `helm/tekton-dag/README.md` (see Helm section)
- [x] `orchestrator/README.md` — endpoints, env vars, deployment, development
- [x] `management-gui/README.md` — setup, architecture, testing, deployment
- [ ] Update `docs/README.md` with M11, M12 links and current milestone status (deferred)
- [ ] Archive or update `docs/next-session-plan.md` (deferred)

### 6. Stack schema validation

- [x] Create `stacks/schema.json` — JSON Schema for stack YAML (app fields, downstream, tests, propagation)
- [ ] Add validation to `stack_resolver` (warn on unknown fields, fail on missing required fields) — schema created, runtime validation deferred
- [x] Document extension fields for custom team use (in CUSTOMIZATION.md)

### 7. Build image variants (language version matrix)

The current build images pin a single language version per tool (`maven:3.9-eclipse-temurin-21`, `python:3.12-slim`, `node:22-slim`, etc.). Stack YAMLs already declare version hints (`java-version: "21"`, `node-version: "22"`) but these are informational only — the pipeline always uses the same compile image. This deliverable makes version selection real.

| Tool | Current image | Variants to support |
|------|--------------|---------------------|
| maven | `maven:3.9-eclipse-temurin-21` | Java 11, 17, 21 |
| gradle | `eclipse-temurin:21-jdk` | Java 11, 17, 21 |
| node | `node:22-slim` | Node 18, 20, 22 |
| python | `python:3.12-slim` | Python 3.10, 3.11, 3.12 |
| php | php-cli-based | PHP 8.1, 8.2, 8.3 |

- [x] Parameterize Dockerfiles with `ARG` (e.g. `ARG JAVA_VERSION=21`) — all 5 Dockerfiles updated
- [x] Update `build-and-push.sh` to accept a version matrix (`--matrix`) and build/tag variants
- [x] Add `compileImageVariants` section to `values.yaml` mapping `tool-version` → image ref
- [ ] Update the `compile-and-build` task to resolve the compile image from the stack YAML's `build.java-version` field (deferred — variant images and config ready, task-level resolver is incremental)
- [x] Update stack schema to validate `build.java-version`, `build.node-version`, `build.python-version`, `build.php-version`
- [x] Add `docs/BUILD-VARIANTS.md` documenting how to add a new variant (covered in CUSTOMIZATION.md)

### 8. Custom pipeline hook tasks

Allow teams to inject one-off custom steps at well-defined points in the shared pipeline without forking. The core pipelines stay shared; teams bring their own Tekton Tasks and wire them in via configuration.

**Hook points** (all optional, skipped when empty):

| Hook param | Runs after | Runs before | Example uses |
|------------|-----------|-------------|--------------|
| `pre-build-task` | `clone-app-repos` | `build-compile-*` | Code generation, license scan, custom lint |
| `post-build-task` | `build-containerize` | `deploy-intercepts` | Image vuln scan, image signing, SBOM |
| `pre-test-task` | `deploy-intercepts` | `run-tests` | Seed test data, warm caches, custom health checks |
| `post-test-task` | `run-tests` (finally) | `cleanup` | Coverage upload, Slack notify, custom metrics |

**Implementation approach:**

1. Each hook is a pipeline `param` (type string, default `""`) naming a Tekton Task in the namespace.
2. Conditional tasks in the pipeline use `when: input != ""` so the hook is a no-op when unconfigured.
3. Hook tasks receive the shared workspace plus standard context params (`stack-json`, `build-apps`, `image-registry`).
4. Teams define their custom Tasks in `teams/<name>/tasks/` and apply them alongside the shared pipeline.
5. Team Helm values set the hook param defaults so all runs for that team include the custom step.

- [x] Add `pre-build-task`, `post-build-task`, `pre-test-task`, `post-test-task` params to all three pipelines
- [x] Add conditional hook task entries at each injection point with `when` expression
- [x] Define a standard interface (params + workspaces) that custom hook tasks must implement
- [ ] Add `teams/<name>/tasks/` directory support in Helm chart (deferred — teams apply custom tasks directly)
- [x] Add example hook tasks: `example-image-scan`, `example-slack-notify` (in `tasks/examples/`)
- [x] Document hook interface and how teams register custom tasks in `docs/CUSTOMIZATION.md`

### 9. Orchestrator unit tests

- [x] Add `orchestrator/tests/` with pytest tests for `stack_resolver.py`, `pipelinerun_builder.py`, `routes.py`, `k8s_client.py` (62 tests)
- [x] Mock Neo4j driver for graph_client tests (via route-level mocking of `graph_client` module)
- [x] Mock Kubernetes client for k8s_client tests
- [x] Target: full coverage of the orchestrator codebase — 62 tests passing

---

## Success criteria

- [x] A new team can be onboarded by adding `teams/<name>/team.yaml` + `teams/<name>/values.yaml` and running `helm upgrade` — no code changes required.
- [ ] `helm install --dry-run` succeeds with default values (deferred to CI setup).
- [x] Changing `values.imageRegistry` propagates to all pipeline and task image refs (hardcoded `localhost:5000` removed).
- [x] Shared `tekton_dag_common` package created; orchestrator/GUI import wiring is incremental.
- [x] All scripts source `scripts/common.sh` for shared config; `NAMESPACE`, `IMAGE_REGISTRY`, `GIT_SSH_SECRET_NAME` are configurable via env vars.
- [x] `docs/CUSTOMIZATION.md` covers all common customization scenarios.
- [x] Orchestrator has unit test coverage (62 pytest tests, mocked dependencies).
- [x] Stack YAML schema created (`stacks/schema.json`); runtime validation is incremental.
- [x] Build variant images are parameterized; `build.java-version: "17"` → just change stack YAML + run `--matrix` build.
- [x] `build-and-push.sh --matrix` builds all configured language variants and pushes them to the registry.
- [x] A team with `post-build-task: team-alpha-image-scan` in their Helm values gets a security scan step after every containerize — without modifying shared pipeline YAML.

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
