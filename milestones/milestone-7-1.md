# Milestone 7.1: Pipeline speed optimizations (bootstrap and PR)

> **Follows [milestone 7](milestone-7.md).** Implements the optimizations identified in [docs/bootstrap-pipeline-speed-analysis.md](../docs/bootstrap-pipeline-speed-analysis.md) to reduce bootstrap and (where applicable) PR pipeline duration.

## Goal

Make the **stack-bootstrap** pipeline (and, where relevant, the **stack-pr-test** pipeline) run faster by parallelizing bottlenecks and enabling Kaniko cache. Target: noticeably shorter wall-clock time on a typical dev machine without changing app build logic.

---

## Background

- **Bootstrap today:** fetch-source → resolve-stack → clone-app-repos (sequential) → build-select-tool-apps → compile tasks (already parallel) → **build-containerize (sequential per app)** → deploy-full-stack.
- **Main bottlenecks:** (1) **build-containerize** — one task, one step, N sequential Kaniko builds and `--cache=false`; (2) **clone-app-repos** — sequential git clones.
- **Compile** is already parallel; optional tuning is resource requests/limits.

See [docs/bootstrap-pipeline-speed-analysis.md](../docs/bootstrap-pipeline-speed-analysis.md) for the full analysis.

---

## Deliverables

### 7.1.1 Parallel containerize (bootstrap)

- **Current:** One task `build-containerize` with a single step that loops over `build-apps` and runs Kaniko once per app in sequence.
- **Target:** Build all app images in parallel.

**Instructions:**

1. **Option A — One pipeline task per app (recommended):**
   - Add a pipeline param or use the existing `build-apps` / stack graph to define the list of apps (e.g. from `resolve-stack` or a static list for stack-one).
   - In `stack-bootstrap-pipeline.yaml`, replace the single `build-containerize` task with **one task per app** (e.g. `build-containerize-demo-fe`, `build-containerize-release-lifecycle-demo`, `build-containerize-demo-api`) or use a matrix/loop if your Tekton version supports it. Each task:
     - `runAfter`: all compile tasks that can produce that app’s build output (for bootstrap, all compile tasks).
     - Runs the existing **build-containerize** logic for a **single** app (either call the same task with a param like `build-apps: <single-app>`, or create a small task that containerizes one app and takes `app`, `stack-json`, `image-registry`, `image-tag`, workspace `source`, and produces a one-entry `built-images` result).
   - Add a **merge step/task** that runs after all per-app containerize tasks and combines their `built-images` results into one JSON (e.g. merge keys from each task’s result). The pipeline’s `deploy-full-stack` then consumes this merged result.
   - Ensure `deploy-full-stack` and any other consumers still receive a single `built-images` map in the same format as today.

2. **Option B — Parallel inside one task:**
   - Keep one `build-containerize` task but change its step script to start one Kaniko process per app in the background (e.g. `for app in $BUILD_APPS; do ... /kaniko/executor ... & done; wait`). Merge the built image names into the final `built-images` result. This avoids pipeline restructuring but is more complex (shared workspace, logging, error handling).

3. **Apply the same pattern to the PR pipeline** (`stack-pr-test`) if it uses a single `build-containerize` task that loops over apps — so PR runs also build images in parallel where multiple apps are built.

**Acceptance:** Bootstrap (and PR, if updated) builds N app images in parallel; total containerize phase time is roughly “max of per-app build times” instead of “sum.”

---

### 7.1.2 Kaniko cache

- **Current:** `build-containerize` (or per-app containerize task) uses `--cache=false`.
- **Target:** Enable Kaniko layer cache so repeat runs (and PR containerize) reuse layers.

**Instructions:**

1. **Cache repo:** Decide on a cache repository (e.g. `$(image-registry)/kaniko-cache` or a dedicated repo). Ensure the registry is writable by the Kaniko step (insecure/skip-tls as needed for local Kind).

2. **Task change:** In the task that runs Kaniko (current `build-containerize` or the per-app containerize task), add params if needed (e.g. `cache-repo`) and pass:
   - `--cache=true`
   - `--cache-repo=<cache-repo>` (e.g. `$(params.image-registry)/kaniko-cache` or `$(params.cache-repo)`)
   - Optionally `--cache-ttl` if you want expiry.

3. **Pipeline param (optional):** Add a pipeline param such as `kaniko-cache-repo` (default empty or a convention like `$(params.image-registry)/kaniko-cache`) and pass it into the containerize task(s).

4. **Document:** In the pipeline or task description (or in [docs/bootstrap-pipeline-speed-analysis.md](../docs/bootstrap-pipeline-speed-analysis.md)), note that the cache repo must be writable and that first run is unchanged; subsequent runs benefit.

**Acceptance:** Second and later bootstrap (and PR) runs show faster containerize phase when layers are reused; first run behavior unchanged.

---

### 7.1.3 Parallel clone (bootstrap)

- **Current:** One task `clone-app-repos` with a single step that loops over `build-apps` and runs `git clone` (and fetch/checkout) sequentially.
- **Target:** Clone all app repos in parallel.

