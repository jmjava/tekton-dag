# Milestone 7: Prototype `deploy-intercept-mirrord` Tekton task (run either backend)

> **Active milestone.** Follows [milestone 6](milestone-6.md) (mirrord validated for all PR pipeline scenarios). **Delayed migration:** do not replace Telepresence yet; add mirrord as an option and support **running either** via a pipeline parameter. Default remains Telepresence so existing behavior is unchanged until you opt in to mirrord.

## Goal

Create a production-ready Tekton task (`deploy-intercept-mirrord`) that uses mirrord for header-based traffic interception, and integrate it into the PR pipeline **alongside** the existing Telepresence task. The pipeline gains an optional parameter (e.g. `intercept-backend: telepresence | mirrord`); when set to `mirrord`, use the new task; otherwise keep using `deploy-stack-intercepts`. This allows running either backend and defers a full cutover until mirrord is preferred.

---

## Background

The current `tasks/deploy-intercept.yaml` (`deploy-stack-intercepts`) works by:

1. Deploying a PR pod with two containers: the built app image + a Telepresence sidecar
2. The Telepresence sidecar runs `telepresence connect` and `telepresence intercept <app> --http-match <header>`
3. Traffic matching the header routes to the PR pod; all other traffic continues to the original deployment

**mirrord replaces this** by:
- Running `mirrord exec` from outside the cluster (or from a task pod with the mirrord CLI)
- The mirrord agent spawns inside the target pod's namespace and steals matching HTTP traffic
- No sidecar container needed; no Telepresence Helm install; no `NET_ADMIN` on the task pod

### Key constraint from M6

One intercept per app at a time. Concurrent PRs on different apps run in parallel with no conflict.

---

## Deliverables

### 7.1 `deploy-intercept-mirrord` Tekton task

New task `tasks/deploy-intercept-mirrord.yaml` with the same interface as the existing task:

| Param | Description |
|-------|-------------|
| `stack-json` | Full stack graph JSON |
| `build-apps` | Space-separated list of apps to intercept |
| `propagation-chain` | Ordered chain (logging context) |
| `built-images` | JSON map of app → image URI |
| `intercept-header-value` | Header match (e.g. `x-dev-session: pr-42`) |
| `default-namespace` | Target namespace (default: `staging`) |

| Result | Description |
|--------|-------------|
| `deployed-pods` | JSON map of app → pod name |

**Approach:**

1. For each app in `build-apps`:
   - Deploy a PR pod running the built image (same as today, but **without** the Telepresence sidecar)
   - Generate a per-app mirrord config JSON (target = `deployment/<app>`, namespace, header filter from `intercept-header-value`)
   - Run `mirrord exec -f <config> -- <proxy-to-pr-pod>` to start the intercept — traffic matching the header is stolen from the original deployment and forwarded to the PR pod
2. The task image needs `mirrord` CLI + `kubectl` + `jq`

**Design decisions to resolve:**

- **Where does `mirrord exec` run?** Option A: from the task pod itself (requires the mirrord binary in the task image and sufficient RBAC to spawn agents). Option B: from a sidecar. Option A is simpler.
- **How does stolen traffic reach the PR pod?** mirrord wraps a local process — in this case a lightweight TCP proxy (socat/netcat) that forwards to the PR pod's ClusterIP. Alternatively, the PR pod runs the app directly and mirrord wraps it (but then mirrord must run on the same pod as the app, which loses the "no sidecar" benefit). **Recommended:** mirrord wraps a socat proxy in the task pod that forwards to the PR pod.
- **Task image:** Build a `tekton-dag-build-mirrord` image with `mirrord` CLI, `kubectl`, `jq`, and `socat`. Publish alongside existing compile images.

### 7.2 Update `stack-pr-pipeline.yaml` (run either, do not replace)

