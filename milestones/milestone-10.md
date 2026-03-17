# Milestone 10: Multi-Team Scaling and In-Cluster Orchestration

> **Follows [milestone 7.1](milestone-7-1.md).** Scales the tekton-dag system for multiple teams, each with their own cluster and up to 40 apps. Adds an in-cluster orchestration service, Helm chart packaging, and ArgoCD-based team provisioning. **Tekton remains the pipeline execution engine.**

## Goal

Move orchestration logic from developer-workstation scripts into an **in-cluster service** so that:

1. Multiple teams can each run their own cluster with their own stacks (up to 40 apps per team).
2. GitHub webhooks are handled by a service (not hardcoded CEL overlays).
3. The entire system is packaged as a **Helm chart** and deployed via **ArgoCD**.
4. **Local dev workflow is preserved** — `kubectl apply`, `generate-run.sh`, and E2E scripts still work.

---

## Background

### Current state

- Pipelines and tasks are applied with `kubectl apply -f tasks/ -f pipeline/`.
- PipelineRuns are triggered by `generate-run.sh` (manual) or EventListener with hardcoded CEL overlays (webhook).
- One stack (`stack-one`) with 3 apps. Repo-to-stack mapping is hardcoded in `pipeline/triggers.yaml`.
- Multi-namespace support exists (M4) but no multi-team or multi-cluster concept.
- [docs/argocd-architecture-guide.md](../docs/argocd-architecture-guide.md) has the ArgoCD integration design (not yet implemented).

### Target state

- N teams, each with a cluster, each with 1+ stacks, each stack with up to 40 apps.
- Orchestration service pod handles all webhook routing and PipelineRun creation.
- Helm chart deploys the full system (tasks, pipelines, RBAC, orchestration service) with per-team values.
- ArgoCD ApplicationSet auto-provisions teams from Git.
- Local dev: `helm install` or raw `kubectl apply` + existing scripts.

---

## Architecture

### Layers

```
┌─────────────────────────────────────────────────────────────┐
│  ArgoCD (GitOps)                                            │
│  - Deploys tekton-dag Helm chart to each team cluster       │
│  - ApplicationSet: teams/*/values.yaml → auto-provision     │
│  - Sync waves: CRDs → RBAC → Tasks → Pipelines → Orch Svc  │
├─────────────────────────────────────────────────────────────┤
│  Orchestration Service (new, in-cluster pod)                │
│  - Receives GitHub webhooks (replaces CEL overlays)         │
│  - Resolves repo → stack → team dynamically                 │
│  - Creates Tekton PipelineRuns via Kubernetes API            │
│  - REST API for manual triggers, status, bootstrap           │
├─────────────────────────────────────────────────────────────┤
│  Tekton (execution engine — unchanged)                      │
│  - Tasks: clone, compile, containerize, deploy, test         │
│  - Pipelines: stack-pr-test, stack-merge-release, bootstrap  │
│  - PipelineRuns created by orchestration service or scripts  │
├─────────────────────────────────────────────────────────────┤
│  Kubernetes                                                  │
│  - Pods, Deployments, Services, PVCs, RBAC                   │
│  - One cluster per team (or shared with namespace isolation) │
└─────────────────────────────────────────────────────────────┘
```

### What replaces what

| Today (scripts) | M10 (in-cluster) | Notes |
|---|---|---|
| `generate-run.sh` | Orchestration Service REST API | CLI wrapper optional |
| CEL overlays in `triggers.yaml` | Orchestration Service webhook handler | Dynamic routing |
| `stacks/registry.yaml` | ConfigMap (loaded by orchestration service) | Dynamic scan |
| `stacks/versions.yaml` | ConfigMap per team | Same format |
| `bootstrap-namespace.sh` | ArgoCD Application | Declarative |

### What does NOT change

- Tekton Tasks (`tasks/*.yaml`)
- Tekton Pipelines (`pipeline/stack-*.yaml`)
- Stack YAML format (`stacks/*.yaml`)
- PVC workspaces, Kaniko builds, intercepts (Telepresence/mirrord)
- E2E scripts (`run-e2e-with-intercepts.sh`, `generate-run.sh`)
- Local dev workflow

