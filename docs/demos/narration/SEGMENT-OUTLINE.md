# Demo Segment Outline — 17 segments

Proposed restructure for the tekton-dag demo video series.
Segments follow the natural lifecycle: understand → setup → build → test → merge → operate → extend.

---

## Segment map

| #  | Title                        | Status   | Visual   | ~Duration | Notes |
|----|------------------------------|----------|----------|-----------|-------|
| 01 | Architecture overview        | Refresh  | Manim    | 80s       | Already strong — minor polish for M12 hook tasks, customization mention |
| 02 | Quickstart                   | Refresh  | VHS      | 65s       | Update to reflect current scripts, build-image matrix |
| 03 | Bootstrap dataflow           | Refresh  | Mixed    | 70s       | Keep propagation walkthrough, update Kaniko cache mention |
| 04 | PR pipeline                  | Refresh  | VHS      | 90s       | Good as-is — minor wording tweaks |
| 05 | Intercept routing            | Refresh  | Manim    | 75s       | Good — keep dual-backend (Telepresence + mirrord) |
| 06 | Local debug                  | Refresh  | Manim    | 70s       | Good — keep mirrord focus |
| 07 | **Merge & release pipeline** | **New**  | Manim    | 75s       | version-bump → build → crane tag → push version commit |
| 08 | Orchestrator API             | Refresh  | VHS      | 80s       | Was 07 — add /api/reload, /api/graph/stats |
| 09 | Multi-team Helm              | Refresh  | Manim    | 75s       | Was 08 — minor polish |
| 10 | **Baggage middleware**       | **New**  | Manim    | 70s       | Per-framework deep dive: Spring, Node, Flask, PHP. Roles, headers, safety. |
| 11 | Testing ecosystem            | Refresh  | VHS      | 80s       | Was 10 — rename, cover Newman + pytest + Playwright + Artillery |
| 12 | Test-trace graph             | Refresh  | Mixed    | 75s       | Was 11 — good as-is |
| 13 | Results DB                   | Refresh  | VHS      | 65s       | Was 09 — good, slight reorder for flow |
| 14 | **Customization**            | **New**  | Manim    | 80s       | Hook tasks, build variants, stack schema, language versions |
| 15 | Regression suite             | Rewrite  | VHS      | 75s       | Was 12 — expand from 9 lines to real Phase 1/2 walkthrough |
| 16 | Management GUI               | Rewrite  | Manim    | 80s       | Was 13 — full screen tour: DAG, runs, triggers, team switcher, logs |
| 17 | Extending the GUI            | Rewrite  | Manim    | 70s       | Was 14 — concrete Flask route → Vue store → Playwright example |
| 18 | **What's coming next**       | **New**  | Manim    | 90s       | M13 roadmap: retry, sizing, multi-cluster, observability |

**Total: ~19 minutes** (was ~14 minutes with thin 12–14)

---

## Segment details

### 01 — Architecture overview (refresh)

**What stays:** DAG model, three pipelines, polyglot stacks, orchestrator, GUI, Results, Neo4j.
**What changes:** Add explicit mention of merge/release pipeline as third pipeline. Reference M12 customization (hook tasks, build variants). Mention baggage middleware as the routing mechanism.
**Visual:** Manim — update StackDAGScene with merge pipeline box and hook task annotation.

---

### 02 — Quickstart (refresh)

**What stays:** Kind cluster, Tekton install, build images, kubectl apply.
**What changes:** Mention `--matrix` flag for build-image variants. Note optional components (Results, Neo4j, Dashboard, management GUI).
**Visual:** VHS terminal recording of the 4-command setup.

---

### 03 — Bootstrap dataflow (refresh)

**What stays:** resolve-stack → clone → build → deploy → trace request through propagation chain.
**What changes:** Minor wording updates. Mention Kaniko cache PV for faster rebuilds.
**Visual:** Mixed (Manim HeaderPropagationScene + VHS bootstrap terminal).

---

### 04 — PR pipeline (refresh)

