# Regression testing (run before updating testing / demo docs)

Single entrypoint: **`scripts/run-regression.sh`** (see `--help`). Run when green before changing milestone-8 / testing documentation.

**Cursor / agents:** follow **[AGENT-REGRESSION.md](AGENT-REGRESSION.md)** — run **`scripts/run-regression-agent.sh`** (or **`run-regression-agent-full.sh`**) and **iterate with fixes until exit 0**, not a single partial run. Repo **[AGENTS.md](../AGENTS.md)** points here.

## Application PR pipeline vs platform (system) regression

Do **not** confuse these:

| Scope | What runs | Typical trigger |
|-------|-----------|-----------------|
| **Application PR** (`stack-pr-test` on an **app** repo) | Stack-defined tests only — e.g. that app’s Newman/Playwright/Artillery as declared in `stacks/*.yaml`, against the intercept build. | Every PR on the **application** repository (when webhooks/Tekton are wired). |
| **Platform regression** (`scripts/run-regression*.sh` on **this** repo) | **System / integration** tiers: Phase 1 + orchestrator + shared libs + GUI pytest, Playwright for **management-gui**, real **`stack-dag-verify`** PipelineRun, Newman against **orchestrator** API, optional Tekton Results, optional Kind E2E. | **Manual**, **scheduled**, **pre-release**, or **agent loop** — **not** “automatically on every pull request” unless *you* add GitHub Actions (or similar) to do so. |

So: **not all tests run on every PR.** The full regression driver is a **system test** bar for the platform; app PRs run a narrower, stack-scoped test stage.

**Streaming / timestamps:** use **`scripts/run-regression-stream.sh`** — same arguments, prefixes each line with `[HH:MM:SS]` and preserves the real exit code (plain `| while read` does not).

**Port-forward prep:** [common.sh](../scripts/common.sh) defines **`free_tcp_port`**. Regression (**[run-regression.sh](../scripts/run-regression.sh)**) runs a **prep** step when `kubectl` works: frees **`ORCHESTRATOR_TEST_PORT`** (default **9091**) and **`RESULTS_API_LOCAL_PORT`** (default **8080**). Set **`REGRESSION_FREE_PORTS=0`** to skip that prep. [run-orchestrator-tests.sh](../scripts/run-orchestrator-tests.sh) also frees the orchestrator local port; [verify-results-in-db.sh](../scripts/verify-results-in-db.sh) frees **8080** (or **`RESULTS_API_LOCAL_PORT`**) before forwarding the Results API.

## What actually runs Tekton PipelineRuns?

| Kind | Creates / waits for PipelineRuns? | Notes |
|------|-------------------------------------|--------|
| **pytest / vitest / Playwright** | **No** | Mocks and UI only. |
| **Newman** (orchestrator API) | **Yes** — bootstrap / PR / merge runs | Runs are **deleted** in script cleanup. The post-Newman “integration” step only waits for `fetch-source` to start on the latest bootstrap run (best-effort; may time out without failing the job). **Do not rely on this alone as “we ran pipelines.”** |
| **`verify-dag-phase2.sh`** | **Yes** — one **`stack-dag-verify`** run to **Succeeded** | Compares `resolve-stack` results to `stack-graph.sh` CLI. **This is the required real pipeline check** when the pipeline is installed in the cluster. |
| **`run-full-test-and-verify-results.sh`** | **Yes** — runs **`verify-dag-phase2`** then checks Tekton Results DB | Used when Results is installed (or `--with-results-verify`). Regression **skips** a duplicate standalone `verify-dag-phase2` when this will run. |
| **`run-all-setup-and-test.sh`** (`--kind-e2e`) | **Yes** — full bootstrap / intercept E2E | Very long; optional. |

## What runs (tiers)

