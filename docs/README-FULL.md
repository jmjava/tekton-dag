# Tekton Job Standardization

One universal Tekton pipeline system that adapts to any combination of applications — single services, multi-tier stacks, or fan-out graphs — while managing versioning, build toolchains, header propagation, and container image lifecycle automatically.

## Problem

Each application stack (frontend → middleware → persistence, middleware → vendor, standalone API, etc.) previously needed its own bespoke Tekton pipeline, trigger template, and test wiring. Adding a new app or a new group of related apps meant duplicating pipeline YAML and manually threading the baggage header through each hop.

## Solution

Define each application group as a **stack graph** in a simple YAML file. Two universal pipelines — one for PRs and one for merges — read the graph at runtime and adapt their behavior accordingly:

```
                    ┌──────────────────────┐
                    │   Stack Definition   │
                    │   (YAML graph)       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                  ▼
     ┌─────────────────┐              ┌─────────────────────┐
     │  stack-pr-test   │              │  stack-merge-release │
     │  (PR pipeline)   │              │  (merge pipeline)    │
     └────────┬────────┘              └────────┬────────────┘
              │                                 │
   ┌──────────┼──────────┐          ┌──────────┼──────────┐
   │ resolve  │ bump RC  │          │ resolve  │ promote  │
   │ graph    │ version  │          │ graph    │ to       │
   │          │          │          │          │ release  │
   │ compile  │ container│          │ compile  │ container│
   │ (per     │ ize      │          │ (per     │ ize      │
   │  tool)   │ (Kaniko) │          │  tool)   │ (Kaniko) │
   │          │          │          │          │          │
   │ deploy   │ validate │          │ tag      │ push     │
   │ intercept│ headers  │          │ release  │ version  │
   │          │          │          │ image    │ commit   │
   │ run      │ push     │          └──────────┴──────────┘
   │ tests    │ version  │
   └──────────┴──────────┘
```

## Key Concepts

### DAG system and arbitrary stacks

The pipeline is driven by a **single source of truth**: a stack YAML file that defines a **directed acyclic graph (DAG)** of applications. There is no second pipeline or trigger template per stack — the same two pipelines (`stack-pr-test`, `stack-merge-release`) run for every stack. Behavior is fully determined by the graph and per-app config at runtime.

**Graph model**

- **Nodes** = apps. Each app has a name, repo, role, and arbitrary config (build tool, runtime, ports, tests, legacy env, etc.).
- **Edges** = `downstream: [app-a, app-b]`. “This app calls these apps.” Direction is caller → callee.
- The graph must be a **DAG** (no cycles). Cycle detection runs at resolve time (topological sort fails if a cycle exists).

**What “arbitrary config” means**

- **Stack-level:** `name`, `description`, `propagation` (header name, baggage key), `defaults` (namespace, image-registry, service-port, container-port).
- **Per-app:** anything under each `apps[]` entry: `context-dir`, `dockerfile`, `build` (tool, runtime, versions, `build-command`, `pre-command`, `post-command`, `env`, `legacy`), `namespace`, `container-port`, `service-port`, `tests` (postman, playwright, artillery), `downstream`.
- The **resolve-stack** task reads the stack file and versions, then emits a single **stack-json** plus derived results. Downstream tasks (build, deploy, validate, test) only see this JSON and the pipeline params — they never read the raw YAML. So you can add new per-app or stack-level fields and, as long as resolve passes them through (or you extend resolve), the rest of the pipeline can use them without pipeline YAML changes.

**Derived values from the DAG (resolve-stack)**

| Result | Meaning |
|--------|--------|
| `stack-json` | Full graph + all app config (what downstream tasks consume). |
| `app-list` | **Topological order** of all apps (dependencies before dependents). Used for build order and as the full app list. |
| `entry-app` | **Entry point**: the app that no other app lists as downstream (e.g. frontend or root API). |
| `propagation-chain` | **Ordered chain from entry**: depth-first walk from `entry-app` following `downstream` edges. Used for header propagation validation and to understand the request path. |
| `build-apps` | Either the single `changed-app` (PR) or the full topo list (merge / full build). |
| `intercept-header-value` | Header value for this run (e.g. `x-dev-session:pr-42`) so intercepts and tests use the same session. |

