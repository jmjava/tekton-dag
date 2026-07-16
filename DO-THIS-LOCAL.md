# Do this local — M13 cluster / E2E follow-up

Cloud agents for this PR ran **`--local-only`** (no `kubectl` / Docker / Kind). Unit, schema, manifest, and Newman-collection coverage for the new features ships in the PR; **cluster-backed verification must be done on a machine with a Tekton-capable cluster**.

**Coverage already in CI/local-only:** pytest for webhook HMAC, injection helpers, reliability classifier, resource profiles, promote builder/API, JSON Schema fixture validation, and static checks that PR/promote YAML include `retries` / `max-retries` / `validate-secrets`. Newman requests for promote + injection-status are in `tests/postman/orchestrator-tests.json` (run when orchestrator is live).

## Prerequisites

- Kind (or equivalent) cluster with Tekton Pipelines installed
- This repo checked out on branch `cursor/m13-production-hardening-features-b923` (or `main` after merge)
- Python venv + tools from [docs/AGENT-REGRESSION.md](docs/AGENT-REGRESSION.md)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r orchestrator/requirements.txt -r management-gui/backend/requirements-dev.txt
pip install -e 'libs/tekton-dag-common[test]' -e 'libs/baggage-python[test]'
# optional, for schema fixture tests:
pip install 'jsonschema>=4.0'
```

## 1. Apply new Tekton definitions

```bash
kubectl apply -f tasks/promote-images.yaml -n tekton-pipelines
kubectl apply -f tasks/deploy-full-stack.yaml -n tekton-pipelines
kubectl apply -f pipeline/stack-promote-pipeline.yaml -n tekton-pipelines
kubectl apply -f pipeline/stack-pr-pipeline.yaml -n tekton-pipelines   # retries + max-retries param
```

Rebuild/republish images so in-cluster pods pick up webhook HMAC, promote mode, and injection-status:

```bash
./scripts/publish-orchestrator-image.sh
# optional: GUI BFF (injection-status proxy)
./scripts/publish-management-gui-image.sh
# then restart the orchestrator / management-gui Deployments / Helm release
```

## 2. Platform regression (required)

```bash
bash scripts/run-regression-agent.sh
# expect: regression exit code: 0
# with kubectl: should NOT fall back to --local-only
```

Stricter (Newman + required `stack-dag-verify`):

```bash
bash scripts/run-regression-stream.sh --cluster --require-dag-verify
```

Newman collection now includes **promote** and **injection-status** requests (`tests/postman/orchestrator-tests.json`).

## 3. Feature smoke (manual / scripted)

### 3a. Secrets/config injection

1. Create a Secret + ConfigMap in the app namespace (e.g. `staging`):

```bash
kubectl -n staging create secret generic demo-fe-db --from-literal=PASSWORD=test
kubectl -n staging create configmap demo-fe-config --from-literal=LOG_LEVEL=debug
```

2. Temporarily add to an app in a stack YAML (local-only edit is fine):

```yaml
secrets:
  env-from: [demo-fe-db]
config:
  env-from: [demo-fe-config]
```

3. Call injection-status (port-forward orchestrator first):

```bash
curl -s "http://localhost:9091/api/apps/demo-fe/injection-status?namespace=staging" | jq .
# expect: ok=true, secrets.demo-fe-db=present, configmaps.demo-fe-config=present
```

4. Run bootstrap (or a deploy that uses `deploy-full-stack`) and confirm the Deployment has `envFrom` for those refs. Delete the Secret and re-deploy to confirm **fail-fast** when `validate-secrets=true`.

### 3b. Webhook HMAC

```bash
# Create webhook secret (key: secret)
kubectl -n tekton-pipelines create secret generic github-webhook-secret \
  --from-literal=secret='local-test-secret'

# With WEBHOOK_SECRET / WEBHOOK_SECRET_NAME configured on the orchestrator:
# - request WITHOUT X-Hub-Signature-256 → 401
# - request WITH valid sha256 HMAC → 200 and PipelineRun created
```

### 3c. Promote pipeline (dry-run)

`target_environment: staging` resolves URL/creds from `stacks/registries.yaml` when
`target_registry` / `credentials_secret` are omitted. Multi-app: `"changed_app": "demo-fe,demo-api"`.

```bash
curl -s -X POST http://localhost:9091/api/run \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "promote",
    "release_version": "0.0.1",
    "target_environment": "staging",
    "changed_app": "demo-fe",
    "target_registry": ""
  }' | jq .
# Empty target_registry → promote-images dry-run (no crane copy)
kubectl get pipelinerun -n tekton-pipelines -l tekton.dev/pipeline=stack-promote
```

Management GUI BFF: `GET /api/teams/<team>/apps/<app>/injection-status` (same shape as orchestrator).

Approval gate:

```bash
curl -s -X POST http://localhost:9091/api/run \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "promote",
    "release_version": "0.0.1",
    "target_environment": "production",
    "changed_app": "demo-fe",
    "require_approval": true,
    "approved_by": "you@example.com"
  }' | jq .
```

### 3d. Reliability

- Confirm PR PipelineRuns include `spec.timeouts.pipeline` and param `max-retries`.
- Confirm `stack-pr-test` compile/containerize tasks show `retries: 2` in the applied Pipeline.
- Optional: set `PIPELINE_TIMEOUT=45m` / `MAX_RETRIES=0` on the orchestrator Deployment and trigger a run.

## 4. Optional heavy E2E

```bash
bash scripts/run-regression.sh --kind-e2e
```

Use when changing bootstrap, intercepts, or full-stack deploy behavior. Long-running.

## 5. Still open after local smoke (product follow-ups)

These are **not** blocked on this checklist; track in [milestones/milestone-13.md](milestones/milestone-13.md):

- Intercept deploy (`deploy-intercept*`) secret/config wiring
- Management GUI panel for injection-status
- Helm `appConfig` / ESO templates
- Cross-cluster deploy task
- `pytest-cov` CI gate

## Done when

- [ ] `bash scripts/run-regression-agent.sh` → **`regression exit code: 0`** with cluster tiers (not `--local-only` only)
- [ ] Newman includes promote + injection-status green against live orchestrator
- [ ] At least one promote dry-run PipelineRun **Succeeded**
- [ ] injection-status shows present/missing correctly for a test Secret
- [ ] Webhook rejects bad HMAC when secret is configured
