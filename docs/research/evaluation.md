# Evaluation evidence inventory

Workshop and tool-demo reviewers accept **functional** evidence if claims stay inside it. Research-track and SEIP reviewers will not. This inventory lists what already exists in-tree so the paper does not invent numbers.

**Short answer: no, the testing work is not “all done.”** There is a real, passing *local* unit/static suite, now **gated on GitHub PRs**. This Cloud Agent Kind cluster ran isolation-eval, Phase 2, and Newman. Intercept E2E (S34) and GitHub `cluster-regression` artifacts have not. Comparative studies a research PC would ask for remain incomplete.

## What actually ran (this packaging branch)

On 2026-09-07, `bash scripts/run-regression-stream.sh --local-only --require-lang-tests` is the CI path (Phase 1 + pytest + vitest + isolation-eval protocol + Maven + PHPUnit + operator `go test`). Playwright later ran locally (**69 passed**, Vite only). Nested Docker + Kind:

- `run-isolation-eval.sh --cluster`: **6/6** `isolation_ok=true` (dummy echo stacks; after `kubectl wait` race fix).
- `stack-dag-verify` Phase 2: **Succeeded**.
- Newman vs in-cluster orchestrator: **18 requests / 36 assertions, 0 failed** (`run-cluster-ci.sh --skip-isolation --skip-phase2` after S39; `kind load` warned overlayfs on this nested VM, image came from `localhost:5000`).
- Operator Kind soak (`STACKRUN_VIA_CRD=true`): **18/18 Newman**; **6/6** StackRuns received a `status.pipelineRunName` and a PipelineRun labeled `tektondag.io/stackrun` (bootstrap ×2, pr ×2, merge, promote). Some PipelineRuns then hit Tekton `CouldntGetTask` / `ResolvingTaskRef` (task catalog on this cluster, not operator create). `scripts/install-operator-kind.sh` + `WAIT_STACKRUN_RECONCILE=1`.
- Intercept E2E (S34) was **not** run. GitHub `cluster-regression` was **not** dispatched (no Actions artifact).

| Suite | Collected / result |
|-------|-------------------|
| Phase 1 DAG (`verify-dag-phase1.sh`) | PASSED (stack-one, stack-two-vendor, single-app, single-flask-app) |
| pytest orchestrator | **105 passed** (README still says 62) |
| pytest `tekton-dag-common` | **47 passed** (README still says 14) |
| pytest management-gui backend | **61 passed** (README still says 56) |
| pytest baggage-python | **17 passed** |
| pytest isolation-eval | **10 passed** |
| vitest baggage-node | **15 passed** |
| PHPUnit baggage-php | **19 passed** |
| Maven Java baggage | both modules OK (`--require-lang-tests`) |
| operator `go test` | `internal/pipeline` + `internal/controller` OK |

`--local-only` **skips** Playwright on purpose. This environment ran `npx playwright test` in `management-gui/frontend`: **69 passed** (Vite only, no cluster). Kind isolation-eval **6/6**, Phase 2 **Succeeded**, Newman **18/18 requests**, operator soak **6/6** StackRun→PipelineRun. S34 intercept E2E was not run.

## What exists but is *not* CI-gated on every PR

`--local-only --require-lang-tests` **does** run on pull requests ([`.github/workflows/local-regression.yml`](../../.github/workflows/local-regression.yml)). The suites below are **not** on PRs; they run on [`.github/workflows/cluster-regression.yml`](../../.github/workflows/cluster-regression.yml) (nightly / dispatch / tags) unless noted.

