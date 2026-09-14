# Milestone 17 — End-to-end quality and production-readiness closure

**Status:** In progress

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

## P0 — Security and execution truth

- [ ] **M17.1 Replace default `cluster-admin` pipeline RBAC**
  - Default Helm installs must use a documented least-privilege role.
  - `rbac.clusterAdmin=true` remains an explicit local-development escape hatch.
  - Acceptance: `helm template` assertions cover both defaults and opt-in
    cluster-admin; Phase 2, Newman, and intercept E2E pass with least privilege.

- [ ] **M17.2 Authenticate mutation APIs**
  - Protect orchestrator `/api/run`, `/api/bootstrap`, `/api/reload`, and graph
    ingestion, plus Management GUI trigger/approval routes.
  - Health/readiness and read-only APIs remain independently configurable.
  - Use constant-time bearer-token comparison, Secret-backed Helm wiring,
    deny-by-default production configuration, and negative-path tests.
  - Acceptance: pytest and Newman prove missing/invalid/valid credentials.

- [ ] **M17.3 Automate a real PR/intercept product path**
  - Scheduled/manual CI must cover webhook or trigger → StackRun → operator →
    PR PipelineRun → build → intercept route → app tests → cleanup.
  - Cover Telepresence and mirrord over an explicit cadence; neither may be
    described as continuously verified without current evidence.
  - Acceptance: artifacts retain PipelineRun/TaskRun logs and traffic evidence.

- [ ] **M17.4 Add scheduled Tekton Results verification**
  - Install Results/Postgres and run the strict Results DB verification.
  - Acceptance: `run-regression-agent-full.sh` equivalent exits zero and uploads
    diagnostic artifacts on failure.

## P1 — CI gates and operator assurance

- [ ] **M17.5 Activate operator CI from root `.github/workflows/`**
  - Run formatting/lint, unit tests, controller envtest, and domain E2E.
  - Pin Kind and action dependencies.
  - Acceptance: StackRun→PipelineRun creation, status, approval, idempotency,
    continuation, and invalid Stack admission are exercised.

- [ ] **M17.6 Add coverage gates**
  - Establish ratcheting thresholds for Python and Go production packages.
  - Initial floors must not exceed measured baselines:
    orchestrator 92%, GUI backend 91%, common 83%, baggage Python 88%,
    operator pipeline 80%, operator controller 32%.
  - Acceptance: CI fails when coverage drops below configured floors.

- [ ] **M17.7 Add static quality gates**
  - Python Ruff, Go lint/vet, ShellCheck, YAML/JSON parsing, frontend lint/build,
    and Helm package/template validation.
  - Resolve existing findings before making a gate required.
  - Acceptance: all gates run on relevant PR path changes and pass.

- [ ] **M17.8 Add supply-chain automation**
  - Dependabot/Renovate-equivalent updates for actions, npm, Go, Python, Maven,
    and Composer.
  - Add dependency and container scanning; remove known production dependency
    findings; pin CI tools and runtime images by version/digest where practical.
  - Acceptance: no unresolved critical/high production findings without an
    expiring, documented exception.

- [ ] **M17.9 Enforce demo validation**
  - Run `docgen validate --pre-push` in CI for demo-source changes.
  - Acceptance: A/V drift, narration lint, missing streams, and broken terminal
    recordings fail CI.

## P2 — Test-depth gaps

- [ ] **M17.10 Make Newman integration assertions authoritative**
  - Remove the nightly `--skip-integration` default or replace the warning-only
    wait with explicit success criteria.
  - Acceptance: CI fails if the expected StackRun/PipelineRun path does not
    reconcile and reach the declared checkpoint.

- [ ] **M17.11 Exercise optional graph and GUI API suites**
  - Run Neo4j graph Newman on a scheduled cadence and GUI Newman against a live
    backend.
  - Acceptance: both collections report zero failed assertions in CI.

- [ ] **M17.12 Test Helm and representation synchronization**
  - Test chart packaging/rendering, CRD copies, Stack YAML→CR conversion, and
    parameter compatibility across StackRun, operator builders, and Pipelines.
  - Acceptance: drift in any duplicated representation fails PR CI.

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