| Tier | What | When |
|------|------|------|
| **A — Local static DAG** | [scripts/verify-dag-phase1.sh](../scripts/verify-dag-phase1.sh) (repo layout, `stack-graph.sh`, registry/versions via **yq**) | Always |
| **A — Python** | pytest in `orchestrator/`, `libs/tekton-dag-common/`, `management-gui/backend/`, `libs/baggage-python/` | Always |
| **A — Node** | vitest in `libs/baggage-node` | Always |
| **B — Browser** | Playwright in `management-gui/frontend` | Default; skip with `--local-only` or `--skip-playwright` |
| **C — Tekton DAG pipeline** | [scripts/verify-dag-phase2.sh](../scripts/verify-dag-phase2.sh) — **`stack-dag-verify`** to **Succeeded** | **Auto** if `kubectl` works and `Pipeline/stack-dag-verify` exists in `NAMESPACE`. **Skipped** when [run-full-test-and-verify-results.sh](../scripts/run-full-test-and-verify-results.sh) will run (it already includes Phase 2). **Forced failure if missing** with `--require-dag-verify`. **Off** with `--skip-dag-verify` or `REGRESSION_DAG_VERIFY=skip`. |
| **D — Cluster API** | Newman via [run-orchestrator-tests.sh](../scripts/run-orchestrator-tests.sh) `--all` | **Auto** if orchestrator `Service` exists and `newman` on `PATH`; **required** with `--cluster` |
| **E — Results + DB** | [run-full-test-and-verify-results.sh](../scripts/run-full-test-and-verify-results.sh) | **Auto** if `tekton-results-api` exists; **forced** with `--with-results-verify`; **off** with `--skip-results-verify` |
| **F — GUI Postman** | [management-gui-tests.json](../tests/postman/management-gui-tests.json) vs `http://localhost:5000` | `--gui-newman` |
| **G — Full Kind E2E** | [run-all-setup-and-test.sh](../scripts/run-all-setup-and-test.sh) | `--kind-e2e` |

## Prerequisites

- **Python 3.10+** with pytest and package deps.
  - **One shot:** `./scripts/bootstrap-regression-venv.sh`
  - `run-regression.sh` prepends **`./.venv/bin`** to `PATH` automatically if the default `python3` has no pytest (you do not have to `activate` first).
  - Manual: `python3 -m venv .venv && . .venv/bin/activate` then `pip install -r orchestrator/requirements.txt -r management-gui/backend/requirements-dev.txt` and `pip install -e 'libs/tekton-dag-common[test]' -e 'libs/baggage-python[test]'`

- **`yq`** (Mike Farah YAML processor) on `PATH` — required for Phase 1.
- **Node.js + npm** for baggage-node and Playwright.
- **Cluster:** `kubectl`, Tekton `Pipeline/stack-dag-verify` + tasks for **Tier C**, orchestrator **Service** for Newman, optional Tekton Results for **Tier E**.

## Common commands

```bash
chmod +x scripts/run-regression.sh   # once, if needed

# Fast (no browser, no cluster): Phase 1 + pytest + vitest
./scripts/run-regression.sh --local-only

# Default: local + Playwright + Tekton stack-dag-verify (if pipeline exists) + Newman + Results script (if API exists)
./scripts/run-regression.sh

# CI with cluster: fail if orchestrator or newman missing; fail if stack-dag-verify missing (no silent skip)
./scripts/run-regression.sh --cluster --require-dag-verify

# Only skip the long Tekton PipelineRun (not recommended for “full” regression)
./scripts/run-regression.sh --skip-dag-verify

# Require Tekton Results + DAG pipeline + DB check
./scripts/run-regression.sh --with-results-verify

# Skip Results script only (Phase 2 still runs standalone if pipeline exists and Results API absent)
./scripts/run-regression.sh --skip-results-verify

# Full platform smoke (Kind + Tekton + intercepts + DB) — use sparingly
./scripts/run-regression.sh --local-only --kind-e2e
```

Environment:

- `NAMESPACE` — Tekton namespace (see [scripts/common.sh](../scripts/common.sh)).
- `REGRESSION_RESULTS_VERIFY=auto|skip|yes`
- `REGRESSION_DAG_VERIFY=auto|skip|yes`
- `DAG_VERIFY_TIMEOUT` — seconds passed to `verify-dag-phase2.sh` `--timeout` (default **300** in regression).

## Suggested regression cadence (not all on every PR)

1. **Often (fast, no cluster):** `./scripts/run-regression.sh --local-only` — Phase 1 + pytest + vitest; good for frequent pushes; safe to wire into lightweight CI.
2. **System bar (cluster):** **`./scripts/run-regression.sh --cluster --require-dag-verify`** when you need a real **Succeeded** `stack-dag-verify` and orchestrator Newman — treat as **integration / system** work: before releases, after big platform changes, on a schedule, or when agents/docs require proof — **not** as “must pass on every GitHub PR” unless you explicitly configure that.
3. **With Tekton Results:** `--with-results-verify` or rely on **auto** when the API exists.
4. **Kind E2E:** `--kind-e2e` when changing bootstrap, intercepts, or Results integration (heavy; occasional).

After the tiers you care about are green, update [milestones/milestone-8.md](../milestones/milestone-8.md) and related testing docs.
