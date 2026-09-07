# Isolation evaluation data

CSV produced by [`scripts/run-isolation-eval.sh`](../../../scripts/run-isolation-eval.sh).

| File | How it is produced | May be cited in a paper? |
|------|--------------------|---------------------------|
| `isolation-eval-plan.csv` | `--offline` (CI / laptop). Pod counts are the **model**, probes empty. | No — experiment *plan* only |
| `isolation-eval-measured-*.csv` | `--cluster` on Kind. Dummy echo servers + header router. | Yes, as a **Kind strategy comparison**, not as site/SEIP production evidence |

Do not mix these rows with production PipelineRun exports (Workstream B).

## Columns

See `CSV_FIELDS` in `scripts/isolation_eval/protocol.py`. `isolation_ok` is the probe contract:

- **intercept:** matched body contains `pr/<changed-app>`; unmatched contains `baseline/` and not `pr/`.
- **clone:** both probes hit `pr/` (the PR namespace has no baseline replica).