### Framework decisions

| Framework | Role | Why |
|---|---|---|
| **Tekton** | Pipeline execution engine | Already in use; keeps all Tasks/Pipelines |
| **Helm** | Package tekton-dag for deployment | Repeatable, parameterized; values per team |
| **ArgoCD** | GitOps deployment to clusters | Hub-and-spoke; ApplicationSet for auto-provision |
| **Orkestra** | Not used | Its DAG is for Helm chart deps, not app deps; would add Argo Workflows alongside Tekton — unnecessary |

---

## Deliverables

### 10.1 Helm chart for tekton-dag

Package the entire system as a Helm chart.

**Structure:**

```
helm/tekton-dag/
  Chart.yaml
  values.yaml                    # defaults
  templates/
    _helpers.tpl
    rbac.yaml                    # ServiceAccount, ClusterRole, ClusterRoleBinding
    tasks/                       # one template per task (or a loop over tasks/*.yaml)
    pipelines/                   # one template per pipeline
    orchestration-deployment.yaml
    orchestration-service.yaml
    orchestration-configmap.yaml # stack YAMLs + team config
    pvc.yaml                     # shared-workspace, build-cache
```

**Values (excerpt):**

```yaml
teamName: "team-alpha"
namespace: "tekton-pipelines"
imageRegistry: "localhost:5000"
cacheRepo: "localhost:5000/kaniko-cache"
interceptBackend: "telepresence"
maxParallelBuilds: 5
orchestrationService:
  enabled: true
  image: "localhost:5000/tekton-dag-orchestrator:latest"
  replicas: 1
stacks:
  - stacks/stack-one.yaml
```

**Instructions:**

1. Create `helm/tekton-dag/Chart.yaml` with name, version, description.
2. Create `values.yaml` with sensible defaults matching current Kind setup.
3. Template each resource in `tasks/`, `pipeline/`, and RBAC from existing YAMLs.
4. Add orchestration service Deployment, Service, ConfigMap templates.
5. Validate: `helm template tekton-dag ./helm/tekton-dag` renders correctly; `helm install --dry-run` passes.
6. Test: `helm install tekton-dag ./helm/tekton-dag -n tekton-pipelines` deploys the full system on Kind, and existing E2E scripts pass.

**Acceptance:** `helm install` on Kind deploys the same system as `kubectl apply -f tasks/ -f pipeline/`. E2E regression passes.

---

### 10.2 Orchestration service

A lightweight Python/Flask service running as a Deployment in the cluster.

