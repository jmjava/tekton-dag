# Milestone 6: Full MetalBear (mirrord) testing — all scenarios

> **Active milestone.** Follows [milestone 5](milestone-5.md) (mirrord PoC complete; recommendation: go with mirrord for lower environment). Production is a separate cluster; intercept tooling runs only in dev/test.

## Goal

Prove that MetalBear (mirrord) works correctly in **all** scenarios required for the PR pipeline, including:

1. **Single intercept** — one PR’s traffic goes to its local/PR process; normal traffic goes to original deployments. (Already validated in M5 PoC.)
2. **Multiple concurrent intercepts** — two or more PRs active at once, each with a distinct `x-dev-session` value; no overlap (PR-A traffic never hits PR-B’s process).
3. **Normal traffic unaffected** — requests **without** any intercept header continue to hit the original deployments while one or more intercepts are active.
4. **Combined scenario** — multiple intercepts + normal traffic all working at the same time (multiple PRs + baseline traffic, no cross-talk, no dropped traffic).

Success means we can confidently prototype `deploy-intercept-mirrord` and migrate off Telepresence licensing.

---

## Test matrix (scenarios)

| # | Scenario | What we prove | Pass criteria |
|---|----------|----------------|---------------|
| 1 | **Single intercept** | One session, header `x-dev-session: pr-1` → local process; no header → original. | Repeated curls: with header → local response; without → original response. (M5 PoC already passed.) |
| 2 | **Two concurrent intercepts (same service)** | Two mirrord sessions targeting the same deployment (e.g. `release-lifecycle-demo`), different headers: `pr-1` and `pr-2`. Traffic with `pr-1` → process 1 only; `pr-2` → process 2 only. | No cross-talk: each header value hits only its session’s process; no header hits original. |
| 3 | **Two concurrent intercepts (different services)** | Session A intercepts service A (e.g. BFF); session B intercepts service B (e.g. API). Each header value routes only to its session. | Same as above, per service; full chain (e.g. fe → BFF → API) respects both intercepts when headers are present. |
| 4 | **Normal traffic during intercepts** | While one or more intercepts are active, send a sustained burst of requests **without** the intercept header (e.g. Artillery or curl loop). All must hit original deployments and return 2xx. | 0% of “no header” requests go to any PR process; all go to original pods; error rate &lt; threshold (e.g. &lt; 1%). |
| 5 | **Combined: N intercepts + normal traffic** | N ≥ 2 mirrord sessions active; continuous “normal” traffic (no header) in parallel; occasional traffic with each of the N session headers. | All of: (a) each session header reaches only its process, (b) no-header traffic always reaches originals, (c) no errors or timeouts attributable to overlap or contention. |

---

## Implementation

### 6.1 Test environment

- **Cluster:** Same lower-environment cluster used for M5 (e.g. Kind with stack-one deployed in `staging`).
- **Tooling:** mirrord CLI (install via `./scripts/install-mirrord.sh`), configs per scenario (e.g. `docs/mirrord-poc/mirrord-pr-1.json`, `mirrord-pr-2.json` with distinct `header_filter` values).
- **Local processes:** Minimal HTTP servers (e.g. `docs/mirrord-poc/local_server.py` or one-liners) that return a **unique body** per session (e.g. `LOCAL-PR-1`, `LOCAL-PR-2`) so responses are unambiguous.

### 6.2 Test procedures

- **Scripts:** Add (or extend) scripts under `scripts/` to:
  - Start N mirrord sessions in the background (each with its own config and port).
  - Run curl/Artillery for “no header” traffic and for each session header.
  - Assert response bodies and status codes; fail if any request with a session header hits the wrong process or the original, or if any no-header request hits a PR process.
- **Documentation:** Document each scenario in `docs/mirrord-m6-test-scenarios.md` (or equivalent): steps, commands, expected outputs, and how to interpret results.

### 6.3 Success criteria for milestone completion

- [ ] Scenario 1 (single intercept) documented and re-validated (or referenced to M5).
- [ ] Scenario 2 (two concurrent intercepts, same service) implemented and passing.
- [ ] Scenario 3 (two concurrent intercepts, different services) implemented and passing.
- [ ] Scenario 4 (normal traffic during intercepts) implemented and passing (e.g. Artillery burst without headers while intercepts active).
- [ ] Scenario 5 (combined: N intercepts + normal traffic) implemented and passing.
- [ ] Test results and any flakiness or edge cases recorded; if any scenario fails, document and either fix or call out as a blocker for mirrord adoption.
- [ ] README or docs updated to point to M6 test scenarios and state that mirrord is validated for “multiple intercepts + normal traffic” before proceeding to `deploy-intercept-mirrord` prototype.

---

## Deliverables

| Deliverable | Description |
|-------------|-------------|
| **Scenario configs** | mirrord JSON configs for multi-session tests (e.g. `header_filter`: `x-dev-session: pr-1`, `pr-2`). |
| **Test scripts** | Scripts to run scenarios 2–5 (start sessions, send traffic, assert responses). |
| **Scenario doc** | `docs/mirrord-m6-test-scenarios.md` (or similar): procedure, commands, pass/fail interpretation. |
| **Results summary** | Short summary of runs: all scenarios pass (or list of failures and next steps). |

---

## Outcomes

- **Confidence** that mirrord supports multiple concurrent intercepts without overlap and that normal traffic is unaffected under load.
- **Clear go-ahead** (or documented blockers) for Milestone 7 (or follow-on): prototype `deploy-intercept-mirrord` Tekton task and migration off Telepresence.

---

## References

- [Milestone 5](milestone-5.md) — original traffic validation, mirrord PoC, recommendation to go with mirrord.
- [docs/mirrord-poc-results.md](../docs/mirrord-poc-results.md) — PoC results, config, security/mitigations, licensing.
- [docs/mirrord-poc/](../docs/mirrord-poc/) — working mirrord config and local server used in M5.
