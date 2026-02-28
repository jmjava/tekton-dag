# Milestone 4: Production-safe baggage middleware libraries and multi-namespace pipeline scaling

## 1. Production-safe baggage middleware libraries

### Goal

Deliver one **standalone, reusable middleware library per supported framework** (Spring Boot, Spring Legacy, Node, Flask, PHP) that handles W3C baggage / `x-dev-session` header propagation. Each library supports all three propagation roles (originator, forwarder, terminal) via configuration so that an app on any framework can sit at any position in any DAG. The libraries are **framework-level infrastructure**, not tied to any specific stack or DAG definition. Any future stack that includes an app built on one of these frameworks can depend on the corresponding library and get baggage propagation for free.

The middleware must be **structurally impossible to activate in production** — not just toggled by a runtime flag. Two independent guard layers (build-time exclusion and runtime env-var gate) ensure zero chance of execution in production.

### Scope

#### 1.1 One standalone library per framework

Each library is published as its own package so that any app on that framework can opt in by adding a single dependency:

| Library | Package type | Framework coverage |
|---------|--------------|--------------------|
| `baggage-spring-boot-starter` | Maven artifact | Spring Boot (auto-configuration module) |
| `baggage-servlet-filter` | Maven artifact | Spring Legacy / any WAR-deployed Servlet app |
| `@tekton-dag/baggage` | npm package | Node (Express, Nitro, SSR) + browser-side (Vue, React, plain JS) |
| `tekton-dag-baggage` | pip package | Flask / any WSGI app |
| `tekton-dag/baggage-middleware` | Composer package | PHP (PSR-15 + Guzzle) |

#### 1.2 All three roles in every library

Each library is config-driven via a single property (`baggage.role` / env var / constructor arg). The role determines behavior:

- **Originator** — always sets `x-dev-session` + W3C `baggage` headers on all outgoing HTTP calls, regardless of whether an incoming header exists. Sources the session value from config/env.
- **Forwarder** — extracts `x-dev-session` from incoming requests, stores in request-scoped context, and propagates it on all outgoing HTTP calls. No-op if the incoming header is absent.
- **Terminal** — extracts `x-dev-session` from incoming requests for logging/routing. Does not register any outgoing interceptors.

Any framework can fill any role. Flask can be a forwarder, PHP can be an originator, Node can be a terminal — any combination is valid for any future DAG.

#### 1.3 Per-framework design

**Spring Boot** (`baggage-spring-boot-starter`):

- Incoming: `OncePerRequestFilter` (extends the existing `BaggageContextFilter` pattern). Extracts header, stores in OpenTelemetry Baggage + `ThreadLocal` context.
- Outgoing: auto-configured `ClientHttpRequestInterceptor` (RestTemplate), `ExchangeFilterFunction` (WebClient), Feign `RequestInterceptor`. Reads from context, sets headers on outgoing calls.
- Activation: `@ConditionalOnProperty(name = "baggage.enabled", havingValue = "true")`. Role via `baggage.role` property.
- Starting point: the existing `BaggageContextFilter.java` in `tekton-dag-spring-boot` handles incoming extraction and OTel Baggage storage. It needs to be extracted into the standalone starter, made role-aware, and paired with outgoing interceptors.

**Spring Legacy** (`baggage-servlet-filter`):

- Incoming: standard `javax.servlet.Filter` (no Boot dependency). Stores in `ThreadLocal`.
- Outgoing: `ClientHttpRequestInterceptor` for `RestTemplate` or `HttpURLConnection` wrapper.
- Activation: declared in `web.xml` or programmatic `FilterRegistration`, only if present in WAR. Role via init-param or system property.

**Node** (`@tekton-dag/baggage`):

- Client-side (Vue/browser): Axios request interceptor or `fetch` wrapper. For originator role, reads session value from `VITE_DEV_SESSION` env at build time (Vite injects it).
- Server-side (Express/Nitro/SSR): Express middleware for incoming extraction into `AsyncLocalStorage` context. Axios / `node-fetch` interceptor for outgoing.
- Role via `BAGGAGE_ROLE` env var or constructor config.

