# Plan for next working session (archived)

> **Archived (M12.2).** Historical scratchpad only. Current branch references and task lists are obsolete. See [m7-mirrord-intercept-task.md](../m7-mirrord-intercept-task.md) and [milestones/milestone-7.md](../../milestones/milestone-7.md) for the delivered design.

Quick reference for what to do when you return. Current branch: **milestone-7**. Last updated: session that added M8/M9 docs, milestone status table, and "run either" (Telepresence/mirrord) to M7.

---

## 1. Milestone 7 — Run either Telepresence or mirrord (priority)

**Goal:** Implement the "run either" design so the PR pipeline can use Telepresence (default) or mirrord via param `intercept-backend`.

### Tasks (in order)

1. **Implement `tasks/deploy-intercept-mirrord.yaml`**
   - Same params/results as `deploy-stack-intercepts` (stack-json, build-apps, propagation-chain, built-images, intercept-header-value, default-namespace → deployed-pods).
   - For each build-app: deploy PR pod (no Telepresence sidecar), generate mirrord config, run mirrord exec with socat proxy to PR pod. Write `deployed-pods` JSON to workspace path (e.g. `$(workspaces.shared-workspace.path)/deployed-pods.json`).

2. **Build and publish `tekton-dag-build-mirrord` image**
   - Dockerfile in build-images/; contents: mirrord CLI, kubectl, jq, socat. Add to `scripts/publish-build-images.sh`.

3. **Update `deploy-stack-intercepts` (Telepresence task)**
   - Ensure it can write `deployed-pods` to the same workspace path used by the pass-through (so both deploy tasks write to one shared location). If it currently only emits a result, add a step that also writes the result to the workspace path.

4. **Add pass-through task `deploy-intercepts-result`**
   - Single step: read `deployed-pods.json` from workspace, write to result `deployed-pods`. Used so downstream has one result to reference regardless of which deploy task ran.

5. **Update `pipeline/stack-pr-pipeline.yaml`**
   - Add param `intercept-backend` (default: `telepresence`).
   - Replace single `deploy-intercepts` with: `deploy-intercepts-telepresence` (when: intercept-backend == telepresence), `deploy-intercepts-mirrord` (when: intercept-backend == mirrord), `deploy-intercepts-result` (runAfter: both). Both deploy tasks need the shared workspace and must write to the same path.
   - Point validate-propagation, validate-original-traffic, run-tests, and finally/cleanup at `$(tasks.deploy-intercepts-result.results.deployed-pods)`.

6. **Update `pipeline/stack-pr-continue-pipeline.yaml`**
   - Same pattern: intercept-backend param, two deploy tasks + pass-through, downstream use pass-through result.

7. **Update cleanup task**
   - When cleaning up, also delete pods with label `app: mirrord` in the relevant namespace(s) (for runs that used mirrord).

8. **Trigger binding**
   - Add `intercept-backend` to TriggerTemplate (default `telepresence`). Optionally add to TriggerBinding so webhook can pass it later.

9. **Test**
   - Run full PR pipeline with default (Telepresence) — no behavior change.
   - Run with `intercept-backend=mirrord` — intercepts work, cleanup removes mirrord agents.

10. **Docs**
    - Add `docs/m7-mirrord-intercept-task.md` (mirrord task + run-either design). Update README when M7 is complete.

---

## 2. After M7 — optional same session or next

- **Milestone 9:** Start implementation (mock Datadog API, graph storage, query task, extend run-stack-tests) or continue planning.
- **Milestone 8:** Demo assets / playbook — already have [docs/demo-playbook.md](../demo-playbook.md); recording can wait.

---

## 3. Repo state to remember

- **Branch:** `milestone-7` (WIP until M7 is done and merged).
- **Milestone status table** in README gives at-a-glance Completed / In progress / Planned.
- **M9 before M8** in planned order (test-trace regression first, demo assets after).
- **Telepresence** remains default; mirrord is opt-in via param.
