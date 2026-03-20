Testing is a first-class concern in tekton-dag. Every stack definition includes test specifications — Postman collections, Playwright suites, and Artillery load tests — attached to each app.

The run-stack-tests task in the pipeline executes these tests with the PR header injected. For Postman collections, it uses Newman — the Postman CLI runner — to execute API tests against the live stack. The x-dev-session header is added to every request, so the tests hit the PR build through the intercept chain.

Let's run the orchestrator test suite. The run-orchestrator-tests script activates the test environment and executes pytest against the orchestrator's unit tests. These cover every module — the Flask app factory, route handlers, stack resolver, PipelineRun builder, and the Kubernetes client wrapper — with mocked dependencies so they run without a cluster.

Watch the output — 62 tests across five modules, all passing. The tests verify stack resolution logic, PipelineRun manifest generation, webhook payload parsing, and error handling for every endpoint.

The shared Python package — tekton-dag-common — has its own test suite as well. Fourteen tests cover the base stack resolver, PipelineRun builder, and Kubernetes constants that are shared between the orchestrator and the management GUI backend.

For end-to-end testing, the run-e2e-with-intercepts script triggers a full PR pipeline flow and validates that header propagation works through the entire stack. The management GUI's Playwright suite adds another 69 end-to-end tests covering the web interface.

Postman integration tests, pytest unit tests, Playwright end-to-end tests, and Artillery load tests — all wired into the pipeline and running automatically on every pull request.