**Endpoints:**

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/webhook/github` | Receive GitHub PR/merge webhook events |
| `POST` | `/api/run` | Manual trigger (replaces `generate-run.sh --apply`) |
| `POST` | `/api/bootstrap` | Trigger bootstrap pipeline |
| `GET` | `/api/stacks` | List registered stacks and their apps |
| `GET` | `/api/runs` | List recent PipelineRuns (proxy to `kubectl`) |
| `GET` | `/healthz` | Liveness probe |
| `GET` | `/readyz` | Readiness probe |

**Webhook handler (`POST /webhook/github`):**

1. Validate webhook signature (HMAC with `github-webhook-secret`).
2. Parse event: extract `action`, `pull_request.base.repo.name`, `pull_request.head.sha`, `pull_request.number`.
3. Resolve: scan loaded stacks to find which stack+app matches the repo name (replaces hardcoded CEL overlays and `registry.yaml`).
4. If PR opened/synchronize/reopened → create `stack-pr-test` PipelineRun.
5. If PR closed+merged → create `stack-merge-release` PipelineRun.
6. Return 200 with PipelineRun name.

**Stack resolver:**

- On startup, load stack YAMLs from mounted ConfigMap or `/stacks/` volume.
- Build an in-memory map: `repo-name → {stack-file, app-name, team}`.
- Watch for ConfigMap changes (or reload on SIGHUP) for dynamic updates.

**PipelineRun creator:**

- Generate PipelineRun YAML (same structure as `generate-run.sh` output).
- Apply via Kubernetes Python client (`kubernetes.client.CustomObjectsApi`).
- ServiceAccount needs: `create` on `pipelineruns.tekton.dev`, `get/list` on `pods`, `pipelineruns`.

**Instructions:**

1. Create `orchestrator/` directory with Flask app, Dockerfile, requirements.txt.
2. Implement webhook handler, stack resolver, PipelineRun creator.
3. Add Dockerfile, build image, publish to Kind registry.
4. Add `build-images/orchestrator/` for the build image definition.
5. Test: send mock webhook payload → PipelineRun created → pipeline runs.

**Acceptance:** GitHub webhook → orchestration service → PipelineRun created → pipeline runs to completion. Same result as EventListener+CEL but with dynamic routing.

---

### 10.3 Multi-team data model

Extend stacks and config for multiple teams.

**Team config (`teams/<team>/team.yaml`):**

```yaml
name: team-alpha
namespace: tekton-pipelines
cluster: kind-tekton-stack    # ArgoCD cluster name
imageRegistry: localhost:5000
cacheRepo: localhost:5000/kaniko-cache
interceptBackend: telepresence
maxConcurrentRuns: 3
maxParallelBuilds: 5
stacks:
  - stacks/stack-one.yaml
  # teams with 40 apps would list larger stacks here
