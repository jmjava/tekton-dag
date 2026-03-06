# M4 §2: Multi-namespace pipeline scaling

Pipelines and tasks are namespace-agnostic: they have no hardcoded namespace in metadata. You apply them to the namespace you want and run PipelineRuns in that same namespace. This supports a three-tier flow: **local (Kind) → test namespace → production namespace**.

## Three-tier model

1. **Local (Kind)** — Run pipeline changes locally via `generate-run.sh`. Fast iteration.
2. **Test namespace** (e.g. `tekton-test`) — Apply pipeline/task/trigger YAML to a dedicated namespace; trigger runs against test repos/branches. Validate before promoting.
3. **Production namespace** (e.g. `tekton-pipelines`) — Promote proven pipeline versions here. Webhook-triggered runs from real PRs/merges.

## Bootstrap a namespace

Create a namespace with ServiceAccount, RBAC, secrets, build-cache PVC, catalog tasks, and this repo’s tasks/pipelines:

```bash
./scripts/bootstrap-namespace.sh tekton-test
# Optional: --ssh-key, --github-token, --webhook-secret
```

Default namespace if you omit the argument is `tekton-pipelines`.

## Run pipelines in a namespace

- **Env var:** `NAMESPACE=tekton-test ./scripts/generate-run.sh --mode pr --repo demo-fe --pr 1 --apply`
- **Flag:** `./scripts/generate-run.sh --mode pr --repo demo-fe --pr 1 --namespace tekton-test --apply`

Generated PipelineRuns use the given namespace. Apply with `kubectl create -f -` (or `--apply`) so they run in that namespace.

## Promote pipelines to another namespace

After validating in a test namespace, apply the same YAML to production:

```bash
./scripts/promote-pipelines.sh --from tekton-test --to tekton-pipelines
# Optional: --dry-run to print without applying
```

This applies `tasks/` and `pipeline/` from the repo into the target namespace. Promotion is manual — the operator decides when a pipeline version is ready for production.

## EventListener and webhooks per namespace

Each namespace has its own EventListener and Service. Webhook URLs must target the namespace you want (different host, path, or port). See [m4-eventlistener-per-namespace.md](m4-eventlistener-per-namespace.md).

## Pipeline versioning

Pipeline and task resources are labeled with `app.kubernetes.io/version: "1.0.0"` so operators can see which version is deployed in each namespace. Update the version in the YAML when you cut a new pipeline release.
