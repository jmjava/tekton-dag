# Agent instructions (tekton-dag)

## Regression — iterate until complete

Do **not** stop after a single partial test run. Follow **[docs/AGENT-REGRESSION.md](docs/AGENT-REGRESSION.md)**:

- Run **`bash scripts/run-regression-agent.sh`** (or **`run-regression-agent-full.sh`** if Results + DB must pass).
- **Loop**: fix failures → re-run until **`regression exit code: 0`** and done criteria in the doc are met.

## Quick commands

| Intent | Command |
|--------|---------|
| Best effort for current env | `bash scripts/run-regression-agent.sh` |
| Strict + Tekton Results | `bash scripts/run-regression-agent-full.sh` |
| Timestamped log + correct exit code | `bash scripts/run-regression-stream.sh …` |

Python bootstrap: see [docs/REGRESSION.md](docs/REGRESSION.md).

## Cursor

Rule **regression-iterate** (always on) reinforces the same behavior in `.cursor/rules/regression-iterate.mdc`.
