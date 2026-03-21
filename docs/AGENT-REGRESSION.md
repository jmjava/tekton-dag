# Agent playbook: regression until fully done

Human or **Cursor agent**: do not treat testing as complete after a single partial command (e.g. pytest only, or Newman only). **Iterate**: run → read output → fix → re-run **until** the target command exits **0** and the log matches the done criteria below.

## Target commands (pick one)

| Goal | Command (repo root) |
|------|---------------------|
| **Strict cluster** (orchestrator + `newman` + **required** `stack-dag-verify` PipelineRun) | `bash scripts/run-regression-stream.sh --cluster --require-dag-verify` |
| **+ Tekton Results DB** (fails if Results API missing) | `bash scripts/run-regression-stream.sh --cluster --require-dag-verify --with-results-verify` |
| **No cluster** (explicitly limited) | `bash scripts/run-regression-stream.sh --local-only` — then **state** that Tekton/Newman/Results were not run. |

Convenience (detects `kubectl`; uses strict cluster if context works, else local-only with a stderr banner):

```bash
bash scripts/run-regression-agent.sh
```

Bootstrap Python once if needed:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r orchestrator/requirements.txt -r management-gui/backend/requirements-dev.txt
pip install -e 'libs/tekton-dag-common[test]' -e 'libs/baggage-python[test]'
```

## Done criteria (all must hold for “cluster regression done”)

1. Final line: **`regression exit code: 0`** (use `run-regression-stream.sh`, not a broken pipe to `while read`).
2. Log contains **either**:
   - **`Phase 2 PASSED`** (standalone `verify-dag-phase2`), **or**
   - **`Tekton DAG verify: will run inside run-full-test-and-verify-results.sh`** and that script completes successfully, **or**
   - You documented **why** the cluster cannot run Phase 2 (and you did not claim full cluster verification).
3. **No unexplained `SKIP Tekton DAG verify`** when `stack-dag-verify` should exist — if you see it, fix install/namespace or pass `--require-dag-verify` and resolve the failure.
4. Newman/orchestrator: no port-forward bind failure; if it fails, free port or set `ORCHESTRATOR_TEST_PORT`.

## Iteration loop (required agent behavior)

```
repeat {
  run the chosen target command; capture full log
  if exit 0 and done criteria met → STOP (success)
  identify failing tier (pytest / Playwright / Phase 2 / Newman / Results)
  apply minimal fix (code, script, manifest, env, cluster)
} until success or human abort
```

Do **not** stop after only:

- Phase 1 + unit tests, or  
- Newman without a **Succeeded** `stack-dag-verify` path (see [REGRESSION.md](REGRESSION.md) “What actually runs Tekton PipelineRuns?”).

## References

- [REGRESSION.md](REGRESSION.md) — tiers, flags, env vars  
- [GITHUB-PAGES.md](GITHUB-PAGES.md) — if work touches Pages  