**Flask** (`tekton-dag-baggage`):

- Incoming: WSGI middleware or `@app.before_request` hook. Stores header value in Flask `g` (request context).
- Outgoing: `requests.Session` subclass or `requests` event hook that reads from `g` and sets headers.
- Role via `BAGGAGE_ROLE` env var or `init_app(app, role=...)`.

**PHP** (`tekton-dag/baggage-middleware`):

- Incoming: PSR-15 `MiddlewareInterface` implementation. Stores in a request attribute.
- Outgoing: Guzzle middleware handler that reads from context and injects headers.
- Role via env var or constructor config.

#### 1.4 Production safety — zero chance of execution in production

Two independent guard layers so the middleware **cannot** run in production even if accidentally included:

**Layer 1 — build-time exclusion** (strongest guard):

- Spring Boot / Legacy: Maven/Gradle profile excludes the baggage artifact from production builds entirely. The classes do not exist in the production JAR/WAR.
- Node: Vite tree-shaking via `import.meta.env.MODE !== 'production'` dead-code-eliminates interceptor registration in browser bundles. Server-side: listed in `devDependencies` only, not installed in production `node_modules`.
- Flask: packaged as an extras group (`pip install myapp[baggage]`). Production Dockerfile uses `pip install myapp` without the extra — module is never installed.
- PHP: `composer require-dev tekton-dag/baggage-middleware`. Production builds run `composer install --no-dev` — package is absent.

**Layer 2 — runtime guard** (defense-in-depth):

Even if the classes are present (e.g. a developer accidentally includes them in a production build), the middleware refuses to activate unless an explicit env var is set:

- All frameworks: `BAGGAGE_ENABLED=true` required. This env var is never set in production deployments.
- Spring Boot: `@ConditionalOnProperty(name = "baggage.enabled", havingValue = "true", matchIfMissing = false)`.
- Flask: `if not os.environ.get("BAGGAGE_ENABLED"): return` in `init_app`.
- Node: interceptor registration skipped if `process.env.BAGGAGE_ENABLED !== "true"`.
- PHP: middleware returns early (passes through) if env var absent.

#### 1.5 W3C Baggage compliance

All libraries implement proper W3C Baggage header handling:

- Parse existing `baggage` header (preserve other key-value pairs from upstream).
- Add/update the `dev-session=<value>` entry.
- Serialize back to spec-compliant format (character escaping, size limits).
- Merge rather than overwrite — existing tracing baggage from other tools (OpenTelemetry, Datadog) is preserved.

#### 1.6 Test stacks for the testing phase

Create new stack YAML files specifically to exercise every framework in every role. These are test-only stacks, not production DAGs:

- Stacks that place Flask as a forwarder, PHP as a forwarder, Node/Express as a forwarder.
- Stacks that place Spring Boot as an originator, Flask as an originator.
- Stacks that exercise multi-hop forwarding (originator → forwarder → forwarder → terminal) across mixed frameworks.
- Pipeline runs against these test stacks validate that every library correctly handles all three roles and that `validate-propagation.yaml` passes for any framework combination.

#### 1.7 Testing strategy

- **Unit tests per library**: each library has its own test suite covering all three roles, W3C baggage parsing/merging, missing-header behavior, and production-guard (verify middleware is inert when `BAGGAGE_ENABLED` is absent).
- **Integration tests**: test stacks + pipeline runs via `validate-propagation.yaml` that send requests through the full chain and verify header presence at each hop.
- **Cross-framework matrix**: CI runs test stacks covering all framework-in-role combinations.

### Outcomes

- **Five standalone library packages** (Maven, npm, pip, Composer) — one per framework — each supporting all three propagation roles.
- **Production safety** verified: unit tests confirm middleware is inert when `BAGGAGE_ENABLED` is absent; build profiles confirmed to exclude the artifact from production containers.
- **W3C Baggage compliance**: proper parsing, merging, and serialization tested per library.
- **Test stack YAML files** that exercise every framework in every role (forwarder, originator, terminal) for pipeline-level integration testing.
- **Documentation**: README per library covering installation, configuration (role, header name, baggage key), production-safety setup, and examples.

