The management GUI is a Vue three single-page application backed by a Flask API. The browser never touches the Kubernetes API directly — every cluster action goes through Flask, which uses the configured kubeconfig or in-cluster service account. This keeps credentials off the client and simplifies RBAC.

The first thing you see is the team switcher. Select a team and every view in the application filters to that team's namespace. Team alpha sees its stacks, its pipeline runs, its test results. Team beta sees only its own. The selection persists across page navigation.

The DAG view renders the stack graph using Vue Flow. Each node represents an application — color-coded by propagation role. Click a node and a detail panel shows the app's repository, build tool, downstream dependencies, and test specifications. The edges show the dependency chain that the pipeline uses to resolve build order and propagation routing.

The pipeline runs view shows active and completed PipelineRuns for the selected team. Each row displays the pipeline name, the trigger — bootstrap, pull request, or merge — the status, start time, and duration. Click a run to expand it and see individual TaskRun details. Click a TaskRun to view its logs — streamed from the cluster in real time for running tasks, or fetched from Tekton Results for completed ones.

The triggers panel lets operators start pipelines manually. Select a mode — bootstrap, pull request, or merge — choose the stack, specify the changed app and optional parameters, and submit. The GUI calls the orchestrator's POST slash api slash run endpoint, and the new PipelineRun appears in the runs view within seconds.

Test results are surfaced per run. Newman, Playwright, and Artillery results are displayed with pass-fail counts and expandable detail for individual test cases. If the Neo4j graph is configured, the GUI can also show the blast-radius visualization — which services and tests were in scope for a given change.

The Git browser lets you explore application repositories from within the GUI. Navigate directories, view file contents, and see recent commits — useful for checking what changed in a pull request without leaving the management interface.

For deeper Tekton inspection, the GUI embeds the Tekton Dashboard in an iframe. This gives operators access to the full Tekton resource browser — PipelineRuns, TaskRuns, Pipelines, Tasks, and cluster configuration — without switching tools.

Under the hood, the architecture follows a clean pattern. Vue components use Pinia stores for state management. Each store calls a shared API helper that prepends the team-scoped base URL. The Flask backend maps routes under slash api, wrapping the Kubernetes Python client for cluster operations and proxying to the orchestrator for pipeline management.

The testing story is thorough. The Flask backend has its own pytest suite — fifty-plus tests covering every route with mocked Kubernetes responses. The Vue frontend has a Playwright end-to-end suite — sixty-nine tests that navigate every view, trigger actions, and verify rendering. Newman collections test the REST API contract against a live backend.

One web interface for the whole platform. Team-scoped. Cluster-safe. Fully tested. That is the management GUI.