So: **one stack file → one DAG → one resolved JSON → same pipeline for all stacks**, with arbitrary per-stack and per-app configuration.

### Intercepts for debugging (PR flow)

On PRs, the pipeline builds images, then **deploys one pod per built app** and configures **Telepresence intercepts** so that traffic carrying the PR’s header is routed to those PR pods instead of the normal staging deployment. That gives you “this PR’s code path” end-to-end for debugging.

**How it works**

1. **Intercept header**  
   `resolve-stack` sets `intercept-header-value` (e.g. `x-dev-session:pr-42`) from the stack’s `propagation.header-name` and the PR number. The same value is used for intercepts and for validation/tests.

2. **Per-app PR pods**  
   The **deploy-stack-intercepts** task, for each app in `build-apps`:
   - Reads from `stack-json` and `built-images`: image, namespace, container port, service port.
   - Creates a **Pod** with (1) the built image (PR build) and (2) a Telepresence sidecar.
   - The sidecar runs `telepresence intercept <app> --namespace <ns> --port <container>:<service> --http-match <intercept-header-value>`.
   - So any request that matches the header (e.g. `x-dev-session: pr-42`) to the **existing** Kubernetes Service for that app is intercepted and sent to this PR pod instead of the normal deployment.

3. **Arbitrary config support**  
   Namespace and ports come from the graph: per-app `namespace` / `container-port` / `service-port`, with fallback to `defaults`. So different stacks can use different namespaces and port layouts; the deploy task has no hardcoded stack shape.

4. **Propagation validation**  
   **validate-stack-propagation** uses `propagation-chain` (the ordered list from entry through all downstreams). It sends one request to the **entry** app with the intercept header (and W3C baggage/traceparent). It then checks that the response indicates the request flowed through the chain and that the header value appears where expected. For single-app stacks it reduces to a health check. This validates that the DAG’s request path and intercepts line up.

**End-to-end for a developer**

- Open the app (e.g. frontend) with a header `x-dev-session: pr-<PR#>`.  
- That request hits the entry service; Telepresence sends it to the PR pod for the entry app.  
- The entry app calls its downstreams (from the DAG); those requests carry the same header, so they are intercepted to the corresponding PR pods.  
- So the entire path from entry through the DAG runs the PR build, enabling debugging of the full stack for that PR.

**Summary**

- **DAG**: One stack YAML defines nodes (apps) and edges (`downstream`). Resolve computes topo order, entry, and propagation chain.  
- **Arbitrary config**: All behavior is driven by stack-json and params; pipelines stay generic.  
- **Intercepts**: One PR pod per built app, Telepresence sidecar, header-based routing so “this PR” traffic hits PR pods end-to-end for debugging.

### Stack Graph — Arbitrary DAG (examples)

A stack is a YAML file that declares apps and the directed edges between them. The graph is a pure DAG — any topology is valid. The `downstream` field on each app defines which apps it calls. The system computes topological order, entry points, and propagation chains from the graph at runtime.

Common patterns (but any shape works):

```
FE → middleware → persistence                    (3-tier)
FE → middleware → vendor-adapter                 (vendor integration)
                → persistence
                → notifications-svc              (fan-out)
standalone-api                                   (single node)
```

```yaml
name: stack-one
apps:
  - name: demo-fe
    role: frontend
    build:
      tool: npm
      runtime: vue
    downstream: [release-lifecycle-demo]
  - name: release-lifecycle-demo
    role: middleware
    build:
      tool: maven
      runtime: spring-boot
    downstream: [demo-api]
  - name: demo-api
    role: persistence
    build:
      tool: maven
      runtime: spring-boot
    downstream: []
propagation:
  header-name: x-dev-session
  baggage-key: dev-session
```

### Build Toolchains

Each app declares its build tool and runtime. The pipeline's compile step installs the right toolchain lazily and runs the build before Kaniko containerizes.

