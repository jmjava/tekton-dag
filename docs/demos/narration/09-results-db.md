Every pipeline run in tekton-dag is recorded. Tekton Results — an official Tekton component — watches for completed PipelineRuns and TaskRuns and stores them in a Postgres database.

The setup is straightforward. The install Postgres Kind script deploys a Postgres instance into the cluster. Then install Tekton Results deploys the Results API server and the watcher. From that point on, every pipeline run is automatically persisted.

Let's verify. The verify results in database script queries the Tekton Results API and shows stored records. Here you can see our bootstrap run and two pull-request runs with their start times, durations, and outcomes.

This matters for auditability — you have a permanent record of every build, every test result, every deployment. But it also powers the run full test and verify results workflow, which triggers a pipeline, waits for completion, and confirms the results appear in the database.

The management GUI surfaces this data through the pipeline monitor view. You can browse runs by team, filter by status, and drill into individual TaskRun logs — all backed by the same Tekton Results API.

The GET slash api slash runs endpoint on the orchestrator also reads from the Kubernetes API to show recent runs, giving you both live status and historical data.

Persistent pipeline history. Queryable results. Full audit trail. That is Tekton Results integrated into tekton-dag.