**What stays:** Webhook → orchestrator → generate PipelineRun → build → intercept → validate → test → cleanup → PR comment.
**What changes:** Minor polish. Clarify "validation cluster" vs "production cluster" language. Mention query-test-plan integration with Neo4j.
**Visual:** VHS showing generate-run.sh and pipeline execution.

---

### 05 — Intercept routing (refresh)

**What stays:** Blue/green request paths, header routing, dual backend, concurrent PRs, validate propagation/original traffic.
**What changes:** Minor wording. Keep as-is — this is one of the strongest segments.
**Visual:** Manim InterceptRoutingScene.

---

### 06 — Local debug (refresh)

**What stays:** mirrord tunnel, IDE breakpoints, live cluster data, clean disconnect.
**What changes:** Minor polish. Reference VS Code launch configs in the repo.
**Visual:** Manim LocalDebugScene.

---

### 07 — Merge & release pipeline (NEW)

**Story arc:**
1. Open — "PR passed, tests green. What happens when you merge?"
2. Merge trigger — webhook fires, orchestrator generates merge PipelineRun
3. Version bump — `version-bump` task in release mode: strip `-rc.N` → release semver (e.g. `0.1.0-rc.3` → `0.1.0`)
4. Build — full compile + Kaniko containerize with merge tag
5. Tag release — `tag-release-images` uses crane to copy to `registry/app:v0.1.0`
6. Push version commit — bump to next dev cycle (`0.1.1-rc.0`), push `versions.yaml` back to repo
7. Hook tasks — optional pre-build/post-build hooks (image scan, SBOM, Slack)
8. Close — "Released image ready for promotion. PR to merge to release."

**Visual:** Manim — new MergeReleaseScene showing pipeline flow with version numbers transforming.

---

### 08 — Orchestrator API (refresh, was 07)

**What stays:** healthz/readyz, /api/stacks, POST /api/run, webhook, test-plan, graph endpoints, /api/runs, /api/teams.
**What changes:** Add /api/reload (hot-reload config). Add /api/graph/stats. Clarify deployment via Helm ConfigMap.
**Visual:** VHS terminal showing curl calls.

---

### 09 — Multi-team Helm (refresh, was 08)

**What stays:** Single team → three teams, values.yaml knobs, team-scoped ConfigMaps, GUI team switcher, webhook isolation.
**What changes:** Reference hook task parameters in values.yaml. Mention ArgoCD ApplicationSet for GitOps provisioning.
**Visual:** Manim MultiTeamScene.

---

### 10 — Baggage middleware (NEW)

**Story arc:**
1. Open — "Intercept routing depends on one thing: every service must propagate the dev-session header. The baggage libraries make this automatic."
2. The three roles — originator sets, forwarder passes through, terminal accepts but does not forward
3. Spring Boot — `@ConditionalOnProperty`, `BaggageContextFilter` + `BaggageRestTemplateInterceptor`, auto-configured
4. Node/Vue — `createBaggageFetch` wraps fetch, `createAxiosInterceptor` for axios, browser env gating via `VITE_BAGGAGE_ENABLED`
5. Flask/Python — `init_app` + `BaggageSession` subclassing `requests.Session`
6. PHP — PSR-15 `BaggageMiddleware` + Guzzle middleware
7. W3C baggage — standard `baggage` header alongside custom `x-dev-session`
8. Production safety — all gated by `BAGGAGE_ENABLED=false` in prod
9. Close — "Five frameworks, one header contract, zero application code changes beyond config."

**Visual:** Manim — new BaggageMiddlewareScene showing header flow through each framework icon.

---

### 11 — Testing ecosystem (refresh + rename, was 10)

**What stays:** Newman/Postman for API tests, pytest for orchestrator, tekton-dag-common tests, e2e intercept validation.
**What changes:** Rename from "Newman tests" to "Testing ecosystem." Add Playwright (69 e2e tests for management GUI). Mention Artillery load tests. Clarify stack-scoped vs system-level test distinction.
**Visual:** VHS terminal showing pytest + Newman output.

---

### 12 — Test-trace graph (refresh, was 11)

