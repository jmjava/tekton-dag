#!/usr/bin/env bash
# Verify M4 §1.6 (test stacks) and §2.7 (version labels): YAML parse, required fields, generate-run accepts test stacks.
# Run from repo root: ./scripts/verify-m4-stacks-and-labels.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

ERRORS=0

echo "=== 1. Stack YAML parse and required fields (stacks/*.yaml, excluding registry/versions) ==="
for f in stacks/*.yaml; do
  [[ -f "$f" ]] || continue
  [[ "$f" != *registry.yaml ]] || continue
  [[ "$f" != *versions.yaml ]] || continue
  if ! python3 -c "
import yaml, sys
p = sys.argv[1]
with open(p) as h:
    d = yaml.safe_load(h)
assert d, 'empty doc'
assert 'name' in d, 'missing name'
assert 'propagation' in d, 'missing propagation'
assert 'apps' in d and isinstance(d['apps'], list), 'missing or invalid apps'
for i, a in enumerate(d['apps']):
    assert 'name' in a, 'apps[%d] missing name' % i
    assert 'propagation-role' in a, 'apps[%d] missing propagation-role' % i
    assert a['propagation-role'] in ('originator', 'forwarder', 'terminal'), 'apps[%d] bad propagation-role' % i
    assert 'repo' in a, 'apps[%d] missing repo' % i
print('  OK:', p)
" "$f" 2>/dev/null; then
    echo "  FAIL: $f"
    ((ERRORS++)) || true
  fi
done

echo ""
echo "=== 2. Pipeline and task YAML have app.kubernetes.io/version label ==="
for f in pipeline/*.yaml tasks/*.yaml; do
  [[ -f "$f" ]] || continue
  if ! grep -q 'app.kubernetes.io/version:' "$f" 2>/dev/null; then
    echo "  MISSING version label: $f"
    ((ERRORS++)) || true
  fi
done
if [[ $ERRORS -eq 0 ]]; then
  echo "  All pipeline and task YAMLs have version label"
fi

echo ""
echo "=== 3. generate-run.sh accepts test stack (dry-run) ==="
OUT=$(./scripts/generate-run.sh --mode pr --stack test-stack-flask-forwarder.yaml --app analytics-api --pr 99 \
  --registry localhost:5000 --no-build-images --storage-class "" 2>&1) || true
if echo "$OUT" | grep -q 'namespace:'; then
  echo "  OK: generate-run emits namespace"
else
  echo "  FAIL: generate-run output missing namespace"
  ((ERRORS++)) || true
fi
if echo "$OUT" | grep -q 'stack-pr-test'; then
  echo "  OK: generate-run emits pipelineRef stack-pr-test"
else
  echo "  FAIL: generate-run output missing pipelineRef"
  ((ERRORS++)) || true
fi
if echo "$OUT" | grep -q 'stacks/test-stack-flask-forwarder.yaml'; then
  echo "  OK: stack-file param uses test stack path"
else
  echo "  FAIL: stack-file param missing or wrong"
  ((ERRORS++)) || true
fi

echo ""
if [[ $ERRORS -gt 0 ]]; then
  echo "FAILED: $ERRORS check(s) failed"
  exit 1
fi
echo "All M4 stack and version-label checks passed."
