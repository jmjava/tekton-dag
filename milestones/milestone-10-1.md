# Milestone 10.1: Orchestration Service Testing

> **Follows [milestone 10](milestone-10.md).** Builds, deploys, and tests the orchestration service end-to-end using a Postman test suite against the live service running in Kind.

## Goal

Validate the M10 orchestration service by:

1. Building and publishing the orchestrator Docker image to the Kind registry.
2. Deploying the service to the cluster (via Helm or kubectl).
3. Running a Postman/Newman test suite against every REST endpoint.
4. Verifying that PipelineRuns created by the service actually execute.

---

## Background

M10 introduced the orchestration service (`orchestrator/`) with endpoints for webhook handling, manual triggers, stack listing, and bootstrap. The code exists but has not been built as a container image, deployed to the cluster, or tested against a live instance.

---

## Deliverables

### 10.1.1 Build and publish orchestrator image

**Instructions:**

1. Add `orchestrator/` to `build-images/` or create a dedicated build script (`scripts/publish-orchestrator-image.sh`).
2. Script builds the Docker image from `orchestrator/Dockerfile`, tags it as `localhost:5001/tekton-dag-orchestrator:latest`, and pushes to the Kind registry.
3. Verify: `docker pull localhost:5001/tekton-dag-orchestrator:latest` succeeds; `curl localhost:5001/v2/tekton-dag-orchestrator/tags/list` shows the tag.

**Acceptance:** Orchestrator image is in the Kind registry, pullable by pods as `localhost:5000/tekton-dag-orchestrator:latest`.

---

### 10.1.2 Deploy orchestrator to cluster

**Instructions:**

1. **Option A (Helm):** Run `./helm/tekton-dag/package.sh && helm install tekton-dag ./helm/tekton-dag -n tekton-pipelines` — orchestrator deploys as part of the chart (already templated in `orchestration-deployment.yaml`).
2. **Option B (kubectl):** Apply a standalone manifest for the Deployment + Service + ConfigMap (for cases where you don't want the full Helm install).
3. Mount the stacks directory as a ConfigMap: `kubectl create configmap tekton-dag-stacks --from-file=stacks/ -n tekton-pipelines`.
4. Verify: `kubectl get pods -n tekton-pipelines -l app=tekton-dag-orchestrator` shows Running; `kubectl logs` shows "Orchestrator started" and loaded stacks.

**Acceptance:** Orchestrator pod is Running, healthz returns 200, stacks are loaded.

---

### 10.1.3 Postman test collection

Create a Postman/Newman collection (`tests/postman/orchestrator-tests.json`) that tests every endpoint.

**Test cases:**

#### Health and readiness
- `GET /healthz` — status 200, body `{"status": "ok"}`
- `GET /readyz` — status 200, body has `stacks_loaded >= 1`

#### Stack and team queries
- `GET /api/stacks` — status 200, array with at least 1 stack, each has `name`, `apps` (array), `stack_file`
- `GET /api/teams` — status 200, object (may be empty in single-team mode)

#### PipelineRun listing
- `GET /api/runs` — status 200, array (may be empty)
- `GET /api/runs?limit=5` — status 200, array length <= 5

#### Manual triggers
- `POST /api/run` with `{"mode": "bootstrap"}` — status 200, body has `pipelinerun` name and `mode: "bootstrap"`
- `POST /api/run` with `{"mode": "pr", "changed_app": "demo-fe", "pr_number": 999}` — status 200, body has `pipelinerun` name
- `POST /api/run` with `{"mode": "pr"}` (missing params) — status 400, body has `error`

#### Bootstrap endpoint
- `POST /api/bootstrap` — status 200, body has `pipelinerun` name

#### Webhook simulation
- `POST /webhook/github` with PR opened payload for `tekton-dag-vue-fe` — status 200, body has `pipelinerun` name and `mode: "pr"`
- `POST /webhook/github` with PR closed+merged payload — status 200, body has `mode: "merge"`
- `POST /webhook/github` with unknown repo — status 200, body has `status: "ignored"`
- `POST /webhook/github` with non-PR event header — status 200, body has `status: "ignored"`

#### Config reload
- `POST /api/reload` — status 200, body has `stacks >= 1`

**Instructions:**

1. Create `tests/postman/orchestrator-tests.json` with the collection above.
2. Use environment variable `baseUrl` (e.g. `http://localhost:8080` when port-forwarded).
3. Add a run script: `scripts/run-orchestrator-tests.sh` that port-forwards the service and runs `newman run tests/postman/orchestrator-tests.json --env-var baseUrl=http://localhost:8080`.
4. After trigger tests, clean up any PipelineRuns created by the test (delete by label or name prefix).

**Acceptance:** `newman run` passes all tests. PipelineRuns are created for trigger tests.

---

### 10.1.4 Integration validation

After the Postman suite passes (PipelineRuns created), verify at least one created run executes:

1. The bootstrap PipelineRun created by `POST /api/bootstrap` should reach at least `fetch-source` Succeeded.
2. The PR PipelineRun created by `POST /api/run` should reach at least `resolve-stack` Succeeded.
3. Clean up test PipelineRuns after validation.

**Instructions:**

1. In `scripts/run-orchestrator-tests.sh`, after Newman completes, poll the bootstrap PipelineRun until `fetch-source` succeeds (or 120s timeout).
2. Delete test PipelineRuns: `kubectl delete pipelinerun -l app.kubernetes.io/part-of=tekton-job-standardization -n tekton-pipelines` (or by name prefix from test).
3. Document that this validates the full webhook-to-pipeline flow.

**Acceptance:** At least one PipelineRun created by the service starts executing successfully.

---

## Success criteria

- [x] Orchestrator Docker image built and available in Kind registry (10.1.1).
- [x] Orchestrator pod Running in cluster, healthz OK, stacks loaded (10.1.2).
- [x] Postman collection covers all endpoints; Newman run passes (10.1.3) — 15 requests, 30 assertions, 0 failures.
- [x] PipelineRuns created by the service start executing (10.1.4) — bootstrap PipelineRun fetch-source Succeeded.
- [x] Existing E2E tests (telepresence + mirrord) still pass — verified before M10.1 started.

---

## Non-goals

- Production-hardening the service (TLS, auth, rate limiting).
- Load testing / performance benchmarking.
- Testing with multiple teams or multiple clusters (single-team Kind is sufficient).

---

## References

- [milestones/milestone-10.md](milestone-10.md) — parent milestone
- [orchestrator/](../orchestrator/) — service source code
- [helm/tekton-dag/](../helm/tekton-dag/) — Helm chart (includes orchestrator deployment)
- [docs/m10-multi-team-architecture.md](../docs/m10-multi-team-architecture.md) — architecture overview
