# Milestone 6: Full MetalBear (mirrord) testing — all scenarios

> **Completed.** Follows [milestone 5](milestone-5.md) (mirrord PoC complete; recommendation: go with mirrord for lower environment). Production is a separate cluster; intercept tooling runs only in dev/test.

## Constraint: one intercept per app at a time

Each PR targets a single app repo, so there is at most **one** active mirrord intercept per deployment at any time. Concurrent PRs that change **different** apps run intercepts in parallel with no issues. This is a pipeline design constraint, not a tooling limitation.

> **Note:** OSS mirrord does not support multiple concurrent steal sessions on the same pod (requires the paid mirrord Operator). This is irrelevant for our use case since we enforce 1 intercept per app. Documented for reference only.

## Goal

Prove that MetalBear (mirrord) works correctly in **all** scenarios required by the PR pipeline:

1. **Single intercept** — one PR's traffic goes to its local/PR process; normal traffic goes to original deployments. (**PASS** — validated in M5 PoC.)
2. **Multiple concurrent intercepts (different services)** — two PRs active at once, each intercepting a different app. Each PR's header routes only to its session; no cross-talk. (**PASS**)
3. **Normal traffic unaffected** — requests without any intercept header continue to hit original deployments while intercepts are active. (**PASS**)
4. **Combined scenario** — multiple intercepts on different services + normal traffic, all at the same time. (**PASS**)

---

## Test results

All test traffic originated from **inside the cluster** (ephemeral curl pod → Kubernetes service DNS → pod) to ensure requests traverse the normal service routing where mirrord agents intercept.

### Scenario 1: Single intercept (M5 re-validation)

| Request | Expected | Actual | Result |
|---------|----------|--------|--------|
| `curl http://release-lifecycle-demo/` (no header) | `tekton-dag-spring-boot` | `tekton-dag-spring-boot` | **PASS** |
| `curl -H "x-dev-session: pr-1" http://release-lifecycle-demo/` | `LOCAL-PR-1` | `LOCAL-PR-1` | **PASS** |

### Scenario 3: Two concurrent intercepts (different services)

Two mirrord agents running simultaneously — one on `release-lifecycle-demo` (BFF), one on `demo-api` (API).

| Request | Expected | Actual | Result |
|---------|----------|--------|--------|
| BFF no header | `tekton-dag-spring-boot` | `tekton-dag-spring-boot` | **PASS** |
| BFF `x-dev-session: pr-1` | `LOCAL-PR-1-BFF` | `LOCAL-PR-1-BFF` | **PASS** |
| API no header | `tekton-dag-spring-boot-gradle` | `tekton-dag-spring-boot-gradle` | **PASS** |
| API `x-dev-session: pr-2` | `LOCAL-PR-2-API` | `LOCAL-PR-2-API` | **PASS** |

### Scenario 4: Normal traffic during intercepts

10 rounds of no-header requests to both BFF and API while both intercepts active — **all hit originals, 0 leaked to local processes**.

### Scenario 5: Combined (N intercepts + normal traffic)

Both intercepts active; interleaved header and no-header requests — **all routed correctly, no cross-talk, no dropped traffic**.

### Scenario 2: Same-service concurrent intercepts (out of scope)

OSS mirrord blocks this with "dirty iptables" error. **Not required** — pipeline enforces 1 intercept per app. Documented as a known limitation; the mirrord Operator (paid) would enable this if ever needed.

---

## Test matrix (final)

| # | Scenario | Status | Notes |
|---|----------|--------|-------|
| 1 | Single intercept | **PASS** | M5 PoC, re-validated in M6 |
| 2 | Two intercepts, same service | **N/A** | Out of scope (1 per app constraint); OSS mirrord limitation documented |
| 3 | Two intercepts, different services | **PASS** | Two agents, two deployments, no conflict |
| 4 | Normal traffic during intercepts | **PASS** | 10/10 rounds all original |
| 5 | Combined: N intercepts + normal | **PASS** | Interleaved, no cross-talk |

---

## Implementation

### Configs

| Config | Target | Header filter |
|--------|--------|---------------|
| `docs/mirrord-poc/mirrord-pr-1.json` | `deployment/release-lifecycle-demo` | `x-dev-session: pr-1` |
| `docs/mirrord-poc/mirrord-pr-2.json` | `deployment/release-lifecycle-demo` | `x-dev-session: pr-2` |
| `docs/mirrord-poc/mirrord-pr-1-bff.json` | `deployment/release-lifecycle-demo` | `x-dev-session: pr-1` |
| `docs/mirrord-poc/mirrord-pr-2-api.json` | `deployment/demo-api` | `x-dev-session: pr-2` |

### Scripts and docs

- **`scripts/run-mirrord-m6-scenarios.sh [3|4|5|all]`** — automated test runner using in-cluster curl pod.
- **[docs/mirrord-m6-test-scenarios.md](../docs/mirrord-m6-test-scenarios.md)** — procedures, architecture, pass/fail interpretation.
- **`docs/mirrord-poc/local_server.py`** — configurable local HTTP server (env: `MIRRORD_M6_RESPONSE`, `PORT`).

---

## Outcomes

- **mirrord is validated** for the PR pipeline's actual concurrency model (1 intercept per app, N apps in parallel).
- **No cross-talk** between concurrent intercepts on different services.
- **Normal traffic is never disrupted** by active intercepts.
- **Clear go-ahead** for Milestone 7: prototype `deploy-intercept-mirrord` Tekton task and begin Telepresence migration.
- **OSS mirrord is sufficient** — the paid Operator is not needed for our use case.

---

## References

- [Milestone 5](milestone-5.md) — original traffic validation, mirrord PoC, recommendation.
- [docs/mirrord-poc-results.md](../docs/mirrord-poc-results.md) — PoC results, config, security/mitigations, licensing.
- [docs/mirrord-m6-test-scenarios.md](../docs/mirrord-m6-test-scenarios.md) — full scenario procedures.
- [docs/mirrord-poc/](../docs/mirrord-poc/) — configs and local server.