```

**Dynamic registry:**

- Orchestration service scans all team configs on startup.
- Builds global map: `repo-name → {team, stack-file, app-name}`.
- No more `stacks/registry.yaml` with manual entries (backward-compatible: if no team configs exist, fall back to `registry.yaml`).

**Per-team versions:**

- Each team gets its own `versions.yaml` section (or separate file).
- Orchestration service resolves versions per team context.

**Instructions:**

1. Create `teams/default/team.yaml` matching current single-team setup.
2. Update orchestration service to load team configs.
3. Keep backward compatibility: if `teams/` doesn't exist, fall back to `stacks/registry.yaml`.
4. Document the team config schema.

**Acceptance:** Adding a new `teams/<name>/team.yaml` registers that team's stacks in the orchestration service. Existing single-team setup works unchanged.

---

### 10.4 ArgoCD ApplicationSet for team provisioning

**ApplicationSet (`argocd/applicationset.yaml`):**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: tekton-dag-teams
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/jmjava/tekton-dag.git
        revision: main
        files:
          - path: "teams/*/values.yaml"
  template:
    metadata:
      name: "tekton-dag-{{team}}"
    spec:
      project: tekton-dag
      source:
        repoURL: https://github.com/jmjava/tekton-dag.git
        targetRevision: main
        path: helm/tekton-dag
        helm:
          valueFiles:
            - "../../teams/{{team}}/values.yaml"
      destination:
        server: "{{cluster}}"
        namespace: "{{namespace}}"
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

**Instructions:**

1. Create `argocd/` directory with ApplicationSet, AppProject, and RBAC manifests.
2. Create `teams/default/values.yaml` with current Kind defaults.
3. Document: adding `teams/new-team/values.yaml` auto-provisions via ArgoCD.
4. Test locally: install ArgoCD on Kind, apply ApplicationSet, verify Helm chart deployed.

**Acceptance:** Adding a team values file to Git triggers ArgoCD to deploy the full tekton-dag stack for that team. Removing it cleans up.

---

### 10.5 Bootstrap at scale (40 apps)

Current `build-containerize` spawns one Kaniko pod per app. With 40 apps, that's 40 pods simultaneously — may exhaust node resources.

**Batched parallel builds:**

- Add `max-parallel-builds` param to `build-containerize` task (default: 5).
- Task script spawns Kaniko pods in batches of `max-parallel-builds`, waits for batch, then next batch.
- Pipeline param `max-parallel-builds` passed through from `values.yaml`.

**Selective bootstrap:**

- Orchestration service `POST /api/bootstrap` accepts optional `?apps=app1,app2` query.
- Generates PipelineRun with `build-apps` param containing only the requested apps.
- Full bootstrap (no `apps` param) builds everything.

**Incremental bootstrap:**

- Before building, check if the image already exists in the registry (e.g., `crane manifest <image>` or registry API).
- Skip apps whose images are already present and match the expected tag.
- Add `force-rebuild` param (default: false) to override.

**Instructions:**

1. Add `max-parallel-builds` param to `build-containerize` task and both pipelines.
2. Modify task script to batch Kaniko pods.
3. Add selective bootstrap support to orchestration service.
4. Document incremental bootstrap as future optimization (or implement if time permits).

**Acceptance:** Bootstrap with 40 apps runs in batches without exhausting resources. Selective bootstrap builds only requested apps.

---

### 10.6 Documentation and migration guide

**New docs:**

- `docs/m10-multi-team-architecture.md` — architecture overview, layers, data flow, framework decisions.
- `docs/m10-team-onboarding.md` — step-by-step for adding a new team (create team.yaml, values.yaml, stack files, ArgoCD provisions automatically).
- `docs/m10-migration-guide.md` — how to migrate from script-driven single-team to Helm+ArgoCD multi-team.

**Updated docs:**

- `README.md` — milestone status, next session, new M10 section.
- `docs/argocd-architecture-guide.md` — update with actual ApplicationSet and Helm chart details.

**Acceptance:** A new team can be onboarded by following the runbook. Existing users can migrate by following the migration guide.

---

## Local dev workflow (preserved)

| Method | When to use | What happens |
|---|---|---|
| `kubectl apply -f tasks/ -f pipeline/` | Quick iteration on task/pipeline YAML | Raw apply, no Helm |
| `helm install tekton-dag ./helm/tekton-dag` | Test full chart locally | Same resources, parameterized |
| `./scripts/generate-run.sh --apply` | Trigger a run manually | Creates PipelineRun directly |
| `./scripts/run-e2e-with-intercepts.sh` | E2E regression | Full bootstrap+PR or skip-bootstrap |
| Orchestration service webhook | Test webhook flow locally | Service runs in Kind, receives events |

---

## Success criteria

- [ ] Helm chart installs on Kind and E2E passes (10.1).
- [ ] Orchestration service receives webhook, creates PipelineRun, pipeline succeeds (10.2).
- [ ] Multi-team config loads; adding a team registers its stacks (10.3).
- [ ] ArgoCD ApplicationSet provisions a team from Git (10.4).
- [ ] Bootstrap with `max-parallel-builds` batching works for large app counts (10.5).
- [ ] Architecture docs, onboarding runbook, migration guide written (10.6).
- [ ] Existing local dev workflow (scripts, raw kubectl apply) still works.
- [ ] Existing E2E tests (telepresence + mirrord) pass unchanged.

---

## Non-goals

- Replacing Tekton with another execution engine.
- Implementing a full multi-cluster control plane (ArgoCD handles cross-cluster deployment).
- Building a UI for the orchestration service (REST API + CLI is sufficient for M10).
- Production hardening (TLS, auth, rate limiting) — this is PoC/dev.

---

## References

- [docs/argocd-architecture-guide.md](../docs/argocd-architecture-guide.md) — existing ArgoCD design
- [docs/bootstrap-pipeline-speed-analysis.md](../docs/bootstrap-pipeline-speed-analysis.md) — M7.1 optimizations (parallel builds, cache)
- [docs/m4-multi-namespace.md](../docs/m4-multi-namespace.md) — multi-namespace foundation
- [pipeline/triggers.yaml](../pipeline/triggers.yaml) — current EventListener/CEL (to be replaced by orchestration service)
- [scripts/generate-run.sh](../scripts/generate-run.sh) — current PipelineRun generation (orchestration service replaces this for production)
- ArgoCD ApplicationSet docs: Git File Generator, Cluster Generator
- Red Hat: Operating Tekton at scale — 10 lessons learned
