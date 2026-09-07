# Related work (for the paper and for reviewers)

The engineering docs describe *how the system works*. Reviewers ask *what is already known*. This note is the positioning layer; bibliographic records live in [`paper/refs.bib`](paper/refs.bib).

## 1. Continuous integration at scale

Hilton et al. documented CI adoption, costs, and benefits in open-source projects. Shahin et al. surveyed continuous practices (CI/CD/CD). Duvall and Humble & Farley established the industrial vocabulary. None of these prescribe how to isolate a **single node** in a **running multi-service graph** during a pull request.

**Position:** we assume CI is desirable and expensive; the gap is *graph-aware PR isolation* for polyglot stacks, not “CI vs. no CI.”

## 2. Task DAGs vs. application DAGs

Tekton Pipelines, Argo Workflows, GitHub Actions (`needs:`), GitLab DAGs, Dagger, and Earthly all model **build/task** graphs. Those graphs answer “which jobs run after which.” They do not, by themselves, answer “which *runtime service* in the user’s architecture changed, and how does a request still reach it.”

**Position (C1):** tekton-dag’s DAG is the *application* topology (`downstream:` edges). Task order is derived from that topology plus `changed-app`. This is closer to an architecture description than to a Jenkinsfile.

## 3. Preview and ephemeral environments

Common practice: clone a namespace, Helm release, or PaaS review app per PR (Heroku, Vercel, namespace-per-PR on Kubernetes, some GitOps preview-environment operators). Cost and drift grow with stack width. Service-mesh traffic splitting (Istio/Envoy header match, Linkerd) can route a fraction of traffic to a canary without cloning the world, but every hop must forward the routing key, and CI still has to build and attach the canary.

**Position (C3):** we keep a **shared baseline stack** and steal only header-matched requests to PR pods. That is a preview-environment *strategy* (routing) rather than a *duplication* strategy. We do not claim it is cheaper until measured (see [evaluation.md](evaluation.md)).

## 4. Developer intercepts (local-to-cluster)

Telepresence (Ambassador) and mirrord (MetalBear) intercept cluster traffic to a local process or alternate pod, including HTTP header filters. They are **developer tools**, typically one service at a time, driven from a laptop.

**Position:** C3 is not a new dataplane. It is **pipeline-placed** intercepts: the PR pipeline decides *which* nodes to intercept from the stack DAG, uses the **same** header the apps propagate (C2), and adds **original-traffic** validation so baseline users are not stolen. Dual-backend (Telepresence vs. mirrord) is an engineering portability result, useful in a tool paper, not a theory result.

## 5. Distributed context: tracing and baggage

W3C Trace Context and W3C Baggage, OpenTelemetry, and vendor APM (Datadog, etc.) already propagate keys across services. Feature-flag SDKs similarly thread targeting keys.

**Position (C2):** we reuse baggage as a **dev-session** identifier for *routing and validation*, with explicit **originator / forwarder / terminal** roles derived from the application DAG, plus framework libraries that are **dev-gated** (Maven profile, `require-dev`, etc.). The novelty is the role model + CI integration, not the header format.

## 6. Test-impact analysis and blast radius

Ekstazi, HyRTS, Microsoft test-impact analysis, and various CI “failed-test selection” tools shrink *unit/integration* suites from code diffs. Microservice papers on blast-radius use traces or service meshes to see which tests or monitors a change might affect.

**Position (C4):** we store a **test-to-node** graph (Neo4j) from observed traces and query it with `changed-app`. This is TIA at *service* granularity for e2e/API tests declared in the stack, not bytecode-level dependency analysis. Do not cite C4 as beating Ekstazi; cite it as complementary (different artifact: HTTP tests vs. class files).

## 7. GitOps and multi-team platforms

Argo CD, Flux, Backstage, Internal Developer Platforms (IDP) literature, and Helm umbrellas address *how teams consume a platform*. tekton-dag’s Helm chart + team values + ApplicationSet is in that family (M10).

**Position:** packaging is C5 (artifact completeness), not the research thesis. SESoS readers will recognize it as **platform governance** for a SECO.

## 8. Kubernetes operators for CI

Tekton itself is operator-style (PipelineRun CRDs). Crossplane, Keptn, and various “pipeline operator” projects exist. M14 adds `Stack` / `StackRun` as a CRD-primary control plane.

**Position:** mention as an implementation path. Do not lead the workshop paper with “we wrote an operator.”

## Citation hygiene

- Prefer **peer-reviewed** CI/CD and TIA papers for claims about the field.
- Tools (Tekton, Telepresence, mirrord, Istio) may be cited as **software** (URL + year) when no canonical paper exists.
- Do **not** cite only vendor blogs for the related-work section.
- Confirm every `\cite` key in [`paper/refs.bib`](paper/refs.bib) exists; hallucinated references are a desk-reject risk (SERS CFP states this explicitly; other tracks will notice too).
