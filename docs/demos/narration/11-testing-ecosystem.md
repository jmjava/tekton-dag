Testing is a first-class concern in tekton-dag. The platform supports four testing frameworks — Newman for API contracts, pytest for Python services, Playwright for end-to-end GUI testing, and Artillery for load testing — all integrated into the pipeline and regression workflows.

Every stack definition includes test specifications attached to each app. The run stack tests task in the pipeline executes these tests with the dev-session header injected. For Postman collections, it uses Newman — the Postman CLI runner — to execute API tests against the live stack. The dev-session header is added to every request so the tests hit the pull-request build through the intercept chain.

For orchestrator HTTP contracts against a live cluster, Newman runs the Postman collection via the run orchestrator tests shell script: port-forward to the cluster, call the REST API, and optionally trigger PipelineRuns. That workflow differs from a full system regression, which is documented in the regression guide.

For fast unit coverage without a cluster, pytest exercises the orchestrator's Flask app, routes, stack resolver, PipelineRun builder, and Kubernetes client wrapper with mocks. Watch the output — dozens of tests across the orchestrator modules, all passing. They verify stack resolution, manifest generation, webhook parsing, and endpoint error handling.

The shared Python package tekton-dag-common has its own test suite as well. Fourteen tests cover the base stack resolver, PipelineRun builder, and Kubernetes constants that are shared between the orchestrator and the management GUI backend.

The management GUI has its own Playwright end-to-end suite — sixty-nine tests covering the web interface. These navigate every view, trigger pipeline actions, verify DAG rendering, and check team switching. The Flask backend has fifty-plus pytest tests covering every API route with mocked Kubernetes responses.

For load testing, Artillery scenarios exercise the stack under concurrent traffic. The artillery variants script runs multiple configurations — baseline load, burst traffic, and sustained throughput — and captures response time distributions. These run during regression or on demand, not on every pull request.

For end-to-end integration, the run e2e with intercepts script triggers a full pull-request pipeline flow and validates that header propagation works through the entire stack. This is the highest-fidelity test — it proves the complete workflow from webhook to cleanup on a live cluster.

Application repos run their Postman, Playwright, and Artillery suites inside stack-pr-test when a pull request opens — those are stack-scoped tests. The orchestrator pytest suite and the full platform regression scripts are system-level: they validate this platform against a cluster and are run on demand, on a schedule, or before releases.

Four frameworks. Stack-scoped and system-level tiers. Full coverage from unit to load. That is the testing ecosystem.