- Add a pipeline param **`intercept-backend`** (default: `telepresence`). Values: `telepresence` | `mirrord`.
- **Keep** the existing `deploy-stack-intercepts` task (Telepresence). Add the new `deploy-intercept-mirrord` task.
- Use **two pipeline tasks** with `when` conditions so only one runs:
  - `deploy-intercepts-telepresence` (taskRef: `deploy-stack-intercepts`) when `intercept-backend == telepresence`
  - `deploy-intercepts-mirrord` (taskRef: `deploy-intercept-mirrord`) when `intercept-backend == mirrord`
- Both tasks write **`deployed-pods`** to a shared workspace path (e.g. `$(workspaces.shared-workspace.path)/deployed-pods.json`). Add a small **pass-through task** `deploy-intercepts-result` that runs after both, reads that file from the workspace, and writes it to its result `deployed-pods`. Downstream tasks (validate-propagation, validate-original-traffic, run-tests) and `finally` (cleanup) reference **`$(tasks.deploy-intercepts-result.results.deployed-pods)`** instead of `$(tasks.deploy-intercepts.results.deployed-pods)`.
- Trigger binding / manual runs: default remains Telepresence; to use mirrord, pass `intercept-backend=mirrord` when creating the PipelineRun (or set in TriggerTemplate for webhook).
- Apply the same pattern to **stack-pr-continue-pipeline.yaml** (re-run from deploy): add `intercept-backend` param and the two deploy tasks + pass-through result so continuation can use either backend.

### 7.3 Cleanup task update

The existing cleanup task deletes pods with label `managed-by: tekton-job-standardization`. When mirrord is used, mirrord agents are labeled `app: mirrord` — ensure cleanup removes mirrord agent pods when present (e.g. cleanup task reads `deployed-pods` and also deletes pods with `app: mirrord` in the same namespace(s), or a separate step when `intercept-backend == mirrord`).

### 7.4 Build image: `tekton-dag-build-mirrord`

| Image | Base | Contents |
|-------|------|----------|
| `tekton-dag-build-mirrord` | `bitnami/kubectl:latest` | mirrord CLI + jq + socat |

Add to `scripts/publish-build-images.sh`.

### 7.5 End-to-end validation

- Run the full `stack-pr-test` pipeline with the new task against the Kind cluster
- Verify: PR traffic (with header) reaches the PR pod; normal traffic reaches originals
- Compare behavior to the Telepresence-based flow

### 7.6 Documentation

- Document the **intercept-backend** pipeline param and how to run with Telepresence (default) vs mirrord. Do not mark the Telepresence task as superseded — both remain supported.
- Add `docs/m7-mirrord-intercept-task.md` explaining the mirrord task and the "run either" design
- Update README to reflect M7 completion (ability to run either backend)

---

## Success criteria

- [ ] `deploy-intercept-mirrord` task works in a PipelineRun when `intercept-backend=mirrord` (intercept active, header-routed traffic reaches PR pod)
- [ ] Pipeline **default** (`intercept-backend=telepresence` or unset) still uses `deploy-stack-intercepts` — no behavior change for existing runs
- [ ] Normal traffic unaffected during intercepts for both backends (re-validate via pipeline)
- [ ] Cleanup removes PR pods and, when mirrord was used, mirrord agent pods
- [ ] `tekton-dag-build-mirrord` image published to Kind registry
- [ ] End-to-end PR flow validated with **both** backends (Telepresence and mirrord)
- [ ] Documentation updated (run either; param and trigger binding)

---

## Non-goals (this milestone)

- **Removing or replacing Telepresence** — both backends remain available; migration/cutover is deferred.
- mirrord Operator evaluation (not needed per M6 findings)
- Multi-cluster intercept scenarios

---

## References

- [Milestone 6](milestone-6.md) — mirrord validation results (all scenarios pass)
- [tasks/deploy-intercept.yaml](../tasks/deploy-intercept.yaml) — current Telepresence-based task (to be replaced)
- [docs/mirrord-poc-results.md](../docs/mirrord-poc-results.md) — M5 PoC, config format, security notes
- [docs/mirrord-m6-test-scenarios.md](../docs/mirrord-m6-test-scenarios.md) — validated test scenarios
