# Milestone 15 — Control-plane hygiene

**Status:** Completed (squash-merged [#19](https://github.com/jmjava/tekton-dag/pull/19)).

**Goal:** Make the Stack/StackRun path **idempotent and consistent** across Flask, GUI, Triggers, Helm, Kind, and GHA. No new CRDs. This is the punch list from the post-M14 code review.

M14 made CRD-primary the default. M15 removes the leftover dual-path bugs: a second PipelineRun on status conflict, a GHA flag that cannot turn the operator off, Triggers omitting typed `prNumber`, Flask vs GUI promote approval, a soak gate that greens on one of N runs, and dead PipelineRun builders.

## Checklist

- [x] StackRun reconciler: deterministic PipelineRun name (`metadata.name` = StackRun name); adopt existing by name or `tektondag.io/stackrun` label before Create
- [x] `RetryOnConflict` on StackRun status writes; `fail()` requeues if status update fails
- [x] Watch labeled PipelineRuns (backup `RequeueAfter` until terminal)
- [x] Do not mutate `spec.stackRef` in memory during options lookup
- [x] GHA `cluster-regression.yml`: `workflow_dispatch` `with_operator=false` passes `--skip-operator`
- [x] TriggerTemplates set unquoted `spec.prNumber`; keep annotation as fallback; document Stack lookup by `changedApp`
- [x] Flask CRD path: `require_approval` without `approved_by` creates a waiting promote (`PendingApproval`), matching the GUI
- [x] Operator soak: `ready == total` (not `>= 1`)
- [x] Kind orchestrator `imagePullPolicy` patch uses strategic merge (no silent `|| true`)
- [x] Helm `operator.enabled` fails loud when `raw/stack-crs` is empty (run `package.sh`)
- [x] Delete unused GUI `pipelinerun_builder.py`; remove unreachable `generate-run.sh` merge PipelineRun block
- [x] Fix Team CR comment (does not replace Git `team.yaml` yet — that is M16)
- [x] `docs/SCRIPTS.md` describes StackRun default for `generate-run.sh`

## Exit criteria

1. `cd operator && go test ./internal/...` covers adopt-existing, annotation `prNumber`, and `lookupStack`.
2. Orchestrator pytest: promote without `approved_by` returns 200 (operator `PendingApproval`). Direct PipelineRun create was removed in M16.
3. `bash scripts/run-regression-agent.sh` (or `--local-only` if no cluster) exits 0.
4. GHA workflow YAML actually emits `--skip-operator` when the dispatch checkbox is false.

## Out of scope (M16)

Team CR as the Flask/GUI source of truth, in-cluster Stack admission webhook + certs, retiring `--pipeline-run` / `STACKRUN_VIA_CRD=false`, `stack-pr-continue` as a field, demo **spoken** narration/MP4 rebuild, S34 intercept E2E.