| Tool | Runtime | What it does | Example |
|------|---------|-------------|---------|
| `npm` | `vue` | `npm ci && npm run build` | Vue/React frontends |
| `maven` | `spring-boot` | `mvn -B clean package -DskipTests` | Spring Boot fat JAR |
| `maven` | `spring-legacy` | `mvn -B clean package -DskipTests` | Legacy Spring WAR (containerized in Tomcat/Jetty) |
| `gradle` | `spring-boot` | `./gradlew clean bootJar -x test` | Spring Boot via Gradle |
| `gradle` | `spring-legacy` | `./gradlew clean war -x test` | Legacy Spring WAR via Gradle |
| `composer` | `php` | `composer install --no-dev --optimize-autoloader` | PHP apps |
| `pip` | `flask` | `pip install -r requirements.txt` | Flask / Python apps |
| `none` | `custom` | Skip compile, Dockerfile-only | Pre-built or multi-stage Dockerfiles |

Every app has a `build-command` override if the defaults don't fit. Everything gets containerized — the Dockerfile in each repo handles the final image.

### Build customization and legacy requirements (Java, PHP, Python, etc.)

Each app can customize builds and satisfy legacy requirements in one place under `build`:

| Field | Purpose | Example use |
|-------|---------|-------------|
| `build-command` | Override the default compile command | `mvn -B clean package -P legacy -DskipTests` |
| `pre-command` | Run before the main build (same dir) | Apply patches, install legacy deps, set up env |
| `post-command` | Run after the main build | Repackage, sign artifacts, copy legacy assets |
| `env` | Extra env vars for the build (key/value) | `JAVA_HOME`, `NODE_OPTIONS`, custom config paths |
| `legacy` | Tool/runtime-specific env vars | `MAVEN_OPTS`, `GRADLE_OPTS`, `COMPOSER_*`, `PIP_*` |

**Java (Maven/Gradle)** — use `legacy` and/or `env` for JVM/build opts; use `pre-command`/`post-command` for one-off steps:

```yaml
build:
  tool: maven
  runtime: spring-boot
  java-version: "17"
  build-command: "mvn -B clean package -P legacy-profile -DskipTests"
  env:
    JAVA_HOME: "/usr/lib/jvm/java-17-openjdk-amd64"
  legacy:
    MAVEN_OPTS: "-Xmx2g -Dlegacy.mode=true"
    JAVA_TOOL_OPTIONS: "-Dfile.encoding=UTF-8"
  pre-command: "apply-legacy-patches.sh || true"
```

**PHP (Composer)** — use `legacy` for Composer/PHP env; use `pre-command` for extensions or ini:

```yaml
build:
  tool: composer
  runtime: php
  php-version: "8.2"
  legacy:
    COMPOSER_MEMORY_LIMIT: "1G"
    COMPOSER_NO_INTERACTION: "1"
  pre-command: "phpenv config-add legacy.ini 2>/dev/null || true"
```

**Python (pip)** — use `legacy` for pip env; use `pre-command` for venv or constraints:

```yaml
build:
  tool: pip
  runtime: flask
  python-version: "3.11"
  env:
    PIP_DISABLE_PIP_VERSION_CHECK: "1"
  legacy:
    PIP_CONSTRAINT: "constraints.txt"
    PIP_EXTRA_INDEX_URL: "https://internal-pypi.example.com/simple"
  pre-command: "python3 -m venv .venv && . .venv/bin/activate"
  build-command: "pip install -r requirements.txt && pip install -e ."
```

All of `env`, `legacy`, `pre-command`, and `post-command` are optional. The pipeline runs in order: **pre-command → (tool build) → post-command**. Define these in each app's `build` section in the stack YAML (e.g. `stacks/single-app.yaml`, `stacks/stack-one.yaml`).

### Versioning — Independent of Application Code

`stacks/versions.yaml` lives in this infrastructure repo, not in any app repo. It's the platform-level version registry.

```
PR passes  →  bump RC  →  image pushed as v0.1.0-rc.4
                           ↓
                     stays as RC in registry
                           ↓
Merge      →  promote  →  full build  →  image pushed as v0.1.0
                           ↓
                     available for production promotion
                           ↓
Production →  Argo Rollouts / release.sh promotes v0.1.0
```

