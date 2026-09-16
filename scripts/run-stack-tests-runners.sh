#!/bin/sh
# Newman / Playwright / Artillery runner used by tasks/run-stack-tests.
# Source from the Task after Tekton params are exported, or execute locally
# with the same environment variables.
# shellcheck shell=sh
set -eu

STACK_JSON="${STACK_JSON:-}"
APP_LIST="${APP_LIST:-}"
ENTRY_APP="${ENTRY_APP:-}"
CHAIN="${CHAIN:-}"
BUILD_APPS="${BUILD_APPS:-}"
INTERCEPT="${INTERCEPT:-}"
DEFAULT_NS="${DEFAULT_NS:-staging}"
TESTS_TO_RUN="${TESTS_TO_RUN:-}"
UNMAPPED_AREA="${UNMAPPED_AREA:-}"
APPS_TO_TEST="${APPS_TO_TEST:-}"
TEST_SOURCE="${TEST_SOURCE:-.}"
TEST_SUMMARY_PATH="${TEST_SUMMARY_PATH:-/tmp/run-stack-tests-summary.json}"

cd "$TEST_SOURCE"

echo '{}' > /tmp/test-summary.json
OVERALL_PASS=true

if [ -n "$UNMAPPED_AREA" ] && [ -z "$TESTS_TO_RUN" ]; then
  echo ""
  echo "####################################################"
  echo "  NO MAPPED REGRESSION for area: $UNMAPPED_AREA"
  echo "  This area needs regression tests to be built."
  echo "####################################################"
  echo ""
  jq --arg area "$UNMAPPED_AREA" \
    '. + {"unmapped-area": $area, "message": "No mapped regression; area needs tests"}' \
    /tmp/test-summary.json > /tmp/test-summary-tmp.json
  mv /tmp/test-summary-tmp.json /tmp/test-summary.json
  tee "$TEST_SUMMARY_PATH" < /tmp/test-summary.json
  exit 0
fi

if ! printf '%s' "$STACK_JSON" | jq -e 'type == "object"' >/dev/null 2>&1; then
  echo "ERROR: stack-json is not valid JSON" >&2
  exit 1
fi

HEADER_NAME=""
HEADER_VAL=""
BAGGAGE_KEY=$(printf '%s' "$STACK_JSON" | jq -r '.propagation."baggage-key" // "dev-session"')
if [ -n "$INTERCEPT" ]; then
  HEADER_NAME=$(printf '%s' "$INTERCEPT" | cut -d: -f1)
  HEADER_VAL=$(printf '%s' "$INTERCEPT" | cut -d: -f2-)
fi

FILTERED=false
HAS_E2E=false
if [ -n "$TESTS_TO_RUN" ]; then
  FILTERED=true
  echo ""
  echo "####################################################"
  echo "  FILTERED TEST RUN (from test-plan graph)"
  echo "  Tests: $TESTS_TO_RUN"
  echo "  Apps:  $APPS_TO_TEST"
  echo "####################################################"
  echo ""
  if printf '%s' "$TESTS_TO_RUN" | grep -q "e2e/"; then
    HAS_E2E=true
  fi
fi

app_in_test_plan() {
  [ "$FILTERED" = "false" ] && return 0
  [ -z "$APPS_TO_TEST" ] && return 0
  printf '%s' ",$APPS_TO_TEST," | grep -q ",$1,"
}

run_newman() {
  collection="$1"
  base_url="$2"
  label="$3"
  echo "  [$label] Running: $collection"
  if [ -n "$HEADER_NAME" ]; then
    newman run "$collection" --env-var "baseUrl=$base_url" --reporters cli,json \
      --global-var "${HEADER_NAME}=${HEADER_VAL}"
  else
    newman run "$collection" --env-var "baseUrl=$base_url" --reporters cli,json
  fi
}

run_playwright() {
  suite_dir="$1"
  base_url="$2"
  label="$3"
  echo "  [$label] Running: $suite_dir"
  package_dir=$(dirname "$suite_dir")
  if [ ! -f "${package_dir}/package.json" ]; then
    echo "  [$label] No package.json found (skipping)"
    return 0
  fi
  cd "$package_dir"
  npm install --legacy-peer-deps 2>/dev/null || true
  BASE_URL="$base_url"
  export BASE_URL
  if [ -n "$HEADER_NAME" ]; then
    INTERCEPT_HEADER_NAME="$HEADER_NAME"
    INTERCEPT_HEADER_VALUE="$HEADER_VAL"
    export INTERCEPT_HEADER_NAME
    export INTERCEPT_HEADER_VALUE
  fi
  rel_path=$(printf '%s' "$suite_dir" | sed "s|^${package_dir}/||")
  status=0
  npx playwright test "$rel_path" --reporter=list 2>/dev/null || status=$?
  cd "$TEST_SOURCE"
  return "$status"
}

