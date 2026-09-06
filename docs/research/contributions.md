# Contribution claims

These are the **only** claims the workshop/tool paper is allowed to make until evaluation is extended. Each claim is mapped to code. Overclaiming (e.g. “reduces CI cost by X%” or “first system to …”) will not survive review.

## Research question (tool / workshop)

> How can a polyglot, multi-repo application *group* share one CI/CD pipeline family while isolating a pull request to the changed node(s) of the runtime graph, without cloning a full preview stack and without breaking baseline traffic?

## Contributions

### C1 — Stack-as-DAG as the single source of pipeline behavior

**Claim.** One YAML graph of independently versioned apps is resolved at runtime into topological order, entry app, propagation chain, and the subset of apps to build. The same Tekton pipeline family (`stack-bootstrap`, `stack-pr-test`, `stack-merge-release`, `stack-promote`) runs for every stack; behavior is data, not duplicated pipeline YAML.

**Not claimed.** That DAGs in CI are new (GitHub Actions, Argo Workflows, Tekton Pipelines already have task DAGs). What is distinct is using the *application* graph, not the *task* graph, as the driver of build isolation, intercept placement, and header validation.

**Evidence in repo.** [`stacks/stack-one.yaml`](../../stacks/stack-one.yaml), [`stacks/schema.json`](../../stacks/schema.json), resolve-stack task, [`docs/DAG-AND-PROPAGATION.md`](../DAG-AND-PROPAGATION.md), [`docs/README-FULL.md`](../README-FULL.md).

### C2 — Three-role session propagation across polyglot hops

**Claim.** Each node is an **originator**, **forwarder**, or **terminal** for a session header (`x-dev-session`) plus optional W3C Baggage. Roles are declared or inferred from the DAG. Standalone libraries exist for Spring Boot, servlet/WAR, Node, Flask/WSGI, and PHP PSR-15, with build-time exclusion so production artifacts need not ship the middleware.

**Not claimed.** A new tracing standard (this *uses* W3C Baggage / OpenTelemetry-style context). Not claimed: formal verification of propagation.

**Evidence in repo.** [`libs/`](../../libs/), [`docs/m4-baggage-libraries-overview.md`](../m4-baggage-libraries-overview.md), [`docs/m41-publishing-strategy.md`](../m41-publishing-strategy.md), [`docs/TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md`](../TEAM-ONBOARDING-STACKS-AND-BAGGAGE.md). Validation task: `validate-stack-propagation`.

### C3 — Header-matched intercepts with original-traffic safety

**Claim.** On a PR, only `changed-app`(s) are built and intercepted. Matching is the same session header used for propagation. Two backends are implemented and E2E-exercised: Telepresence (`--http-match`) and mirrord (`header_filter`). A separate **validate-original-traffic** path checks that requests *without* the header still hit baseline pods.

**Not claimed.** That Telepresence or mirrord are novel. The contribution is *CI-orchestrated, graph-aware placement* of intercepts plus an explicit safety check, not the intercept dataplane.

**Evidence in repo.** [`docs/mirrord-poc-results.md`](../mirrord-poc-results.md) (header match 5/5 vs. unmatched 5/5 on stack-one), [`docs/m7-mirrord-intercept-task.md`](../m7-mirrord-intercept-task.md), `scripts/run-e2e-with-intercepts.sh`, milestone 5–7.

### C4 — Graph-guided test selection (test-trace graph)

**Claim.** A system test graph (Neo4j; traces from a mock Datadog API) maps tests to nodes so a PR can request a minimal test plan for `changed-app`, flagging unmapped areas.

**Not claimed.** A new test-impact-analysis algorithm that outperforms Ekstazi / MS TIA / HyRTS. This is an *integration* of blast-radius selection into the stack DAG and PR pipeline.

**Evidence in repo.** [`milestones/milestone-9.md`](../../milestones/milestone-9.md), orchestrator test-plan API, demo segment 12. Treat evaluation as **illustrative** until a coverage/time comparison is published.

### C5 — Reproducible platform artifact

**Claim.** The platform, sample polyglot apps, regression driver, and narrated demos are public and regenerable. Local Kind bootstrap is documented. Demo generation is extracted toward a reusable `docgen` toolchain.

**Not claimed.** That the Kind path currently meets the ICSE demo CFP’s “do not expect reviewers to build your code” bar without a pre-built cluster image or hosted GUI. See [artifact-checklist.md](artifact-checklist.md).

**Evidence in repo.** this repository, [`sample-repos/README.md`](../../sample-repos/README.md), [`docs/REGRESSION.md`](../REGRESSION.md), [GitHub Pages demos](https://jmjava.github.io/tekton-dag/), [`documentation-generator/`](../../documentation-generator/), [`milestones/milestone-doc-generator.md`](../../milestones/milestone-doc-generator.md).

## Non-contributions (do not list as novelty)

- Kubernetes, Tekton, Helm, Argo CD as such.
- Kaniko, Crane, Newman, Playwright, Artillery.
- The Management GUI as a research result (it is a usability artifact supporting C1–C3).
- The M14 operator (`Stack` / `StackRun` CRDs) as a *primary* workshop claim — it is an implementation path, still optional (`operator.enabled` defaults off). Mention as status, not as the paper’s thesis.
- Production-hardening items still open on M13 (ESO, Prometheus, cross-cluster deploy).

## Mapping claims → paper sections

| Claim | Tool-demo paper | SESoS short paper |
|-------|-----------------|-------------------|
| C1 | Approach § stack model | SoS constituents + shared platform |
| C2 | Approach § propagation | Emergent end-to-end session identity |
| C3 | Demo walkthrough | Operational isolation of a constituent change |
| C4 | Optional one paragraph | V&V / test selection in the ecosystem |
| C5 | Artifact + URL | Open exemplar for the community |