| Event | Version Change | Image Tag in Registry |
|-------|---------------|----------------------|
| PR build passes | `0.1.0-rc.3` → `0.1.0-rc.4` | `v0.1.0-rc.4` |
| PR merged to develop | `0.1.0-rc.4` → released `0.1.0`, next `0.1.1-rc.0` | `v0.1.0` |
| Production promote | (no version change) | Argo Rollouts switches traffic to `v0.1.0` |

You can **override any version** at run time by passing `version-overrides` (a JSON map) to the pipeline. This lets you pin specific versions for a stack without editing `versions.yaml`:

```bash
./scripts/generate-run.sh --mode pr --repo demo-fe --pr 42 \
  --version-overrides '{"demo-fe":"1.0.0-rc.0","demo-api":"0.5.0-rc.2"}'
```

For **major/minor** bumps, edit `versions.yaml` manually (e.g. change `0.1.1-rc.0` to `1.0.0-rc.0`).

### Header Propagation — Three Roles

Every app in a stack has a **propagation role** that defines its responsibility in the baggage chain. Any of the three can be the intercepted app in a PR build — the app code must be correct for its role regardless.

| Role | Behavior | App Code Must... |
|------|----------|-----------------|
| **originator** | Starts the baggage chain | Set `baggage` and `x-dev-session` headers on ALL outgoing requests |
| **forwarder** | Accepts and forwards | Parse incoming baggage, store in context (OTel/Feign), propagate on ALL outgoing calls |
| **terminal** | Accepts, never forwards | Accept the header for routing/logging — no downstream propagation needed |

```yaml
apps:
  - name: demo-fe
    propagation-role: originator     # sets headers
    downstream: [release-lifecycle-demo]
  - name: release-lifecycle-demo
    propagation-role: forwarder      # accepts + forwards
    downstream: [demo-api]
  - name: demo-api
    propagation-role: terminal       # accepts, end of chain
    downstream: []
```

For a PR numbered 42, the header flows:

```
Browser → demo-fe (originator: SETS baggage=dev-session=pr-42, x-dev-session=pr-42)
              → release-lifecycle-demo (forwarder: ACCEPTS header, FORWARDS via Feign/OTel)
                  → demo-api (terminal: ACCEPTS header, end of chain)
```

**The header only needs to propagate up to the intercepted app.** Beyond the intercept, downstream calls are normal -- there's no Telepresence intercept on those services, so the header doesn't need to be there.

