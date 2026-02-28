# PR and webhook merge test flow (runbook)

End-to-end test: real PR in app repo → PR pipeline → merge PR → **webhook triggers merge pipeline**.

## Prerequisites

- Cluster (Kind) with Tekton, registry, SSH secret `git-ssh-key`, optional Telepresence/Results.
- App repo cloned at `$APP_REPOS_ROOT/jmjava/tekton-dag-vue-fe` (default `$HOME/github/...`).
- `.env` with `GITHUB_TOKEN` (and optionally `EVENT_LISTENER_URL`, Cloudflare vars).
- **Webhook:** GitHub webhooks on app repos pointing to your EventListener (e.g. https://tekton-el.menkelabs.com). Run `./scripts/configure-github-webhooks.sh` once with that URL.
- **Tunnel + port-forward** (if EventListener is behind Cloudflare tunnel):
  - `cloudflared tunnel run menkelabs-sso-tunnel-config &`
  - `kubectl port-forward svc/el-stack-event-listener 8080:8080 -n tekton-pipelines &`

---

## 1. Create a real PR in the app repo

```bash
cd /home/ubuntu/github/jmjava/tekton-dag
set -a && source .env && set +a
./scripts/create-test-pr.sh --app demo-fe
```

Note the output: `APP=demo-fe`, `PR_NUMBER=<N>`, `BRANCH_NAME=<branch>`.

---

## 2. Run the PR pipeline

Use the values from step 1:

```bash
./scripts/generate-run.sh --mode pr --stack stack-one.yaml --app demo-fe --pr <PR_NUMBER> \
  --app-revision demo-fe:<BRANCH_NAME> --apply
```

Example: `--pr 1 --app-revision demo-fe:test-pr-20260227215326`

Watch the run:

```bash
kubectl get pipelinerun -n tekton-pipelines -l tekton.dev/pipeline=stack-pr-test -w
```

Or wait for completion:

```bash
kubectl wait --for=condition=Succeeded pipelinerun -l tekton.dev/pipeline=stack-pr-test -n tekton-pipelines --timeout=900s
```

(Adjust the label if you need the specific run name.)

---

## 3. Merge the app PR (webhook triggers merge pipeline)

After the PR pipeline **succeeds**, merge the PR:

```bash
./scripts/merge-pr.sh <PR_NUMBER> --app demo-fe
```

Example: `./scripts/merge-pr.sh 1 --app demo-fe`

- **If the webhook is set up:** GitHub sends `pull_request` `closed` + `merged` to your EventListener; the `pr-merged` trigger creates a **stack-merge-release** PipelineRun automatically. No further command needed.
- **If the webhook is not set up:** Run the merge pipeline manually:
  ```bash
  ./scripts/generate-run.sh --mode merge --stack stack-one.yaml --app demo-fe --apply
  ```

---

## 4. Verify merge pipeline

List merge runs:

```bash
kubectl get pipelinerun -n tekton-pipelines -l tekton.dev/pipeline=stack-merge-release
```

Check the latest run status and logs if needed.

---

## One-shot (after creating the PR)

Replace `<PR_NUMBER>` and `<BRANCH_NAME>` with the output from step 1.

```bash
cd /home/ubuntu/github/jmjava/tekton-dag
set -a && source .env && set +a

# Start PR pipeline
./scripts/generate-run.sh --mode pr --stack stack-one.yaml --app demo-fe --pr <PR_NUMBER> \
  --app-revision demo-fe:<BRANCH_NAME> --apply

# Wait for success (optional; or watch in another terminal)
kubectl get pipelinerun -n tekton-pipelines -w

# When PR pipeline succeeded: merge the PR
./scripts/merge-pr.sh <PR_NUMBER> --app demo-fe
```

Then either the webhook starts the merge pipeline, or you run `./scripts/generate-run.sh --mode merge --stack stack-one.yaml --app demo-fe --apply`.

---

## Troubleshooting

### "pod has unbound immediate PersistentVolumeClaims" / fetch-source Pending

The PipelineRun’s workspace PVC is not binding. Common cause on **Kind**: `STORAGE_CLASS` is set to something the cluster doesn’t have (e.g. `gp3`).

- **Fix:** Don’t set `STORAGE_CLASS` in `.env` on Kind (or set it to `standard` if that’s your default). Re-run with explicit empty storage class:
  ```bash
  unset STORAGE_CLASS
  ./scripts/generate-run.sh --mode pr --stack stack-one.yaml --app demo-fe --pr <N> \
    --app-revision demo-fe:<BRANCH> --storage-class "" --apply
  ```
- **Ensure default StorageClass:** `./scripts/install-kind-default-storage.sh` (no-op if one already exists).
- **After fixing:** Delete the stuck run so its PVCs are removed, then re-run the pipeline:
  ```bash
  kubectl delete pipelinerun stack-pr-1-rggcr -n tekton-pipelines
  ```
