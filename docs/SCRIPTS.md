# Shell scripts index (`scripts/`)

Authoritative map of **bash entrypoints** in the repo root `scripts/` directory.  
Shared helpers live in [`scripts/common.sh`](../scripts/common.sh) (sourced by many scripts).

**Obsolete scripts** are not deleted outright: when retired, they are moved under [`scripts/archive/`](../scripts/archive/) with an entry in that folder’s README (same hygiene as [docs/archive/](archive/README.md)).

---

## Regression and testing (start here)

| Script | Purpose |
|--------|---------|
| [`run-regression.sh`](../scripts/run-regression.sh) | **Main regression driver** — pytest, vitest, isolation-eval protocol, Java/PHP/operator unit tests, Playwright, cluster/Newman, optional DAG verify & Results DB. See [REGRESSION.md](REGRESSION.md). |
| [`run-lang-unit-tests.sh`](../scripts/run-lang-unit-tests.sh) | Maven (both baggage modules), PHPUnit, operator `go test ./internal/... ./api/...`. |
| [`run-isolation-eval.sh`](../scripts/run-isolation-eval.sh) | Clone-vs-intercept harness: `--offline` plan CSV; `--cluster` Kind measurements. |
| [`run-cluster-ci.sh`](../scripts/run-cluster-ci.sh) | Kind cluster CI: isolation-eval `--cluster`, `stack-dag-verify`, Newman. Used by [cluster-regression.yml](../.github/workflows/cluster-regression.yml) (not on PRs). |
| [`run-regression-agent.sh`](../scripts/run-regression-agent.sh) | Streamed output for **agents** (Cursor); wraps tiers for iterative fix loops. [AGENT-REGRESSION.md](AGENT-REGRESSION.md) |
| [`run-regression-agent-full.sh`](../scripts/run-regression-agent-full.sh) | Full agent-oriented run (heavier than default agent script). |
| [`run-regression-stream.sh`](../scripts/run-regression-stream.sh) | Regression with streaming log-friendly behavior. |
| [`bootstrap-regression-venv.sh`](../scripts/bootstrap-regression-venv.sh) | Create/refresh Python venv for orchestrator/shared-package tests. |
| [`run-orchestrator-tests.sh`](../scripts/run-orchestrator-tests.sh) | Pytest for orchestrator (+ optional integration / PipelineRun checks). |
| [`run-full-test-and-verify-results.sh`](../scripts/run-full-test-and-verify-results.sh) | Longer path including Results verification (used by regression flags). |
| [`verify-results-in-db.sh`](../scripts/verify-results-in-db.sh) | Assert Tekton Results / DB expectations after runs. |
| [`verify-dag-phase1.sh`](../scripts/verify-dag-phase1.sh) | Local DAG structure checks (Phase 1). |
| [`verify-dag-phase2.sh`](../scripts/verify-dag-phase2.sh) | Cluster: `stack-dag-verify` PipelineRun + CLI match (Phase 2). |
| [`verify-m4-stacks-and-labels.sh`](../scripts/verify-m4-stacks-and-labels.sh) | M4-era stack/label checks (still useful for multi-namespace stacks). |
| [`run-artillery-variants.sh`](../scripts/run-artillery-variants.sh) | Load / Artillery variant runs (optional performance testing). |

---

## Kind cluster, Tekton, data plane

| Script | Purpose |
|--------|---------|
| [`kind-with-registry.sh`](../scripts/kind-with-registry.sh) | Create Kind cluster with local registry (quick start). Nested VMs: `kind.x-k8s.io` + kube-proxy **nftables**. |
| [`cloud-agent-install.sh`](../scripts/cloud-agent-install.sh) | Cloud Agent `install`: refresh regression venv + Newman. |
| [`cloud-agent-start-docker.sh`](../scripts/cloud-agent-start-docker.sh) | Cloud Agent `start`: dockerd with fuse-overlayfs; does not create Kind. |
| [`install-kind-default-storage.sh`](../scripts/install-kind-default-storage.sh) | Default StorageClass for Kind. |
| [`install-tekton.sh`](../scripts/install-tekton.sh) | Install Tekton Pipelines (and related baseline). |
| [`install-tekton-dashboard.sh`](../scripts/install-tekton-dashboard.sh) | Install Tekton Dashboard. |
| [`uninstall-tekton-dashboard.sh`](../scripts/uninstall-tekton-dashboard.sh) | Remove Tekton Dashboard. |
| [`port-forward-tekton-dashboard.sh`](../scripts/port-forward-tekton-dashboard.sh) | `kubectl port-forward` to dashboard. |
| [`install-tekton-results.sh`](../scripts/install-tekton-results.sh) | Tekton Results components. |
| [`install-postgres-kind.sh`](../scripts/install-postgres-kind.sh) | Postgres in Kind (Results / app DB). |
| [`install-neo4j-kind.sh`](../scripts/install-neo4j-kind.sh) | Neo4j in Kind for graph features. |
| [`bootstrap-namespace.sh`](../scripts/bootstrap-namespace.sh) | Bootstrap namespace resources for a stack. |