run_artillery() {
  script_path="$1"
  base_url="$2"
  label="$3"
  echo "  [$label] Running: $script_path"
  if [ -n "$HEADER_NAME" ]; then
    cat > /tmp/artillery-override.yml <<ARTYEOF
config:
  target: $base_url
  phases:
    - duration: 30
      arrivalRate: 5
  defaults:
    headers:
      ${HEADER_NAME}: ${HEADER_VAL}
scenarios:
  - flow:
      - get:
          url: "/"
ARTYEOF
    artillery run /tmp/artillery-override.yml
  else
    artillery run "$script_path" --target "$base_url"
  fi
}

# ===========================================================
# Phase 1: E2E through entry point
# ===========================================================
if [ "$FILTERED" = "true" ] && [ "$HAS_E2E" = "false" ]; then
  echo ""
  echo "####################################################"
  echo "  PHASE 1: SKIPPED (no e2e tests in test plan)"
  echo "####################################################"
  jq '. + {"e2e-entry-point": "skipped (no e2e in plan)"}' \
    /tmp/test-summary.json > /tmp/test-summary-tmp.json
  mv /tmp/test-summary-tmp.json /tmp/test-summary.json
else
  echo ""
  echo "####################################################"
  echo "  PHASE 1: E2E test through entry point ($ENTRY_APP)"
  echo "####################################################"
  echo ""
  echo "  Chain:           $CHAIN"
  echo "  Intercepted:     $BUILD_APPS"
  echo "  Header:          $HEADER_NAME=$HEADER_VAL"
  echo ""

  ENTRY_NS=$(printf '%s' "$STACK_JSON" | jq -r --arg a "$ENTRY_APP" --arg d "$DEFAULT_NS" \
    '(.defaults.namespace // $d) as $dn | .apps[]|select(.name==$a)|.namespace // $dn')
  ENTRY_SPORT=$(printf '%s' "$STACK_JSON" | jq -r --arg a "$ENTRY_APP" \
    '(.defaults."service-port" // "80") as $dp | .apps[]|select(.name==$a)|."service-port" // $dp')
  ENTRY_URL="http://${ENTRY_APP}.${ENTRY_NS}.svc.cluster.local:${ENTRY_SPORT}"

  echo "  Entry URL: $ENTRY_URL"
  echo ""

  E2E_PASS=true
  E2E_RESULT=$(curl -s \
    -H "${HEADER_NAME}: ${HEADER_VAL}" \
    -H "baggage: ${BAGGAGE_KEY}=${HEADER_VAL}" \
    --connect-timeout 15 --max-time 60 \
    "$ENTRY_URL" 2>/dev/null || echo '{"error":"unreachable"}')

  echo "  Response:"
  printf '%s\n' "$E2E_RESULT" | jq '.' 2>/dev/null || echo "  $E2E_RESULT"
  echo ""

  HOP=0
  for APP in $CHAIN; do
    HOP=$((HOP + 1))
    IS_INTERCEPTED=false
    for BA in $BUILD_APPS; do
      [ "$BA" = "$APP" ] && IS_INTERCEPTED=true
    done

    MARKER=""
    if [ "$IS_INTERCEPTED" = "true" ]; then
      MARKER=" [INTERCEPTED → PR build]"
    fi

    if printf '%s' "$E2E_RESULT" | grep -qi "$APP"; then
      echo "  HOP $HOP ($APP)${MARKER}: REACHED"
    else
      echo "  HOP $HOP ($APP)${MARKER}: NOT CONFIRMED"
    fi
  done

  if [ -n "$HEADER_VAL" ] && printf '%s' "$E2E_RESULT" | grep -qi "$HEADER_VAL"; then
    echo ""
    echo "  Header value '$HEADER_VAL' found in response"
  fi

  echo ""
  if [ "$E2E_PASS" = "true" ]; then
    echo "  E2E: PASS"
  else
    echo "  E2E: FAIL"
    OVERALL_PASS=false
  fi

  jq --arg s "$([ "$E2E_PASS" = "true" ] && echo pass || echo fail)" \
    '. + {"e2e-entry-point": $s}' \
    /tmp/test-summary.json > /tmp/test-summary-tmp.json
  mv /tmp/test-summary-tmp.json /tmp/test-summary.json

  ENTRY_POSTMAN=$(printf '%s' "$STACK_JSON" | jq -r --arg a "$ENTRY_APP" \
    '.apps[]|select(.name==$a)|.tests.postman // ""')
  ENTRY_PLAYWRIGHT=$(printf '%s' "$STACK_JSON" | jq -r --arg a "$ENTRY_APP" \
    '.apps[]|select(.name==$a)|.tests.playwright // ""')

  if [ -n "$ENTRY_POSTMAN" ] && [ -f "$ENTRY_POSTMAN" ]; then
    echo ""
    if run_newman "$ENTRY_POSTMAN" "$ENTRY_URL" "e2e/postman"; then
      echo "  [e2e/postman] PASS"
    else
      echo "  [e2e/postman] FAIL"
      OVERALL_PASS=false
    fi
  fi

  if [ -n "$ENTRY_PLAYWRIGHT" ] && [ -d "$ENTRY_PLAYWRIGHT" ]; then
    echo ""
    if run_playwright "$ENTRY_PLAYWRIGHT" "$ENTRY_URL" "e2e/playwright"; then
      echo "  [e2e/playwright] PASS"
    else
      echo "  [e2e/playwright] FAIL"
      OVERALL_PASS=false
    fi
  fi
