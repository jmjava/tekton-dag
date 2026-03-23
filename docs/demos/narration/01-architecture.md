Welcome to tekton-dag — a stack-aware CI/CD system built on Tekton Pipelines.

Most CI/CD tools treat each repository in isolation. tekton-dag takes a different approach. It models your applications as a directed acyclic graph — a DAG — where each node is a service and each edge represents a runtime dependency. The system understands which services call which, how requests flow, and what needs testing when something changes.

Here is the architecture. On the left, a webhook from GitHub triggers the orchestrator — a Flask service that decides which pipelines to run. The orchestrator reads the stack definition, resolves which applications are affected by a change, and generates Tekton PipelineRun manifests on the fly.

In the center, you see the demo stack: three services — a Vue front-end, a Spring Boot BFF, and a Spring Boot API — connected by dependency edges. Each service declares a propagation role: originator, forwarder, or terminal. These roles define how the dev-session routing header — written x-dev-session in YAML — flows through the call chain during pull-request testing.

The system is polyglot by design. A second stack in the repo demonstrates five services spanning npm, Maven, Gradle, Composer, and pip — all sharing the same pipeline infrastructure. Parameterized build images support Java 11, 17, and 21, Node 18, 20, and 22, Python 3.10 through 3.12, and PHP 8.1 through 8.3.

Below the stack, three pipelines fan out. The bootstrap pipeline builds and deploys every service in the stack from scratch. The PR pipeline builds only the changed service, deploys it alongside the existing baseline deployment in your validation cluster, and wires up traffic interception using either Telepresence or mirrord so the pull request build receives only tagged requests. The merge pipeline promotes the tested image to the mainline deployment with semantic version tagging — separate from shipping to a customer-facing production cluster, if that is another environment.

Pipelines are also extensible. Teams can inject custom hook tasks — pre-build, post-build, pre-test, post-test — for things like image scanning, software bill of materials generation, or Slack notifications, without modifying the core pipeline definitions.

A management GUI built with Vue and Flask provides a web interface for team switching, DAG visualization, pipeline monitoring, and manual triggers. Everything is deployed through a Helm chart with multi-team support, and Tekton Results stores every pipeline outcome in a Postgres database. A Neo4j graph tracks which tests touch which services, enabling intelligent blast-radius analysis.

That is the high-level picture. Let's dive in.
