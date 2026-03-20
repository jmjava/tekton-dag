---
theme: default
title: "tekton-dag: Stack-Aware CI/CD with Traffic Interception"
info: |
  Narrated demo companion deck — all diagrams generated from code.
class: text-center
drawings:
  persist: false
transition: slide-left
---

# tekton-dag

**Stack-Aware CI/CD with Header-Based Traffic Interception**

Built on Tekton Pipelines · Polyglot · Multi-team

---

## Architecture

```mermaid
graph LR
    GH[GitHub Webhook] --> O[Orchestrator<br/>Flask :8080]
    O --> PR[PR Pipeline]
    O --> BS[Bootstrap Pipeline]
    O --> MR[Merge Pipeline]
    PR --> K8s[Kubernetes Cluster]
    BS --> K8s
    MR --> K8s
    K8s --> TR[(Tekton Results<br/>Postgres)]
    K8s --> N4[(Neo4j<br/>Test Graph)]
    GUI[Management GUI<br/>Vue + Flask] --> O
```

<div class="text-sm mt-4 opacity-70">
Webhook → Orchestrator → PipelineRun → Kubernetes · Results DB · Test Graph
</div>

---

## Stack DAG — The Core Model

```mermaid
graph LR
    FE["demo-fe<br/>(Vue · originator)"] --> BFF["BFF<br/>(Spring Boot · forwarder)"]
    BFF --> API["demo-api<br/>(Spring Boot · terminal)"]
```

Each app declares:
- **Build tool**: npm, Maven, Gradle, pip, Composer
- **Propagation role**: originator → forwarder → terminal
- **Tests**: Postman, Playwright, Artillery

Stack YAML is the single source of truth.

---

## Polyglot — 5 Build Toolchains

| Tool | Languages | Version variants |
|------|-----------|-----------------|
| **npm** | Node 18, 20, 22 | `tekton-dag-build-node:node22` |
| **Maven** | Java 11, 17, 21 | `tekton-dag-build-maven:java21` |
| **Gradle** | Java 11, 17, 21 | `tekton-dag-build-gradle:java17` |
| **pip** | Python 3.10–3.12 | `tekton-dag-build-python:python312` |
| **Composer** | PHP 8.1–8.3 | `tekton-dag-build-php:php83` |

Parameterized Dockerfiles + `build-and-push.sh --matrix`

---

## Header Propagation — x-dev-session

```mermaid
sequenceDiagram
    participant User
    participant FE as demo-fe (originator)
    participant BFF as BFF (forwarder)
    participant API as demo-api (terminal)
    User->>FE: GET / + x-dev-session: pr-42
    FE->>BFF: forward + header preserved
    BFF->>API: forward + header preserved
    API-->>BFF: 200 OK
    BFF-->>FE: 200 OK
    FE-->>User: 200 OK
```

Header propagation enables per-request routing to PR builds.

---

## PR Pipeline — Build Only What Changed

```mermaid
graph TD
    A[fetch-source] --> B[resolve-stack]
    B --> C[clone-app-repos]
    C --> D[pr-snapshot-tag]
    D --> E{build-select-tool}
    E -->|npm| F1[compile-npm]
    E -->|maven| F2[compile-maven]
    E -->|gradle| F3[compile-gradle]
    F1 & F2 & F3 --> G[containerize / Kaniko]
    G --> H[deploy-intercepts]
    H --> I[validate-propagation]
    I --> J[validate-original-traffic]
    J --> K[query-test-plan]
    K --> L[run-tests]
    L --> M[cleanup + pr-comment]
```

---

## Intercept Routing — PR vs Normal Traffic

```mermaid
graph LR
    subgraph "Same Cluster"
        FE[demo-fe]
        BFF[BFF]
        API_prod[demo-api<br/>production]
        API_pr[demo-api<br/>PR-42 build]
    end
    User1["🔵 Normal request<br/>(no header)"] --> FE --> BFF --> API_prod
    User2["🟢 PR request<br/>(x-dev-session: pr-42)"] --> FE --> BFF --> API_pr
```

