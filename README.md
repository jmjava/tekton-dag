# tekton-dag

Standalone Tekton pipeline system for **local development and proof-of-concept**. No AWS. Run on Kind (or any Kubernetes) with a local registry and optional Telepresence. Proves out the stack DAG and pipelines locally; [share back to reference-architecture-poc](SHARING-BACK.md) when ready.

## Quick start (local)

```bash
# 1. Kind cluster + local registry
./scripts/kind-with-registry.sh

# 2. Tekton + stack tasks/pipelines (labels namespace for Pod Security)
./scripts/install-tekton.sh

# 3. Optional: Telepresence Traffic Manager (for full PR pipeline with intercepts)
./scripts/install-telepresence-traffic-manager.sh

# 4. Optional: Postgres + Tekton Results (persist run history)
./scripts/install-postgres-kind.sh
./scripts/install-tekton-results.sh

# 5. Prove the DAG
./scripts/verify-dag-phase1.sh
# Phase 2 clones this repo; after push set GIT_URL to the repo URL:
export GIT_URL="https://github.com/jmjava/tekton-dag.git"
./scripts/verify-dag-phase2.sh

# 6. Full test + verify results in DB (after Results is installed)
./scripts/run-full-test-and-verify-results.sh

# Or run everything in one go (setup + test; idempotent). Run in your terminal:
#   cd /path/to/tekton-dag && ./scripts/run-all-setup-and-test.sh
./scripts/run-all-setup-and-test.sh
```

For manual pipeline runs, use `--registry localhost:5000 --storage-class ""`. See the full [README in docs](docs/README-FULL.md) (copied from the main design) for concepts, stack YAML, and pipeline flows.

## App repos (no monorepo)

Apps are **separate standalone Git repos**, not subdirectories of this repo. The pipeline (1) clones the **platform repo** (this repo, tekton-dag) for stacks and versions, (2) resolves the stack to get `build-apps`, then (3) **clones each app repo** from `stacks/*.yaml` (`.apps[].repo`, e.g. `jmjava/tekton-dag-vue-fe`) into `workspace/<app-name>` and builds. Create and push the sample app repos with `./scripts/create-and-push-sample-repos.sh` so the pipeline can clone them.

## Layout

- **stacks/** — Stack YAML (DAG), registry, versions
- **tasks/** — Tekton tasks (resolve, clone-app-repos, build, deploy-intercept, validate, test, version, cleanup)
- **pipeline/** — stack-pr-test, stack-merge-release, stack-dag-verify
- **scripts/** — run-all-setup-and-test (run everything), kind-with-registry, install-tekton, install-postgres-kind, install-tekton-results, verify-dag-phase1/2, verify-results-in-db, run-full-test-and-verify-results, generate-run, stack-graph
- **docs/** — C4 diagrams, local DAG verification plan

## Sharing back to reference-architecture

See [SHARING-BACK.md](SHARING-BACK.md).