**What stays:** Neo4j graph model, trace ingestion, query-test-plan, blast radius 1/2, gap detection, focused test execution.
**What changes:** Minor polish. This is already one of the best segments.
**Visual:** Mixed (Manim BlastRadiusScene + VHS graph query terminal).

---

### 13 — Results DB (refresh, was 09)

**What stays:** Tekton Results + Postgres setup, verify-results script, auditability, GUI pipeline monitor.
**What changes:** Slight reorder in the series (was 09, now 13) to group testing/data together. Minor wording.
**Visual:** VHS terminal showing Results API queries.

---

### 14 — Customization (NEW)

**Story arc:**
1. Open — "tekton-dag is designed to be extended without forking. Every integration point is config-driven."
2. Stack schema — `stacks/schema.json` validates stack YAML, prevents typos
3. Add an app — new entry in `apps[]` with role, build tool, propagation-role, downstream, tests
4. Build variants — `compileImageVariants` in Helm for multiple Java/Node/Python/PHP versions
5. Hook tasks — `pre-build-task`, `post-build-task`, `pre-test-task`, `post-test-task` parameters; pipeline `when` skips if empty
6. Example hooks — image scan (`tasks/examples/example-image-scan.yaml`), Slack notification
7. New team onboarding — `teams/<name>/team.yaml` + `values.yaml` → Helm release
8. Registry and infrastructure — change image registry, switch intercept backend
9. Close — "Config-only onboarding. No pipeline forks."

**Visual:** Manim — new CustomizationScene showing schema → stack → hooks → team flow.

---

### 15 — Regression suite (REWRITE, was 12)

**Story arc:**
1. Open — "How do we know the platform itself works? Unit tests cover Python services. But a CI/CD platform needs cluster-level verification."
2. Phase 1 (no cluster) — stack YAML validation, registry wiring, pytest orchestrator + common + management-gui-backend
3. Phase 2 (with cluster) — port prep, `stack-dag-verify` PipelineRun, wait for Succeeded, Newman against live orchestrator
4. Optional Phase 2+ — Tekton Results verification, management GUI Playwright suite
5. The regression script — `run-regression-agent.sh`: iterates Phase 1 → Phase 2, exits 0 or non-zero
6. CI integration — agent loops until `regression exit code: 0`, reads failures, fixes, re-runs
7. Close — "Layered verification. No cluster? Phase one still catches regressions. Full cluster? Phase two proves the platform end to end."

**Visual:** VHS terminal showing actual regression run with Phase 1 pass, Phase 2 pass, exit code 0.

---

### 16 — Management GUI (REWRITE, was 13)

**Story arc:**
1. Open — "The management GUI is a Vue 3 single-page app. The browser never touches the Kubernetes API directly — every action goes through Flask."
2. Team switcher — select active team, all views filter to that team's namespace
3. DAG view — Vue Flow renders the stack graph, click a node to see app details
4. Pipeline runs — monitor active and completed runs, drill into TaskRun logs
5. Triggers — manual bootstrap, PR, or merge trigger from the UI
6. Test results — Newman/Playwright/Artillery results per run
7. Git browser — browse app repos from the GUI
8. Embedded Tekton Dashboard — iframe integration for deeper Tekton inspection
9. Architecture — Vue 3 + Vite frontend, Flask backend, Pinia stores, team-scoped API helpers
10. Testing — pytest backend, Playwright e2e (69 tests), Postman/Newman API tests
11. Close — "One web interface for the whole platform. Team-scoped, cluster-safe, fully tested."

**Visual:** Manim — new ManagementGUITourScene showing each view with transitions.

---

### 17 — Extending the GUI (REWRITE, was 14)

**Story arc:**
1. Open — "Adding a new operator surface — like TaskRun logs or Results views — follows a four-step pattern."
2. Step 1: Flask route — add a JSON endpoint wrapping the Kubernetes client; return stable response shapes
3. Step 2: pytest — mock the K8s client, test the route with the same pattern as existing tests
4. Step 3: Vue store — add a Pinia store using `useApiHelper` and `teamUrl` for team-scoped reads
5. Step 4: View + router — add a Vue component and router entry
6. Step 5: Playwright spec — e2e test the new view end to end
7. Concrete example — walk through adding a "TaskRun Logs" panel: Flask reads logs API → Vue displays in monospace → Playwright verifies
8. Close — "Five files, one pattern. The extension guide in the repo lists more ideas."

