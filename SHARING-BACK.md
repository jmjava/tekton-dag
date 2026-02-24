# Sharing changes back to reference-architecture-poc

This repo is a **standalone copy** of the `milestones/tekton-job-standardization` content, tuned for local runs (Kind, local registry, no AWS). When you have it working locally, you can bring changes back into the main reference-architecture repo.

## Option A: Copy files back by hand

Copy the modified files from this repo into `reference-architecture-poc/milestones/tekton-job-standardization/`:

- `stacks/`, `tasks/`, `pipeline/`, `scripts/`, `docs/`
- In the main repo, paths stay as `milestones/tekton-job-standardization/...` in pipeline params and resolve-stack/version-bump defaults.

So when copying back, **re-add the path prefix** where the main repo expects it:

- In pipeline YAML defaults: `stacks/stack-one.yaml` → `milestones/tekton-job-standardization/stacks/stack-one.yaml`
- In tasks (resolve-stack, version-bump): `stacks/versions.yaml` → `milestones/tekton-job-standardization/stacks/versions.yaml`
- In scripts (generate-run, verify-dag-phase2): `STACK_PATH="stacks/$STACK"` → `STACK_PATH="milestones/tekton-job-standardization/stacks/$STACK"` (or `$STACK_FILE`)

## Option B: Branch in reference-architecture and apply diffs

1. In `reference-architecture-poc`, create a branch from the commit that has the current milestone.
2. For each logical change (e.g. “Phase 2 HTTPS default”, “Pod Security in install-tekton”), apply the same edit in the milestone tree, keeping `milestones/tekton-job-standardization/` paths.
3. Open a PR to merge the branch into the main branch.

## What to share back

- **Script fixes**: install-tekton (Pod Security labels), verify-dag-phase2 (HTTPS default, polling, timeout), kind-with-registry, install-telepresence-traffic-manager.
- **Pipeline/task changes**: any fixes or features you added for local runs (path defaults stay under `milestones/tekton-job-standardization/` in the main repo).
- **Docs**: verification plan, README sections for “Running locally”, “Kind + registry”, “Traffic Manager”.

Keeping this standalone repo in sync with the milestone is optional; the main goal is to get a working local proof-of-concept and then merge the important changes back.
