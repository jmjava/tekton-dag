# Evaluation evidence inventory

Workshop and tool-demo reviewers accept **functional** evidence if claims stay inside it. Research-track and SEIP reviewers will not. This inventory lists what already exists in-tree so the paper does not invent numbers.

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

**How to report:** “In a controlled Kind deployment of the three-app exemplar, unmatched requests remained on the baseline replica; matched requests were stolen (5/5 each). Both intercept backends completed the PR pipeline E2E path.”  
**Do not report:** production latency, multi-tenant interference, or statistical significance. N=5 is a **smoke test**, not an experiment.

### Pipeline and resolver behavior (C1)

- Phase 1: `scripts/verify-dag-phase1.sh` — stack YAML, registry, `stack-graph.sh` without a cluster.
- Phase 2: `scripts/verify-dag-phase2.sh` — live `stack-dag-verify` PipelineRun vs. CLI resolution.
- Multiple stack files: three-tier, vendor, single-app, mixed-hop test stacks.

**How to report:** worked example + “resolver and pipeline agree on topo order / entry / chain.”  
**Do not report:** “arbitrary industry stacks” unless you add them.

### Propagation libraries (C2)

Unit tests under `libs/baggage-*`; integration via stack test stacks (`test-stack-flask-originator.yaml`, `test-stack-php-forwarder.yaml`, …) and `validate-stack-propagation`.

**How to report:** libraries exist for five ecosystems; roles are encoded in YAML; validation task checks the chain.  
**Do not report:** overhead in milliseconds unless measured.

### Platform regression layers (C5)

From [`docs/TESTING-AND-REGRESSION-OVERVIEW.md`](../TESTING-AND-REGRESSION-OVERVIEW.md) and [`docs/REGRESSION.md`](../REGRESSION.md):

| Layer | Proves | Typical command |
|-------|--------|-----------------|
| Static DAG | YAML graph consistency | `verify-dag-phase1.sh` |
| Python / Node unit | resolver, orchestrator, baggage | pytest, vitest |
| GUI | operator workflows | Playwright (`management-gui/frontend`) |
| Orchestrator API | HTTP contracts | Newman (`run-orchestrator-tests.sh`; README: 15 requests / 30 assertions) |
| Live PipelineRun | `stack-dag-verify` Succeeded | `verify-dag-phase2.sh` |
| Results DB | persistence | `verify-results-in-db.sh` |

README also records Management GUI as **69 Playwright E2E** and **56 pytest** (M11), orchestrator **62 pytest** and shared package **14** (M12). Re-run and **update the paper with the counts from the submission commit**; do not copy stale milestone numbers if they have drifted.

### Demonstrations (C5 / demo track)

Eighteen composed segments + concat videos on [GitHub Pages](https://jmjava.github.io/tekton-dag/). These are **communication artifacts**, not experiments. The ICSE demo CFP requires a **3–5 minute** video with voice-over; use a cut of 01 + 04 + 05 (architecture, PR pipeline, intercept routing), not `full-demo-complete.mp4`.

### Test-trace graph (C4)

Milestone 9 + demo segment 12 + orchestrator test-plan API. Evaluation today is **capability demonstration** (query returns a plan for `changed-app`). No precision/recall vs. full suite, no time-saved measurement.

**Paper treatment:** one paragraph + “planned study” language, or omit from a 4-page demo paper if space is tight.

## What we cannot cite (gaps)

| Missing study | Why reviewers ask | Minimum credible version |
|---------------|-------------------|--------------------------|
| Cost/time vs. namespace-per-PR | Central claim of routing vs. cloning | Wall-clock and node-minutes for stack-one: full clone vs. intercept-one-app, repeated ≥3 times, hardware described |
| Propagation completeness | C2 | Fault injection: drop baggage at forwarder, show validation fail; all five libraries on one path |
| Concurrent PRs | Multi-tenant intercepts | Two PRs, two headers, no cross-steal |
| Developer study | Demo “envisioned users” | Even n=3 think-aloud on the GUI or local-debug path helps a tool paper |
| Industrial case | SEIP | Named org, constraints, what broke, what shipped |
| TIA comparison | C4 | Tests selected vs. full e2e on a seeded change set |

Until those exist, keep the paper in **tool / experience / exemplar** voice.

## Threats to validity (pre-written for the paper)

**Construct.** “Isolation” is measured as HTTP routing to the intended replica, not as absence of shared-disk or shared-DB side effects. Sample apps are intentionally small.

**Internal.** PoC counts are small and operator-run (author is the experimenter). Kind + local registry is not a production control plane. Intercept tools require elevated capabilities; results may not transfer to locked-down clusters.

**External.** Six first-party sample repos under one GitHub user are not an independent software ecosystem. Polyglot coverage is real (Vue, Spring, Flask, PHP) but all examples were written to fit the platform.

**Reliability.** Cluster E2E is timing-sensitive (image pulls, intercept attach). Report the **script** (`run-e2e-with-intercepts.sh`) rather than a single laptop run as the result.

## Carbon / sustainability (ICSE encourages a mention)

Kind-based evaluation is local. Demo video generation (TTS, Manim, ffmpeg) has a non-trivial cost if regenerated often; `docgen` is designed to regenerate only changed segments. A one-sentence acknowledgement is enough for a 4-page paper; do not invent kgCO2e numbers.