### Notes

- The existing `BaggageContextFilter.java` in `tekton-dag-spring-boot` is the only middleware code that exists today. It handles incoming `x-dev-session` extraction and OTel Baggage storage but has no outgoing propagation, no role awareness, and is not packaged as a standalone library. It serves as the starting point for `baggage-spring-boot-starter`.
- The other four app repos (`tekton-dag-vue-fe`, `tekton-dag-flask`, `tekton-dag-php`, `tekton-dag-spring-legacy`) have no middleware code at all — they are minimal hello-world apps. Each needs the corresponding library added as a dependency and wired into the app's request lifecycle.
- Header names and baggage keys are configurable per library (default: `x-dev-session` / `dev-session`) to match the `propagation` section in stack YAML files.
- The propagation `strategy: w3c-baggage` defined in stack YAML is what the libraries implement. If a future strategy is added, the libraries should be extensible to support it.

---

## 2. Multi-namespace pipeline scaling and promotion

### Goal

Scale the Tekton pipeline infrastructure from a single hardcoded namespace (`tekton-pipelines`) to a **multi-namespace model** that supports isolated testing of pipeline changes before promoting them to production. Pipeline upgrades follow a progression: **local (Kind) → test namespace → production namespace**, ensuring changes are validated at each stage.

### Scope

#### 2.1 Current state

All pipelines, tasks, triggers, EventListeners, and PipelineRuns live in a single hardcoded namespace (`tekton-pipelines`):

- Pipeline/task/trigger YAML files have `namespace: tekton-pipelines` hardcoded in metadata.
- `scripts/install-tekton.sh` accepts a `NAMESPACE` env var but YAML metadata overrides it.
- `scripts/generate-run.sh` hardcodes `namespace: tekton-pipelines` in generated PipelineRuns.
- `pipeline/triggers.yaml` hardcodes namespace in EventListener and TriggerTemplates.
- ServiceAccount `tekton-pr-sa` and secrets (`git-ssh-key`, `github-token`, `github-webhook-secret`) exist only in `tekton-pipelines`.

#### 2.2 Namespace strategy (three tiers)

1. **Local (Kind cluster)** — developer runs pipeline changes locally via `generate-run.sh`. Uses the existing Kind + local registry setup. Fastest iteration loop for pipeline YAML changes.
2. **Test namespace** (`tekton-test` or configurable) — pipeline YAML is applied to a dedicated test namespace on a shared cluster (or the same Kind cluster). Runs are triggered against test repos/branches. Validates pipeline logic, task changes, and trigger configuration before promoting to production.
3. **Production namespace** (`tekton-pipelines`) — proven pipeline versions are promoted here. Webhook-triggered runs from real PRs and merges. This is the namespace that serves live development workflows.

#### 2.3 YAML parameterization

- Remove hardcoded `namespace: tekton-pipelines` from all pipeline, task, and trigger YAML metadata. Let `kubectl apply -n <namespace>` set the namespace at apply time.
- Update `scripts/install-tekton.sh` to accept a target namespace and apply all resources into it.
- Update `scripts/generate-run.sh` to accept a `--namespace` flag (defaulting to `tekton-pipelines` for backward compatibility).
- Update `pipeline/triggers.yaml` so TriggerTemplates generate PipelineRuns in the namespace where the EventListener lives (use `$(context.eventlistener.namespace)` or similar).

#### 2.4 Promotion workflow

- Pipeline and task YAML are versioned in Git (already the case).
- Promotion = applying the same YAML to the next namespace tier.
- Script: `scripts/promote-pipelines.sh --from tekton-test --to tekton-pipelines` that applies tasks, pipelines, and triggers from one namespace to another.
- Secret/SA bootstrapping per namespace: `scripts/bootstrap-namespace.sh <namespace>` to create ServiceAccount, secrets (git-ssh-key, github-token, github-webhook-secret), PVCs (build-cache), and RBAC in a new namespace.
- Promotion is a manual, deliberate step — not automatic. The operator decides when a pipeline version is ready for production.