| Suite | Approx. cases | How you run it today |
|-------|---------------|----------------------|
| Go `operator/` e2e | present | Kind soak via `run-cluster-ci.sh --with-operator` (opt-in; not default cluster-regression) |
| Playwright GUI | 69 `test(` | cluster-regression Playwright job; `npx playwright test` locally |
| Newman orchestrator | collection grew past the README “15 requests / 30 assertions” | `run-cluster-ci.sh` (live orchestrator Service) |
| Newman graph (M9) | ~10 requests in `tests/postman/graph-tests.json` | `run-cluster-ci.sh --with-graph` |
| Newman management GUI | optional | `--gui-newman` (not in cluster-regression) |
| `stack-dag-verify` PipelineRun | one real Tekton run | `run-cluster-ci.sh` / `--require-dag-verify` |
| Intercept E2E both backends | scripts exist | S34: `run-e2e-with-intercepts.sh` |
| Kind clone-vs-intercept **measurements** | CSV rows | `run-cluster-ci.sh` / `run-isolation-eval.sh --cluster` |
| Sample **app-repo** tests (Newman/Playwright/Artillery in the six `tekton-dag-*` repos) | declared in stack YAML | only during `stack-pr-test`, not platform regression |

C2 (polyglot baggage **unit** tests) is PR-gated for Python, Node, Java, and PHP. In-cluster hop validation (`validate-stack-propagation`) remains a pipeline task. C3 isolation **probes on Kind** run in cluster-regression (dummy HTTP stacks, not Telepresence). C4 (test-plan) has mocked pytest + a Postman collection; `milestones/milestone-9.md` still says **Planned** even though `query-test-plan` is wired in `stack-pr-pipeline.yaml`.

## What we can cite today (with location)

### Functional correctness of intercept isolation (C3)

[`docs/mirrord-poc-results.md`](../mirrord-poc-results.md) §2.3, stack-one `release-lifecycle-demo` in `staging`:

| Traffic | Expected pod | Result |
|---------|--------------|--------|
| No `x-dev-session` header (5 rounds) | baseline `tekton-dag-spring-boot` | 5/5 |
| `x-dev-session: pr-test` (5 rounds) | intercept / local PR process | 5/5 |

Same header-filter idea is documented as parity with Telepresence `--http-match`. E2E scripts exist for **both** backends:

```bash
./scripts/run-e2e-with-intercepts.sh --intercept-backend telepresence
./scripts/run-e2e-with-intercepts.sh --intercept-backend mirrord
```

**How to report:** “In a controlled Kind deployment of the three-app exemplar, unmatched requests remained on the baseline replica; matched requests were stolen (5/5 each).” Cite [`docs/mirrord-poc-results.md`](../mirrord-poc-results.md) for that smoke, and `run-isolation-eval.sh --cluster` for dummy-stack probes (this Cloud Agent: 6/6 `isolation_ok`). Neither is a site measurement (S21).
**Do not report:** production latency, multi-tenant interference, or statistical significance. N=5 is a **smoke test**, not an experiment.

### Pipeline and resolver behavior (C1)

- Phase 1: `scripts/verify-dag-phase1.sh` — stack YAML, registry, `stack-graph.sh` without a cluster (**ran green** on this branch).
- Phase 2: `scripts/verify-dag-phase2.sh` — live `stack-dag-verify` PipelineRun vs. CLI resolution (**not run** without a cluster).
- Multiple stack files: three-tier, vendor, single-app, mixed-hop test stacks.

**How to report:** worked example + “resolver and pipeline agree on topo order / entry / chain” only if Phase 2 was run on the tagged commit.
**Do not report:** “arbitrary industry stacks” unless you add them.

### Propagation libraries (C2)

Unit tests exist for Python, Node, Java (Spring starter + servlet filter), and PHP. Those unit tests run on every PR via `--require-lang-tests`. Integration via stack test stacks and `validate-stack-propagation` is a **pipeline** task, not a laptop pytest.

**How to report:** libraries exist; unit tests are CI-gated; roles are encoded in YAML.
**Do not report:** “every hop was validated in-cluster on every commit.”

### Platform regression layers (C5)

From [`docs/TESTING-AND-REGRESSION-OVERVIEW.md`](../TESTING-AND-REGRESSION-OVERVIEW.md) and [`docs/REGRESSION.md`](../REGRESSION.md):

