# Artillery E2E tests for intercept variants

Artillery runs E2E load/flow tests against the stack **entry point** with the intercept header set. Each **intercept variant** (one run per app as `changed-app`) is executed so all forms of intercept are covered.

## Variants

- **stack-one**: 3 variants — `demo-fe`, `release-lifecycle-demo`, `demo-api`
- **stack-two-vendor**: 5 variants — `vendor-fe`, `vendor-middleware`, `vendor-adapter`, `internal-api`, `notifications-svc`

For each variant, the same scenario runs: GET `/` on the entry URL with headers `x-dev-session: pr-N` and `baggage: dev-session=pr-N`. This matches what the Tekton `run-stack-tests` task does in Phase 1 (E2E through entry).

## Run all variants (local)

From repo root:

```bash
# Requires: artillery (npm install -g artillery), yq, jq
./scripts/run-artillery-variants.sh --stack stacks/stack-one.yaml --pr 1
./scripts/run-artillery-variants.sh --stack stacks/stack-two-vendor.yaml --pr 1
```

If the entry service is not at in-cluster DNS (e.g. you use port-forward), set the URL:

```bash
ENTRY_URL=http://localhost:3000 ./scripts/run-artillery-variants.sh --stack stacks/stack-one.yaml --pr 1
```

Dry run (generate configs only, no artillery run):

```bash
./scripts/run-artillery-variants.sh --stack stacks/stack-one.yaml --dry-run
```

## Output

- Generated configs: `tests/artillery/output/artillery-variant-<app>.yml`
- Reports: `tests/artillery/output/report-<app>.json`

## Base config

`entry-e2e.yml` is the reference scenario. The runner script generates a config per variant with the correct `target` and `defaults.headers` and runs Artillery against it.
