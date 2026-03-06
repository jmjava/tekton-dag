# Milestone 5: Original traffic validation during intercepts and MetalBear (mirrord) evaluation

> **Complete.** Section 1 (original traffic validation) implemented. Section 2 (mirrord PoC) proven; **recommendation: go with mirrord** for lower environment (multiple intercepts without overlap, free cost, production separate cluster) — see [docs/mirrord-poc-results.md](../docs/mirrord-poc-results.md).

## 1. Original traffic validation while intercepts are active

### Problem

Milestones 1–4 validate that **intercepted traffic** (requests carrying the `x-dev-session` header) correctly reaches the PR pod via Telepresence. However, there is no explicit test proving that **original traffic** — requests without the header — continues to be served by the original deployments during the same window.

The design guarantees this (Telepresence uses header-based matching, so bare requests bypass the intercept), but a guarantee without a test is an assumption. If a Telepresence upgrade, a misconfigured Traffic Manager, or a Kubernetes networking change broke the header-match isolation, the original service could be disrupted during every PR pipeline run.

### Goal

Add a dedicated pipeline task that sends traffic to every service in the stack **without any intercept headers** while Telepresence intercepts are active, and fails the pipeline if any original deployment is unreachable or returns errors.

### Implementation

#### 1.1 New task: `validate-original-traffic`

**File:** `tasks/validate-original-traffic.yaml`

Three validation phases:

| Phase | What it does | Pass criteria |
|-------|-------------|---------------|
| **1. Direct health check** | `curl` each service in the chain without headers | HTTP 2xx/3xx from every service |
| **2. Entry-point passthrough** | Single request through the entry app without headers — exercises the full chain via original deployments | HTTP 2xx/3xx, response indicates normal operation |
| **3. Artillery load burst** | 10-second burst at 5 req/s through the entry point without headers | < 10% error rate (configurable via `ensure.maxErrorRate`) |

For intercepted apps, Phase 1 is the critical check: even though a Telepresence intercept is active on that service, a request **without** the matching header must still reach the original pod.

**Result:** `original-traffic-summary` — JSON summary per app + overall pass/fail.

#### 1.2 Pipeline integration

The task runs **in parallel** with `validate-propagation` — both depend on `deploy-intercepts` and both must pass before `run-tests` begins:

```
deploy-intercepts
      │
      ├──→ validate-propagation       (intercepted traffic works?)
      │
      └──→ validate-original-traffic   (original traffic still works?)
              │
              ▼
          run-tests                    (only runs if both validations pass)
```

This means:
- No additional pipeline duration — runs concurrently with existing validation
- `run-tests` now depends on both validation tasks
- The pipeline result includes `original-traffic-summary` alongside `test-summary`

#### 1.3 Artillery template

**File:** `tests/artillery/original-traffic-e2e.yml`

Standalone Artillery config for local testing. No `x-dev-session` or `baggage` headers — intentionally bare requests. Can be run locally against a stack with active intercepts:

```bash
artillery run tests/artillery/original-traffic-e2e.yml --target http://localhost:3000
```

#### 1.4 What this catches

| Failure mode | How this test detects it |
|--------------|------------------------|
| Telepresence intercepts all traffic (not just header-matched) | Phase 1 returns PR pod response or error for intercepted app |
| Traffic Manager crash disrupts service networking | Phase 1/2 return connection errors |
| Intercept misconfiguration routes bare requests to PR pod | Phase 2 response differs from normal behavior |
| Load-related degradation under dual routing | Phase 3 Artillery burst shows elevated error rate |

### Acceptance criteria

- [ ] `validate-original-traffic` task passes for all stack configurations (stack-one, stack-two-vendor)
- [ ] Pipeline fails if original traffic is disrupted during intercept window
- [ ] Task result `original-traffic-summary` included in pipeline output
- [ ] Artillery burst completes with < 10% error rate

---

## 2. MetalBear (mirrord) evaluation as alternative to Telepresence

### Background

