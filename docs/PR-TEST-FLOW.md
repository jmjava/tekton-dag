# Valid PR test: real GitHub PR → pipeline → merge → merge build

The **only valid test** for the PR feature is using a **real GitHub PR in the app repo** (the app being tested with the intercept, e.g. `jmjava/tekton-dag-vue-fe` for `demo-fe`). Create the PR in that app repo, run the PR pipeline with that app’s PR number and branch, then merge the app PR — the **merge pipeline** then runs automatically (via GitHub webhook to the EventListener) or you run it manually. Other runs (e.g. `--pr 999` with `--git-revision main` on the platform repo) only verify that the pipeline runs; they do **not** test the PR flow.

## Why the PR is in the app repo

- The PR pipeline tests **one changed app** (intercept). That app’s code is cloned from **its** repo (e.g. `jmjava/tekton-dag-vue-fe`). The valid test is: open a PR **in that app repo**, so the pipeline clones the app at the PR branch and builds/tests it. The **platform repo** (tekton-dag) stays on `main` (or your chosen revision); only the changed app uses the PR branch.
- Merging that app PR and running the merge pipeline verifies the full lifecycle: app PR branch → main after merge → release build.

## Prerequisites

- Kind (or cluster) with Tekton, registry, SSH secret for git, optional Telepresence/Results.
- **App repo** cloned under `APP_REPOS_ROOT` (default `$HOME/github`), e.g. `$HOME/github/jmjava/tekton-dag-vue-fe`.
- Push access to the app repo (SSH or token). For creating/merging the PR: `gh` CLI or `GITHUB_TOKEN` with repo scope.

## Step 1: Create a real PR in the app repo

From the **platform repo** (tekton-dag) root, create the PR in the **app** that you want to test (e.g. `demo-fe` → repo `jmjava/tekton-dag-vue-fe`):

```bash
./scripts/create-test-pr.sh --app demo-fe
```

This uses the app repo at `$APP_REPOS_ROOT/jmjava/tekton-dag-vue-fe`: creates a new branch (e.g. `test-pr-20260226120000`), adds a trivial change, pushes it, and opens a PR **in that app repo**. Output:

```
APP=demo-fe
PR_NUMBER=3
BRANCH_NAME=test-pr-20260226120000
```

If you don’t have `gh` or `GITHUB_TOKEN`, the script still pushes the branch; create the PR manually on GitHub for that app repo and note the PR number.

## Step 2: Run the PR pipeline

Use the **app**, **PR number**, and **app branch** from step 1. The pipeline will clone the platform repo at `main` (or your `--git-revision`) and the **changed app** at its PR branch via `--app-revision`:

```bash
./scripts/generate-run.sh --mode pr --stack stack-one.yaml --app demo-fe --pr 3 \
  --app-revision demo-fe:test-pr-20260226120000 --apply
```

Wait for the pipeline to succeed. On success it pushes the version-bump commit to the PR branch (in the platform repo; the app repo PR branch is unchanged). Optionally, the post-pr-comment task will comment on the PR with status and a Dashboard link.

## Step 3: Merge the app PR (this triggers the merge pipeline)

After the PR pipeline succeeds, merge the PR **in the app repo**:

```bash
./scripts/merge-pr.sh 3 --repo jmjava/tekton-dag-vue-fe
```

Or use `--app` so the repo is resolved from the stack: `./scripts/merge-pr.sh 3 --app demo-fe`.

**If the GitHub webhook is configured** (see below), merging the PR automatically triggers the **merge pipeline** (`stack-merge-release`). The EventListener receives the `pull_request` `closed` + `merged` event and creates a PipelineRun that clones the platform repo at `main`, clones app repos at `main` (including the merged change), promotes the RC version to release, builds, tags, and pushes. No manual run of `generate-run.sh --mode merge` is needed.

**If the webhook is not configured**, run the merge pipeline manually after merging:

```bash
./scripts/generate-run.sh --mode merge --stack stack-one.yaml --app demo-fe --apply
```

### Configuring the webhook so merge triggers the pipeline

**Option A — script (recommended):** Run the helper script so merge automatically triggers the pipeline. It adds the webhook to every app repo from your stack(s) and creates/updates the Kubernetes secret.

1. Install Tekton Triggers and apply `pipeline/triggers.yaml` (EventListener, bindings, templates).
2. Expose the EventListener so GitHub can reach it (e.g. `kubectl port-forward svc/el-stack-event-listener 8080:8080 -n tekton-pipelines`, or use a LoadBalancer/Ingress URL).
3. Run the script (use a URL that GitHub can POST to; for local port-forward you need a tunnel like ngrok or your cluster's public URL):
   ```bash
   # GITHUB_TOKEN must have admin:repo_hook (or repo) scope
   ./scripts/configure-github-webhooks.sh --url https://your-event-listener-url
   ```
   The script reads app repos from the stack (default `stack-one.yaml`), creates or updates a Pull requests webhook on each repo, and creates/updates the `github-webhook-secret` secret in the cluster. Use `--dry-run` to see what would be done.

**Option B — manual:** In each **app repo** (e.g. jmjava/tekton-dag-vue-fe), add a GitHub webhook: Payload URL = EventListener URL, Content type = `application/json`, Events = “Pull requests”. Set the same secret as in the `github-webhook-secret` Kubernetes secret.
When a PR is merged in an app repo, the `pr-merged` trigger fires and creates a merge PipelineRun automatically.

---

## What is *not* the valid PR test

- **`run-e2e-with-intercepts.sh`** with `--pr 1` or `--pr 999` and default `--git-revision main`: runs the PR pipeline against `main` with a PR number used only for naming and optional comment. No real PR in the app repo; the intercept is not testing an app PR branch. Use this only for **pipeline sanity checks** (bootstrap + one PR-style run).
- **`generate-run.sh --mode pr --pr 999 --git-revision main`** (no `--app-revision`): same idea; not the PR feature test.

The **valid** test is: create real PR **in the app repo** → run PR pipeline with that app, PR number, and `--app-revision app:branch` → merge that app PR → merge pipeline runs (automatically via webhook or manually).
