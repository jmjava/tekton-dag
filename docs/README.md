# Documentation index

This folder contains design, operations, and verification docs for the tekton-dag project. The main [README](../README.md) describes layout, milestones, and quick start.

| Document | Description |
|----------|-------------|
| [DAG-AND-PROPAGATION.md](DAG-AND-PROPAGATION.md) | Stack DAG model, propagation roles (originator, forwarder, terminal), and intercept behavior |
| [c4-diagrams.md](c4-diagrams.md) | C4 context/container diagrams: PR/merge flow, intercept scenarios, version lifecycle |
| [PR-TEST-FLOW.md](PR-TEST-FLOW.md) | Valid PR test flow: create PR, run pipeline, merge |
| [PR-WEBHOOK-TEST-FLOW.md](PR-WEBHOOK-TEST-FLOW.md) | Webhook-driven PR and merge trigger flow |
| [CLOUDFLARE-TUNNEL-EVENTLISTENER.md](CLOUDFLARE-TUNNEL-EVENTLISTENER.md) | Exposing the EventListener via Cloudflare Tunnel |
| [argocd-architecture-guide.md](argocd-architecture-guide.md) | tekton-dag + ArgoCD + Tekton responsibilities and GitOps layout |
| [local-dag-verification-plan.md](local-dag-verification-plan.md) | Plan and scripts for verifying DAG structure locally (Phase 1/2) |
| [mirrord-poc-results.md](mirrord-poc-results.md) | Milestone 5: MetalBear mirrord PoC — install, header filter, security/mitigations, recommendation (go with mirrord) |
| [mirrord-m6-test-scenarios.md](mirrord-m6-test-scenarios.md) | Milestone 6: Full mirrord test scenarios (multiple intercepts + normal traffic) — to be created |
| [README-FULL.md](README-FULL.md) | Full design document: Tekton Job Standardization, stack model, intercepts, versioning |

**Milestones** (planning and completed) live in [../milestones/](../milestones/) and [../milestones/completed/](../milestones/completed/). See the main README sections “Planned: Milestone 4” and “Planned: Milestone 5” for current work.
