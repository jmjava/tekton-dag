# Evaluation evidence inventory

Workshop and tool-demo reviewers accept **functional** evidence if claims stay inside it. Research-track and SEIP reviewers will not. This inventory lists what already exists in-tree so the paper does not invent numbers.

**Short answer: no, the testing work is not “all done.”** There is a real, passing *local* unit/static suite. Cluster E2E, several language libraries, the operator, GitHub Actions coverage, and every comparative study a workshop PC might still ask for are incomplete or unenforced.

## What actually ran (this packaging branch)

On 2026-09-07, `bash scripts/run-regression-stream.sh --local-only` exited **0** in a laptop-style environment (`kubectl` not installed). That path is **Phase 1 + pytest + vitest only**. Playwright, Newman, `stack-dag-verify`, Tekton Results, and intercept E2E were **not** run.

| Suite | Collected / result |
|-------|-------------------|
| Phase 1 DAG (`verify-dag-phase1.sh`) | PASSED (stack-one, stack-two-vendor, single-app, single-flask-app) |
| pytest orchestrator | **105 passed** (README still says 62) |
| pytest `tekton-dag-common` | **47 passed** (README still says 14) |
| pytest management-gui backend | **61 passed** (README still says 56) |
| pytest baggage-python | **17 passed** |
| vitest baggage-node | **15 passed** |

`--local-only` **skips** Playwright on purpose. The 69 Playwright files are still in `management-gui/frontend/e2e/`; they were not executed here.

## What exists but is *not* in `run-regression.sh`

These tests are in the tree. The encompassing regression driver does **not** invoke them. GitHub Actions on this repo also does **not** run them (workflows are Pages deploy + a `docgen demo-function` smoke only).

| Suite | Approx. cases | How you run it today |
|-------|---------------|----------------------|
| JUnit `libs/baggage-spring-boot-starter` | 18 `@Test` | `mvn test` in that module |
| JUnit `libs/baggage-servlet-filter` | 13 `@Test` | `mvn test` in that module |
| PHPUnit `libs/baggage-php` | 19 methods | phpunit in that module |
| Go `operator/` unit | 4 `Test*` | `go test ./internal/...` |
| Go `operator/` e2e | present | needs a cluster |
| Playwright GUI | 69 `test(` | `npx playwright test` (regression default, **not** `--local-only`) |
| Newman orchestrator | collection grew past the README “15 requests / 30 assertions” | needs live orchestrator Service |
| Newman graph (M9) | ~10 requests in `tests/postman/graph-tests.json` | `--all` on orchestrator-tests script |
| Newman management GUI | optional | `--gui-newman` |
| `stack-dag-verify` PipelineRun | one real Tekton run | cluster + `--require-dag-verify` |
| Intercept E2E both backends | scripts exist | `run-e2e-with-intercepts.sh` |
| Sample **app-repo** tests (Newman/Playwright/Artillery in the six `tekton-dag-*` repos) | declared in stack YAML | only during `stack-pr-test`, not platform regression |

C2 (polyglot baggage) is therefore only **partially** regression-gated: Python and Node yes; Java and PHP no. C3 (intercept isolation) is **scripted**, not CI-gated. C4 (test-plan) has mocked pytest + a Postman collection; `milestones/milestone-9.md` still says **Planned** even though `query-test-plan` is wired in `stack-pr-pipeline.yaml`.

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

**How to report:** “In a controlled Kind deployment of the three-app exemplar, unmatched requests remained on the baseline replica; matched requests were stolen (5/5 each).” Cite the **script**, not a run from this Cloud Agent environment (no `kubectl` here).
**Do not report:** production latency, multi-tenant interference, or statistical significance. N=5 is a **smoke test**, not an experiment.

### Pipeline and resolver behavior (C1)

- Phase 1: `scripts/verify-dag-phase1.sh` — stack YAML, registry, `stack-graph.sh` without a cluster (**ran green** on this branch).
- Phase 2: `scripts/verify-dag-phase2.sh` — live `stack-dag-verify` PipelineRun vs. CLI resolution (**not run** without a cluster).
- Multiple stack files: three-tier, vendor, single-app, mixed-hop test stacks.

**How to report:** worked example + “resolver and pipeline agree on topo order / entry / chain” only if Phase 2 was run on the tagged commit.
**Do not report:** “arbitrary industry stacks” unless you add them.

