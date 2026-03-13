# Milestone 7: mirrord intercept task and "run either" design

This document describes the `deploy-intercept-mirrord` Tekton task and how the PR pipeline supports **running either** Telepresence or mirrord as the intercept backend via the `intercept-backend` parameter. See [milestones/milestone-7.md](../milestones/milestone-7.md) for the full milestone.

---

## Pipeline parameter: `intercept-backend`

| Value         | Behavior |
|---------------|----------|
| `telepresence` (default) | Uses the existing `deploy-stack-intercepts` task (Telepresence sidecar in PR pods). |
| `mirrord`     | Uses the new `deploy-intercept-mirrord` task (mirrord proxy pods + header-based steal). |

- **Default:** `telepresence`. Existing runs and trigger bindings are unchanged.
- **To use mirrord:** Pass `intercept-backend=mirrord` when creating the PipelineRun, or set it in the TriggerTemplate for webhook-triggered runs.

---

## deploy-intercept-mirrord task

Same interface as `deploy-stack-intercepts` (params and result `deployed-pods`), so the pipeline can switch backends by task reference and `when` conditions.

### Behavior

1. **Per built app:**
   - Deploy a **PR pod** with only the built image (no Telepresence sidecar).
   - Create a **mirrord config** (target = `deployment/<app>`, namespace, header filter from `intercept-header-value`).
   - Deploy a **mirrord-proxy pod** that runs `mirrord exec -f <config> -- socat TCP-LISTEN:<port>,fork TCP:<pr-pod-ip>:<port>`.
2. Traffic that matches the intercept header is **stolen** from the original deployment and forwarded to the PR pod via the proxy. All other traffic goes to the original deployment.
3. The task writes **`deployed-pods`** (JSON map app → PR pod name) to the shared workspace and to its result.

### Build image: tekton-dag-build-mirrord

| Image                      | Base                  | Contents                          |
|----------------------------|------------------------|-----------------------------------|
| `tekton-dag-build-mirrord` | `bitnami/kubectl:latest` | mirrord CLI, jq, socat            |

Publish with the other build images:

```bash
./scripts/publish-build-images.sh
```

The pipeline uses this image for the mirrord-proxy pods (param `mirrord-image` on the task, default `localhost:5001/tekton-dag-build-mirrord:latest`).

---

## Pass-through result (deploy-intercepts-result)

Both deploy tasks (Telepresence and mirrord) write **`deployed-pods.json`** to the shared workspace. A small **pass-through task** `deploy-intercepts-result` runs after both (only one runs per PipelineRun due to `when`). It reads that file and writes it to its result **`deployed-pods`**.

Downstream and `finally` tasks use **`$(tasks.deploy-intercepts-result.results.deployed-pods)`** so they work with either backend. Cleanup uses this result and, when `intercept-backend=mirrord`, also deletes mirrord agent and proxy pods.

---

## Cleanup

When **`intercept-backend=mirrord`**, the cleanup task:

- Deletes PR pods from `deployed-pods` (same as today).
- Deletes pods with label **`app=mirrord`** (mirrord agents) in the same namespace(s).
- Deletes pods with label **`app=mirrord-proxy`** (our proxy pods) in the same namespace(s).

When **`intercept-backend=telepresence`**, behavior is unchanged (PR pods + orphaned `managed-by=tekton-job-standardization` pods).

---

## Continuation pipeline (stack-pr-continue)

The same pattern applies: **`intercept-backend`** param, conditional deploy tasks, and **`deploy-intercepts-result`**. When re-running from deploy (e.g. via `scripts/rerun-pr-from.sh` or a manual PipelineRun), pass the same **`intercept-backend`** value that the original run used (e.g. add `intercept-backend: mirrord` to the pipeline params) so the correct deploy task and cleanup behavior are used.

---

## References

- [milestone-7.md](../milestones/milestone-7.md) — full deliverables and success criteria
- [mirrord-poc-results.md](mirrord-poc-results.md) — config format, header filter
- [mirrord-m6-test-scenarios.md](mirrord-m6-test-scenarios.md) — validated scenarios
- [tasks/deploy-intercept-mirrord.yaml](../tasks/deploy-intercept-mirrord.yaml) — task definition