**Visual:** Manim — new GUIExtensionPatternScene showing the 5-step flow with code snippets.

---

### 18 — What's coming next (NEW)

**Story arc:**
1. Open — "tekton-dag handles the full lifecycle today: build, test, intercept, merge, release. Here is what we are building next to make it production-grade on real infrastructure."
2. Retry on transient failures — spot instance preemptions, registry throttling, DNS timeouts. Task-level `retries` on build/deploy tasks, but never on test tasks. Structured retry annotations for post-mortem.
3. Precise build image sizing — per-tool resource profiles (Maven needs heap, Node needs less), Helm-configurable `resources.*` values, stack-level overrides for large apps, Kaniko sizing separate from compile, monitoring baseline to inform decisions.
4. Multi-cluster push — today builds and deploys in one cluster. Next: push released images to remote registries (ECR, GCR, Harbor), promotion pipeline with environment gates (staging → production approval), cross-cluster deploy task, full audit trail in Tekton Results.
5. Operational reliability — explicit pipeline timeouts, graceful cleanup on timeout (finally block still runs), health-check gates before tests, Results DB backup, Neo4j persistence.
6. Observability — Prometheus metrics (build duration, retry count, queue time), alerting rules (failure rate, registry push failures), cost attribution labels per team/stack/app.
7. Close — "Infrastructure-grade reliability. Cost-aware sizing. Multi-environment promotion. That is milestone thirteen."

**Visual:** Manim — new RoadmapScene with a timeline/roadmap layout showing each pillar with icons.

---

## Concat groups

| Name | Segments | ~Duration |
|------|----------|-----------|
| `full-demo` | 01–13 | ~14 min |
| `full-demo-complete` | 01–18 | ~19 min |
| `platform-core` | 01–07 | ~8.5 min |
| `operations` | 08–09, 14–15 | ~5 min |
| `testing` | 11–13 | ~3.5 min |
| `gui` | 16–17 | ~2.5 min |
| `roadmap` | 18 | ~1.5 min |

---

## Visual asset inventory

### Existing Manim scenes (update)
- `StackDAGScene` (01) — add merge pipeline box, hook task annotation
- `InterceptRoutingScene` (05) — keep
- `LocalDebugScene` (06) — keep
- `MultiTeamScene` (09) — add ArgoCD mention
- `BlastRadiusScene` (12) — keep
- `RegressionSuiteScene` (15) — rewrite for Phase 1/2 flow

### New Manim scenes
- `MergeReleaseScene` (07) — version transform pipeline
- `BaggageMiddlewareScene` (10) — header flow through framework icons
- `CustomizationScene` (14) — schema → stack → hooks → team
- `ManagementGUITourScene` (16) — view panels with transitions
- `GUIExtensionPatternScene` (17) — 5-step code flow
- `RoadmapScene` (18) — timeline with M13 pillars: retry, sizing, multi-cluster, observability

### Existing VHS tapes (update)
- `02-quickstart.tape` — minor script name updates
- `03-bootstrap.tape` — keep
- `04-pr-pipeline.tape` — keep
- `07-orchestrator-api.tape` (now 08) — add reload/stats endpoints
- `09-results-db.tape` (now 13) — keep
- `10-newman.tape` (now 11) — add pytest/Playwright output
- `11-graph-tests.tape` (now 12) — keep

### New VHS tapes
- `15-regression.tape` — real regression-agent run showing Phase 1 + 2

---

## Decision: start fresh or refresh?

**Recommendation:** Refresh narration for 01–06, 08–09, 11–13 (they're already good — just align numbering and minor wording). **Write new** narration for 07, 10, 14, 18. **Rewrite** 15, 16, 17.

This avoids re-spending TTS budget on segments that are already strong while filling the real gaps.
