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

Verification is defined in [docs/local-dag-verification-plan.md](../docs/local-dag-verification-plan.md). Status as of this session:

| Phase / Test | Script / trigger | What it checks | Status |
|--------------|------------------|----------------|--------|
| **Phase 1** (no cluster) | `./scripts/verify-dag-phase1.sh` | Repo layout, stack YAMLs, `stack-graph.sh --validate` for all stacks, topo order, entry, propagation chain, registry/versions | **PASSING** |
| **Phase 2** (cluster) | `./scripts/verify-dag-phase2.sh [--stack STACK]` | `stack-dag-verify` pipeline: fetch + resolve; compare resolve output to CLI | Not run yet |
| **Bootstrap pipeline** | `stack-bootstrap` via `run-e2e-with-intercepts.sh` | fetch → resolve → clone-app-repos → build-all → deploy-full-stack | **PASSING** (run `stack-bootstrap-6v8nf`) |
| **PR pipeline** | `stack-pr-test` via `generate-run.sh --mode pr` | fetch → resolve → clone → bump-rc → build → deploy-intercepts → validate → test → push | **FAILING** at containerize step (see below) |
| **Full E2E** | `./scripts/run-e2e-with-intercepts.sh` | Bootstrap + PR pipeline + Tekton Results DB verify | **FAILING** — bootstrap passes, PR pipeline fails |

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

## PR pipeline — FAILING at containerize

Latest run: `stack-pr-1-g95x8`

| Task | Status | Notes |
|------|--------|-------|
| fetch-source | **Succeeded** | |
| resolve-stack | **Succeeded** | |
| clone-app-repos | **Succeeded** | |
| bump-rc-version | **Succeeded** | Bumps demo-fe `0.1.0-rc.0 → 0.1.0-rc.1`, git commit OK |
| build-apps (compile) | **Succeeded** | Build cache used (`/workspace/build-cache`) |
| build-apps (containerize) | **FAILED** | Two bugs (see below) |

### Containerize bugs (to fix next)

1. **Registry URL has trailing `}`**: The `image-registry` param value is `localhost:5000}` (with a stray `}`). Shows up in Kaniko destination as `kind-registry:5000}/demo-fe:v...`. Root cause: likely in how `generate-run.sh` or `run-e2e-with-intercepts.sh` passes the value.

2. **JSON image-tag not parsed**: The `image-tag` param from `bump-rc-version` is a JSON map `{"demo-fe":"0.1.0-rc.1"}`, but the containerize step (BusyBox shell, no `jq`) was treating it as a plain string. This produces an invalid tag like `v{"demo-fe":"0.1.0-rc.1"}`. **Fix already staged** in `build-app.yaml` — uses `sed`/`grep` to extract per-app version from the JSON. Needs to be applied and tested.

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
