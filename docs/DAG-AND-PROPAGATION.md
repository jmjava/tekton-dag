# DAG, propagation roles (baggage), and intercepts

This doc explains: (1) what the **DAG** is, (2) the **three app types** that handle **baggage** (header propagation), and (3) how that ties to **intercepting** and **which app has changes**.

---

## 1. The DAG (directed acyclic graph)

A **stack** is a single YAML file that defines a **directed acyclic graph** of applications.

- **Nodes** = apps (e.g. `demo-fe`, `release-lifecycle-demo`, `demo-api`). Each has a repo, build tool, ports, tests, and a list of **downstream** apps it calls.
- **Edges** = `downstream: [app-a, app-b]`. Meaning: “this app makes requests to these apps.” So the edge direction is **caller → callee** (e.g. frontend → middleware → API).
- **No cycles** — the graph must be a DAG. The pipeline runs a topological sort; if there’s a cycle, resolve fails.

From this graph the pipeline derives:

| Derived value | Meaning |
|---------------|--------|
| **Topological order** | Build order: dependencies before dependents (e.g. `demo-fe` → `release-lifecycle-demo` → `demo-api`). |
| **Entry app** | The node no one lists as downstream — usually the frontend or the single API. All test traffic enters here. |
| **Propagation chain** | Ordered path from entry through downstreams (used to validate that the header flows along the request path). |
| **build-apps** | On a **PR**: only the app(s) that changed (the repo whose PR triggered the run). On **merge** or full build: all apps in topo order. |

So: **one stack YAML → one DAG → one pipeline**. The same PR and merge pipelines run for every stack; behavior is entirely driven by the graph and params (e.g. `changed-app`, `pr-number`).

---

## 2. Three propagation roles (how apps handle baggage)

Traffic is tagged with a **session header** (e.g. `x-dev-session: pr-42`) and optionally **W3C Baggage** (and traceparent) so we can route “this PR’s” requests to the right pods and validate propagation. The stack defines a **propagation** section (e.g. `header-name: x-dev-session`, `baggage-key: dev-session`, `strategy: w3c-baggage`). Each app has a **propagation role** that defines how it handles that header/baggage:

| Role | Who they are | Responsibility with baggage/header |
|------|----------------|------------------------------------|
| **Originator** | Entry app (usually the frontend). No other app lists it as downstream. | **Sets** the header (and baggage) on **all outgoing** requests. The first hop that attaches the dev-session so downstream calls can be identified. |
| **Forwarder** | Middle apps that have both upstream and downstream (e.g. BFF, middleware). | **Accepts** the header/baggage on incoming requests, stores it in context, and **forwards** it on outgoing requests to downstreams. Needed so that when a **terminal** or another forwarder downstream is the one being intercepted, the header still reaches it. |
| **Terminal** | Apps that have no downstream (leaf nodes: APIs, backends). | **Accepts** the header/baggage for routing/logging but **does not forward** (no outgoing service calls). |

Roles can be set explicitly in the stack YAML with `propagation-role: originator | forwarder | terminal`. If omitted, resolve-stack infers them: no downstream → `terminal`; frontend role → `originator`; else → `forwarder`.

**Example (stack-one):**

- `demo-fe` (frontend) → **originator**: sets `x-dev-session` (and baggage) on requests to `release-lifecycle-demo`.
- `release-lifecycle-demo` (BFF) → **forwarder**: receives header, stores in context, forwards when calling `demo-api`.
- `demo-api` (API) → **terminal**: receives header, uses it for routing/logging, does not call other apps.

So: **originator** starts the chain, **forwarder** carries it through the middle, **terminal** ends the chain. That’s how “this PR’s” traffic is consistently tagged end-to-end.

---

## 3. Intercepting and “which app has changes”

### What “intercept” means

On a **PR run**, the pipeline:

1. Builds only the **changed app(s)** — i.e. the app whose repo had the PR (the `changed-app` param, e.g. `demo-fe` or `release-lifecycle-demo`). That becomes **build-apps** (one or more apps).
2. Deploys **one PR pod per built app**, each running the PR’s image, with a **Telepresence** sidecar.
3. Configures Telepresence to **intercept** traffic that matches the run’s header (e.g. `x-dev-session: pr-42`): requests to the **existing** Kubernetes Service for that app are sent to the **PR pod** instead of the normal (e.g. staging) deployment.

So: **“intercepted”** = “this app’s traffic, when it carries the PR header, is routed to the PR build of that app.” The app that **has changes** is exactly the app (or set of apps) in **build-apps** — the one(s) we built and deployed as PR pods. That’s the app “being intercepted” for that run.

### How baggage/header relates to intercepting

- The **same header** (e.g. `x-dev-session: pr-42`) is used for:
  - Telepresence intercept matching (route to PR pod when request has this header).
  - Validation: **validate-stack-propagation** sends a request from the entry with this header and checks it flows along the propagation chain and appears where expected.
  - Your own testing: you hit the entry with this header so the whole path uses “this PR’s” code where intercepts are active.
- So that **one header value** ties together: “which run,” “which PR’s build,” and “which traffic gets routed to PR pods.”

### Why the three roles matter for intercepts

- **Originator** must set the header so that any request from the user (or test harness) into the entry carries the session; then Telepresence can route that first hop to the entry’s PR pod if the entry is the changed app.
- **Forwarder** must accept and **forward** the header so that when the **changed app** is a downstream service (e.g. `demo-api`), the request from the forwarder to that service still carries the header and Telepresence can route it to the API’s PR pod.
- **Terminal** only needs to accept (and optionally log); it doesn’t forward. If the terminal is the changed app, the forwarder (or originator) must have sent the header so the terminal’s intercept can match.

So:

- **Which app has changes?** → The app(s) in **build-apps** (on a PR, the `changed-app`).
- **Which app is “intercepted”?** → Exactly those same apps: we deploy PR pods only for **build-apps** and attach intercepts for them; traffic that carries the run’s header is routed to those pods.
- **How does baggage fit in?** → The three roles (originator / forwarder / terminal) define who **sets**, **forwards**, or **only accepts** the header/baggage so that intercepts can work no matter which node in the DAG is the one that changed.

---

## 4. Quick reference

| Concept | Meaning |
|--------|--------|
| **DAG** | Stack = graph of apps; edges = `downstream` (caller → callee). Topo order, entry, propagation chain and build-apps come from this. |
| **Originator** | Entry app; **sets** header/baggage on outgoing requests. |
| **Forwarder** | Middle app; **accepts** and **forwards** header/baggage to downstreams. |
| **Terminal** | Leaf app; **accepts** header/baggage, does not forward. |
| **build-apps** | On PR = changed app(s); on merge = all apps. Only these are built and get PR pods (intercepts). |
| **Intercept** | Telepresence routes requests with the run’s header to the PR pod for that app. |
| **“Which app has changes”** | The app whose PR triggered the run = the single **changed-app** (and thus in **build-apps**); that’s the app being intercepted for that run. |

For sequence diagrams that show intercept scenarios (originator only, forwarder only, terminal only, or multiple intercepted), see [docs/c4-diagrams.md](c4-diagrams.md) (“Dynamic Diagram: PR Intercept Scenarios”).