- **Telepresence** or **mirrord** — one parameter switch
- Multiple concurrent PRs, each isolated by header value
- Cleanup in pipeline `finally` block

---

## Local Debug with mirrord

```mermaid
graph LR
    subgraph Cluster
        FE[demo-fe] --> BFF[BFF] --> POD[demo-api pod]
    end
    POD -.->|mirrord tunnel| IDE["💻 Local IDE<br/>breakpoint set"]
```

- `mirrord exec` mirrors cluster traffic to your laptop
- Real requests, real headers, real downstream calls
- Full breakpoint debugging with live data
- No mocks, no SSH into pods

---

## Custom Pipeline Hooks (M12)

| Hook | When | Example |
|------|------|---------|
| `pre-build-task` | After clone, before compile | Code generation, license scan |
| `post-build-task` | After containerize, before deploy | Image scan, SBOM |
| `pre-test-task` | After deploy, before tests | Seed test data |
| `post-test-task` | After tests (finally block) | Slack notification |

All optional — empty string skips the hook. Teams customize without forking pipelines.

---

## Multi-Team Helm Deployment

```mermaid
graph TD
    HC[Helm Chart] --> A[team-alpha<br/>release]
    HC --> B[team-beta<br/>release]
    HC --> C[team-gamma<br/>release]
    A --> OA[orchestrator-alpha]
    B --> OB[orchestrator-beta]
    C --> OC[orchestrator-gamma]
```

- Each team gets isolated ConfigMaps, orchestrator, and pipeline runs
- `compileImageVariants` per team (e.g. Java 17 vs 21)
- Management GUI provides team switcher

---

## Tekton Results — Pipeline History

- **Results API + Watcher** → Postgres
- Every PipelineRun and TaskRun persisted automatically
- Query historical runs, durations, outcomes
- `verify-results-in-db.sh` validates data
- Management GUI surfaces run history

---

## Test-Trace Graph — Blast Radius

```mermaid
graph TD
    subgraph "Neo4j Graph"
        S1((demo-fe)) -->|CALLS| S2((BFF))
        S2 -->|CALLS| S3((demo-api))
        T1{fe-e2e} -.->|TOUCHES| S1
        T2{bff-post} -.->|TOUCHES| S2
        T3{api-post} -.->|TOUCHES| S3
        T4{api-intg} -.->|TOUCHES| S3
        T5{api-load} -.->|TOUCHES| S3
    end
```

- **Radius 1**: direct tests for changed app
- **Radius 2**: tests for neighbor services
- `query-test-plan` task → focused test execution

---

## 23 Tekton Tasks

<div class="grid grid-cols-3 gap-2 text-sm">
<div>

**Source**
- resolve-stack
- clone-app-repos
- build-select-tool-apps

</div>
<div>

**Build**
- compile-npm/maven/gradle/pip/composer
- build-containerize
- pr-snapshot-tag

</div>
<div>

**Deploy & Test**
- deploy-full-stack
- deploy-intercept (telepresence)
- deploy-intercept-mirrord
- validate-propagation
- validate-original-traffic
- query-test-plan
- run-stack-tests

</div>
</div>

Plus: cleanup, version-bump, tag-release-images, post-pr-comment, 2 example hooks

---

## Demo Asset Toolchain

| Tool | Produces |
|------|----------|
| **Manim** | 6 animated architecture videos |
| **VHS** | 7 terminal recording GIFs/MP4s |
| **OpenAI TTS** | 11 narration audio tracks |
| **ffmpeg** | Composed segment + full demo videos |
| **Slidev** | This presentation |

All generated from source: `./docs/demos/generate-all.sh`

---
layout: center
---

# Thank You

**tekton-dag** — Stack-aware CI/CD with header-based traffic interception

GitHub: `jmjava/tekton-dag`

<div class="mt-8 text-sm opacity-60">
All demo assets generated programmatically — no manual recording
</div>
