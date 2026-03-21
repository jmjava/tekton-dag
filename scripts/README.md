# `scripts/` — automation entrypoints

This directory contains **bash** automation for Kind/Tekton setup, image builds, regression, and E2E flows.

## Where to look

- **Full index (every script):** [docs/SCRIPTS.md](../docs/SCRIPTS.md)
- **Shared shell API:** `common.sh` (sourced by install/publish/regression scripts)
- **Primary regression:** `./scripts/run-regression.sh` — details in [docs/REGRESSION.md](../docs/REGRESSION.md)
- **Cursor / agents:** `./scripts/run-regression-agent.sh` — [docs/AGENT-REGRESSION.md](../docs/AGENT-REGRESSION.md)

## Obsolete scripts

Retired scripts are moved to **`scripts/archive/`** (see [scripts/archive/README.md](archive/README.md)), mirroring the policy for [docs/archive/](../docs/archive/README.md).

## Demo video generation

Demo pipelines live under **`docs/demos/`** (e.g. `generate-all.sh`, `compose.sh`), not here.