**Instructions:**

1. **Option A — Parallel in one step (simplest):**
   - In `tasks/clone-app-repos.yaml`, change the clone loop to start each `git clone` (and optional fetch/checkout) in the background (e.g. `git clone ... &`), then `wait` at the end. Ensure SSH and `known_hosts` are set up once before the loop. Collect errors (e.g. `wait` exit codes or a small wrapper) and fail the step if any clone fails.

2. **Option B — One pipeline task per app:**
   - In `stack-bootstrap-pipeline.yaml`, replace `clone-app-repos` with N tasks (e.g. one per app in the stack), each `runAfter: resolve-stack`, each cloning a single repo into the shared workspace (e.g. `source/<app>`). Ensure only one task writes to each path. Then `build-select-tool-apps` and compile tasks run after all clone tasks (e.g. `runAfter: [clone-app-1, clone-app-2, clone-app-3]`). This may require a dynamic pipeline or a fixed list of apps per stack.

**Acceptance:** Clone phase wall time is roughly “max of per-repo clone times” instead of “sum”; behavior (revisions, SSH, layout) unchanged.

---

### 7.1.4 Optional: compile step resources

- **Current:** Compile tasks (npm, maven, gradle, etc.) do not set explicit CPU/memory requests or limits.
- **Target:** Allow pipelines to request more CPU/memory for compile steps so they finish faster when CPU-bound.

**Instructions:**

1. In the **bootstrap** (and optionally **PR**) pipeline, set `taskRunTemplate.spec.resources` or step-level `resources` for the compile tasks (e.g. `requests.cpu: "2"`, `requests.memory: "2Gi"`). Alternatively add optional params to the compile tasks and use them in a `taskRunTemplate` in the pipeline.
2. Document in the milestone or in the pipeline that these are tunable for faster runs on capable machines.

**Acceptance:** Pipeline runs with higher compile resource requests where configured; no change to correctness.

---

### 7.1.5 Missing Postman test collections (run-tests)

- **Current:** The `run-tests` task looks for Postman collections per app; when they are absent, it skips and continues. E2E output shows:
  - **release-lifecycle-demo:** `Collection not found: tests/postman/bff-tests.json (skipping)`
  - **demo-api:** `Collection not found: tests/postman/api-tests.json (skipping)`
- **Gap:** Those paths are not present in the app repos, so Postman-based API/BFF tests are never executed.

**Instructions:**

1. **Document:** In this milestone (or in run-tests task docs), note that Postman collections are optional and that `bff-tests.json` (release-lifecycle-demo) and `api-tests.json` (demo-api) are currently missing; the pipeline skips them without failing.
2. **Optional — add collections:** In the respective app repos (e.g. release-lifecycle-demo, demo-api), add the expected files under `tests/postman/` (e.g. `bff-tests.json`, `api-tests.json`) so run-tests executes them. Alternatively add a convention doc that lists expected collection paths per app so future stacks can add tests consistently.
3. **Optional — fail if required:** If you want run-tests to fail when a collection is declared but missing, add a pipeline param or task param (e.g. `require-postman-collections: "true"`) and have the run-tests script exit non-zero when a collection is not found and that param is set.

**Acceptance:** The missing Postman collections are documented; optionally, collections are added or behavior (skip vs fail) is configurable.

---

## Success criteria

- [ ] Bootstrap pipeline builds app images in parallel (7.1.1).
- [ ] Kaniko cache is enabled and repeat runs show faster containerize phase (7.1.2).
- [ ] App repos are cloned in parallel in bootstrap (7.1.3).
- [ ] (Optional) Compile resource requests are configurable and documented (7.1.4).
- [ ] Missing Postman collections (bff-tests.json, api-tests.json) documented; optionally add collections or make skip/fail configurable (7.1.5).
- [ ] Existing behavior preserved: same `built-images` format, same deploy and PR pipeline behavior; only wall-clock time improves.
- [ ] [docs/bootstrap-pipeline-speed-analysis.md](../docs/bootstrap-pipeline-speed-analysis.md) updated to note that optimizations have been implemented (and how).

---

## Non-goals

- Changing app build commands or stack definitions for speed.
- Optimizing fetch-source or deploy-full-stack beyond what is trivial.
- Making the pipeline work on minimal hardware; focus is “faster on a decent machine.”

---

## References

- [docs/bootstrap-pipeline-speed-analysis.md](../docs/bootstrap-pipeline-speed-analysis.md) — analysis and recommendations
- [pipeline/stack-bootstrap-pipeline.yaml](../pipeline/stack-bootstrap-pipeline.yaml) — bootstrap pipeline
- [pipeline/stack-pr-pipeline.yaml](../pipeline/stack-pr-pipeline.yaml) — PR pipeline (containerize if parallelized)
- [tasks/build-containerize.yaml](../tasks/build-containerize.yaml) — current containerize task
- [tasks/clone-app-repos.yaml](../tasks/clone-app-repos.yaml) — current clone task
