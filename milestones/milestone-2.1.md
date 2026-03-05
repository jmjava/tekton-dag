# Milestone 2.1: Version-selection GUI and Results GUI (follow-up)

> **Active milestone.** Carries forward the uncompleted items from [milestone 2](completed/milestone-2.md) (archived). Other active: [milestone-4](milestone-4.md), [milestone-4.1](milestone-4.1.md), [milestone-5](milestone-5.md).

This milestone covers only the two areas that were left incomplete when milestone 2 was archived: (1) a proper version-selection GUI instead of raw JSON override, and (2) Results GUI integration with the Tekton Results API/DB instead of live `kubectl` queries.

---

## 1. Version-selection GUI

### Current state

`TriggerView.vue` exposes a raw JSON override field for run parameters. There is no dropdown or picker that reads `stacks/versions.yaml` and presents selectable runtime versions (JDK, Node, PHP, etc.).

### Goal

Deliver a **GUI for selecting versions at run time** so users (or operators) can choose which JDK, Node, PHP, or other runtime/version to use for a given pipeline run, instead of editing JSON or relying only on hardcoded values in `stacks/versions.yaml`.

### Scope

- Replace or augment the raw JSON override with a **dropdown picker** (or equivalent) that reads `versions.yaml` and presents selectable runtime versions.
- Define **what “versions”** means: container image tags, tool versions (Java 21 vs 17, Node 20 vs 22), or both; ensure it maps clearly to `versions.yaml` and pipeline parameters.
- **How selections flow** into a run: PipelineRun params, ConfigMap/overlay, or a generated `versions.yaml` (or fragment) passed as workspace/param.
- **Defaults and overrides**: start from `versions.yaml` as default, allow GUI to override per run (or per stack/app).
- Document **trade-offs**: ease of use vs. auditability, reproducibility (recording chosen versions in run metadata or Results).

### Outcomes

- Version-selection UI in the existing run/trigger flow (e.g. in `TriggerView.vue` or equivalent) that reads `versions.yaml`, lets the user pick runtime versions, and triggers the PipelineRun with the chosen params.
- Any required changes to pipeline/task params or to `versions.yaml` schema (e.g. optional overrides, run-time source) documented or implemented.
- Optional: short options doc if multiple GUI approaches were evaluated.

### Notes

- Keep `versions.yaml` as the single source of *available* versions; GUI chooses among them or allows custom overrides for experimentation.
- Align with local dev workflow (e.g. `generate-run.sh`, Telepresence, optional Tekton Results) so chosen versions are visible in run history.

---

## 2. Results GUI — Tekton Results API/DB integration

### Current state

`TestResultsView.vue` queries **live** PipelineRuns via `kubectl` (or cluster API). It does not use the Tekton Results database or Results API, so there is no persistent history, time-range filtering, or canned queries against stored results.

### Goal

Add a **Results GUI** that filters and queries the **Tekton Results database** (or Results API) for pipeline and task run info, with **canned queries** for common questions (e.g. recent runs, runs by stack/app, failures, duration).

### Scope

- **Backend integration**: connect the Vue app to Tekton Results — via Results API (preferred) or a thin read-only backend that queries Postgres used by Tekton Results.
- **Filter and query**: UI to filter by time range, pipeline name, stack, app, status (success/failure), and optionally run labels/annotations; support parameterized/canned queries only (no raw user SQL).
- **Canned queries**: ship a set of predefined queries, e.g.:
  - Recent pipeline runs (last N or last 24h)
  - Runs by stack or by app
  - Failed runs with task/step details
  - Runs by duration (slowest first)
  - Runs that used a given version (if recorded in Results)
- **Security and deployment**: read-only access to Results data; document how the app is served (e.g. static build behind a BFF that queries Postgres/Results API) and how to run it locally (e.g. against the same Postgres as `install-postgres-kind.sh` / Tekton Results).
- Keep the app **simple**: no heavy framework beyond Vue; focus on tables, filters, and one-click canned queries.

### Outcomes

- **Vue app** (existing Results view or dedicated) with:
  - Filter UI (date range, pipeline, stack, app, status).
  - Canned-query buttons or dropdown that run predefined queries and show results in a table or list.
  - Optional: export (e.g. CSV) or deep link to a specific run.
- **Canned-queries list** documented (name, purpose, SQL or API call shape).
- Short **README** (or doc section) for running the Results GUI locally and pointing it at the Tekton Results DB or Results API.

### Notes

- Tekton Results stores pipeline/task run records in Postgres; the GUI should use the Results API where available to stay upgrade-safe; otherwise a thin read-only backend is acceptable.
- Reuse patterns from existing Vue app in the DAG (e.g. `tekton-dag-vue-fe`) for consistency; keep this app focused on “query Results” only.
- Canned queries must be read-only and safe (no writes, no raw user SQL unless strictly parameterized).
