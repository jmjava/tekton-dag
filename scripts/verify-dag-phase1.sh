#!/usr/bin/env bash
set -euo pipefail

# verify-dag-phase1.sh — Phase 1 of local DAG verification (no cluster).
# Run from repo root or from .
# Exits 0 if all checks pass, 1 otherwise.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MILESTONE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$MILESTONE_DIR"

die()  { echo "FAIL: $*" >&2; exit 1; }
ok()   { echo "  OK: $*"; }
fail() { echo "FAIL: $*" >&2; ERRORS=$((ERRORS + 1)); }

ERRORS=0

echo "=============================================="
echo "  Phase 1: DAG verification (no cluster)"
echo "  Dir: $MILESTONE_DIR"
echo "=============================================="

# 1.1 Repo structure
echo ""
echo "1.1 Repo structure"
for dir in stacks tasks pipeline scripts docs; do
  [ -d "$dir" ] || fail "missing directory: $dir"
done
[ -f "stacks/registry.yaml" ] || fail "missing stacks/registry.yaml"
[ -f "stacks/versions.yaml" ] || fail "missing stacks/versions.yaml"
[ -f "scripts/stack-graph.sh" ] || fail "missing scripts/stack-graph.sh"
[ -f "scripts/generate-run.sh" ] || fail "missing scripts/generate-run.sh"
[ $ERRORS -eq 0 ] && ok "repo structure"

# 1.2 + 1.3 + 1.4 Stack validation, topo, entry, chain
STACKS=(
  "stacks/stack-one.yaml"
  "stacks/stack-two-vendor.yaml"
  "stacks/single-app.yaml"
  "stacks/single-flask-app.yaml"
)

echo ""
echo "1.2–1.4 Stack validation, topo order, entry, propagation chain"
for stack in "${STACKS[@]}"; do
  [ -f "$stack" ] || { fail "stack file not found: $stack"; continue; }
  name=$(basename "$stack" .yaml)
  echo "  --- $name ---"

  # validate
  out=$(./scripts/stack-graph.sh "$stack" --validate 2>&1) || true
  if [[ "$out" == *"VALID"* ]]; then
    ok "$name --validate"
  else
    fail "$name --validate: $out"
  fi

  # topo
  topo=$(./scripts/stack-graph.sh "$stack" --topo 2>&1)
  [ -n "$topo" ] && ok "$name --topo: $topo" || fail "$name --topo empty"

  # entry
  entry=$(./scripts/stack-graph.sh "$stack" --entry 2>&1)
  [ -n "$entry" ] && ok "$name --entry: $entry" || fail "$name --entry empty"

  # chain from entry
  chain=$(./scripts/stack-graph.sh "$stack" --chain "$entry" 2>&1)
  [ -n "$chain" ] && ok "$name --chain $entry: $chain" || fail "$name --chain empty"
done

# 1.5 Registry and versions: every app in each stack exists in registry and versions
echo ""
echo "1.5 Registry and versions (apps in stack exist in registry.yaml and versions.yaml)"
need() { command -v "$1" >/dev/null 2>&1 || die "required: $1"; }
need yq

for stack in "${STACKS[@]}"; do
  [ -f "$stack" ] || continue
  name=$(basename "$stack" .yaml)
  apps=$(yq -r '.apps[].name' "$stack" 2>/dev/null | tr '\n' ' ')
  for app in $apps; do
    if yq -e ".repos.\"$app\"" stacks/registry.yaml >/dev/null 2>&1; then
      ok "$name: $app in registry"
    else
      fail "$name: $app missing from registry.yaml"
    fi
    if yq -e ".apps.\"$app\"" stacks/versions.yaml >/dev/null 2>&1; then
      ok "$name: $app in versions"
    else
      fail "$name: $app missing from versions.yaml"
    fi
  done
done

echo ""
echo "=============================================="
if [ $ERRORS -eq 0 ]; then
  echo "  Phase 1 PASSED"
  exit 0
else
  echo "  Phase 1 FAILED ($ERRORS error(s))"
  exit 1
fi