fi

# ===========================================================
# Phase 2: Per-app tests
# ===========================================================
echo ""
echo "####################################################"
echo "  PHASE 2: Per-app tests"
echo "####################################################"

for APP in $APP_LIST; do
  if [ "$APP" = "$ENTRY_APP" ]; then
    echo ""
    echo "  Skipping $APP (already tested in e2e phase)"
    continue
  fi

  if ! app_in_test_plan "$APP"; then
    echo ""
    echo "  Skipping $APP (not in test plan)"
    jq --arg a "$APP" '. + {($a): "skipped (not in plan)"}' \
      /tmp/test-summary.json > /tmp/test-summary-tmp.json
    mv /tmp/test-summary-tmp.json /tmp/test-summary.json
    continue
  fi

  echo ""
  echo "========================================="
  echo "  Testing: $APP"

  IS_INTERCEPTED=false
  for BA in $BUILD_APPS; do
    [ "$BA" = "$APP" ] && IS_INTERCEPTED=true
  done
  if [ "$IS_INTERCEPTED" = "true" ]; then
    echo "  (INTERCEPTED — hitting PR build via Telepresence)"
  else
    echo "  (normal cluster deployment)"
  fi

  echo "========================================="

  NS=$(printf '%s' "$STACK_JSON" | jq -r --arg a "$APP" --arg d "$DEFAULT_NS" \
    '(.defaults.namespace // $d) as $dn | .apps[]|select(.name==$a)|.namespace // $dn')
  SPORT=$(printf '%s' "$STACK_JSON" | jq -r --arg a "$APP" \
    '(.defaults."service-port" // "80") as $dp | .apps[]|select(.name==$a)|."service-port" // $dp')
  SERVICE_URL="http://${APP}.${NS}.svc.cluster.local:${SPORT}"

  POSTMAN=$(printf '%s' "$STACK_JSON" | jq -r --arg a "$APP" \
    '.apps[]|select(.name==$a)|.tests.postman // ""')
  PLAYWRIGHT=$(printf '%s' "$STACK_JSON" | jq -r --arg a "$APP" \
    '.apps[]|select(.name==$a)|.tests.playwright // ""')
  ARTILLERY=$(printf '%s' "$STACK_JSON" | jq -r --arg a "$APP" \
    '.apps[]|select(.name==$a)|.tests.artillery // ""')

  APP_PASS=true

  if [ -n "$POSTMAN" ] && [ -f "$POSTMAN" ]; then
    if run_newman "$POSTMAN" "$SERVICE_URL" "postman"; then
      echo "  [postman] PASS"
    else
      echo "  [postman] FAIL"
      APP_PASS=false
    fi
  elif [ -n "$POSTMAN" ]; then
    echo "  [postman] Collection not found: $POSTMAN (skipping)"
  fi

  if [ -n "$PLAYWRIGHT" ] && [ -d "$PLAYWRIGHT" ]; then
    if run_playwright "$PLAYWRIGHT" "$SERVICE_URL" "playwright"; then
      echo "  [playwright] PASS"
    else
      echo "  [playwright] FAIL"
      APP_PASS=false
    fi
  elif [ -n "$PLAYWRIGHT" ]; then
    echo "  [playwright] Test dir not found: $PLAYWRIGHT (skipping)"
  fi

  if [ -n "$ARTILLERY" ] && [ -f "$ARTILLERY" ]; then
    if run_artillery "$ARTILLERY" "$SERVICE_URL" "artillery"; then
      echo "  [artillery] PASS"
    else
      echo "  [artillery] FAIL"
      APP_PASS=false
    fi
  elif [ -n "$ARTILLERY" ]; then
    echo "  [artillery] Script not found: $ARTILLERY (skipping)"
  fi

  STATUS="pass"
  if [ "$APP_PASS" = "false" ]; then
    STATUS="fail"
    OVERALL_PASS=false
  fi

  jq --arg a "$APP" --arg s "$STATUS" '. + {($a): $s}' \
    /tmp/test-summary.json > /tmp/test-summary-tmp.json
  mv /tmp/test-summary-tmp.json /tmp/test-summary.json
done

echo ""
echo "========================================="
echo "  Test Summary"
echo "========================================="
jq '.' /tmp/test-summary.json
tee "$TEST_SUMMARY_PATH" < /tmp/test-summary.json

if [ "$OVERALL_PASS" = "false" ]; then
  echo ""
  echo "FAILED: One or more test phases failed."
  exit 1
fi
