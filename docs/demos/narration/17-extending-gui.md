Adding a new operator surface to the management GUI follows a five-step pattern. Let's walk through a concrete example — adding a TaskRun logs panel that shows real-time logs for any running task.

Step one: add a Flask route. Create a new endpoint under slash api slash teams slash team name slash taskruns slash taskrun name slash logs. The route uses the Kubernetes Python client to call the pod logs API, streaming the output. Return the logs as a JSON response with a stable shape — a logs array with timestamp and line fields. Follow the same error handling pattern as existing routes: catch ApiException, return a meaningful HTTP status.

Step two: add pytest coverage. Create a test that mocks the Kubernetes client's read namespaced pod log method. Verify the route returns the expected JSON shape, handles missing TaskRuns with a four-oh-four, and handles cluster errors gracefully. Use the same fixture pattern as the existing route tests — a test client, a mock Kubernetes config, and patched API calls.

Step three: add a Pinia store in the Vue frontend. Create a useTaskRunLogs composable that calls the API helper with the team-scoped URL. The store manages loading state, error state, and the logs array. Use the same useApiHelper and teamUrl utilities that existing stores use, so the team switcher works automatically.

Step four: create a Vue component and router entry. The TaskRunLogs view renders the logs in a monospace font with auto-scroll. It accepts a taskrun name as a route parameter. Add the route to the router configuration and a navigation link in the sidebar or the run detail view.

Step five: write a Playwright spec. The end-to-end test navigates to a pipeline run, clicks into a TaskRun, verifies the logs panel renders, and checks that log lines appear. Use the same page object pattern and test fixtures as the existing Playwright suite.

Five files. One pattern. The Flask route wraps the cluster API. Pytest verifies the contract. The Pinia store manages client state. The Vue component renders the UI. Playwright proves it works end to end.

This pattern scales to any Tekton surface — Tekton Results read-only views, cluster event streams, resource quota dashboards, or webhook configuration panels. The extension guide in the repository lists concrete file paths, API patterns, and more ideas for deeper Tekton coverage.

Five steps, one pattern, unlimited extensibility. That is how you extend the management GUI.
