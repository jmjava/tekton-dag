# Plan: Verifying the DAG Structure Locally

This plan verifies that the **stack DAG** (directed acyclic graph), resolve outputs, and pipeline behavior are correct when running locally (no AWS, no Argo).

---

## Running the plan (automated)

| Phase | Script | When to run |
|-------|--------|-------------|
| **Phase 1** | `./scripts/verify-dag-phase1.sh` | No cluster needed. Run from repo root or from ``. |
| **Phase 2** | `./scripts/verify-dag-phase2.sh [--stack STACK] [--timeout N]` | After Tekton is installed and tasks + pipelines are applied (including `stack-dag-verify`). Uses HTTPS for git clone by default. Polls every 5s (default 120s timeout). Requires `kubectl` and cluster access. |

**One-liner (Phase 1 only):**

```bash
./scripts/verify-dag-phase1.sh
```

**Phase 2 (after cluster + Tekton ready):**

```bash
# Apply the DAG-verify pipeline (fetch + resolve only) and tasks
kubectl apply -f tasks/
kubectl apply -f pipeline/

# Run Phase 2 (default: stack-one.yaml)
./scripts/verify-dag-phase2.sh

# Or for another stack / changed-app
./scripts/verify-dag-phase2.sh --stack stack-two-vendor.yaml
./scripts/verify-dag-phase2.sh --stack single-app.yaml --storage-class ""
```

Phase 3 (full pipeline behavior) is manual: run a full PR or merge pipeline and confirm build order and deploy/validate params match the DAG.

---

## Phase 1 — No cluster (repo and script checks)

**Goal:** Confirm repo layout, stack YAMLs, and CLI behavior before touching Kubernetes.

**Automated:** Run `./scripts/verify-dag-phase1.sh` from the milestone dir (or repo root). It runs all steps below and exits 0 if all pass.

### 1.1 Repo structure

From the milestone dir (``):

```bash
# Required dirs and key files
test -d stacks && test -d tasks && test -d pipeline && test -d scripts && test -d docs
test -f stacks/registry.yaml && test -f stacks/versions.yaml
test -f scripts/stack-graph.sh && test -f scripts/generate-run.sh
```

### 1.2 Stack YAML validation (DAG rules)

For **every** stack file, ensure:

- No cycles (topological sort must succeed).
- Every `downstream` entry refers to an existing app name in the same stack.

```bash
./scripts/stack-graph.sh stacks/stack-one.yaml       --validate   # expect: VALID
./scripts/stack-graph.sh stacks/stack-two-vendor.yaml --validate   # expect: VALID
./scripts/stack-graph.sh stacks/single-app.yaml      --validate   # expect: VALID
./scripts/stack-graph.sh stacks/single-flask-app.yaml --validate   # expect: VALID
```

If any prints `INVALID` or exits non-zero, fix the stack YAML before continuing.

### 1.3 Topological order (build order)

Record expected build order (dependencies before dependents), then compare to CLI:

| Stack | Expected topo order (example) |
|-------|-------------------------------|
| stack-one | demo-fe → release-lifecycle-demo → demo-api |
| stack-two-vendor | vendor-fe → vendor-middleware → (vendor-adapter, internal-api, notifications-svc) — order of the three terminals may vary by implementation |
| single-app | inventory-api |
| single-flask-app | analytics-api |

```bash
./scripts/stack-graph.sh stacks/stack-one.yaml --topo
./scripts/stack-graph.sh stacks/stack-two-vendor.yaml --topo
./scripts/stack-graph.sh stacks/single-app.yaml --topo
./scripts/stack-graph.sh stacks/single-flask-app.yaml --topo
```

Verify: no node appears before its dependencies (every node appears before any app that lists it in `downstream`).

### 1.4 Entry point and propagation chain

- **Entry** = app that no other app lists as downstream (e.g. frontend or root API).
- **Chain** = depth-first walk from entry following `downstream`; used for propagation validation.

```bash
# Entry points
./scripts/stack-graph.sh stacks/stack-one.yaml --entry        # expect: demo-fe
./scripts/stack-graph.sh stacks/stack-two-vendor.yaml --entry # expect: vendor-fe
./scripts/stack-graph.sh stacks/single-app.yaml --entry      # expect: inventory-api
./scripts/stack-graph.sh stacks/single-flask-app.yaml --entry # expect: analytics-api

# Propagation chain from entry (order matters for header validation)
./scripts/stack-graph.sh stacks/stack-one.yaml --chain demo-fe
./scripts/stack-graph.sh stacks/stack-two-vendor.yaml --chain vendor-fe
```

Check: chain starts with entry app and includes all reachable apps via `downstream` (no missing nodes for a connected graph).

### 1.5 Registry and versions

- Every app in each stack must exist in `stacks/registry.yaml` (repo → stack mapping) and in `stacks/versions.yaml` (version entry).
- Manually spot-check: list apps from one stack, confirm they’re in `registry.yaml` and `versions.yaml`.

---

## Phase 2 — Local cluster + Tekton (resolve task)

