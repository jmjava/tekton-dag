# Session notes — 2026-03-12 through 2026-03-17

Changes since the 2026-02-28 session notes. Covers milestones 4.1 through 10.

---

## 1. Milestone 4.1 — Standalone baggage libraries (completed, merged)

Extracted embedded baggage middleware from each app repo into standalone, publishable libraries under `libs/`. App repos now consume these as dependencies.

- `baggage-spring-boot-starter` (Maven, Spring Boot)
- `baggage-servlet-filter` (Maven, Spring Legacy / WAR)
- `@tekton-dag/baggage` (npm, Node/Express/Nitro/Vue)
- `tekton-dag-baggage` (pip, Flask/WSGI)
- `tekton-dag/baggage-middleware` (Composer, PHP PSR-15 + Guzzle)

Build-time exclusion: Maven profiles, devDependencies, requirements-dev.txt, require-dev.

---

## 2. Milestone 5 — Original traffic validation + mirrord evaluation (completed, merged)

- **validate-original-traffic** task: sends requests to every service WITHOUT intercept headers while Telepresence intercepts are active. Proves original deployments continue serving normal traffic.
- **mirrord evaluation**: header-based intercept works identically to Telepresence. Recommendation: use mirrord in the lower environment.

---

## 3. Milestone 6 — Full MetalBear testing (completed, merged)

Validated mirrord for all required PR pipeline scenarios: concurrent intercepts on different services, normal traffic unaffected, combined (N intercepts + normal traffic). OSS mirrord is sufficient.

---

## 4. Milestone 7 — Run either Telepresence or mirrord (completed, merged)

- `deploy-intercept-mirrord` Tekton task with socat TCP proxy and header-based traffic stealing.
- `tekton-dag-build-mirrord` build image (mirrord CLI + kubectl + jq + socat).
- Pipeline `intercept-backend` param (default: telepresence). When set to `mirrord`, pipeline routes to the mirrord task instead of Telepresence.
- Pass-through result task for mirrord intercept output.
- E2E passed for both backends (telepresence and mirrord).
- **Fixes**: mirrord proxy Pod securityContext (capabilities under container, hostPID at spec level), E2E script bash re-exec guard, PipelineRun name capture from `kubectl create -o name`, Tekton Results RBAC (ClusterRoleBinding for default SA).
- `--skip-bootstrap` flag added to `run-e2e-with-intercepts.sh`.
- Regression docs added to README.

---

## 5. Milestone 7.1 — Pipeline speed optimizations (completed, merged)

- **Parallel containerize**: `build-containerize` task spawns one Kaniko pod per app in parallel (via kubectl), each mounting the shared workspace PVC. Wall-clock = max(per-app) instead of sum.
- **Kaniko cache**: `--cache=true --cache-repo=<registry>/kaniko-cache --cache-ttl=168h` via new `cache-repo` pipeline param (default: `localhost:5000/kaniko-cache`).
- **Parallel clone**: `clone-app-repos` task clones all app repos in background (`&`) and waits.
- Both bootstrap and PR pipelines updated.
- E2E passed for both backends.

---

## 6. Milestone 9 — Plan only (not yet implemented)

Plan written for test-trace regression graph and minimal test selection:
- Collect traces via mock Datadog API.
- Store graph in Neo4j.
- Query: changed-app → minimal e2e + individual tests.
- Integrate into PR pipeline before `run-tests`.

---

## 7. Milestone 10 — Multi-team scaling (in progress)

### 10.1 Helm chart (`helm/tekton-dag/`)

Packages the entire system as a single Helm chart:
- All 22 Tekton Tasks, 5 Pipelines, Triggers
- RBAC (ServiceAccount, ClusterRoleBinding)
- Orchestration Service (Deployment + Service)
- `package.sh` stages raw task/pipeline YAMLs into chart
- `values.yaml` with per-team parameterization
- `helm template` renders 39 resources

### 10.2 Orchestration service (`orchestrator/`)

Python/Flask service running as an in-cluster pod:
- `POST /webhook/github` — receives GitHub PR/merge events, replaces CEL overlays
- `POST /api/run` — manual PipelineRun trigger (replaces `generate-run.sh` for production)
- `POST /api/bootstrap` — trigger bootstrap pipeline
- `GET /api/stacks`, `/api/teams`, `/api/runs` — query endpoints
- `POST /api/reload` — hot-reload stack configs
- Stack resolver: loads stack YAMLs, builds dynamic repo-to-stack map
- PipelineRun builder: generates manifests via Kubernetes Python client

### 10.3 Multi-team data model (`teams/default/`)

- `team.yaml`: team config (namespace, registry, stacks, limits)
- `values.yaml`: Helm values for ArgoCD ApplicationSet
- Orchestration service loads team configs on startup

### 10.4 ArgoCD ApplicationSet (`argocd/`)

- Git File Generator: scans `teams/*/values.yaml`
- Auto-provisions team clusters when team config added to Git
- AppProject with scoped RBAC for tekton-dag resources

### 10.5 Bootstrap at scale

- `max-parallel-builds` param added to `build-containerize` task and both pipelines
- Batched Kaniko pod creation: launches pods in groups of `max-parallel-builds`, waits per batch
- Default: 0 (unlimited, all at once — same as before for small stacks)

### 10.6 Architecture docs

- `docs/m10-multi-team-architecture.md` — layers, request flow, framework decisions
- `milestones/milestone-10.md` — full deliverables and acceptance criteria

### Framework decisions

| Framework | Used? | Role |
|---|---|---|
| Tekton | Kept | Pipeline execution engine (unchanged) |
| Helm | New | Package tekton-dag for deployment |
| ArgoCD | New | GitOps provisioning across clusters |
| Orkestra | Rejected | Its DAG is for Helm chart deps, not app deps |

### Local dev preserved

- `kubectl apply -f tasks/ -f pipeline/` still works
- `generate-run.sh`, `run-e2e-with-intercepts.sh` still work
- Orchestration service is an additional entry point, not a replacement

---

## 8. Milestone 10.1 — Orchestration service testing (planned)

Plan written for:
- Build and publish orchestrator Docker image to Kind registry
- Deploy orchestrator to cluster via Helm
- Postman/Newman test suite covering all endpoints
- Integration validation (verify PipelineRuns execute)

---

## 9. Bug fixes in this session

- **Containerize batch wait_for_batch()**: status messages went to stdout and got captured as "failures" even when pods succeeded. Fixed by redirecting status output to stderr (`>&2`).

---

## 10. Milestone ordering (updated)

1. M7.1 — Done (merged to main)
2. M10 — In progress (multi-team scaling)
3. M10.1 — Planned (orchestration service testing)
4. M9 — Planned (test-trace regression graph)
5. M8 — Last (demo assets)

---

## Files changed (key additions)

```
helm/tekton-dag/                     # NEW: Helm chart
orchestrator/                        # NEW: Flask orchestration service
teams/default/                       # NEW: Default team config
argocd/                              # NEW: ArgoCD manifests
docs/m10-multi-team-architecture.md  # NEW: Architecture doc
milestones/milestone-10.md           # NEW: M10 plan
milestones/milestone-10-1.md         # NEW: M10.1 plan
tasks/build-containerize.yaml        # MODIFIED: parallel Kaniko pods, cache, batching
tasks/clone-app-repos.yaml           # MODIFIED: parallel clone
pipeline/stack-bootstrap-pipeline.yaml  # MODIFIED: cache-repo, max-parallel-builds
pipeline/stack-pr-pipeline.yaml         # MODIFIED: cache-repo, max-parallel-builds
README.md                            # MODIFIED: M7.1 completed, M10 in progress
```
