# Milestone 13 — Production Hardening

**Goal:** Make tekton-dag reliable and cost-effective on real infrastructure — spot instances, shared clusters, multi-environment promotion.

---

## 1. Retry on transient failures

Pipeline tasks that fail due to infrastructure problems — not test failures — should automatically retry.

- [ ] **Task-level retry policy** — add `retries: N` to build, deploy, and containerize tasks; leave test/validation tasks at `retries: 0` so real failures surface immediately
- [ ] **Spot instance preemption handling** — detect `node lost` / `pod evicted` / `DeadlineExceeded` exit codes and retry only those; distinguish from OOMKilled (which needs sizing, not retry)
- [ ] **Registry throttle / timeout retry** — Kaniko push and crane tag can hit rate limits or transient DNS failures; add retry with exponential backoff to `build-containerize` and `tag-release-images`
- [ ] **Configurable retry counts** — expose `max-retries` as a pipeline parameter so teams can tune per environment (e.g. 3 retries on spot, 0 on dedicated nodes)
- [ ] **Retry logging** — emit structured annotations on TaskRuns showing retry attempt number and original failure reason for post-mortem

## 2. Precise build image sizing

Build images currently use default resource requests. On shared clusters, this wastes capacity or causes OOMKill.

- [ ] **Per-tool resource profiles** — define CPU/memory requests and limits per build tool (Maven needs more heap than npm; Gradle benefits from more CPU for parallel compilation)
- [ ] **Helm-configurable sizing** — expose `resources.compile-maven`, `resources.compile-npm`, etc. in `values.yaml` so teams size to their workloads
- [ ] **Stack-level overrides** — allow `build.resources` in stack YAML per app (e.g. a large Spring Boot monolith needs 4Gi; a small Node service needs 512Mi)
- [ ] **Kaniko sizing** — separate resource profile for container build step; large multi-stage Dockerfiles need more memory than compile
- [ ] **LimitRange defaults** — document recommended `LimitRange` for the pipeline namespace so pods that don't specify limits get sane defaults
- [ ] **Monitoring baseline** — add a script or dashboard template that captures peak CPU/memory per TaskRun to inform sizing decisions

## 3. Multi-cluster push

Today tekton-dag builds and deploys within a single cluster. Production environments need images promoted to separate clusters.

- [ ] **Remote registry push** — after `tag-release-images`, optionally push released images to one or more remote registries (ECR, GCR, ACR, Harbor)
- [ ] **Registry list in config** — `stacks/registries.yaml` or Helm values: list of `{name, url, credentials-secret}` targets per environment (staging, production, DR)
- [ ] **Promotion pipeline** — new `stack-promote` pipeline: takes a release version + target environment, pulls from build registry, pushes to target, optionally triggers deployment (ArgoCD sync, Helm upgrade, Argo Rollouts)
- [ ] **Cross-cluster deploy task** — new Tekton task that applies manifests to a remote cluster using a kubeconfig secret (for non-GitOps setups)
- [ ] **Environment gates** — optional manual approval step between environments (e.g. staging → production requires a `/approve` comment or GUI button)
- [ ] **Promotion audit trail** — record which image was promoted to which environment, when, and by whom in Tekton Results

## 4. Operational reliability

- [ ] **Pipeline timeouts** — set explicit `timeout` on pipelines and critical tasks; today some tasks can hang indefinitely on a slow cluster
- [ ] **Graceful cleanup on timeout** — ensure `finally` block still runs when pipeline times out (intercept cleanup, PR comment with "timed out" status)
- [ ] **Health-check gates** — after deploy, wait for readiness probes before running tests (today deploy-full-stack doesn't confirm pods are Ready)
- [ ] **Results DB backup** — script to pg_dump Tekton Results Postgres on a schedule; document restore procedure
- [ ] **Neo4j persistence** — ensure graph data survives pod restarts (PVC + documented backup)

## 5. Observability

- [ ] **Pipeline metrics** — export Prometheus metrics: build duration per tool, test pass rate, retry count, queue time
- [ ] **Alerting rules** — sample Prometheus/Alertmanager rules: pipeline failure rate > threshold, build queue depth, registry push failures
- [ ] **Cost attribution** — label TaskRun pods with team/stack/app for cluster cost allocation tools (Kubecost, OpenCost)

---

## Segment 18 — What's Coming Next

A demo video (segment 18) will present these production hardening features as a roadmap walkthrough, showing the problems each solves and the planned approach.
