# PR / Telepresence Intercept — Setup Confirmation

**Date:** 2026-03-04  
**Repository:** tekton-dag  
**Pipeline:** `stack-pr-test` (`pipeline/stack-pr-pipeline.yaml`)

---

## 1. PR Code Runs Alongside Original Services — Not Replacing Them

The PR pipeline deploys a **separate Pod** for the changed app. The original
Deployment and Service remain running and continue to serve all normal traffic.

### How it works

| Component | Behavior during PR test |
|-----------|------------------------|
| **Original service** | Untouched. Continues running and serving non-PR traffic. |
| **PR pod** | Created as a standalone Pod with labels `app: pr-test`, `component: <app>`, `managed-by: tekton-job-standardization`. |
| **Telepresence intercept** | Routes **only** requests carrying the PR header (e.g. `x-dev-session:pr-42`) to the PR pod. All other traffic goes to the original service. |
| **After tests** | PR pod is removed by the `cleanup-stack-pods` finally task. Original service is never modified. |

### Concrete example

For a stack **A → B → C → D** where **C** changed in the PR:

- **A, B, D** — normal deployed services, untouched
- **C** — Telepresence intercepts the existing C service so that requests
  carrying the PR's baggage header get routed to the PR pod running the new C build
- The e2e test enters through **A** with the header; **B** forwards it to **C**
  (intercepted → PR pod); **C** forwards to **D** normally
- All other traffic to **C** (without the header) continues to the original C deployment

### Key configuration

- **Intercept header:** `x-dev-session:pr-<number>` (configurable via stack `propagation.header-name`)
- **Intercept command:** `telepresence intercept <app> --namespace <ns> --port <container>:<service> --http-match <header>`
- **PR pod naming:** `pr-<app>-<timestamp>`
- **Telepresence image:** `ghcr.io/telepresenceio/tel2:2.20.0`

### Source references

| File | What it confirms |
|------|------------------|
| `tasks/deploy-intercept.yaml` (lines 9–23) | PR pods are additive; original services are untouched |
| `pipeline/stack-pr-pipeline.yaml` (lines 9–13) | Pipeline uses currently running apps; only changed app is built |
| `tasks/deploy-intercept.yaml` (lines 193–227) | PR pod spec with distinct labels, separate from original Deployment |
| `tasks/cleanup-stack.yaml` | PR pods are removed in `finally` block |

---

## 2. Valid Tests Exist for the Telepresence Intercept

The pipeline executes three layers of testing after intercepts are deployed.

### Layer 1 — Propagation Validation

**Task:** `validate-stack-propagation` (`tasks/validate-propagation.yaml`)

Sends a request through the entry app with the intercept header and verifies
hop-by-hop that the header reaches the intercepted app(s). Confirms the
Telepresence routing is active and the baggage chain is intact.

- Validates header propagation from entry point **up to** the intercepted app
- Understands propagation roles: originator sets, forwarder passes through, terminal receives
- Accounts for multi-intercept scenarios (header must continue past forwarders when another intercept is downstream)

### Layer 2 — End-to-End Through Entry Point

**Task:** `run-stack-tests` (`tasks/run-stack-tests.yaml`) — Phase 1

Sends requests through the stack's entry app (frontend) with the intercept
header attached. This exercises the **full chain** including the PR build.

- Request enters at A, flows through the chain, hits the PR build via Telepresence
- Proves the PR app works correctly in the context of the full stack
- Uses Artillery load test template with intercept headers pre-configured

### Layer 3 — Per-App Test Suites

**Task:** `run-stack-tests` (`tasks/run-stack-tests.yaml`) — Phase 2

Runs each app's configured test suites with the intercept header:

| Test type | Tool | Purpose |
|-----------|------|---------|
| API tests | Postman / Newman | Functional API validation |
| UI tests | Playwright | Browser-based UI testing |
| Load tests | Artillery | Performance under load |

- For **intercepted apps**: validates the PR build directly
- For **non-intercepted apps**: validates they still work correctly with the header present

### Test execution order in pipeline

```
deploy-intercepts
      │
      ▼
validate-propagation    ← Header reaches intercepted app(s)?
      │
      ▼
run-tests               ← E2E + per-app suites with intercept header
      │
      ▼
finally:
  ├── cleanup           ← Remove PR pods
  └── post-pr-comment   ← Report results on GitHub PR
```

### Source references

| File | What it confirms |
|------|------------------|
| `tasks/validate-propagation.yaml` | Propagation validation logic and scenarios |
| `tasks/run-stack-tests.yaml` | Two-phase test execution (E2E + per-app) |
| `tests/artillery/entry-e2e.yml` | Artillery template with `x-dev-session` and `baggage` headers |
| `pipeline/stack-pr-pipeline.yaml` (lines 306–341) | Pipeline wiring: validate → test → cleanup |

---

## 3. Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| PR code does **not** replace the original service | **Confirmed** | Separate Pod with distinct labels; Telepresence header-based routing; original Deployment untouched |
| PR code runs **alongside** the original service | **Confirmed** | Both original Deployment and PR Pod serve traffic simultaneously; header determines routing |
| Original service continues serving non-PR traffic | **Confirmed** | Only requests with `x-dev-session:pr-<N>` route to PR pod |
| Valid tests exist for the intercept | **Confirmed** | Three-layer testing: propagation validation, E2E through entry, per-app suites |
| Tests use the intercept header | **Confirmed** | All test phases inject `x-dev-session` and `baggage` headers |
| PR pods are cleaned up after tests | **Confirmed** | `cleanup-stack-pods` runs in pipeline `finally` block |

---

## 4. Milestone 5: Original Traffic Validation and MetalBear Evaluation

Milestone 5 ([milestones/milestone-5.md](milestones/milestone-5.md)) adds two areas of work:

### 4.1 Original traffic validation (implemented)

A new pipeline task `validate-original-traffic` sends requests to every service
**without any intercept headers** while Telepresence intercepts are active. This
explicitly proves that the original deployments continue to serve normal traffic
during the PR test window.

Three validation phases:

| Phase | What it does |
|-------|-------------|
| Direct health check | `curl` each service without headers — must get HTTP 2xx/3xx |
| Entry-point passthrough | Request through the full chain without headers — must reach all original deployments |
| Artillery load burst | 10-second burst at 5 req/s without headers — must maintain < 10% error rate |

The task runs **in parallel** with `validate-propagation` (no additional pipeline
duration) and both must pass before `run-tests` begins.

| File | Purpose |
|------|---------|
| `tasks/validate-original-traffic.yaml` | Tekton task with 3-phase validation |
| `tests/artillery/original-traffic-e2e.yml` | Standalone Artillery config for local testing |
| `pipeline/stack-pr-pipeline.yaml` | Pipeline wiring (parallel validation) |

### 4.2 MetalBear (mirrord) evaluation (planned)

Evaluate [mirrord](https://mirrord.dev/) as an alternative to Telepresence for
header-based traffic interception in the PR pipeline. Key evaluation areas:

- Header-based intercept parity with `--http-header-filter`
- In-cluster execution feasibility (Tekton pod → mirrord → target service)
- Reduced cluster footprint (no persistent Traffic Manager)
- Traffic mirroring capability for shadow/comparison testing

See [milestones/milestone-5.md](milestones/milestone-5.md) for full PoC tasks
and decision criteria.
