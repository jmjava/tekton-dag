The orchestrator is the brain of tekton-dag — a Flask service running on port 8080 that translates events into pipeline runs.

Let's call its API endpoints. First, a health check — HTTP GET slash healthz confirms the service is alive, and HTTP GET slash readyz confirms it has loaded the stack definitions.

GET slash api slash stacks returns every stack the system knows about — stack one with its three-tier demo graph, stack two with the five-app polyglot stack, and any test stacks for Flask, PHP, or multi-hop scenarios.

Now the interesting part. POST slash api slash run accepts a mode — pull request, bootstrap, or merge — along with the stack name, changed app, and pull request number. The orchestrator resolves the stack YAML, builds a complete PipelineRun manifest with all the correct parameters — image registry, compile images, intercept backend, version overrides — and submits it to the Kubernetes API.

POST slash webhook slash github is the webhook URL GitHub calls — the orchestrator endpoint exposed on whichever cluster hosts your automation, typically validation or CI, not your separate production cluster. When GitHub sends a pull request event, the orchestrator extracts the repo name, looks it up in the registry mapping to find the containing stack, determines the changed app, and triggers the appropriate pipeline. All automatic, no manual intervention.

The orchestrator also bridges to the test-trace graph. GET slash api slash test-plan takes a changed app name and a blast radius, queries Neo4j for the relevant tests, and returns the test plan. POST slash api slash graph slash ingest loads trace data — which services called which during a test run — into the Neo4j graph. GET slash api slash graph slash stats returns the current node and edge counts.

GET slash api slash runs lists recent PipelineRuns with their status. GET slash api slash teams lists the configured team namespaces. POST slash api slash reload refreshes the in-memory stack and team configuration without restarting the service.

The orchestrator is deployed by the Helm chart as a Kubernetes Deployment with a matching Service, and it reads its stack configuration from a ConfigMap generated from the stacks directory.