---

## Images, pipelines, sample data

| Script | Purpose |
|--------|---------|
| [`publish-build-images.sh`](../scripts/publish-build-images.sh) | Build/push **compile** images (polyglot builders). |
| [`publish-orchestrator-image.sh`](../scripts/publish-orchestrator-image.sh) | Build/push **orchestrator** image. |
| [`generate-run.sh`](../scripts/generate-run.sh) | Emit/apply a **StackRun** (operator). Pass `--pipeline-run` for a raw Tekton PipelineRun (`pr` / `merge` only). |
| [`promote-pipelines.sh`](../scripts/promote-pipelines.sh) | Promote pipeline definitions across environments/namespaces. |
| [`create-and-push-sample-repos.sh`](../scripts/create-and-push-sample-repos.sh) | Sample app repos for demos/regression. |
| [`ensure-git-ssh-secret.sh`](../scripts/ensure-git-ssh-secret.sh) | Git SSH secret for cluster git operations. |

---

## PR flow, webhooks, E2E

| Script | Purpose |
|--------|---------|
| [`run-valid-pr-flow.sh`](../scripts/run-valid-pr-flow.sh) | Scripted valid PR path against cluster. |
| [`create-test-pr.sh`](../scripts/create-test-pr.sh) | Create a test PR (automation helper). |
| [`merge-pr.sh`](../scripts/merge-pr.sh) | Merge helper for test PRs. |
| [`rerun-pr-from.sh`](../scripts/rerun-pr-from.sh) | Re-trigger PR pipeline from a ref. |
| [`configure-github-webhooks.sh`](../scripts/configure-github-webhooks.sh) | Wire GitHub webhooks to EventListener. |
| [`run-e2e-with-intercepts.sh`](../scripts/run-e2e-with-intercepts.sh) | End-to-end with **telepresence** or **mirrord** intercept backend. |
| [`run-all-setup-and-test.sh`](../scripts/run-all-setup-and-test.sh) | Broad setup + test orchestration (legacy-style “do a lot”). |

---

## Intercept tooling (Telepresence, mirrord)

| Script | Purpose |
|--------|---------|
| [`install-telepresence-traffic-manager.sh`](../scripts/install-telepresence-traffic-manager.sh) | Install Telepresence traffic manager in cluster. |
| [`install-mirrord.sh`](../scripts/install-mirrord.sh) | Install mirrord CLI / related setup. |
| [`run-mirrord-poc.sh`](../scripts/run-mirrord-poc.sh) | Early mirrord PoC scenarios. |
| [`run-mirrord-m6-scenarios.sh`](../scripts/run-mirrord-m6-scenarios.sh) | M6 mirrord test scenario driver. |

---

## Dashboards, tunnels, utilities

| Script | Purpose |
|--------|---------|
| [`cloudflare-add-tunnel-cname.sh`](../scripts/cloudflare-add-tunnel-cname.sh) | Cloudflare DNS for tunnel (EventListener exposure). See [CLOUDFLARE-TUNNEL-EVENTLISTENER.md](CLOUDFLARE-TUNNEL-EVENTLISTENER.md). |
| [`stack-graph.sh`](../scripts/stack-graph.sh) | Stack / graph helper (CLI glue for Neo4j or exports). |
| [`install-php-local.sh`](../scripts/install-php-local.sh) | Local PHP toolchain helper for sample apps. |

---

## One-off / migration

| Script | Purpose |
|--------|---------|
| [`extract-standalone-repo.sh`](../scripts/extract-standalone-repo.sh) | Historical: copy milestone into a **standalone** repo layout (see [README-FULL.md](README-FULL.md)). Rarely needed now that `tekton-dag` is the main repo. |

---

## Demo toolchain (not under `scripts/`)

| Location | Purpose |
|----------|---------|
| [`docs/demos/generate-all.sh`](../docs/demos/generate-all.sh) | Regenerate Manim, VHS, TTS, and composed MP4s (M8 + M12.2 segments). |
| [`docs/demos/compose.sh`](../docs/demos/compose.sh) | FFmpeg: merge visuals + narration per segment. |

See [milestones/milestone-8.md](../milestones/milestone-8.md) and [milestones/milestone-12.2.md](../milestones/milestone-12.2.md).

---

## Related documentation

- [REGRESSION.md](REGRESSION.md) — tier matrix and flags for `run-regression.sh`
- [AGENT-REGRESSION.md](AGENT-REGRESSION.md) — agent loop
- [local-dag-verification-plan.md](local-dag-verification-plan.md) — Phase 1/2 verification
- [README](../README.md) — quick start commands that invoke many of the scripts above
