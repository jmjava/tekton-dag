# Milestone 14 — Kubernetes Operator (CRD-primary)

**Status:** In progress — CRD-primary is the **intended** control plane. Foundations shipped (Stack/StackRun CRDs, Go reconciler, Flask `STACKRUN_VIA_CRD` bridge, Helm `operator.enabled`). Remaining work is Kind soak and default-on, not a paper-driven deferral.

**Goal:** Make **Stack** and **StackRun** custom resources the source of truth for desired stack graphs and pipeline executions. The Flask orchestrator thins to webhook/API that creates CRs; a Go Kubebuilder operator reconciles StackRuns into Tekton PipelineRuns. Academic packaging in `docs/research/` may mention this as status; it must not keep `operator.enabled=false` as a permanent product choice.

## Architecture

```
GitHub webhook / POST /api/run
        │
        ▼
Flask orchestrator (HMAC + resolve)
        │  STACKRUN_VIA_CRD=true
        ▼
StackRun CR  ──►  tekton-dag-operator  ──►  PipelineRun (orphaned for Results)
Stack CR     ──►  validation / topo status only
```

**API group:** `tektondag.io/v1alpha1`

| CRD | Purpose |
|-----|---------|
| **Stack** | Desired app DAG (mirrors `stacks/schema.json` fields) |
| **StackRun** | One execution: `mode` = `pr` \| `bootstrap` \| `merge` \| `promote` |

**Garbage collection:** PipelineRuns are **orphaned** when StackRuns are deleted (no cascading delete) so Tekton Results history is retained. StackRuns are labeled `tektondag.io/stackrun=<name>`.

## Implementation layout

| Path | Role |
|------|------|
| [`operator/`](../operator/) | Kubebuilder project (API types, controllers, Dockerfile) |
| [`operator/internal/pipeline/`](../operator/internal/pipeline/) | Go PipelineRun builders (golden-tested vs Python) |
| [`orchestrator/stackrun_builder.py`](../orchestrator/stackrun_builder.py) | Flask → StackRun manifest |
| [`helm/tekton-dag/`](../helm/tekton-dag/) | `operator.enabled`, CRDs under `crds/`, `STACKRUN_VIA_CRD` env |
| Golden fixtures | `libs/tekton-dag-common/tests/fixtures/pipelineruns/` (+ Go testdata) |

Regenerate goldens: `python scripts/generate-pipelinerun-goldens.py`

## Checklist

- [x] Fix M13 webhook unit-test isolation (empty default `WEBHOOK_SECRET_NAME`)
- [x] Scaffold Kubebuilder operator with Stack + StackRun
- [x] Port PipelineRun builders to Go with shared goldens
- [x] StackRun reconciler (create PipelineRun, sync status) + Stack validation
- [x] Flask `STACKRUN_VIA_CRD` path + Helm wiring
- [x] Milestone / README / DO-THIS-LOCAL smoke notes
- [ ] Kind: build/push operator image + live StackRun → PipelineRun create (`scripts/install-operator-kind.sh`)
- [ ] Newman with `STACKRUN_VIA_CRD=true` against cluster (`run-cluster-ci.sh --with-operator`)
- [ ] Default `operator.enabled=true` after soak

## Exit criteria

1. Regression green (Phase 0 + cluster DAG verify when Tekton installed).
2. `cd operator && go test ./internal/...` (builders + Stack validation).
3. Sample Stack + StackRun applied; operator creates a PipelineRun with correct params.
4. With `STACKRUN_VIA_CRD=true`, orchestrator API creates StackRuns.
5. Docs + Helm `operator.enabled` documented.

## Follow-ons (not in this ship slice)

- **Team** CR replacing `teams/*/team.yaml` ConfigMaps
- GUI native StackRun views / promote approve via patching `StackRun.spec.approvedBy`
- Validating admission webhook for Stack
- Retire direct PipelineRun creation path once CRD path is default-on
