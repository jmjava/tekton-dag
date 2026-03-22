Testing is a first-class concern in tekton-dag. Every stack definition includes test specifications — Postman collections, Playwright suites, and Artillery load tests — attached to each app.

The run-stack-tests task in the pipeline executes these tests with the PR header injected. For Postman collections, it uses Newman — the Postman CLI runner — to execute API tests against the live stack. The x-dev-session header is added to every request, so the tests hit the PR build through the intercept chain.

For **orchestrator HTTP contracts** against a live service, **Newman** runs the Postman collection via **`run-orchestrator-tests.sh`** — port-forward to the cluster, hit `/api/*`, and optionally trigger PipelineRuns (see [REGRESSION.md](../../REGRESSION.md) for how that differs from a full system regression).

For **fast unit coverage** without a cluster, **`pytest`** under **`orchestrator/`** exercises the Flask app, routes, stack resolver, PipelineRun builder, and Kubernetes client wrapper with mocks.

Watch the pytest output — dozens of tests across the orchestrator modules, all passing when green. They verify stack resolution, manifest generation, webhook parsing, and endpoint error handling.

The shared Python package — tekton-dag-common — has its own test suite as well. Fourteen tests cover the base stack resolver, PipelineRun builder, and Kubernetes constants that are shared between the orchestrator and the management GUI backend.

For end-to-end testing, the run-e2e-with-intercepts script triggers a full PR pipeline flow and validates that header propagation works through the entire stack. The management GUI's Playwright suite adds another 69 end-to-end tests covering the web interface.

Application repos run their Postman, Playwright, and Artillery suites inside **stack-pr-test** when a PR opens against that app — those are **stack-scoped** tests. The **orchestrator** pytest suite and the **full platform regression** scripts are **system-level**: they validate this platform against a cluster and are run on demand, on a schedule, or before releases — not the same as “every test on every pull request.”
