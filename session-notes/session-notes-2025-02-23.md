# Session notes — 2025-02-23 (Monday)

Summary of what we did in the **tekton-dag** project on this date.

---

## 1. Sample app repos for each application type

The pipeline runs Tekton PR scripts for DAGs built from many small application repos. We created **sample repos** for each application type in the plan and added them to the **jmjava** GitHub org as `tekton-dag-<name>`:

| Repo | Build tool | Used by stacks |
|------|------------|----------------|
| **tekton-dag-vue-fe** | npm | demo-fe, vendor-fe |
| **tekton-dag-spring-boot** | Maven | release-lifecycle-demo, demo-api, inventory-api |
| **tekton-dag-spring-boot-gradle** | Gradle | vendor-middleware |
| **tekton-dag-php** | Composer | vendor-adapter |
| **tekton-dag-spring-legacy** | Maven (WAR) | internal-api |
| **tekton-dag-flask** | pip | notifications-svc, analytics-api |

Each repo is a minimal but valid app (Dockerfile, tests where applicable) so the pipeline can clone, build, and run the DAG locally.

---

## 2. sample-repos directory and scripts

- **`sample-repos/`** — Added in the tekton-dag repo with a **README** that:
  - Explains sample apps are separate GitHub repos under jmjava
  - Lists clone commands for `~/github/jmjava` and all six repos (SSH URLs)
  - Includes a table of repo name, clone URL, and build tool

- **`scripts/create-and-push-sample-repos.sh`** — Script to create and/or push the sample repos. Supports `--dry-run` and optional app names. Can use `SAMPLE_REPOS_ROOT` (e.g. `~/github/jmjava`) when using clones instead of nested `sample-repos/`.

- **`.gitignore`** — Updated so nested app dirs under `sample-repos/` are treated as standalone repos: ignore `sample-repos/*/.git/`, `node_modules/`, `target/`, `build/`, `.gradle/`, `vendor/`, `__pycache__`, `.venv`, etc., so the pipeline can clone from GitHub and we don't commit build artifacts from sample apps.

---

## 3. Stacks and version registry

- **`stacks/versions.yaml`** — Version registry for all apps (Stack One, Stack Two, standalone). Tracks `version` (e.g. `0.1.0-rc.0`) and `last-released` per app. Used as the default version set; overridable at run time via version-overrides.

- **Stack YAMLs** — stack-one, stack-two-vendor, single-app, single-flask-app, registry define the DAG and reference app repos as `repo: jmjava/tekton-dag-<name>`.

---

## 4. VS Code launch configs

- **`.vscode/launch.json`** — Added launch and attach configurations for local debugging of each app type:
  - Vue (demo-fe): npm run dev + Chrome debug
  - Spring Boot (release-lifecycle-demo): Java launch & attach (port 5005)
  - Spring Boot Gradle: Java launch & attach
  - PHP, Spring Legacy, Flask: corresponding launch/attach configs  
  Uses multi-root workspace folders (e.g. `tekton-dag-vue-fe`, `tekton-dag-spring-boot`) when those repos are opened alongside tekton-dag.

---

## 5. Session notes

- **`session-notes/`** directory created; this file is the first session note (renamed from sessions-notes-today.md to include date: **session-notes-2025-02-23.md**).

---

## Test results so far

**Valid PR test:** The only valid test for the PR feature is the **real PR flow**: create a real GitHub PR (`./scripts/create-test-pr.sh`), run the PR pipeline with that PR number and branch, then merge the PR (`./scripts/merge-pr.sh`) and run the merge pipeline. See [docs/PR-TEST-FLOW.md](../docs/PR-TEST-FLOW.md).

Runs with a fake PR number (e.g. `--pr 999` or `--pr 1`) and `--git-revision main` are **not** the PR feature test; they only verify that the pipeline runs (sanity check).

| Phase / Test | Script / trigger | What it checks | Status |
|--------------|------------------|----------------|--------|
| **Phase 1** (no cluster) | `./scripts/verify-dag-phase1.sh` | Repo layout, stack YAMLs, `stack-graph.sh --validate`, topo order, registry/versions | **PASSING** |
| **Phase 2** (cluster) | `./scripts/verify-dag-phase2.sh [--stack STACK]` | `stack-dag-verify` pipeline: fetch + resolve | Not run yet |
| **Bootstrap pipeline** | `stack-bootstrap` | fetch → resolve → clone → build → deploy-full-stack | **PASSING** (sanity check) |
| **PR pipeline (valid test)** | `create-test-pr.sh` → `generate-run.sh --mode pr --pr <N> --git-revision <BRANCH>` | Real PR created; pipeline runs on PR branch; version commit pushed to PR branch | **Use this to validate PR feature** |
| **Merge pipeline (valid test)** | `merge-pr.sh <N>` → `generate-run.sh --mode merge --git-revision main` | PR merged; merge build runs from main | **Use after valid PR test** |
| **run-e2e-with-intercepts.sh** | Bootstrap + PR run with e.g. `--pr 999` and main | Pipeline sanity only; no real PR | Not the PR feature test. |

---

## Current cluster state (as of end of session)

**Kind cluster:** `tekton-stack` — running, single node  
**Tekton:** Pipelines, Triggers, Results all installed and running  
**Telepresence:** Traffic Manager installed in `ambassador` namespace  
**Staging namespace:** All 3 apps deployed and healthy:

| App | Deployment | Status |
|-----|------------|--------|
| demo-fe | 1/1 Ready | Running (nginx on port 80) |
| release-lifecycle-demo | 1/1 Ready | Running (Spring Boot on 8080) |
| demo-api | 1/1 Ready | Running (Spring Boot on 8080) |

**Build cache PVC:** `build-cache` (5Gi) created and populated with Maven `.m2` cache.

---

## Bootstrap pipeline — PASSING

Run: `stack-bootstrap-6v8nf`

| Task | Status |
|------|--------|
| fetch-source | **Succeeded** |
| resolve-stack | **Succeeded** |
| clone-app-repos | **Succeeded** — clones `jmjava/tekton-dag-vue-fe`, `jmjava/tekton-dag-spring-boot`, `jmjava/tekton-dag-spring-boot-gradle` via SSH |
| build-apps (compile) | **Succeeded** — npm build for demo-fe, Maven for release-lifecycle-demo and demo-api |
| build-apps (containerize) | **Succeeded** — Kaniko pushes to `kind-registry:5000`, pulls as `localhost:5000` |
| deploy-full-stack | **Succeeded** — all 3 deployments + services in staging |

---

## PR pipeline — status

**Valid test:** Use `create-test-pr.sh` to create a real PR, then run the PR pipeline with that PR number and branch. Previous runs like `stack-pr-999-*` or `stack-pr-1-*` with `main` were pipeline sanity runs only (no real PR).

| Task | Status | Notes |
|------|--------|-------|
| fetch-source | **Succeeded** | |
| resolve-stack | **Succeeded** | |
| clone-app-repos | **Succeeded** | |
| bump-rc-version | **Succeeded** | Bumps RC version, git commit OK |
| build-apps (compile) | **Succeeded** | Build cache used (`/workspace/build-cache`) |
| build-apps (containerize) | **Succeeded** | JSON image-tag parsing and registry handling fixed |
| deploy-intercepts | **Succeeded** | |
| validate-propagation | **Succeeded** | |
| run-tests | **Succeeded** | E2E + per-app tests (postman collections optional) |
| push-version-commit | **Succeeded** | SSH push of version bump |
| cleanup | **Succeeded** | finally block |

### Containerize fixes applied

1. **Registry URL trailing `}`**: `generate-run.sh` now trims any stray trailing `}` from `IMAGE_REGISTRY` so Kaniko destination is valid.
2. **JSON image-tag**: `build-app.yaml` containerize step parses per-app version from JSON (e.g. `{"demo-fe":"0.1.0-rc.1"}`) using `sed`/`grep` (no jq in BusyBox).

---

## Issues fixed during this session

| Issue | Root cause | Fix |
|-------|-----------|-----|
| Pipeline cloning old `menkelabs/*` repos | Local tekton-dag changes never pushed to GitHub (HTTPS auth failed) | Switched remote to SSH, pushed all commits |
| Kaniko `/tmp` doesn't exist | `gcr.io/kaniko-project/executor:debug` uses BusyBox, no `/tmp` | Use workspace path for temp files |
| Kaniko can't push to `localhost:5000` | Pods can't reach `localhost` registry; only the containerd host mapping works for pulls | Map `localhost:PORT` → `kind-registry:PORT` for Kaniko push; use `--insecure` |
| Kaniko `//product_uuid` error | Known Kaniko + containerd issue | `--ignore-path /product_uuid --ignore-path /sys` |
| demo-fe readiness probe failing | Stack had `container-port: 3000` but nginx serves on 80 | Changed to `container-port: 80` |
| demo-api Dockerfile `COPY build/libs/*.jar` | Gradle output path, but we build with Maven (`target/`) | Changed Dockerfile to `COPY target/*.jar` |
| bump-rc-version permission denied | `yq:4` image runs as non-root, can't write root-owned files from git-clone | Added `securityContext: runAsUser: 0` |
| bump-rc-version `not in a git directory` | yq image changes workdir / HOME | Set `GIT_DIR` and `GIT_WORK_TREE` explicitly |
| `coschedule: workspaces` blocks multiple PVCs | Tekton affinity assistant rejects tasks with >1 RWO PVC | Set `coschedule: disabled` (single-node Kind) |

---

## Infrastructure added this session

- **Build cache PVC** (`build-cache`, 5Gi) — persistent across pipeline runs. Caches `.m2`, `.npm`, `.gradle`, `.pip`, `.composer` via optional `build-cache` workspace on `build-stack-apps` task.
- **Continuation pipeline** (`stack-pr-continue`) — skips fetch/resolve/clone/build, starts from deploy-intercepts using results from a failed run.
- **Rerun script** (`scripts/rerun-pr-from.sh <failed-run>`) — extracts task results from a failed PipelineRun, finds the workspace PVC, launches `stack-pr-continue`.
- **`git-cli` Tekton catalog task** installed for push-version-commit step.
- **Tekton `coschedule: disabled`** in feature-flags ConfigMap.

---

## Next steps

1. **Fix the two containerize bugs** and re-run the PR pipeline:
   - Fix the trailing `}` in image-registry param (trace through `generate-run.sh` YAML template)
   - Apply the JSON image-tag parsing fix already in `build-app.yaml`
2. **Test the build cache speedup** — second PR run should skip most Maven/npm downloads.
3. **Test `rerun-pr-from.sh`** on a failed PR run to verify the continuation pipeline.
4. **Complete the E2E flow**: bootstrap → PR pipeline → Tekton Results DB verification.
5. Phase 2 verification (`verify-dag-phase2.sh`) if needed.
