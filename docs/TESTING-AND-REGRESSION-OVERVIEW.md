# Testing and regression overview (for operators and demo narration)

This document is the **story** behind how tekton-dag is verified end-to-end. Use it for **onboarding**, **release checklists**, and **video voiceover**. Operational detail lives in [REGRESSION.md](REGRESSION.md), [AGENT-REGRESSION.md](AGENT-REGRESSION.md), and [scripts/run-regression.sh](../scripts/run-regression.sh).

## Why regression is more than unit tests

| Layer | What it proves | Typical command / artifact |
|-------|----------------|----------------------------|
| **Static DAG** | Stack YAML, registry, and `stack-graph.sh` agree (no cluster). | `verify-dag-phase1.sh` |
| **Libraries** | Resolver, baggage, orchestrator routes behave with mocks. | pytest, vitest |
| **UI** | Management GUI flows work against a running app. | Playwright (`management-gui/frontend`) |
| **Live orchestrator** | HTTP API matches Postman contracts (cluster). | Newman + `run-orchestrator-tests.sh` |
| **Real Tekton run** | A **PipelineRun** (`stack-dag-verify`) reaches **Succeeded** and matches CLI resolution. | `verify-dag-phase2.sh` (via `run-regression.sh` or `run-full-test-and-verify-results.sh`) |
| **Results persistence** | Runs are visible in Tekton Results API / DB. | `verify-results-in-db.sh` |

**Takeaway for demos:** Say explicitly that **pytest green ≠ cluster green**. The regression driver ties local checks to **at least one successful pipeline** when the cluster has `stack-dag-verify` installed.

## One command to aim for

- **Best match to “full” on a dev cluster:**  
  `bash scripts/run-regression-agent.sh`  
  (or `bash scripts/run-regression-stream.sh --cluster --require-dag-verify` for timestamped logs.)

- **Strict + Tekton Results:**  
  `bash scripts/run-regression-agent-full.sh`

- **Laptop without kubeconfig:**  
  `bash scripts/run-regression-stream.sh --local-only`  
  (Document that Tekton/Newman/Results tiers were skipped.)

Prep steps (free ports **9091** / **8080**, auto-`.venv`, etc.) are described in [REGRESSION.md](REGRESSION.md).

## What to show in a “regression” video

1. **Terminal:** run `run-regression-stream.sh` or `run-regression-agent.sh`; scroll log highlights: Phase 1 → pytest → Phase 2 **PipelineRun** → Newman → optional Results.  
2. **Split second:** `kubectl get pipelinerun -n tekton-pipelines` while Phase 2 runs (optional).  
3. **Close:** final line `regression exit code: 0`.

Shot list and timing hooks: [demos/segments-m12-2-regression-gui.md](demos/segments-m12-2-regression-gui.md).

## Related milestones

- [M10.1](../milestones/milestone-10-1.md) — Newman orchestrator tests.  
- [M11](../milestones/milestone-11.md) — Management GUI + Playwright.  
- [M12.2 extension](../milestones/milestone-12.2.md) — this doc + GUI extension guide + demo segments.
