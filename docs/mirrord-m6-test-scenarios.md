# Milestone 6: Full mirrord test scenarios

Procedures, results, and pass/fail interpretation. See [milestones/milestone-6.md](../milestones/milestone-6.md).

## Constraint

**One intercept per app at a time.** Each PR targets a single app repo, so at most one mirrord steal session runs per deployment. Concurrent PRs that change different apps run intercepts in parallel — this is the scenario we validate here.

## Architecture

All test traffic originates from **inside the cluster** via an ephemeral curl pod (`m6-curl-runner`). This ensures requests traverse the normal Kubernetes service → pod path where mirrord agents intercept. `kubectl port-forward` is **not** used — it tunnels directly through the API server, bypassing service routing and mirrord's interception.

```
┌──────────────────────────────────────────────────────────┐
│ Cluster (staging namespace)                              │
│                                                          │
│  m6-curl-runner ──→ svc/release-lifecycle-demo ──→ pod   │
│       (curl)    ──→ svc/demo-api               ──→ pod   │
│                         (ClusterIP)          ↕           │
│                                        mirrord agent     │
│                              ┌─ header match → steal ──┐ │
│                              └─ no match → original ──┘  │
└──────────────────────────────────────────────────────────┘
                                           ↕ (stolen)
                              Host: local_server.py (PR process)
```

## Prerequisites

- Kind (or other) cluster with stack-one deployed in `staging`
- mirrord CLI installed (`./scripts/install-mirrord.sh` or in PATH)
- `kubectl get deployment release-lifecycle-demo -n staging` and `demo-api` succeed

---

## Scenario 1: Single intercept (M5 — reference)

Validated in M5 PoC. Re-run:

```bash
mirrord exec -f docs/mirrord-poc/mirrord.json -- python3 docs/mirrord-poc/local_server.py
# then from inside cluster:
kubectl run m6-test -n staging --rm -it --restart=Never --image=curlimages/curl:8.5.0 -- sh -c \
  'curl -sS http://release-lifecycle-demo/ && echo "---" && curl -sS -H "x-dev-session: pr-test" http://release-lifecycle-demo/'
```

**Result: PASS** — no header → original, with header → local.

---

## Scenario 3: Two concurrent intercepts (different services)

Two mirrord sessions: pr-1 intercepts BFF (`release-lifecycle-demo`), pr-2 intercepts API (`demo-api`).

```bash
./scripts/run-mirrord-m6-scenarios.sh 3
```

**Pass criteria:**

| Request | Expected |
|---------|----------|
| BFF no header | `tekton-dag-spring-boot` (original) |
| BFF `x-dev-session: pr-1` | `LOCAL-PR-1-BFF` (intercepted) |
| API no header | `tekton-dag-spring-boot-gradle` (original) |
| API `x-dev-session: pr-2` | `LOCAL-PR-2-API` (intercepted) |

**Result: PASS** — two agents, two deployments, no conflict, no cross-talk.

---

## Scenario 4: Normal traffic during intercept

Single intercept active on BFF; 20 consecutive no-header requests must all hit original.

```bash
./scripts/run-mirrord-m6-scenarios.sh 4
```

**Result: PASS** — 10/10 rounds, 0 leaked to local process.

---

## Scenario 5: Combined (N intercepts + normal traffic)

Both BFF and API intercepts active; 5 rounds of interleaved no-header and header requests to both services.

```bash
./scripts/run-mirrord-m6-scenarios.sh 5
```

**Result: PASS** — all header requests routed to correct local process, all no-header requests hit originals.

---

## Run all scenarios

```bash
./scripts/run-mirrord-m6-scenarios.sh all
```

Exit code 0 if all pass. The ephemeral curl pod is cleaned up on exit.

---

## Same-service concurrent intercepts (out of scope)

OSS mirrord blocks two steal sessions on the same pod:

> "Detected dirty iptables. Either some other mirrord agent is running... To allow concurrent sessions, consider using the operator available in mirrord for Teams."

This is irrelevant for our pipeline — we enforce 1 intercept per app. If ever needed, the mirrord Operator (paid) enables it.

---

## Interpreting failures

- Check `mirrord --version` and agent pods: `kubectl get pods -n staging | grep mirrord`
- Remove stale agent lock: `kubectl delete pods -n staging -l app=mirrord`
- Remove leftover `/tmp/mirrord` file if present
- Verify deployments exist: `kubectl get deploy -n staging`

## References

- [milestone-6.md](../milestones/milestone-6.md) — full results
- [mirrord-poc-results.md](mirrord-poc-results.md) — M5 PoC
- [docs/mirrord-poc/](mirrord-poc/) — configs and local_server.py