[MetalBear mirrord](https://mirrord.dev/) is an open-source tool for running local processes in the context of a Kubernetes cluster. Like Telepresence, it can intercept traffic to a service, but it takes a different architectural approach:

| Aspect | Telepresence (current) | mirrord |
|--------|----------------------|---------|
| **Architecture** | Traffic Manager (cluster component) + client CLI | Agent pod injected per-session, no persistent cluster component |
| **Install footprint** | Helm chart for Traffic Manager in `ambassador` namespace | No cluster-wide install needed; agent spawned on demand |
| **Intercept mechanism** | Modifies Service routing via Traffic Manager | eBPF-based traffic stealing/mirroring at the pod level |
| **Header-based routing** | `--http-match` flag for header-based splitting | Supports `--http-header-filter` for selective interception |
| **Traffic mirroring** | Not built-in (intercept is steal-only) | Supports mirror mode (copy traffic without stealing) |
| **License** | OSS (Apache 2.0 for community edition) | OSS (MIT) + commercial (mirrord for Teams) |
| **In-cluster usage** | Designed for local-to-cluster; in-cluster via sidecar | Primarily local-to-cluster; in-cluster possible via operator |

### Goal

Evaluate mirrord as a potential replacement for or complement to Telepresence in the PR pipeline. Determine whether mirrord can provide the same header-based intercept behavior with reduced cluster footprint and improved reliability.

**Architecture assumption:** Production runs on a **different cluster** from the one used for the PR pipeline (Tekton, intercepts). Intercept tooling (Telepresence or mirrord) therefore never runs in production. See [docs/mirrord-poc-results.md](../docs/mirrord-poc-results.md) §5 for security risks and mitigations.

### Tasks

#### 2.1 Proof of concept: mirrord intercept in Kind cluster

- [ ] Install mirrord CLI locally
- [ ] Run a local process with mirrord targeting one service in stack-one (e.g. `release-lifecycle-demo`)
- [ ] Verify header-based filtering: `mirrord exec --target deployment/release-lifecycle-demo --http-header-filter "x-dev-session=pr-test" -- <local-process>`
- [ ] Confirm that traffic without the header reaches the original deployment
- [ ] Confirm that traffic with the header reaches the local process
- [ ] Document any behavioral differences from Telepresence

#### 2.2 In-pipeline feasibility

- [ ] Determine whether mirrord can run in-cluster (Tekton task pod → mirrord → target service) without the mirrord Operator
- [ ] If Operator is required, evaluate install complexity vs Telepresence Traffic Manager
- [ ] Prototype a `deploy-intercept-mirrord.yaml` task that uses mirrord instead of Telepresence
- [ ] Run the PR pipeline with mirrord intercepts and compare results to Telepresence

#### 2.3 Feature comparison for this project's needs

Evaluate against the specific requirements of this pipeline:

| Requirement | Telepresence | mirrord | Notes |
|-------------|-------------|---------|-------|
| Header-based intercept (only PR traffic routed) | `--http-match` | `--http-header-filter` | Both support; verify mirrord parity |
| Original traffic unaffected | Yes (by design) | Yes (steal mode with filter) | Validate with milestone 5 tests |
| In-cluster execution (no local machine) | Sidecar pattern (current) | Agent pod or Operator | Key feasibility question |
| Multiple concurrent intercepts (different PRs) | Supported via Traffic Manager | Supported via Operator (Teams) | OSS mirrord may not support concurrent |
| No persistent cluster component | Requires Traffic Manager | Agent-only (no persistent component) | mirrord advantage |
| Cleanup reliability | Depends on cleanup task | Agent auto-terminates | mirrord advantage |

#### 2.4 Traffic mirroring (bonus capability)

mirrord supports a **mirror mode** that copies traffic to the local/PR process without stealing it. This could enable:

- **Shadow testing**: run PR code against production-like traffic without affecting users
- **Comparison testing**: compare PR responses to original responses in real-time
- **Zero-risk validation**: test PR changes with real traffic patterns, no routing changes

Evaluate whether mirror mode is useful for PR testing and whether it can complement or replace the steal-based intercept approach.

#### 2.5 Decision criteria

| Criterion | Weight | Notes |
|-----------|--------|-------|
| Functional parity with current Telepresence setup | High | Must support header-based intercept + original traffic isolation |
| In-cluster execution without Operator | High | Pipeline runs in Tekton pods, not local machines |
| Reduced cluster footprint | Medium | No Traffic Manager install is appealing |
| Concurrent PR support | Medium | Multiple PRs testing simultaneously |
| OSS license sustainability | Medium | MIT vs Apache 2.0 both acceptable |
| Migration effort | Low | Willing to invest if benefits are clear |

### Deliverables

- [x] PoC results document: `docs/mirrord-poc-results.md`
- [x] Side-by-side comparison with Telepresence for this pipeline's use cases
- [x] Recommendation with rationale: **go with mirrord** (lower env — multiple intercepts without overlap, free cost, production separate cluster)
- [ ] Next: prototype `deploy-intercept-mirrord.yaml` task
- [ ] Next: migration plan (run both in parallel during transition, then remove Telepresence)

### Timeline

This is an **evaluation task**, not a commitment to migrate. The PoC should take 1–2 sessions. The decision and potential migration are separate follow-up work.

---

## Summary

| Area | Status | Key files |
|------|--------|-----------|
| Original traffic validation task | **Implemented** | `tasks/validate-original-traffic.yaml` |
| Artillery template (no headers) | **Implemented** | `tests/artillery/original-traffic-e2e.yml` |
| Pipeline integration | **Implemented** | `pipeline/stack-pr-pipeline.yaml` (parallel with validate-propagation) |
| MetalBear/mirrord PoC | **Complete** | [docs/mirrord-poc-results.md](../docs/mirrord-poc-results.md) |
| Recommendation | **Go with mirrord** (lower env): multiple intercepts without overlap + free cost; production is separate cluster. | Next: [milestone 6](milestone-6.md) (full mirrord testing), then prototype `deploy-intercept-mirrord` task. |
