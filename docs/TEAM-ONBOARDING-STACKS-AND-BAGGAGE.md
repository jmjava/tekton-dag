# Team onboarding: baggage libraries and new application stacks

This guide is for **teams adopting tekton-dag** who need to:

1. **Propagate the dev-session header** (`x-dev-session` by default) and W3C Baggage through their services so PR intercepts and validation tasks work.
2. **Define a new stack** (DAG of repos) and wire it into a team deployment.

**Prerequisites:** read [DAG-AND-PROPAGATION.md](DAG-AND-PROPAGATION.md) for propagation roles and intercept behavior, and [CUSTOMIZATION.md](CUSTOMIZATION.md) for Helm, registries, and pipeline hooks. For environment naming (validation vs production), see [ENVIRONMENTS-AND-CLUSTERS.md](ENVIRONMENTS-AND-CLUSTERS.md).

---

## 1. Baggage / header-forwarding libraries (by runtime)

Each app in the propagation chain must **read** incoming baggage (or the plain header), keep it in request context, and **attach** it on outbound calls—except **terminals**, which only consume it. The platform ships **standalone libraries** under `libs/`; sample apps in sibling repos (e.g. `tekton-dag-vue-fe`) also demonstrate integration.

| Runtime / stack | Library (Maven npm pip composer) | Code in this repo | Documentation |
|-----------------|----------------------------------|-------------------|---------------|
| **Spring Boot 2.x+** | `com.tektondag:baggage-spring-boot-starter` | [`libs/baggage-spring-boot-starter`](../libs/baggage-spring-boot-starter) | [README](../libs/baggage-spring-boot-starter/README.md) |
| **Java servlet / legacy Spring (WAR)** | `com.tektondag:baggage-servlet-filter` | [`libs/baggage-servlet-filter`](../libs/baggage-servlet-filter) | [README](../libs/baggage-servlet-filter/README.md) |
| **Python / Flask** | `tekton-dag-baggage` (pip) | [`libs/baggage-python`](../libs/baggage-python) | [README](../libs/baggage-python/README.md) |
| **Node.js / browser (Vue, etc.)** | `@tekton-dag/baggage` | [`libs/baggage-node`](../libs/baggage-node) | [README](../libs/baggage-node/README.md) |
| **PHP (PSR-15 + Guzzle)** | `tekton-dag/baggage-middleware` | [`libs/baggage-php`](../libs/baggage-php) | [README](../libs/baggage-php/README.md) |

### Configuration pattern (all libraries)

- **Roles** align with the stack YAML: `originator` | `forwarder` | `terminal` (Spring uses uppercase enum names in properties).
- **Activation** is gated so production installs stay safe: enable only in dev/CI via env or build profiles (each README documents **production safety**).
- **Defaults** match the platform: header `x-dev-session`, W3C baggage key `dev-session`, unless your stack overrides `propagation.header-name` / `baggage-key` in YAML—then configure the libraries to the **same** names.

### Quick integration notes

| Library | Incoming requests | Outgoing requests |
|---------|-------------------|-------------------|
| **Spring Boot starter** | Auto-configured filter | `RestTemplate` interceptor (auto) |
| **Servlet filter** | `web.xml` or programmatic filter | Your code must copy context to outbound clients |
| **Flask** | `init_app` middleware | `BaggageSession` helper for HTTP calls |
| **Node** | Config + fetch wrapper or **Axios** interceptor | `createBaggageFetch` / `createAxiosInterceptor` |
| **PHP** | `BaggageMiddleware` | `GuzzleMiddleware` on `HandlerStack` |

### Historical note

[M4 baggage overview](m4-baggage-libraries-overview.md) described middleware **embedded** in sample repos before M4.1 extraction. Prefer the **`libs/*` packages** above for new work; the overview remains useful for context.

---

## 2. How to create a new application stack (team checklist)

