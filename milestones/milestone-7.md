# Milestone 7: Prototype `deploy-intercept-mirrord` Tekton task

> **Active milestone.** Follows [milestone 6](milestone-6.md) (mirrord validated for all PR pipeline scenarios). Replaces the Telepresence-based `deploy-stack-intercepts` task with a mirrord equivalent, eliminating Telepresence licensing costs.

## Goal

Create a production-ready Tekton task (`deploy-intercept-mirrord`) that uses mirrord instead of Telepresence for header-based traffic interception in the PR pipeline. Integrate it into `stack-pr-pipeline.yaml` and validate end-to-end.

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

### 7.2 Update `stack-pr-pipeline.yaml`

Replace the `deploy-intercepts` pipeline task reference from `deploy-stack-intercepts` to `deploy-intercept-mirrord`. All params remain the same (interface-compatible).

### 7.3 Cleanup task update

The existing `cleanup-pr-pods` task deletes pods with label `managed-by: tekton-job-standardization`. mirrord agents are labeled `app: mirrord` — add cleanup of mirrord agent pods alongside PR pod cleanup.

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

- Update `tasks/deploy-intercept.yaml` header comment to note it's superseded
- Add `docs/m7-mirrord-intercept-task.md` explaining the new task architecture
- Update README to reflect M7 completion

---

## Success criteria

- [ ] `deploy-intercept-mirrord` task works in a PipelineRun (intercept active, header-routed traffic reaches PR pod)
- [ ] Normal traffic unaffected during intercepts (re-validate via pipeline)
- [ ] Cleanup task removes both PR pods and mirrord agent pods
- [ ] `tekton-dag-build-mirrord` image published to Kind registry
- [ ] Pipeline runs without Telepresence — no Telepresence image, no Helm install, no commercial license required
- [ ] End-to-end PR flow validated (PR → build → intercept → test → cleanup)
- [ ] Documentation updated

---

## Non-goals (future milestones)

- Removing Telepresence entirely from the codebase (keep as fallback until mirrord is proven in CI)
- mirrord Operator evaluation (not needed per M6 findings)
- Multi-cluster intercept scenarios

---

## References

- [Milestone 6](milestone-6.md) — mirrord validation results (all scenarios pass)
- [tasks/deploy-intercept.yaml](../tasks/deploy-intercept.yaml) — current Telepresence-based task (to be replaced)
- [docs/mirrord-poc-results.md](../docs/mirrord-poc-results.md) — M5 PoC, config format, security notes
- [docs/mirrord-m6-test-scenarios.md](../docs/mirrord-m6-test-scenarios.md) — validated test scenarios
