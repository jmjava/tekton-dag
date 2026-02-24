#!/usr/bin/env bash
# Run Artillery E2E for every intercept variant (each app as changed-app).
# Generates a config per variant with entry URL and x-dev-session:pr-N header, then runs artillery.
#
# Prerequisites: artillery (npm install -g artillery), yq, jq.
# Optional: ENTRY_URL already set (e.g. from port-forward). Otherwise script builds in-cluster URL from stack.
#
# Usage:
#   ./scripts/run-artillery-variants.sh [--stack stack-one.yaml] [--pr 1] [--entry-url URL] [--dry-run]
#   ENTRY_URL=http://localhost:3000 ./scripts/run-artillery-variants.sh --stack stacks/stack-one.yaml
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STACKS_DIR="$REPO_ROOT/stacks"
TESTS_DIR="$REPO_ROOT/tests/artillery"
STACK_FILE="$STACKS_DIR/stack-one.yaml"
PR_NUMBER="1"
ENTRY_URL=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stack)     STACK_FILE="$2"; shift 2 ;;
    --pr)        PR_NUMBER="$2"; shift 2 ;;
    --entry-url) ENTRY_URL="$2"; shift 2 ;;
    --dry-run)   DRY_RUN=true; shift ;;
    *)           echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

[[ -f "$STACK_FILE" ]] || { echo "Stack file not found: $STACK_FILE" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need yq
need jq
if [[ "$DRY_RUN" != true ]]; then
  need artillery
fi

STACK_JSON=$(yq -o=json "$STACK_FILE")
ENTRY_APP=$(echo "$STACK_JSON" | jq -r '
  (.apps | map(.downstream) | flatten) as $deps |
  .apps[] | select(.name as $n | ($deps | index($n)) | not) | .name')
DEFAULT_NS=$(echo "$STACK_JSON" | jq -r '.defaults.namespace // "staging"')
ENTRY_NS=$(echo "$STACK_JSON" | jq -r --arg a "$ENTRY_APP" \
  '(.defaults.namespace // "staging") as $dn | .apps[]|select(.name==$a)|.namespace // $dn')
ENTRY_SPORT=$(echo "$STACK_JSON" | jq -r --arg a "$ENTRY_APP" \
  '(.defaults."service-port" // "80") as $def | .apps[]|select(.name==$a)|(."service-port" // $def)')
HEADER_NAME=$(echo "$STACK_JSON" | jq -r '.propagation."header-name" // "x-dev-session"')
BAGGAGE_KEY=$(echo "$STACK_JSON" | jq -r '.propagation."baggage-key" // "dev-session"')

if [[ -z "$ENTRY_URL" ]]; then
  ENTRY_URL="http://${ENTRY_APP}.${ENTRY_NS}.svc.cluster.local:${ENTRY_SPORT}"
fi

INTERCEPT_VAL="pr-${PR_NUMBER}"
BAGGAGE_VAL="${BAGGAGE_KEY}=${INTERCEPT_VAL}"

# All apps in topo order (each is one intercept variant)
TOPO_APPS=()
while IFS= read -r a; do [[ -n "$a" ]] && TOPO_APPS+=("$a"); done < <(echo "$STACK_JSON" | jq -r '.apps[].name')

echo "=============================================="
echo "  Artillery E2E — all intercept variants"
echo "  Stack: $STACK_FILE"
echo "  Entry: $ENTRY_APP @ $ENTRY_URL"
echo "  Header: ${HEADER_NAME}=${INTERCEPT_VAL}"
echo "  Variants: ${TOPO_APPS[*]}"
echo "=============================================="

OUT_DIR="$REPO_ROOT/tests/artillery/output"
mkdir -p "$OUT_DIR"
PASS=0
FAIL=0

for CHANGED_APP in "${TOPO_APPS[@]}"; do
  echo ""
  echo "--- Variant: changed-app=$CHANGED_APP ---"
  CONFIG="$OUT_DIR/artillery-variant-${CHANGED_APP}.yml"
  cat > "$CONFIG" <<EOF
config:
  target: "$ENTRY_URL"
  phases:
    - duration: 15
      arrivalRate: 2
  defaults:
    headers:
      $HEADER_NAME: "$INTERCEPT_VAL"
      baggage: "$BAGGAGE_VAL"
scenarios:
  - name: "Entry E2E (intercepted app: $CHANGED_APP)"
    flow:
      - get:
          url: "/"
EOF
  if [[ "$DRY_RUN" == true ]]; then
    echo "  [dry-run] would run: artillery run $CONFIG"
    echo "  Config: $CONFIG"
    cat "$CONFIG"
    ((PASS++)) || true
    continue
  fi
  if artillery run "$CONFIG" --output "$OUT_DIR/report-${CHANGED_APP}.json" 2>&1; then
    echo "  PASS: $CHANGED_APP"
    ((PASS++)) || true
  else
    echo "  FAIL: $CHANGED_APP"
    ((FAIL++)) || true
  fi
done

echo ""
echo "=============================================="
echo "  Summary: $PASS passed, $FAIL failed (${#TOPO_APPS[@]} variants)"
echo "  Reports: $OUT_DIR/report-*.json"
echo "=============================================="
[[ $FAIL -eq 0 ]]