A **stack** is one YAML file: a DAG of `apps`, each with a GitHub `repo`, `build` tool, `downstream` edges, tests, and a **`propagation-role`**. The orchestrator and pipelines resolve this file at runtime (shared logic also lives in [`libs/tekton-dag-common`](../libs/tekton-dag-common) for tests and tooling).

### Step A — Model the graph

1. List every deployable service and **which service calls which** (caller → callee).
2. Ensure the graph is a **DAG** (no cycles).
3. Assign **propagation roles** (or let resolve infer them—see [DAG-AND-PROPAGATION.md](DAG-AND-PROPAGATION.md)):
   - One **originator** at the user-facing entry (usually frontend).
   - **Forwarders** on middle hops.
   - **Terminals** on leaves (no `downstream`).

### Step B — Implement baggage in each app repo

For each service, add the matching library from §1, configure **role** and **enabled** flags for non-production builds, and verify outbound clients propagate the header. Add automated tests where the library provides them.

### Step C — Author `stacks/<your-stack>.yaml`

Use [`stacks/stack-one.yaml`](../stacks/stack-one.yaml) as a template. Each app typically needs:

| Field | Purpose |
|-------|---------|
| `name` | Unique app id in the stack (used in pipelines and orchestrator). |
| `repo` | `org/repo` on GitHub (must match webhook / registry mapping). |
| `role` | Semantic role (`frontend`, `middleware`, `persistence`, …)—documentation and tooling. |
| `propagation-role` | `originator` \| `forwarder` \| `terminal`. |
| `context-dir`, `dockerfile` | Build context for Kaniko. |
| `build` | `tool` (`npm`, `maven`, `gradle`, `pip`, `composer`), versions, `build-command`. |
| `downstream` | List of app **names** this service calls. |
| `tests` | Optional `postman`, `playwright`, `artillery` paths **as stored in that app repo**. |

Repeat **`propagation:`** at the top if you use non-default header/key (keep libs in sync).

### Step D — Register the stack with a team

1. Add the file under `stacks/` and reference it from **`teams/<team>/team.yaml`** in the `stacks:` list.
2. Copy the stack into the Helm chart raw path when packaging—see [CUSTOMIZATION.md §1](CUSTOMIZATION.md) (`helm/tekton-dag/package.sh`, `raw/stacks/`).
3. Align **`teams/<team>/values.yaml`** (`stackFile`, `imageRegistry`, `gitUrl`, orchestrator image, intercept backend).

### Step E — Orchestrator registry mapping

The orchestrator must map **GitHub repo → stack + app**. If you add new repos, extend the platform config (ConfigMap / Helm templates that load stack definitions and repo registry)—see [m10-multi-team-architecture.md](m10-multi-team-architecture.md) and orchestrator tests for how stacks are loaded.

### Step F — CI images and pipeline apply

1. Ensure **compile images** exist for your toolchains ([CUSTOMIZATION.md §3](CUSTOMIZATION.md), [§7](CUSTOMIZATION.md)).
2. Apply **tasks and pipelines** to the team namespace (or use the chart).
3. Run a **bootstrap** then a **PR** pipeline against the validation cluster; confirm **validate-propagation** and **validate-original-traffic** pass.

### Step G — Docs and ownership

Document your stack name, entry URL, and who owns each repo. Link runbooks to [PR-TEST-FLOW.md](PR-TEST-FLOW.md) and [REGRESSION.md](REGRESSION.md) for local verification.

---

## 3. Related documents

| Topic | Document |
|-------|----------|
| Role semantics & intercepts | [DAG-AND-PROPAGATION.md](DAG-AND-PROPAGATION.md) |
| Teams, Helm, hooks, tool versions | [CUSTOMIZATION.md](CUSTOMIZATION.md) |
| Multi-team Helm layout | [m10-multi-team-architecture.md](m10-multi-team-architecture.md) |
| M4 library history | [m4-baggage-libraries-overview.md](m4-baggage-libraries-overview.md) |
| Publishing / consuming libraries | [m41-publishing-strategy.md](m41-publishing-strategy.md) |
