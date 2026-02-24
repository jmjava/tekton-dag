#!/usr/bin/env bash
set -euo pipefail

# stack-graph.sh — Parse a stack YAML and emit structured JSON that
# downstream generators and Tekton tasks can consume.
#
# Requires: yq (https://github.com/mikefarah/yq)
#
# Usage:
#   ./stack-graph.sh <stack-file>                  # full graph JSON
#   ./stack-graph.sh <stack-file> --topo            # topological order
#   ./stack-graph.sh <stack-file> --entry           # entry-point app (frontend / root)
#   ./stack-graph.sh <stack-file> --chain <app>     # propagation chain starting at <app>
#   ./stack-graph.sh <stack-file> --validate        # validate graph (no cycles, all refs resolve)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die()  { echo "ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "$1 is required but not installed"; }

need yq
need jq

STACK_FILE="${1:?Usage: stack-graph.sh <stack-file> [--topo|--entry|--chain <app>|--validate]}"
shift || true
MODE="${1:-full}"
shift || true
ARG="${1:-}"

[[ -f "$STACK_FILE" ]] || die "Stack file not found: $STACK_FILE"

STACK_JSON=$(yq -o=json "$STACK_FILE")

graph_json() {
  echo "$STACK_JSON" | jq '{
    name:        .name,
    description: .description,
    propagation: .propagation,
    defaults:    .defaults,
    apps:        [.apps[] | {
      name:               .name,
      repo:               .repo,
      role:               .role,
      "propagation-role": (."propagation-role" // (if .downstream == [] or .downstream == null then "terminal" elif (.role == "frontend") then "originator" else "forwarder" end)),
      namespace:          (.namespace // null),
      "container-port":   (."container-port" // null),
      "service-port":     (."service-port" // null),
      "context-dir":      (."context-dir" // "."),
      dockerfile:         (.dockerfile // "Dockerfile"),
      build:              (.build // {tool:"none", runtime:"custom"}),
      downstream:         (.downstream // []),
      tests:              (.tests // {})
    }]
  }'
}

validate() {
  local json
  json=$(graph_json)
  local names
  names=$(echo "$json" | jq -r '.apps[].name')

  local errors=0

  # Check all downstream references resolve
  for app in $(echo "$json" | jq -r '.apps[].name'); do
    for dep in $(echo "$json" | jq -r --arg a "$app" '.apps[] | select(.name==$a) | .downstream[]'); do
      if ! echo "$names" | grep -qx "$dep"; then
        echo "INVALID: $app references unknown downstream '$dep'" >&2
        errors=$((errors + 1))
      fi
    done
  done

  # Cycle detection via topological sort attempt
  local sorted
  sorted=$(topo_sort 2>&1) || {
    echo "INVALID: graph contains a cycle" >&2
    errors=$((errors + 1))
  }

  if [[ $errors -eq 0 ]]; then
    echo "VALID"
    return 0
  else
    return 1
  fi
}

topo_sort() {
  local json
  json=$(graph_json)

  echo "$json" | jq -r '
    def topo_visit($node; $adj):
      if (.temp | index($node)) then .error = true
      elif (.visited | index($node)) then .
      else
        .temp += [$node] |
        reduce ($adj[$node] // [])[] as $dep (.; topo_visit($dep; $adj)) |
        .temp -= [$node] |
        .visited += [$node] |
        .order += [$node]
      end;

    def topo_sort:
      . as $graph |
      ($graph.apps | map({key: .name, value: .downstream}) | from_entries) as $adj |
      ($graph.apps | map(.name)) as $all |
      {visited: [], temp: [], order: [], error: false} |
      reduce $all[] as $node (.;
        if (.visited | index($node)) then .
        else . as $state | $state | topo_visit($node; $adj)
        end
      ) |
      if .error then error("cycle detected")
      else .order | reverse
      end;

    topo_sort | .[]
  '
}

# Walk the propagation chain from a given starting app
chain() {
  local start="${1:?chain requires an app name}"
  local json
  json=$(graph_json)

  echo "$json" | jq -r --arg s "$start" '
    def walk($name):
      . as $graph |
      ($graph.apps[] | select(.name == $name)) as $app |
      if $app then
        [$name] + (reduce ($app.downstream // [])[] as $d ([]; . + ($graph | walk($d))))
      else []
      end;
    walk($s) | .[]
  '
}

entry_point() {
  local json
  json=$(graph_json)

  # Entry point = app that is not a downstream of any other app
  echo "$json" | jq -r '
    (.apps | map(.downstream) | flatten) as $all_deps |
    .apps[] | select(.name as $n | ($all_deps | index($n)) | not) | .name
  '
}

case "$MODE" in
  full|--full)
    graph_json
    ;;
  --topo)
    topo_sort
    ;;
  --entry)
    entry_point
    ;;
  --chain)
    [[ -n "$ARG" ]] || die "--chain requires an app name"
    chain "$ARG"
    ;;
  --validate)
    validate
    ;;
  *)
    die "Unknown mode: $MODE  (use --full, --topo, --entry, --chain <app>, --validate)"
    ;;
esac
