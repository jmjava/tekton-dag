# Milestone 8: Demo assets — recordings, slide deck, demo playbook

> **Planned.** Last milestone in the current sequence. Produces presentation and recording assets that demonstrate the full system as built through M4-M10.1 (and optionally M9 if completed first).

## Goal

Create **screen recordings and/or a slide deck** that demonstrate:

1. **Architecture and data flow** — the stack DAG, pipelines, orchestration service, intercept routing, and multi-team scaling.
2. **Live tests** — real pipeline execution showing header propagation, PR vs normal traffic, and test results.
3. **Local step-debug** — run one app locally with mirrord, attach IDE debugger, step through code with live cluster traffic.
4. **Orchestration service** — webhook handling, stack resolution, PipelineRun creation, Helm deployment.

Success = reusable demo materials for stakeholders and teams, plus a reproducible "local dev + debug" story.

---

## What to demo (cumulative system)

The system now includes capabilities from M4 through M10.1. The demo should cover the full picture:

| Area | What exists | Milestone |
|------|-------------|-----------|
| Baggage middleware + propagation roles | `libs/` (5 frameworks), `x-dev-session` header | M4, M4.1 |
| Multi-namespace pipelines | `bootstrap-namespace.sh`, `promote-pipelines.sh` | M4 |
| Original traffic validation | `validate-original-traffic` task (runs in parallel) | M5 |
| Dual intercept backends | Telepresence or mirrord via `intercept-backend` param | M7 |
| Parallel containerize + Kaniko cache | `build-containerize` spawns Kaniko pods in parallel | M7.1 |
| Orchestration service | Flask service: webhooks, stack resolver, PipelineRun creator | M10 |
| Helm chart + ArgoCD | `helm/tekton-dag/`, `argocd/applicationset.yaml` | M10 |
| Multi-team data model | `teams/`, batched builds | M10 |
| Service testing | Postman/Newman (15 requests, 30 assertions) | M10.1 |
| Tekton Results DB | Postgres + Results API; `verify-results-in-db.sh` | Earlier |

---

## Recording segments

The demo playbook ([docs/demo-playbook.md](../docs/demo-playbook.md)) has detailed OBS Studio instructions. Update it to include M10 segments.

| # | Segment | What to show | Duration |
|---|---------|--------------|----------|
| 1 | **Architecture overview** | Slide: stack DAG (FE -> BFF -> API), three pipelines, orchestrator, Helm/ArgoCD. Use the README mermaid diagrams. | 2-3 min |
| 2 | **Quick start** | Terminal: `kind-with-registry.sh`, `install-tekton.sh`, `publish-build-images.sh`, apply tasks/pipelines. Show it working on a single machine. | 2-3 min |
| 3 | **Bootstrap + data flow** | Run bootstrap pipeline. Then send request through the stack with `x-dev-session` header; show header in logs/response. | 3-5 min |
| 4 | **PR pipeline with intercepts** | Trigger PR pipeline (script or webhook). Show: build changed app, deploy intercepts, validate propagation + original traffic in parallel, run tests, PR comment. | 5-7 min |
| 5 | **Intercept routing: PR vs normal** | Two requests: one with header (hits PR build), one without (hits original). Show mirrord and/or Telepresence. | 2-3 min |
| 6 | **Local step-debug** | Run app locally with mirrord, attach IDE debugger, set breakpoint, send request with header, breakpoint fires. | 3-5 min |
| 7 | **Orchestration service** | Port-forward orchestrator. Show: `GET /api/stacks`, `POST /api/run`, `POST /webhook/github` (simulated). Show PipelineRun created in cluster. | 3-5 min |
| 8 | **Multi-team and Helm** | Show `teams/default/team.yaml`, `helm/tekton-dag/values.yaml`, `argocd/applicationset.yaml`. Explain scaling story. | 2-3 min |
| 9 | **Tekton Results DB** | Run `verify-results-in-db.sh`; show stored pipeline history. | 1-2 min |
| 10 | **Newman test suite** | Run `run-orchestrator-tests.sh`; show 15/15 pass, integration validation. | 2-3 min |

---

## Deliverables

### 8.1 Screen recordings

- At least one recording covering segments 1-6 (core pipeline story).
- At least one recording covering segments 7-10 (orchestrator and scaling story).
- Format: mp4, 1080p. Store in `docs/demos/recordings/` or link to external hosting.

### 8.2 Slide deck (optional)

- PowerPoint or Markdown deck summarizing architecture, data flow, intercept behavior, orchestrator, multi-team.
- Store in `docs/demos/` or `docs/presentations/`.

### 8.3 Updated demo playbook

- Update [docs/demo-playbook.md](../docs/demo-playbook.md) with the new segments (orchestrator, Helm, multi-team, Newman tests).
- Add OBS scenes for new segments.

### 8.4 Reproducibility guide

- Document exact commands to reproduce every demo segment from a fresh Kind cluster.
- Include in playbook or as a separate `docs/demo-reproduce.md`.

---

## Success criteria

- [ ] At least one recording showing **data flow + live intercept test** (request path, headers, PR vs normal traffic).
- [ ] At least one recording showing **local run + step-debug** (mirrord, IDE, breakpoint with live traffic).
- [ ] At least one recording or live walkthrough of the **orchestrator service** (webhook, stacks, PipelineRun creation).
- [ ] Demo playbook updated with all segments and OBS scenes.
- [ ] README or docs link to the demo assets and reproduction steps.

---

## Technical notes

- **Local step-debug:** Works because the intercept tool (mirrord or Telepresence) sends matching traffic to the local process. App runs in the IDE with debugger attached. See [.vscode/README.md](../.vscode/README.md).
- **Stack:** Use the same stack as E2E tests (`stacks/stack-one.yaml`, `staging` namespace).
- **Orchestrator:** Already deployed and tested (M10.1). Port-forward for the demo: `kubectl port-forward svc/tekton-dag-orchestrator 9091:8080 -n tekton-pipelines`.

---

## Non-goals

- Recording every framework combination (one clear example stack is enough).
- Building new tooling; use existing scripts and infrastructure.
- Production deployment demo (Kind is sufficient).

---

## References

- [docs/demo-playbook.md](../docs/demo-playbook.md) — recording playbook with OBS setup
- [Milestone 5](milestone-5.md) — mirrord evaluation
- [Milestone 6](milestone-6.md) — validated intercept scenarios
- [Milestone 7](milestone-7.md) — dual intercept backend
- [Milestone 10](milestone-10.md) — orchestration service, Helm, ArgoCD
- [Milestone 10.1](milestone-10-1.md) — orchestrator testing
- [docs/mirrord-poc-results.md](../docs/mirrord-poc-results.md) — mirrord config
- [.vscode/README.md](../.vscode/README.md) — launch configs for local debug