**Goal:** Confirm that the **resolve-stack** task (running in Tekton) produces the same DAG-derived outputs as the CLI.

**Automated:** Run `./scripts/verify-dag-phase2.sh` (optionally with `--stack`, `--changed-app`, `--storage-class`). It uses the **stack-dag-verify** pipeline (clone + resolve only, no build/registry), waits for completion, then compares resolve-stack task results to `stack-graph.sh` output. Requires the `stack-dag-verify` pipeline and `resolve-stack` + `git-clone` tasks to be applied.

### 2.1 Prerequisites

- Local Kubernetes (kind / minikube / k3d) with Tekton Pipelines installed.
- This repo’s tasks and pipelines applied, including **stack-dag-verify** (`pipeline/stack-dag-verify-pipeline.yaml`).
- The **git-clone** task (Tekton catalog) must exist in the cluster.

### 2.2 Run the DAG-verify pipeline (automated)

The script creates a PipelineRun for the minimal **stack-dag-verify** pipeline (fetch-source → resolve-stack only), waits for it to finish, then compares results to the CLI:

```bash
./scripts/verify-dag-phase2.sh
./scripts/verify-dag-phase2.sh --stack stack-two-vendor.yaml --storage-class ""
```

### 2.3 Inspect resolve results (manual alternative)

If you run the full **merge** or **PR** pipeline instead, inspect the `resolve-stack` task results (e.g. via Tekton CLI or Kubernetes):

- **app-list** — must match `./scripts/stack-graph.sh stacks/stack-one.yaml --topo`.
- **entry-app** — must match `./scripts/stack-graph.sh stacks/stack-one.yaml --entry`.
- **propagation-chain** — same set of apps as `./scripts/stack-graph.sh stacks/stack-one.yaml --chain <entry>`.
- **build-apps** — for merge with `--repo demo-fe`, should be `demo-fe`; for PR with `changed-app: demo-fe`, same.
- **stack-json** — must contain the same apps, `downstream`, and build config as the stack YAML.

Example (tkn):

```bash
tkn pipelinerun describe <run-name> --last
tkn taskrun describe <resolve-stack-taskrun-name> --show-results
```

### 2.4 Repeat for another stack (optional)

Run `verify-dag-phase2.sh --stack single-app.yaml` or `--stack stack-two-vendor.yaml` to verify other stacks.

---

## Phase 3 — Full pipeline behavior (DAG in practice)

**Goal:** Confirm that pipeline behavior is consistent with the DAG (build order, single-app vs multi-app, propagation chain used by deploy/validate).

### 3.1 Build order

- For a **single-app** stack (e.g. `inventory-api` or `analytics-api`), the pipeline should build exactly one app; `build-apps` and the build task should show that single app.
- For **stack-one** with `changed-app: demo-fe`, only `demo-fe` should be built in a PR run; with merge (or no changed-app), all three apps should be built in topo order (demo-fe, then release-lifecycle-demo, then demo-api).

Verify by checking task logs or Tekton task results for the build task: list of built apps and order (if visible) should match the DAG.

### 3.2 Propagation chain in deploy and validate

- **deploy-intercept** and **validate-propagation** use `propagation-chain` and `entry-app`. For a full PR run, confirm that deploy creates pods for the expected apps and that validate sends the request to the entry app and checks the chain. (Exact success depends on services and Telepresence; here we only verify that the pipeline uses the right chain.)

Check task params passed to `deploy-stack-intercepts` and `validate-stack-propagation`: they should receive the same `propagation-chain` and `entry-app` as produced by resolve (and as the CLI shows).

### 3.3 Checklist summary

| Check | How to verify |
|-------|----------------|
| All stack YAMLs valid (no cycles, refs resolve) | Phase 1.2 |
| Topo order matches CLI | Phase 1.3 + Phase 2.3 |
| Entry and chain match CLI | Phase 1.4 + Phase 2.3 |
| Resolve task outputs match CLI | Phase 2.3 |
| build-apps = one app (PR/single) or full topo (merge) | Phase 2.3, Phase 3.1 |
| Deploy/validate receive correct chain and entry | Phase 3.2 |

---

## Quick reference commands

```bash
MILESTONE=
cd "$MILESTONE"

# Phase 1 (automated)
./scripts/verify-dag-phase1.sh

# Phase 1 (manual)
for f in stacks/stack-one.yaml stacks/stack-two-vendor.yaml stacks/single-app.yaml stacks/single-flask-app.yaml; do
  echo "=== $f ==="
  ./scripts/stack-graph.sh "$f" --validate
  ./scripts/stack-graph.sh "$f" --topo
  ./scripts/stack-graph.sh "$f" --entry
done

# Phase 2 (automated, after cluster + Tekton ready)
kubectl apply -f tasks/ && kubectl apply -f pipeline/
./scripts/verify-dag-phase2.sh
./scripts/verify-dag-phase2.sh --stack stack-two-vendor.yaml --storage-class ""
```

After Phase 2 and 3, you’ll have confirmed that the **DAG structure** is correct in the repo, in the resolve task, and in the rest of the pipeline when running locally.
