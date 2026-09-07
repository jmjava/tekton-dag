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
- [x] Kind: build/push operator image + live StackRun → PipelineRun create (`scripts/install-operator-kind.sh`)
- [x] Newman with `STACKRUN_VIA_CRD=true` against cluster (`run-cluster-ci.sh --with-operator`)
- [x] Default `operator.enabled=true` after soak

## Exit criteria

1. Regression green (Phase 0 + cluster DAG verify when Tekton installed).
2. `cd operator && go test ./internal/...` (builders + Stack validation).
3. Sample Stack + StackRun applied; operator creates a PipelineRun with correct params.
4. With `STACKRUN_VIA_CRD=true`, orchestrator API creates StackRuns.
5. Docs + Helm `operator.enabled` documented.

## Follow-ons (not in this ship slice)

- GUI native StackRun **views** (list/detail); trigger already creates StackRuns
- Enable the Stack validating webhook in-cluster (certs / `ValidatingWebhookConfiguration`; validation + webhook code already exist)
- Retire `--pipeline-run` / Flask `STACKRUN_VIA_CRD=false` escape hatches once every cluster runs the operator

## Control plane: what is a CR (and what is not)

Two kinds are the execution control plane: **Stack** (desired DAG) and **StackRun** (one run). Do not add a third execution CR (`Promotion`, `PRBuild`, `InterceptSession`, …). Those are `StackRun.spec.mode` (plus fields already on the spec: intercept backend, promote target, `approvedBy`).

The gaps that actually hurt are **split sources of truth** and **bypasses**, not missing CRD types.

### Do this on the existing CRs / operator

| Gap | Today | Product move |
|-----|--------|----------------|
| Stack YAML vs Stack CR | Git `stacks/*.yaml` + ConfigMap `tekton-dag-stacks` is what Flask/Tekton read. Stack CRs are samples / kubectl only. Flask never sets `stackRef`. | Make **Stack CR the in-cluster desired state**. Orchestrator/GUI resolve from Stacks; Tekton still gets a stack-file param (operator can copy spec → ConfigMap or pass `stackRef`). Git remains the GitOps source; Helm/Argo apply Stacks. |
| GUI / scripts skip the operator | Management GUI `create_pipelinerun`; `generate-run.sh`; EventListener templates create PipelineRuns. Hardcoded CEL repo→stack in `pipeline/triggers.yaml`. | Same create path as Flask: **StackRun only**. Point GitHub at the orchestrator (or a TriggerTemplate that creates a StackRun). Delete the CEL overlay map; resolve from Stack CRs. |
| `stack-pr-continue` | Separate Pipeline + `rerun-pr-from.sh` | New StackRun (`mode=pr` + continue-from) or a field on the failed StackRun — **not** a new CRD. |
| Injection / approval UX | Flask `injection-status` lists Secrets; promote `approvedBy` is already on StackRun spec | Put missing Secret/ConfigMap names on **Stack.status**. GUI patches **StackRun.spec.approvedBy**. |
| Team identity | `teams/*/team.yaml` ConfigMaps | **Team** CR (already named). One per tenant: namespace, registry, stack allowlist, intercept default. |

### Do not invent CRs for

| Tempting CR | Why not |
|-------------|---------|
| Pipeline / Task / PipelineRun | Tekton owns execution. Operator creates PipelineRuns. |
| InterceptSession / PreviewNamespace | Ephemeral PR runtime. Telepresence/mirrord (and our intercept tasks) already create those objects. Lifecycle belongs to the StackRun’s PipelineRun. |
| HookPolicy / CustomHook | Hook names are Pipeline params that resolve to **Tekton Tasks**. |
| Registry / Environment / Cluster | `stacks/registries.yaml` + StackRun promote fields. A Cluster CR only pays off when cross-cluster **deploy** exists (M13); promote copy is not that. |
| AppVersion / CompileImage | `versions.yaml` and Helm `compileImageVariants` are install/build config. |
| WebhookConfig | HMAC Secret + Flask (or Triggers EventListener). Credentials stay Secrets. |
| Graph / TestPlan / Results | Neo4j and Tekton Results are stores, not desired state. |
| IsolationEval | Measurement harness (`run-isolation-eval.sh`), not platform API. |

**Admission webhook** for Stack is the right next *operator* feature. It is not a new CRD.

**Default `operator.enabled=true`** is how this becomes the control plane. Extra kinds before that would freeze the dual path in place.