#### 2.5 EventListener per namespace

- Each namespace gets its own EventListener (different service name / URL).
- Webhook routing: GitHub webhook URL is per-environment. The test namespace uses a separate URL (or the same Cloudflare Tunnel with a different subdomain, e.g. `tekton-el-test.menkelabs.com` vs `tekton-el.menkelabs.com`).
- For local Kind testing, `kubectl port-forward` targets the EventListener in the test namespace.

#### 2.6 Shared vs. isolated resources

- **Catalog tasks** (`git-clone`): either installed per namespace or referenced cross-namespace via Tekton Resolver (bundle or cluster resolver). Per-namespace installation is simpler and avoids cross-namespace RBAC.
- **Build images**: shared across namespaces (same registry, e.g. `localhost:5000`). No per-namespace image builds needed.
- **Secrets**: per namespace. Each namespace needs its own copies of `git-ssh-key`, `github-token`, and `github-webhook-secret`. `bootstrap-namespace.sh` handles this.
- **PVCs** (`build-cache`, `shared-workspace`): per namespace. Storage classes and sizes match the production namespace.

#### 2.7 Pipeline versioning

- Tag pipeline/task YAML with version labels (e.g. `app.kubernetes.io/version: "1.2.0"`) so operators can identify which version is deployed in each namespace.
- Optional: Tekton Bundles to package pipeline + tasks as OCI images, pushed to the same registry, for reproducible versioned deployment. A bundle reference in a PipelineRun pins the exact pipeline version regardless of what is currently applied in the namespace.
- Git tags or branches can mark pipeline releases (e.g. `pipeline-v1.2.0`), and promotion scripts can apply from a specific tag.

### Outcomes

- **Namespace-agnostic YAML**: all pipeline, task, and trigger YAML files have `namespace` removed from metadata. `kubectl apply -n <ns>` sets the target.
- **`scripts/bootstrap-namespace.sh`**: script that creates a new namespace with all required resources (SA, secrets, PVCs, RBAC, catalog tasks).
- **`scripts/promote-pipelines.sh`**: script that applies pipeline/task/trigger YAML from one namespace to another.
- **Updated `install-tekton.sh`**: accepts `NAMESPACE` and applies all resources into it without hardcoded overrides.
- **Updated `generate-run.sh`**: accepts `--namespace` flag.
- **Updated `pipeline/triggers.yaml`**: EventListener and TriggerTemplates are namespace-aware (use context variables or parameterized namespace).
- **Documentation**: README section or dedicated doc explaining the three-tier namespace model, promotion workflow, and how to set up a test namespace.

### Notes

- Backward compatibility: default namespace remains `tekton-pipelines` everywhere. Existing workflows (scripts, webhooks) continue to work without changes unless the operator explicitly targets a different namespace.
- The test namespace is optional — teams that don't need isolated pipeline testing can continue using the single-namespace model.
- For Kind clusters, both test and production namespaces can coexist on the same cluster. For real environments, they may be on separate clusters (promotion scripts work the same way — they apply YAML, not copy in-cluster resources).
- Cross-namespace task references (e.g. referencing a `ClusterTask` or using Tekton Resolver) are an alternative to per-namespace task installation. Document trade-offs (simpler RBAC vs. version isolation) and recommend per-namespace installation as the default.
- Pipeline versioning via Tekton Bundles is optional and adds complexity (OCI image builds for pipeline YAML). Recommend starting with Git-tag-based promotion and adding bundles later if reproducibility requirements grow.
- The milestone-4 test stacks (from section 1.6) are a natural first user of the test namespace: deploy the middleware test stacks into `tekton-test`, validate propagation, then promote the pipeline changes to `tekton-pipelines`.