| Layer | Proves | Typical command | Gated where? |
|-------|--------|-----------------|--------------|
| Static DAG | YAML graph consistency | `verify-dag-phase1.sh` | PR (`local-regression.yml`) |
| Python / Node unit | resolver, orchestrator, baggage (py/node), isolation-eval protocol | pytest, vitest | PR |
| Java / PHP / operator | baggage JUnit, PHPUnit, `go test ./internal/... ./api/...` | `run-lang-unit-tests.sh` | PR (`--require-lang-tests`) |
| GUI | operator workflows | Playwright | Nightly/dispatch/tags (`cluster-regression.yml`), **not** PRs |
| Orchestrator API | HTTP contracts | Newman | Nightly/dispatch/tags (`run-cluster-ci.sh`) |
| Live PipelineRun | `stack-dag-verify` Succeeded | `verify-dag-phase2.sh` | Nightly/dispatch/tags |
| Results DB | persistence | `verify-results-in-db.sh` | No (optional `--with-results-verify`) |
| Clone vs intercept (Kind) | dummy-stack isolation + pod counts | `run-isolation-eval.sh --cluster` | Nightly/dispatch/tags (offline plan still on PRs) |

Update paper numbers from **`pytest` collection on the submission tag**, not from milestone tables.

### Demonstrations (C5 / demo track)

Eighteen composed segments + concat videos on [GitHub Pages](https://jmjava.github.io/tekton-dag/). These are **communication artifacts**, not experiments. The ICSE demo CFP requires a **3–5 minute** video with voice-over; use a cut of 01 + 04 + 05 (architecture, PR pipeline, intercept routing), not `full-demo-complete.mp4`.

### Test-trace graph (C4)

Code exists (`/api/test-plan`, `query-test-plan` task, Neo4j client, Postman graph collection). Evaluation today is **capability demonstration**. No precision/recall vs. full suite, no time-saved measurement. Do not treat M9 as a finished empirical result.

## What we cannot cite (gaps)

| Missing study **or** missing engineering gate | Why it matters | Minimum next step |
|-----------------------------------------------|----------------|-------------------|
| Recorded cluster-regression log on a tag | C1/C3 need a live PipelineRun **artifact**, not only a workflow file | `workflow_dispatch` on [cluster-regression.yml](../../.github/workflows/cluster-regression.yml) or push a `v*` tag after merge |
| Intercept E2E both backends | C3 beyond dummy-stack probes | S34: `run-e2e-with-intercepts.sh` on a chosen tag |
| Cost/time vs. namespace-per-PR (**measured**, ≥3 repeats) | Central *research* claim of routing vs. cloning | Dispatch cluster CI with `isolation_repeats=3`; cite the artifact CSV, not the plan |
| Concurrent PRs | Multi-tenant intercepts | Two PRs, two headers, no cross-steal |
| Developer study | Demo “envisioned users” | Even n=3 think-aloud |
| Industrial case | SEIP | Named org |
| TIA comparison | C4 | Tests selected vs. full e2e |

Until cluster E2E and the *studies* exist, keep the paper in **tool / experience / exemplar** voice. Do not promote it to SEIP or the research track.

## Threats to validity (pre-written for the paper)

**Construct.** “Isolation” is measured as HTTP routing, not as absence of shared-disk or shared-DB side effects. Sample apps are intentionally small.

**Internal.** PoC counts are small and operator-run (author is the experimenter). Kind + local registry is not a production control plane. Intercept tools require elevated capabilities; results may not transfer to locked-down clusters. Author-run `--local-only` does not substitute for cluster E2E.

**External.** Six first-party sample repos under one GitHub user are not an independent software ecosystem. Polyglot coverage is real (Vue, Spring, Flask, PHP) but all examples were written to fit the platform.

**Reliability.** Cluster E2E is timing-sensitive (image pulls, intercept attach). Report the **script** (`run-e2e-with-intercepts.sh`) rather than a single laptop run as the result.

## Carbon / sustainability (ICSE encourages a mention)

Kind-based evaluation is local. Demo video generation (TTS, Manim, ffmpeg) has a non-trivial cost if regenerated often; `docgen` is designed to regenerate only changed segments. A one-sentence acknowledgement is enough for a 4-page paper; do not invent kgCO2e numbers.
