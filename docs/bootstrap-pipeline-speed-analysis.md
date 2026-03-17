# Stack-bootstrap pipeline: speed analysis

Analysis of where time goes and how to make the bootstrap run faster on a decent machine. **No edits** — recommendations only.

---

## 1. Pipeline shape (stack-one: 3 apps)

```
fetch-source → resolve-stack → clone-app-repos → build-select-tool-apps
                                                         ↓
              ┌──────────────────────────────────────────┼──────────────────────────────────────────┐
              ↓                    ↓                     ↓                     ↓                     ↓
     build-compile-npm    build-compile-maven   build-compile-gradle   build-compile-pip   build-compile-composer
              └──────────────────────────────────────────┼──────────────────────────────────────────┘
                                                         ↓
                                              build-containerize
                                                         ↓
                                              deploy-full-stack
```

- **Already parallel:** The five compile tasks all run after `build-select-tool-apps` with no dependencies between them. For stack-one (demo-fe, release-lifecycle-demo, demo-api) only npm + maven (+ optionally gradle) run; the rest are skipped. So compile phase is already as parallel as the stack allows.
- **Bottlenecks:** Everything else is sequential.

---

## 2. Where time goes (rough order)

| Phase | What happens | Why it can be slow |
|-------|----------------|---------------------|
| **fetch-source** | Single `git clone` (platform repo). | Network; depth/shallow already help. Usually &lt;1 min. |
| **resolve-stack** | yq/jq on stack YAML. | Negligible. |
| **clone-app-repos** | **Sequential** loop: clone app1, then app2, then app3. | 3 × (clone + fetch checkout). Network-bound; no parallelism. |
| **build-select-tool-apps** | Writes `.tool-apps.json`. | Negligible. |
| **Compile (npm, maven, …)** | Parallel tasks; each runs e.g. `npm install && npm run build` or `mvn clean package`. | CPU + disk (and first-time dependency download). Build-cache PVC helps repeat runs; first run fills .m2/.npm. |
| **build-containerize** | **Single task, single step:** loop over apps, run Kaniko **one image at a time**. | Largest single bottleneck: N sequential Docker builds, no parallelism. Kaniko `--cache=false` → no layer cache between runs. |
| **deploy-full-stack** | `kubectl apply` per app. | Usually fast (seconds). |

So the two main bottlenecks are:

1. **clone-app-repos** — sequential clones.
2. **build-containerize** — sequential image builds and no Kaniko cache.

---

## 3. Recommendations (no edits applied)

### A. Containerize: parallelize and cache (biggest win)

- **Parallel builds:** Today one task runs one step that loops over apps and calls Kaniko per app. Options:
  - Split into **one pipeline task per app** (e.g. `build-containerize-demo-fe`, `build-containerize-release-lifecycle-demo`, `build-containerize-demo-api`) all `runAfter` the compile tasks, then a final task that merges `built-images` from the three. Then 3 images build in parallel.
  - Or keep one task but run Kaniko in **parallel in the script** (e.g. background jobs and `wait`), so one pod uses multiple cores for 3 concurrent builds (more complex, shared workspace/cache considerations).
- **Kaniko cache:** Today `--cache=false`. Use a cache repo and `--cache=true` (and e.g. `--cache-repo`) so repeat runs reuse layers. First run unchanged; later runs (and PR pipeline containerize) get faster.

### B. Clone: parallelize

- **Per-app clone tasks:** Replace one `clone-app-repos` task with N tasks (e.g. `clone-demo-fe`, `clone-release-lifecycle-demo`, `clone-demo-api`) all `runAfter: resolve-stack`, each cloning one repo into a subpath. Requires workspace layout (e.g. one shared workspace with each task writing to `source/<app>`) or multiple workspaces and a merge step. Then 3 clones run in parallel.
- **Or parallel inside one step:** In the current task script, clone in background (`git clone ... &`) and `wait` at the end. Simpler than pipeline changes, same idea.

### C. Compile: already parallel; optional tuning

- **Resource requests/limits:** Tekton doesn’t set big CPU/memory by default. If compile pods are small, Maven/NPM can be CPU-bound. Giving more CPU (e.g. in `taskRunTemplate` or step `resources`) can shorten compile time.
- **Build-cache:** Already used when the pipeline gets the build-cache workspace. Ensure the PVC is on fast storage (e.g. local SSD or fast cloud volume). First run will still download deps; subsequent runs benefit.

### D. One-off / environment

- **Pre-pull images:** First run of each compile task pulls the compile image (node, maven, …); Kaniko and kubectl pull once. Pre-pulling on the node (or using a base image that’s already in the node cache) avoids paying that cost in the critical path.
- **Registry and network:** Local registry (e.g. Kind’s) avoids network latency for push/pull; already the case if you use localhost:5000. If you ever use a remote registry, that can add time.

---

## 4. Impact vs effort (summary)

| Change | Expected speedup | Effort |
|--------|-------------------|--------|
| Parallel containerize (one task per app) | Large (e.g. ~⅔ of containerize time if 3 apps) | Medium (pipeline + merge step) |
| Kaniko cache=true + cache repo | Large on 2nd+ runs | Low (task param + registry) |
| Parallel clone (parallel tasks or parallel in script) | Moderate (clone phase ~⅓–½) | Medium / Low |
| More CPU for compile steps | Moderate if CPU-bound | Low (resources in pipeline/task) |
| Pre-pull images | Small (one-time per image) | Low |

So: **parallel containerize** and **Kaniko cache** give the biggest gains; **parallel clone** and **compile resources** are next; **pre-pull** is a small, one-time improvement.

---

## 5. Implemented optimizations (M7.1)

The following recommendations from this analysis were implemented in Milestone 7.1:

| Optimization | Implementation |
|---|---|
| **Parallel containerize** | `build-containerize` task spawns one Kaniko **pod per app** in parallel (via kubectl), each mounting the shared workspace PVC. Wall-clock time = max(per-app build) instead of sum. |
| **Kaniko cache** | `--cache=true --cache-repo=<registry>/kaniko-cache --cache-ttl=168h` passed to each Kaniko pod. New pipeline param `cache-repo` (default `localhost:5000/kaniko-cache`). Second+ runs reuse cached layers. |
| **Parallel clone** | `clone-app-repos` task clones all app repos in background (`&`) and waits for all. Wall-clock time = max(per-repo clone) instead of sum. |
| **Compile resources** | Deferred (7.1.4). Compile tasks are already parallel; adding explicit CPU/memory requests is a tuning exercise for specific environments. Documented as optional in milestone-7-1.md. |
| **Postman test collections** | Documented (7.1.5). Missing `bff-tests.json` and `api-tests.json` are noted; pipeline skips them without failing. See milestone-7-1.md for details. |

---

## 6. Stack-one approximate timing (for orientation)

Rough order of magnitude (will vary by machine and cache):

- fetch-source: ~30–60 s  
- resolve-stack: &lt;10 s  
- clone-app-repos: ~1–2 min (3 sequential clones)  
- build-select-tool-apps: &lt;10 s  
- build-compile-npm: ~2–5 min  
- build-compile-maven (2 apps in one task): ~3–8 min (often the slowest)  
- build-containerize: ~2–5 min (3 sequential Kaniko builds)  
- deploy-full-stack: ~30 s  

Total often in the **~8–12 min** range; the longest segments are usually **compile** and **containerize**. Parallelizing containerize (and adding Kaniko cache) targets the segment that’s easiest to speed up without changing app build scripts.