### Propagation libraries (C2)

Unit tests exist for five ecosystems. Only Python + Node are in the default local regression. Java/PHP tests exist but are ungated. Integration via stack test stacks and `validate-stack-propagation` is a **pipeline** task, not a laptop pytest.

**How to report:** libraries exist; roles are encoded in YAML.
**Do not report:** “all five libraries are CI-verified on every commit.”

### Platform regression layers (C5)

From [`docs/TESTING-AND-REGRESSION-OVERVIEW.md`](../TESTING-AND-REGRESSION-OVERVIEW.md) and [`docs/REGRESSION.md`](../REGRESSION.md):

| Layer | Proves | Typical command | Gated on GitHub PR? |
|-------|--------|-----------------|---------------------|
| Static DAG | YAML graph consistency | `verify-dag-phase1.sh` | No |
| Python / Node unit | resolver, orchestrator, baggage (py/node) | pytest, vitest | No |
| GUI | operator workflows | Playwright | No |
| Orchestrator API | HTTP contracts | Newman | No |
| Live PipelineRun | `stack-dag-verify` Succeeded | `verify-dag-phase2.sh` | No |
| Results DB | persistence | `verify-results-in-db.sh` | No |

Update paper numbers from **`pytest` collection on the submission tag**, not from milestone tables.

### Demonstrations (C5 / demo track)

Eighteen composed segments + concat videos on [GitHub Pages](https://jmjava.github.io/tekton-dag/). These are **communication artifacts**, not experiments. The ICSE demo CFP requires a **3–5 minute** video with voice-over; use a cut of 01 + 04 + 05 (architecture, PR pipeline, intercept routing), not `full-demo-complete.mp4`.

### Test-trace graph (C4)

Code exists (`/api/test-plan`, `query-test-plan` task, Neo4j client, Postman graph collection). Evaluation today is **capability demonstration**. No precision/recall vs. full suite, no time-saved measurement. Do not treat M9 as a finished empirical result.

## What we cannot cite (gaps)

| Missing study **or** missing engineering gate | Why it matters | Minimum next step |
|-----------------------------------------------|----------------|-------------------|
| PR CI for `--local-only` regression | Reviewers will clone HEAD and assume tests run in Actions | Add a workflow that runs `run-regression.sh --local-only` |
| Java + PHP baggage in the driver | C2 is otherwise a documentation claim | `mvn test` / phpunit steps in regression |
| Operator `go test` in the driver | M14 is otherwise untested in the encompassing suite | `go test ./internal/...` |
| Cluster Phase 2 + intercept E2E on a tagged release | C1/C3 need a live PipelineRun | Kind job or recorded log from `run-regression-agent-full.sh` |
| Cost/time vs. namespace-per-PR | Central *research* claim of routing vs. cloning | Wall-clock and node-minutes, ≥3 repeats |
| Concurrent PRs | Multi-tenant intercepts | Two PRs, two headers, no cross-steal |
| Developer study | Demo “envisioned users” | Even n=3 think-aloud |
| Industrial case | SEIP | Named org |
| TIA comparison | C4 | Tests selected vs. full e2e |

Until the engineering gates exist, keep the paper in **tool / experience / exemplar** voice. Until the studies exist, do not promote the paper to SEIP or the research track.

## Threats to validity (pre-written for the paper)

**Construct.** “Isolation” is measured as HTTP routing, not as absence of shared-disk or shared-DB side effects. Sample apps are intentionally small.

**Internal.** PoC counts are small and operator-run (author is the experimenter). Kind + local registry is not a production control plane. Intercept tools require elevated capabilities; results may not transfer to locked-down clusters. Author-run `--local-only` does not substitute for cluster E2E.

**External.** Six first-party sample repos under one GitHub user are not an independent software ecosystem. Polyglot coverage is real (Vue, Spring, Flask, PHP) but all examples were written to fit the platform.

**Reliability.** Cluster E2E is timing-sensitive (image pulls, intercept attach). Report the **script** (`run-e2e-with-intercepts.sh`) rather than a single laptop run as the result.

## Carbon / sustainability (ICSE encourages a mention)

Kind-based evaluation is local. Demo video generation (TTS, Manim, ffmpeg) has a non-trivial cost if regenerated often; `docgen` is designed to regenerate only changed segments. A one-sentence acknowledgement is enough for a 4-page paper; do not invent kgCO2e numbers.
