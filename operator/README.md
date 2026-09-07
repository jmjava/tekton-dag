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

# Kind cluster soak (CRDs + Deployment; Newman uses --with-operator)
../scripts/install-operator-kind.sh

# Install CRDs + samples (no image)
kubectl apply -f config/crd/bases/
kubectl apply -f config/samples/
```

## Controllers

- **Stack** — structural validation, topo order, and injection gaps (missing Secrets/ConfigMaps) in status.
- **StackRun** — builds a Tekton PipelineRun (PR/bootstrap/merge/promote); resolves `stackRef` or repo name to a Stack CR; PipelineRuns are **orphaned** on delete.
- **Team** — tenant identity (namespace, registry, stack allowlist).

Helm `operator.enabled` defaults **on**. Kind: `../scripts/install-operator-kind.sh` (applies Stack/Team CRs from Git YAML).

The Stack **validating webhook** is implemented in-process (`SetupWebhookWithManager`) but Kind/Helm do **not** install `ValidatingWebhookConfiguration` until certs exist; the controller still validates in status.

Do not add more CRD kinds for promote, intercepts, hooks, or registries. See [milestones/milestone-14.md](../milestones/milestone-14.md).

## Contract with Python

PipelineRun JSON shape must match `orchestrator/pipelinerun_builder.py`. Shared goldens:

- `libs/tekton-dag-common/tests/fixtures/pipelineruns/`
- `internal/pipeline/testdata/golden/`

Regenerate: `python ../scripts/generate-pipelinerun-goldens.py`
