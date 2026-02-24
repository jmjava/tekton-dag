#!/usr/bin/env bash
# Extract this milestone into a standalone repo for local-only use (no AWS).
# Target repo: github.com/jmjava/tekton-dag. Share changes back to reference-architecture-poc when ready.
#
# Usage: ./extract-standalone-repo.sh [OUTPUT_DIR]
#   OUTPUT_DIR defaults to ../tekton-dag (sibling of reference-architecture-poc)
#
# Then: create repo on GitHub (jmjava/tekton-dag), then:
#   cd OUTPUT_DIR && git init && git add . && git commit -m "Standalone Tekton DAG (local)" && git remote add origin https://github.com/jmjava/tekton-dag.git && git branch -M main && git push -u origin main
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MILESTONE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="${1:-$(cd "$MILESTONE_DIR/../.." && pwd)/tekton-dag}"

echo "  Extracting from: $MILESTONE_DIR"
echo "  Output (new repo root): $OUT_DIR"
echo ""

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# Copy directories (no .git)
for d in stacks tasks pipeline scripts docs; do
  [ -d "$MILESTONE_DIR/$d" ] || continue
  cp -R "$MILESTONE_DIR/$d" "$OUT_DIR/"
  echo "  Copied $d/"
done

# Fix paths:  -> repo root (empty)
find "$OUT_DIR" -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.md" \) -print0 | while IFS= read -r -d '' f; do
  if grep -q "" "$f" 2>/dev/null; then
    sed -i 's|||g' "$f"
    sed -i 's|||g' "$f"
  fi
done
# Default git URL in scripts to jmjava/tekton-dag
for f in "$OUT_DIR/scripts/verify-dag-phase2.sh" "$OUT_DIR/scripts/generate-run.sh"; do
  [ -f "$f" ] && sed -i 's|https://github.com/menkelabs/reference-architecture-poc.git|https://github.com/jmjava/tekton-dag.git|g' "$f" && true
  [ -f "$f" ] && sed -i 's|git@github.com:menkelabs/reference-architecture-poc.git|https://github.com/jmjava/tekton-dag.git|g' "$f" && true
done
echo "  Fixed paths and default GIT_URL → jmjava/tekton-dag"

# Root README for standalone repo
cat > "$OUT_DIR/README.md" <<'README'
# tekton-dag

Standalone Tekton pipeline system for **local development and proof-of-concept**. No AWS. Run on Kind (or any Kubernetes) with a local registry and optional Telepresence. Proves out the stack DAG and pipelines locally; [share back to reference-architecture-poc](SHARING-BACK.md) when ready.

## Quick start (local)

```bash
# 1. Kind cluster + local registry
./scripts/kind-with-registry.sh

# 2. Tekton + stack tasks/pipelines (labels namespace for Pod Security)
./scripts/install-tekton.sh

# 3. Optional: Telepresence Traffic Manager (for full PR pipeline with intercepts)
./scripts/install-telepresence-traffic-manager.sh

# 4. Prove the DAG
./scripts/verify-dag-phase1.sh
# Phase 2 clones this repo; after push set GIT_URL to the repo URL:
export GIT_URL="https://github.com/jmjava/tekton-dag.git"
./scripts/verify-dag-phase2.sh
```

For manual pipeline runs, use `--registry localhost:5000 --storage-class ""`. See the full [README in docs](docs/README-FULL.md) (copied from the main design) for concepts, stack YAML, and pipeline flows.

## Layout

- **stacks/** — Stack YAML (DAG), registry, versions
- **tasks/** — Tekton tasks (resolve, build, deploy-intercept, validate, test, version, cleanup)
- **pipeline/** — stack-pr-test, stack-merge-release, stack-dag-verify
- **scripts/** — kind-with-registry, install-tekton, install-telepresence-traffic-manager, verify-dag-phase1/2, generate-run, stack-graph
- **docs/** — C4 diagrams, local DAG verification plan

## Sharing back to reference-architecture

See [SHARING-BACK.md](SHARING-BACK.md).
README

# Full README (design doc) in docs for reference
[ -d "$OUT_DIR/docs" ] || mkdir -p "$OUT_DIR/docs"
if [ -f "$MILESTONE_DIR/README.md" ]; then
  cp "$MILESTONE_DIR/README.md" "$OUT_DIR/docs/README-FULL.md"
  sed -i 's|||g' "$OUT_DIR/docs/README-FULL.md"
  sed -i 's|||g' "$OUT_DIR/docs/README-FULL.md"
  echo "  Added docs/README-FULL.md"
fi
# Fix paths in other docs (verification plan, etc.) - already under find/sed above

# SHARING-BACK.md
cat > "$OUT_DIR/SHARING-BACK.md" <<'SHARING'
# Sharing changes back to reference-architecture-poc

This repo is a **standalone copy** of the `` content, tuned for local runs (Kind, local registry, no AWS). When you have it working locally, you can bring changes back into the main reference-architecture repo.

## Option A: Copy files back by hand

Copy the modified files from this repo into `reference-architecture-poc/`:

- `stacks/`, `tasks/`, `pipeline/`, `scripts/`, `docs/`
- In the main repo, paths stay as `...` in pipeline params and resolve-stack/version-bump defaults.

So when copying back, **re-add the path prefix** where the main repo expects it:

- In pipeline YAML defaults: `stacks/stack-one.yaml` → `stacks/stack-one.yaml`
- In tasks (resolve-stack, version-bump): `stacks/versions.yaml` → `stacks/versions.yaml`
- In scripts (generate-run, verify-dag-phase2): `STACK_PATH="stacks/$STACK"` → `STACK_PATH="stacks/$STACK"` (or `$STACK_FILE`)

## Option B: Branch in reference-architecture and apply diffs

1. In `reference-architecture-poc`, create a branch from the commit that has the current milestone.
2. For each logical change (e.g. “Phase 2 HTTPS default”, “Pod Security in install-tekton”), apply the same edit in the milestone tree, keeping `` paths.
3. Open a PR to merge the branch into the main branch.

## What to share back

- **Script fixes**: install-tekton (Pod Security labels), verify-dag-phase2 (HTTPS default, polling, timeout), kind-with-registry, install-telepresence-traffic-manager.
- **Pipeline/task changes**: any fixes or features you added for local runs (path defaults stay under `` in the main repo).
- **Docs**: verification plan, README sections for “Running locally”, “Kind + registry”, “Traffic Manager”.

Keeping this standalone repo in sync with the milestone is optional; the main goal is to get a working local proof-of-concept and then merge the important changes back.
SHARING

# .gitignore
cat > "$OUT_DIR/.gitignore" <<'GITIGNORE'
# Local overrides / env
.env
*.local
standalone-repo-output/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
GITIGNORE

echo ""
echo "  Done. Standalone repo root: $OUT_DIR"
echo "  Next steps:"
echo "    1. Create the repo on GitHub: https://github.com/new → owner jmjava, name tekton-dag"
echo "    2. Then:"
echo "       cd $OUT_DIR"
echo "       git init"
echo "       git add ."
echo "       git commit -m 'Standalone Tekton DAG (local, no AWS)'"
echo "       git remote add origin https://github.com/jmjava/tekton-dag.git"
echo "       git branch -M main"
echo "       git push -u origin main"
echo ""
echo "  For Phase 2 DAG verify, set GIT_URL=https://github.com/jmjava/tekton-dag.git (after push)."
echo ""
