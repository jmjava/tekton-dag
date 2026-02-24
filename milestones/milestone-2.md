# Milestone 2: Prebuilt containers, version-selection GUI, and Results GUI

## 1. Prebuilt JDK21, npm, and PHP containers

### Goal

Explore and document options for using **prebuilt** container images for:

- **JDK 21** — Java/Spring Boot builds
- **npm** — Node.js / frontend (e.g. Vue) builds
- **PHP** — PHP app builds

so pipeline tasks can rely on official or well-maintained images instead of building or maintaining custom ones.

### Scope

- Identify suitable **official or community** images for each runtime (JDK21, Node/npm, PHP).
- Compare **slim vs full** variants, tags (e.g. `21`, `21-jdk`, `21-slim`), and maintenance/security posture.
- Document **how each image fits** into existing Tekton tasks (e.g. `build-app`, language-specific build steps).
- Capture **constraints**: registry access, image size, compatibility with `stacks/versions.yaml` and task scripts.
- Optional: propose concrete image choices and any task YAML changes.

### Outcomes

- A short **options matrix** (or appendix) for JDK21, npm, and PHP images.
- Recommendation for default images to use in tasks/pipelines.
- Any required updates to `stacks/versions.yaml` or task parameters (e.g. `IMAGE_*` or similar).

### Notes

- Align with existing stack definitions (e.g. `stack-one.yaml`, `single-app.yaml`) and sample repos (Vue, Spring Boot, Flask, PHP).
- Prefer images that are widely used, kept up to date, and suitable for CI (non-root, minimal where possible).

---

## 2. GUI to select versions for a particular run

### Goal

Explore options for **selecting versions at run time** via a **GUI** instead of relying only on hardcoded values in `stacks/versions.yaml`. Users (or operators) would choose which JDK, Node, PHP, or other runtime/version to use for a given pipeline run.

### Scope

- Identify **GUI approaches**: e.g. simple web UI, Tekton Dashboard integration, VS Code / Cursor extension, or a small CLI wizard that prompts for versions.
- Define **what “versions”** means in this context: container image tags, tool versions (Java 21 vs 17, Node 20 vs 22), or both; ensure it maps clearly to `versions.yaml` and pipeline parameters.
- Explore **how selections flow** into a run: PipelineRun params, ConfigMap/overlay, or a generated `versions.yaml` (or fragment) passed as workspace/param.
- Consider **defaults and overrides**: start from `versions.yaml` as default, allow GUI to override per run (or per stack/app).
- Document **trade-offs**: ease of use vs. auditability, reproducibility (recording chosen versions in run metadata or Results).

### Outcomes

- Short **options doc** for GUI/version-selection (technologies, where it runs, how it plugs into Tekton).
- Recommendation: e.g. “minimal web UI that reads versions.yaml, lets user pick, and triggers PipelineRun with params.”
- Any required changes to pipeline/task params or to `versions.yaml` schema (e.g. optional overrides, run-time source).

### Notes

- Keep `versions.yaml` as the single source of *available* versions; GUI can choose among them or allow custom overrides for experimentation.
- Align with local dev workflow (e.g. `generate-run.sh`, Telepresence, optional Tekton Results) so chosen versions are visible in run history.

---

## 3. Results GUI — filter and query Tekton Results DB

### Goal

Add a **simple Vue app** that acts as a **Results GUI**: filter and query the Tekton Results database for pipeline and task run info, with **canned queries** for common questions (e.g. recent runs, runs by stack/app, failures, duration).

### Scope

- **Stack**: Vue SPA that talks to an API layer (or direct DB connection if appropriate) for the Tekton Results DB (Postgres used by Tekton Results).
- **Filter and query**: UI to filter by time range, pipeline name, stack, app, status (success/failure), and optionally run labels/annotations; support free-form or parameterized queries where safe.
- **Canned queries**: ship a set of predefined queries, e.g.:
  - Recent pipeline runs (last N or last 24h)
  - Runs by stack or by app
  - Failed runs with task/step details
  - Runs by duration (slowest first)
  - Runs that used a given version (if recorded in Results)
- **Security and deployment**: read-only access to Results data; document how the app is served (e.g. static build behind a simple backend or BFF that queries Postgres/Results API) and how to run it locally (e.g. against the same Postgres as `install-postgres-kind.sh` / Tekton Results).
- Keep the app **simple**: no heavy framework beyond Vue; focus on tables, filters, and one-click canned queries.

### Outcomes

- **Vue app** (in this repo or a dedicated one) with:
  - Filter UI (date range, pipeline, stack, app, status).
  - Canned-query buttons or dropdown that run predefined queries and show results in a table or list.
  - Optional: export (e.g. CSV) or deep link to a specific run.
- **Canned-queries list** documented (name, purpose, SQL or API call shape).
- Short **README** for running the Results GUI locally and pointing it at the Tekton Results DB (or Results API).

### Notes

- Tekton Results stores pipeline/task run records in Postgres; the GUI can query via Results API (if exposed) or a thin backend that runs read-only SQL. Prefer API where available to stay upgrade-safe.
- Reuse patterns from existing Vue app in the DAG (e.g. `tekton-dag-vue-fe`) for consistency if useful; keep this app focused on “query Results” only.
- Canned queries should be read-only and safe (no writes, no raw user SQL unless strictly parameterized).
