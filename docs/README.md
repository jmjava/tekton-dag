# Documentation index

This folder contains design, operations, and verification docs for the tekton-dag project. The main [README](../README.md) describes layout, milestones, quick start, and [demo videos on GitHub Pages](https://jmjava.github.io/tekton-dag/).

## Documentation map

| Area | Where |
|------|--------|
| **Milestones (current)** | [../milestones/](../milestones/) — M4 through M12, M12.2, [M8](../milestones/milestone-8.md) (partial demos) |
| **Milestones (historical)** | [../milestones/completed/](../milestones/completed/) — M2, M3 |
| **Archive (not maintained)** | [archive/](archive/) — obsolete session plans and similar |
| **Customization & ops** | [CUSTOMIZATION.md](CUSTOMIZATION.md), [MAINTENANCE.md](MAINTENANCE.md) |
| **Demo toolchain (M8)** | [demos/](demos/) — regenerate with `docs/demos/generate-all.sh`; see [milestones/milestone-8.md](../milestones/milestone-8.md) |
| **GitHub Pages** | [GITHUB-PAGES.md](GITHUB-PAGES.md) — how the demo site is deployed; fix 404 |

## Active documents

### Core architecture and flows

| Document | Description |
|----------|-------------|
| [DAG-AND-PROPAGATION.md](DAG-AND-PROPAGATION.md) | Stack DAG model, propagation roles (originator, forwarder, terminal), intercept behavior |
| [c4-diagrams.md](c4-diagrams.md) | C4 context/container diagrams: PR/merge flow, intercept scenarios, version lifecycle |
| [PR-TEST-FLOW.md](PR-TEST-FLOW.md) | Valid PR test flow: create PR, run pipeline, merge |
| [PR-WEBHOOK-TEST-FLOW.md](PR-WEBHOOK-TEST-FLOW.md) | Webhook-driven PR and merge trigger flow |
| [m10-multi-team-architecture.md](m10-multi-team-architecture.md) | Multi-team Helm, orchestrator, namespaces |

### Platform integration

| Document | Description |
|----------|-------------|
| [CLOUDFLARE-TUNNEL-EVENTLISTENER.md](CLOUDFLARE-TUNNEL-EVENTLISTENER.md) | Exposing the EventListener via Cloudflare Tunnel |
| [argocd-architecture-guide.md](argocd-architecture-guide.md) | tekton-dag + ArgoCD + Tekton responsibilities and GitOps layout |

### Verification and intercept deep-dives

| Document | Description |
|----------|-------------|
| [REGRESSION.md](REGRESSION.md) | **Run full regression before updating testing/demo docs** — `scripts/run-regression.sh` and phases (pytest, Playwright, Newman, Kind) |
| [local-dag-verification-plan.md](local-dag-verification-plan.md) | Plan and scripts for verifying DAG structure locally (Phase 1/2) |
| [mirrord-poc-results.md](mirrord-poc-results.md) | Milestone 5: MetalBear mirrord PoC — install, header filter, security/mitigations, recommendation |
| [mirrord-m6-test-scenarios.md](mirrord-m6-test-scenarios.md) | Milestone 6: Full mirrord test scenarios, procedures and pass criteria |
| [m7-mirrord-intercept-task.md](m7-mirrord-intercept-task.md) | `intercept-backend` param, mirrord task, “run either” design (see [milestone-7.md](../milestones/milestone-7.md)) |
| [bootstrap-pipeline-speed-analysis.md](bootstrap-pipeline-speed-analysis.md) | Bootstrap pipeline performance notes (M7.1) |

### Milestone 4 supplements

| Document | Description |
|----------|-------------|
| [m4-multi-namespace.md](m4-multi-namespace.md) | Multi-namespace pipeline scaling |
| [m4-eventlistener-per-namespace.md](m4-eventlistener-per-namespace.md) | EventListener per namespace |
| [m4-test-stacks-and-integration.md](m4-test-stacks-and-integration.md) | Test stacks and integration |
| [m4-baggage-libraries-overview.md](m4-baggage-libraries-overview.md) | Baggage libraries overview |
| [m41-publishing-strategy.md](m41-publishing-strategy.md) | M4.1 library publishing and consumption |

### Demos and extended design

| Document | Description |
|----------|-------------|
| [demo-playbook.md](demo-playbook.md) | What to record and how to demo (complements [M8](../milestones/milestone-8.md)) |
| [README-FULL.md](README-FULL.md) | Long-form design: Tekton job standardization, stack model, intercepts, versioning (historical depth) |

## Archive

See [archive/README.md](archive/README.md) for historical documents that are no longer maintained.
