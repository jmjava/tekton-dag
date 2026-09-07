# tekton-dag-operator

Go Kubebuilder operator for **Stack** and **StackRun** custom resources (`tektondag.io/v1alpha1`). This is the intended Kubernetes control plane for stack graphs and pipeline executions, not an optional paper extra.

See [milestones/milestone-14.md](../milestones/milestone-14.md) for architecture and exit criteria.

## Quick commands

```bash
# Generate CRDs / RBAC / deepcopy
make generate manifests

# Unit tests (builders + Stack validation; no envtest required)
go test ./internal/pipeline/ ./internal/controller/

# Build image for Kind
../scripts/publish-operator-image.sh

# Install CRDs + samples
kubectl apply -f config/crd/bases/
kubectl apply -f config/samples/
```

## Controllers

- **Stack** — structural validation + topo order in status (no PipelineRuns).
- **StackRun** — builds a Tekton PipelineRun (PR/bootstrap/merge/promote), syncs phase; PipelineRuns are **orphaned** on delete.

## Contract with Python

PipelineRun JSON shape must match `orchestrator/pipelinerun_builder.py`. Shared goldens:

- `libs/tekton-dag-common/tests/fixtures/pipelineruns/`
- `internal/pipeline/testdata/golden/`

Regenerate: `python ../scripts/generate-pipelinerun-goldens.py`
