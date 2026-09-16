# Milestone 17 — End-to-end quality and production-readiness closure

**Status:** In progress after M17.12; next is M17.13 stack test runners

This milestone converts the September 2026 end-to-end audit into an executable
backlog. Work is ordered by production risk, not by subsystem. A checkbox is
closed only when its acceptance evidence has been run and recorded below.

## Iteration protocol

For each slice:

1. Select the highest-priority unchecked item whose dependencies are complete.
2. Implement the smallest coherent change.
3. Add or update automated tests and documentation in the same slice.
4. Run the narrow checks listed on the item.
5. Run `bash scripts/run-regression-agent.sh`.
6. For cluster-affecting changes, run or obtain a green
   `cluster-regression` result; use the strict/Results variants where specified.
7. Record evidence in the table and check the item off.

The milestone is complete only when every P0–P3 item is checked and the final
regression criteria in `docs/AGENT-REGRESSION.md` are satisfied.

## Resume checkpoint — 2026-09-16

- Completed with recorded acceptance: M17.1–M17.12.
- Still open: M17.13–M17.21.
- M17.4 live Results run `35108434664` on [PR #63](https://github.com/jmjava/tekton-dag/pull/63) exited 0 after the Java 21 toolchain fix.
- M17.11 live graph + GUI Newman run `35109309784` on [PR #65](https://github.com/jmjava/tekton-dag/pull/65) reported zero failed assertions.
- M17.12 live static-quality run `35111800721` on [PR #67](https://github.com/jmjava/tekton-dag/pull/67) passed Ruff, Go lint/vet, ShellCheck, both frontend builds, Helm package/render, and representation sync.
- Continue in numeric order from M17.13. Do not skip directly to
  maintainability work because M17.13–M17.14 establish the test evidence needed
  to refactor safely.
- Before starting a slice, fetch the latest `cursor/close-e2e-audit-gaps-fc5f` and
  create a fresh `cursor/<slice>-fc5f` branch. Do not reuse merged slice
  branches.

| Resume order | Work | Terminal condition |
|---|---|---|
| 1 | M17.13–M17.14 test depth | Runner branches and compatibility matrix enforced |
| 2 | M17.15–M17.19 maintainability | Duplication, ownership, legacy surface, errors, and config contracts consolidated behind green tests |
| 3 | M17.20–M17.21 docs/release | Canonical docs, governance, and reproducible release automation complete |
| 4 | Final verification | Full prescribed regression satisfies `docs/AGENT-REGRESSION.md` |

## P0 — Security and execution truth

- [x] **M17.1 Replace default `cluster-admin` pipeline RBAC**
  - Default Helm installs must use a documented least-privilege role.
  - `rbac.clusterAdmin=true` remains an explicit local-development escape hatch.
  - Acceptance: `helm template` assertions cover both defaults and opt-in
    cluster-admin; Phase 2, Newman, and intercept E2E pass with least privilege.

- [x] **M17.2 Authenticate mutation APIs**
  - Protect orchestrator `/api/run`, `/api/bootstrap`, `/api/reload`, and graph
    ingestion, plus Management GUI trigger/approval routes.
  - Health/readiness and read-only APIs remain independently configurable.
  - Use constant-time bearer-token comparison, Secret-backed Helm wiring,
    deny-by-default production configuration, and negative-path tests.
  - Acceptance: pytest and Newman prove missing/invalid/valid credentials.

- [x] **M17.3 Automate a real PR/intercept product path**
  - Scheduled/manual CI must cover webhook or trigger → StackRun → operator →
    PR PipelineRun → build → intercept route → app tests → cleanup.
  - Cover Telepresence and mirrord over an explicit cadence; neither may be
    described as continuously verified without current evidence.
  - Acceptance: artifacts retain PipelineRun/TaskRun logs and traffic evidence.

- [x] **M17.4 Add scheduled Tekton Results verification**
  - Install Results/Postgres and run the strict Results DB verification.
  - Acceptance: `run-regression-agent-full.sh` equivalent exits zero and uploads
    diagnostic artifacts on failure.
  - Evidence: run `35108434664` installed Java 21, compiled both Maven modules,
    passed Phase 2 and Newman, verified Results, and exited 0.

## P1 — CI gates and operator assurance

- [x] **M17.5 Activate operator CI from root `.github/workflows/`**
  - Run formatting/lint, unit tests, controller envtest, and domain E2E.
  - Pin Kind and action dependencies.
  - Acceptance: StackRun→PipelineRun creation, status, approval, idempotency,
    continuation, and invalid Stack admission are exercised.

- [x] **M17.6 Add coverage gates**
  - Establish ratcheting thresholds for Python and Go production packages.
  - Initial floors must not exceed measured baselines:
    orchestrator 92%, GUI backend 91%, common 83%, baggage Python 88%,
    operator pipeline 80%, operator controller 32%.
  - Acceptance: CI fails when coverage drops below configured floors.
  - Evidence: PR coverage measured 97.18%, 92.26%, 83.45%, and 88.14%
    for the Python packages and 80.0%/32.6% for operator pipeline/controller;
    local regression run `34909065149` and operator run `34909065137` passed.

- [x] **M17.7 Add static quality gates**
  - Python Ruff, Go lint/vet, ShellCheck, YAML/JSON parsing, frontend lint/build,
    and Helm package/template validation.
  - Resolve existing findings before making a gate required.
  - Acceptance: all gates run on relevant PR path changes and pass.
  - Evidence: static-quality run `34915661601` passed Ruff, Go lint/vet,
    ShellCheck, actionlint, strict YAML/JSON parsing, both frontend lint/build
    matrices, and staged/package Helm renders.

- [x] **M17.8 Add supply-chain automation**
  - Dependabot/Renovate-equivalent updates for actions, npm, Go, Python, Maven,
    and Composer.
  - Add dependency and container scanning; remove known production dependency
    findings; pin CI tools and runtime images by version/digest where practical.
  - Acceptance: no unresolved critical/high production findings without an
    expiring, documented exception.
  - Evidence: supply-chain run `34974127479` passed filesystem/secret scanning
    and all three production image gates after the M17.8 hotfix.

- [x] **M17.9 Enforce demo validation**
  - Run `docgen validate --pre-push` in CI for demo-source changes.
  - Acceptance: A/V drift, narration lint, missing streams, and broken terminal
    recordings fail CI.
  - Evidence: demo-validation run `34975666059` fetched committed Git LFS
    recordings and passed stream, A/V drift, narration, and OCR validation.

## P2 — Test-depth gaps

- [x] **M17.10 Make Newman integration assertions authoritative**
  - Remove the nightly `--skip-integration` default or replace the warning-only
    wait with explicit success criteria.
  - Acceptance: CI fails if the expected StackRun/PipelineRun path does not
    reconcile and reach the declared checkpoint.
  - Evidence: cluster-regression run `34989095946` passed the current-run
    StackRun reconciliation gate and required bootstrap `fetch-source`
    execution checkpoint.

- [x] **M17.11 Exercise optional graph and GUI API suites**
  - Run Neo4j graph Newman on a scheduled cadence and GUI Newman against a live
    backend.
  - Acceptance: both collections report zero failed assertions in CI.
  - Evidence: run `35109309784` passed GUI Newman (54 assertions) and graph
    Newman (38 + 36 assertions) with zero failures.

- [x] **M17.12 Test Helm and representation synchronization**
  - Test chart packaging/rendering, CRD copies, Stack YAML→CR conversion, and
    parameter compatibility across StackRun, operator builders, and Pipelines.
  - Acceptance: drift in any duplicated representation fails PR CI.
  - Evidence: run `35111800721` passed representation sync plus the rest of
    static-quality after the Ruff import-order hotfix.

- [ ] **M17.13 Test embedded Task shell and stack test runners**
  - Add shell-level fixtures for malformed input and exercise Newman,
    Playwright, and Artillery branches of `run-stack-tests`.
  - Acceptance: each supported runner has success and failure-path coverage.

- [ ] **M17.14 Expand compatibility coverage**
  - Test supported Python, Node, Java, PHP, and Kubernetes/Tekton versions at an
    intentional cadence.
  - Acceptance: documented support matrix exactly matches automated jobs.

## P3 — Maintainability and documentation

- [ ] **M17.15 Consolidate duplicated Python control-plane helpers**
  - Share Kubernetes client primitives and resolver behavior without coupling
    the GUI to orchestrator internals.
  - Acceptance: one tested implementation per shared behavior.

- [ ] **M17.16 Establish one PipelineRun contract owner**
  - Make the Go operator builder canonical; retain Python only as an explicitly
    generated/test oracle or remove it.
  - Acceptance: parameter/schema changes require one implementation edit and
    generated contract checks.

- [ ] **M17.17 Remove or archive the legacy Reporting GUI**
  - Eliminate production dependency exposure and onboarding ambiguity.
  - Acceptance: canonical docs and scripts reference only `management-gui/`.

- [ ] **M17.18 Reduce complexity and error ambiguity**
  - Split the orchestrator route registry, replace broad exception catches with
    typed errors, and split regression tier orchestration into focused scripts.
  - Acceptance: no Ruff violations in production Python and documented stable
    HTTP error contracts.

- [ ] **M17.19 Unify configuration contracts**
  - Document and validate environment, Helm, Team, Stack, and regression
    settings from a machine-readable source where feasible.
  - Acceptance: invalid values fail before creating cluster resources.

- [ ] **M17.20 Correct canonical documentation**
  - StackRun-first API/C4 text, current test/Newman/segment counts, Pages paths,
    M13–M16 index entries, release process, and internal links.
  - Generate volatile counts rather than maintaining them manually.
  - Acceptance: link checker and documentation consistency checks pass in CI.

- [ ] **M17.21 Add project governance and release automation**
  - Add contributing/security/ownership guidance and a reproducible release
    workflow with chart/image provenance.
  - Acceptance: a version tag produces immutable, scanned artifacts and a
    documented rollback path.

## Completion evidence

| Date | Slice | Evidence | Result |
|------|-------|----------|--------|
| 2026-09-14 | Audit baseline | Local regression; Playwright; Go test/vet; coverage; latest cluster CI | Recorded |
| 2026-09-14 | M17.2 mutation API authentication | Shared constant-time bearer check; 108 orchestrator, 68 GUI backend, and 61 common tests; frontend build; local regression exit 0 | Local green; Helm rendering and live-cluster Newman pending because this runner has no Helm or kubectl |
| 2026-09-14 | M17.3 intercept product automation | Weekly/manual Telepresence + mirrord matrix; authenticated trigger-to-StackRun runner; public HTTPS clone fallback; retained traffic diagnostics | Live run 34890630726 passed both trigger-to-traffic jobs and retained backend-specific evidence artifacts |
| 2026-09-14 | M17.4 strict Results automation | Weekly/manual pinned Results v0.20.0 + ephemeral Postgres workflow; fail-closed installers; failure diagnostics; 2 static acceptance tests; local regression exit 0 | Automation green locally; first live strict workflow run still required |
| 2026-09-14 | M17.2 mutation authentication acceptance | Strict Kind run 34874792600; least-privilege RBAC; Phase 2 passed; Newman missing/invalid/valid bearer paths; 38 assertions | Passed, zero Newman failures |
| 2026-09-14 | M17.5 operator CI acceptance | Root operator workflow; lint, unit, envtest, generated-file checks; Kind StackRun domain E2E | Passed in PR #42 |
| 2026-09-14 | M17.1 least-privilege RBAC acceptance | Helm default/opt-in assertions; strict Kind run 34883804213 passed Phase 2 and Newman; intercept run 34890630726 passed Telepresence and mirrord | Passed without pipeline `cluster-admin` |
| 2026-09-15 | M17.6 coverage gates | Python and Go ratcheting floors; focused production-package tests | Local regression and operator CI passed at recorded baselines |
| 2026-09-15 | M17.7 static quality | Ruff, Go lint/vet, ShellCheck, actionlint, structured data, frontend, and Helm gates | Run 34915661601 passed |
| 2026-09-15 | M17.8 supply chain | Dependabot coverage; filesystem, secret, and production image scanning; dependency remediation | Run 34974127479 passed all production scan gates |
| 2026-09-15 | M17.9 demo validation | Git LFS recordings; stream, A/V drift, narration, and OCR checks | Run 34975666059 passed |
| 2026-09-15 | M17.10 Newman execution truth | Current-run StackRun reconciliation and bootstrap fetch-source checkpoint | Run 34989095946 passed; final PR revision passed all checks |
| 2026-09-15 | Pause checkpoint | Completed M17.1–M17.3 and M17.5–M17.10; open M17.4 and M17.11–M17.21 | Resume instructions recorded above |
| 2026-09-16 | M17.4 Results live acceptance | Java 21 toolchain; Phase 2; Newman; Results DB | Run 35108434664 passed |
| 2026-09-16 | M17.11 graph and GUI Newman | Live Flask GUI collection; Kind Neo4j graph collection | Run 35109309784 passed, zero assertion failures |
| 2026-09-16 | M17.12 representation sync acceptance | CRD copy, Stack/Team conversion, PipelineRun param drift, and static-quality | Run 35111800721 passed |
| 2026-09-16 | M17.13 stack test runner fixtures | Extracted `run-stack-tests` Newman/Playwright/Artillery runners; malformed JSON plus success/failure fixtures | Automation added; first live local-regression run still required |