**Intercepted originator** (FE PR): the PR build must set headers on outgoing requests. If there are other intercepted apps downstream, they need the header to route correctly. If the FE is the only intercepted app, the header still needs to reach it (but that's handled by the test harness sending it in).

**Intercepted forwarder** (middleware PR): Telepresence routes matching traffic to the PR pod of B. B's downstream calls to C and D go to their normal deployments — no intercept to match on, so **B does not need to forward the header**. Exception: if both B and C are intercepted in the same PR, B must forward so C's intercept catches it.

**Intercepted terminal** (API PR): the header reached it via Telepresence, end of the line. No forwarding needed.

```
A(originator) → B(forwarder) → C(terminal)
                              → D(terminal)

If B is intercepted:
  header: test → A → B(PR) ✓    (Telepresence routes to PR B)
  B → C: normal call            (C has no intercept, header not needed)
  B → D: normal call            (D has no intercept, header not needed)

If C is intercepted:
  header: test → A → B → C(PR) ✓  (A originates, B forwards, C intercepts)
  B → D: normal call               (D not intercepted)

If B AND C are intercepted:
  header: test → A → B(PR) → C(PR) ✓  (B MUST forward — C has an intercept)
  B → D: normal call                    (D not intercepted)
```

#### Required App Code by Role

**Originator (e.g. Vue frontend)**:
```javascript
// Axios interceptor — sets baggage on every outgoing request
apiClient.interceptors.request.use((config) => {
  const session = import.meta.env.VITE_DEV_SESSION;
  if (session) {
    config.headers["baggage"] = `dev-session=${session}`;
    config.headers["x-dev-session"] = session;
  }
  return config;
});
```

**Forwarder (e.g. Spring Boot middleware)**:
```java
// Feign interceptor — reads baggage from context, forwards to downstream
@Bean
public RequestInterceptor devSessionInterceptor() {
  return template -> {
    String session = Baggage.fromContext(Context.current())
        .getEntryValue("dev-session");
    if (session != null && !session.isBlank()) {
      template.header("x-dev-session", session);
    }
  };
}
```

**Forwarder (e.g. Flask middleware)**:
```python
# Flask — reads incoming header, attaches to outgoing requests
@app.before_request
def propagate_baggage():
    g.dev_session = request.headers.get("x-dev-session")

def call_downstream(url):
    headers = {}
    if hasattr(g, "dev_session") and g.dev_session:
        headers["x-dev-session"] = g.dev_session
        headers["baggage"] = f"dev-session={g.dev_session}"
    return requests.get(url, headers=headers)
```

**Terminal (any language)**: just accept the header — no code needed beyond what the framework/OTel agent already does for routing.

The `validate-propagation` task sends a request through the entry point (originator), verifies the header reaches every downstream hop, and checks that each app behaved according to its role. For single-app stacks this degrades to a health check.

## Directory Structure

```
tekton-job-standardization/
├── README.md
├── stacks/
│   ├── registry.yaml            # repo → stack mapping
│   ├── versions.yaml            # per-app version registry (infra-level)
│   ├── stack-one.yaml           # Vue FE → Spring Boot BFF → Spring Boot API
│   ├── stack-two-vendor.yaml    # Vue + Spring Boot + PHP + Legacy Spring + Flask
│   ├── single-app.yaml          # Standalone Spring Boot service
│   └── single-flask-app.yaml    # Standalone Flask service
├── tasks/
│   ├── resolve-stack.yaml       # Parse graph, topo sort, resolve versions
│   ├── build-app.yaml           # Compile (npm/maven/gradle/composer/pip) + Kaniko
│   ├── deploy-intercept.yaml    # PR pods with Telepresence intercepts
│   ├── validate-propagation.yaml    # Header flow validation
│   ├── run-stack-tests.yaml     # Postman / Playwright / Artillery per app
│   ├── version-bump.yaml        # RC bump (PR) or release promote (merge)
│   ├── tag-release-images.yaml  # crane re-tag with clean semver
│   └── cleanup-stack.yaml       # Delete all PR pods (finally task)
├── pipeline/
│   ├── stack-pr-pipeline.yaml       # Universal PR pipeline
│   ├── stack-merge-pipeline.yaml    # Universal merge/release pipeline
│   ├── stack-dag-verify-pipeline.yaml # Minimal pipeline (fetch + resolve) for DAG verification
│   └── triggers.yaml                # EventListener + bindings + templates
└── scripts/
    ├── stack-graph.sh           # CLI: parse / validate / query stack graphs
    ├── generate-run.sh          # Generate PipelineRun YAML for manual runs
    ├── verify-dag-phase1.sh     # Phase 1 DAG verification (no cluster)
    ├── verify-dag-phase2.sh     # Phase 2 DAG verification (Tekton resolve vs CLI)
    ├── kind-with-registry.sh    # Create kind cluster + local registry (localhost:5000)
    ├── install-tekton.sh        # Install Tekton Pipelines + git-clone + stack tasks/pipelines
    └── install-telepresence-traffic-manager.sh  # Install Traffic Manager for PR intercepts
```

## Pipeline Flows

### PR Flow (`stack-pr-test`)

```
  fetch-source
       │
  resolve-stack      ← reads stack YAML + versions.yaml, merges overrides
       │
  bump-rc-version    ← 0.1.0-rc.3 → 0.1.0-rc.4 (determines the image tag)
       │
  build-apps         ← compile per toolchain, Kaniko pushes v0.1.0-rc.4
       │
  deploy-intercepts  ← PR pods + Telepresence for each built app
       │
  validate-propagation  ← verifies header flows through all hops
       │
  run-tests          ← Postman, Playwright, Artillery per app
       │
  push-version-commit  ← records the RC bump back to repo
       │
  [finally: cleanup] ← delete all PR pods
```

### Merge Flow (`stack-merge-release`)

```
  fetch-source
       │
  resolve-stack
       │
  release-version    ← 0.1.0-rc.4 → released 0.1.0, next dev 0.1.1-rc.0
       │
  build-apps         ← full deployment build
       │
  tag-release        ← crane re-tags image as v0.1.0 in registry
       │
  push-version-commit  ← records release + next dev cycle back to repo
```

## Usage

### Manual Pipeline Runs

```bash
# PR test for demo-fe, PR #42
./scripts/generate-run.sh \
  --mode pr --repo demo-fe --pr 42 | kubectl create -f -

# PR test with version overrides
./scripts/generate-run.sh \
  --mode pr --repo demo-fe --pr 42 \
  --version-overrides '{"demo-fe":"2.0.0-rc.0"}' | kubectl create -f -

# Merge release for demo-api
./scripts/generate-run.sh \
  --mode merge --repo demo-api | kubectl create -f -

# Dry-run (just print YAML)
./scripts/generate-run.sh --mode pr --repo demo-fe --pr 42
```

### Running Tekton locally (no AWS, no Argo)

You can run **both** the build pipelines and the **full PR pipeline** (deploy intercepts, validate propagation, run tests) on a **local Kubernetes cluster**. No AWS, no Argo CD required.

**Verification plan:** For a step-by-step plan to verify the stack **DAG structure** locally (script checks → resolve task in Tekton → full pipeline behavior), see [docs/local-dag-verification-plan.md](docs/local-dag-verification-plan.md).

**Standalone local repo:** To work in a new git repo with no AWS and paths at repo root (easier for local runs and Phase 2 clone), run `./scripts/extract-standalone-repo.sh [OUTPUT_DIR]`. This copies the milestone into a new tree with `stacks/`, `tasks/`, etc. at root and a README + SHARING-BACK.md for contributing back when it works. See the script for next steps (`git init`, remote, push).

- **Full PR pipeline** (`stack-pr-test`): clone → resolve → bump RC → build apps → deploy PR pods + Telepresence intercepts → validate header propagation → run tests (Postman/Playwright/Artillery) → push version → cleanup. Use this for full local testing.
- **Merge pipeline** (`stack-merge-release`): clone → resolve → release version → build apps → tag and push images. Use this for build-only validation or release simulation.

**1. Kind cluster + local registry (recommended for local builds)**

From the milestone dir (or repo root with the right path):

```bash
# Create kind cluster and a local registry at localhost:5000
./scripts/kind-with-registry.sh

# Optional: custom name or port
./scripts/kind-with-registry.sh --name tekton-stack --port 5000
```

Then install Tekton and this repo’s tasks/pipelines:

```bash
./scripts/install-tekton.sh
```

Install the **Telepresence Traffic Manager** so the full PR pipeline (deploy intercepts, validate propagation, run tests) can route traffic to PR pods:

```bash
./scripts/install-telepresence-traffic-manager.sh
```

(Optional: `--version 2.20.0` to match the sidecar image in `deploy-intercept`; default is 2.20.0.)

**1b. Other local clusters (minikube, k3d)**

Create a cluster with [minikube](https://minikube.sigs.k8s.io/) or [k3d](https://k3d.io/). Install Tekton Pipelines and the **Telepresence Traffic Manager** (so the full PR pipeline can run intercepts). Apply this repo’s tasks and pipelines (and the git-clone task from the Tekton catalog if needed):

```bash
kubectl apply -f tasks/
kubectl apply -f pipeline/
```

**2. Container registry**

With **kind + local registry** (from step 1), use `--registry localhost:5000`. From the host you push/pull `localhost:5000/<image>:<tag>`; the cluster is configured to use the same registry. For other clusters, pass your registry (e.g. Docker Hub `docker.io/<user>`, GCR `gcr.io/<project>`).

**3. Storage class (non-AWS)**

Default is `gp3` (AWS). For kind/minikube, omit it so the cluster default is used:

```bash
./scripts/generate-run.sh --mode pr --repo demo-fe --pr 42 \
  --registry localhost:5000 --storage-class ""
```

**4. Service account**

Create `tekton-pr-sa` in namespace `tekton-pipelines` with permissions to clone the repo, push to your registry, and create/delete pods (for deploy-intercept and cleanup). Add image pull/push secrets as needed.

**Example: full PR pipeline (build + deploy + validate + tests) locally**

```bash
./scripts/generate-run.sh --mode pr --repo demo-fe --pr 42 \
  --registry localhost:5000 --storage-class "" | kubectl create -f -
```

**Example: build only (merge pipeline) locally**

```bash
./scripts/generate-run.sh --mode merge --repo demo-fe \
  --registry localhost:5000 --storage-class "" | kubectl create -f -
```

### Querying the Stack Graph

```bash
# Full graph as JSON
./scripts/stack-graph.sh stacks/stack-one.yaml

# Topological build order
./scripts/stack-graph.sh stacks/stack-one.yaml --topo
# → demo-fe release-lifecycle-demo demo-api

# Entry point
./scripts/stack-graph.sh stacks/stack-one.yaml --entry
# → demo-fe

# Propagation chain from entry
./scripts/stack-graph.sh stacks/stack-one.yaml --chain demo-fe
# → demo-fe release-lifecycle-demo demo-api

# Validate (no cycles, all downstream refs resolve)
./scripts/stack-graph.sh stacks/stack-one.yaml --validate
# → VALID
```

### Adding a New App to an Existing Stack

1. Add the app entry to the stack YAML with `downstream` links and `build` config.
2. Add a version entry in `stacks/versions.yaml`.
3. Add the repo → stack mapping in `stacks/registry.yaml`.
4. Update the CEL overlay in `pipeline/triggers.yaml`.

### Creating a New Stack

1. Create `stacks/my-stack.yaml` following the schema.
2. Add version entries for each app.
3. Add all repo → stack mappings in `registry.yaml`.
4. Update the CEL overlay in `triggers.yaml`.
5. Validate: `./scripts/stack-graph.sh stacks/my-stack.yaml --validate`

## Onboarding Checklist

- [ ] Stack YAML created in `stacks/` with `build` config per app
- [ ] `versions.yaml` entries added for each app
- [ ] `registry.yaml` mapping added for each repo
- [ ] CEL overlay in `triggers.yaml` updated
- [ ] `./scripts/stack-graph.sh stacks/<stack>.yaml --validate` passes
- [ ] Tekton tasks applied: `kubectl apply -f tasks/`
- [ ] Pipelines applied: `kubectl apply -f pipeline/`
- [ ] GitHub webhook configured to point at `el-stack-event-listener`

## Architecture Diagrams

See [docs/c4-diagrams.md](docs/c4-diagrams.md) for the full C4 diagram set:
- **Level 1 — System Context**: external actors and systems
- **Level 2 — Container**: pipelines, config stores, CLI scripts
- **Level 3 — Component**: task-level internals for PR and merge pipelines
- **Dynamic — Intercept Scenarios**: sequence diagrams for every intercept combination (originator, forwarder, terminal, multi-intercept)
- **Dynamic — Version Lifecycle**: state diagram of RC → release → next dev cycle
- **Dynamic — Build Toolchain Selection**: how the compile step branches per app
- **Dynamic — Stack Graph Resolution**: how `resolve-stack` processes an arbitrary DAG

## Architecture Notes

- **One pipeline, any stack**: The `resolve-stack` task is the adapter layer. It reads the stack YAML at runtime and emits structured data that downstream tasks consume. No pipeline YAML changes needed per stack.
- **Any DAG topology**: The graph is defined by `downstream` edges. FE → middleware → persistence, FE → middleware → vendor, middleware → middleware chains, single-node stacks — all work the same way. Nothing is hardcoded about the shape.
- **Multi-toolchain**: npm, Maven, Gradle, Composer, pip all work in the same pipeline run. The compile step installs tools lazily and branches per app. Everything gets containerized via Kaniko + each repo's Dockerfile.
- **Versions are infrastructure-level**: `versions.yaml` lives in this platform repo, independent of app code. You pick the version set you want and pass it into the job. Overrides are first-class.
- **RC until promoted**: Every passing PR build pushes an RC-tagged image to the registry. It stays as RC until merge promotes it to a release version. Production promotion is a separate step via Argo Rollouts.
- **Version isolation**: Each app versions independently. A PR to `demo-api` only bumps `demo-api`'s RC. A merge only releases the merged app's version.
