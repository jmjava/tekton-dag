The final piece of the puzzle is intelligent test selection — knowing which tests to run when a specific service changes.

tekton-dag maintains a test-trace graph in Neo4j. Service nodes represent your applications. Test nodes represent individual test cases — Postman collections, Playwright specs, Artillery scenarios. TOUCHES edges connect tests to the services they exercise. CALLS edges connect services to their downstream dependencies.

Here is how the graph gets populated. During test execution, trace data — which services called which — is captured and ingested via the orchestrator's POST /api/graph/ingest endpoint. Over time, the graph builds an accurate map of test-to-service relationships.

Now watch what happens when a developer changes demo-api. The query-test-plan task in the PR pipeline calls GET /api/test-plan with the changed app and a blast radius parameter.

At radius one, the graph returns every test that directly touches demo-api — the API Postman collection, the integration tests that call the API endpoints. These are the tests most likely to catch a regression.

At radius two, the graph expands to neighbor services. The BFF calls demo-api, so BFF tests are included too — they exercise code paths that depend on the changed service. The test plan grows, but only to tests that have a real dependency relationship.

The graph also identifies gaps. If a service node has no TOUCHES edges — no tests exercise it — the graph flags it as unmapped. This tells the team where to add regression test coverage.

The run-tests task receives this focused test plan and executes only the relevant tests, not the entire suite. For a large stack with dozens of services and hundreds of tests, this can reduce test time from thirty minutes to three.

Stack graph query. Focused test plan. Faster feedback. That is blast-radius-aware test selection.
