#!/usr/bin/env bash
# Configure GitHub webhooks on all app repos so that merging a PR triggers the
# merge pipeline (EventListener pr-merged trigger). Creates or updates the webhook
# in each repo and optionally creates/updates the Kubernetes secret used by the
# EventListener to validate payloads.
#
# Prerequisites:
#   - GITHUB_TOKEN with admin:repo_hook (or repo) scope, or `gh` CLI logged in
#   - EventListener must be reachable at the URL you pass (e.g. port-forward or LoadBalancer)
#
# Usage:
#   ./scripts/configure-github-webhooks.sh --url https://el.example.com
#   ./scripts/configure-github-webhooks.sh --url http://localhost:8080 --stack stack-one.yaml --webhook-secret my-val
#
# Options:
#   --url              EventListener payload URL (required); GitHub will POST pull_request events here
#   --webhook-secret   Webhook shared key (optional); if omitted, a random value is generated for K8s secret
#   --stack     Stack file(s), comma-separated (default: stack-one.yaml); app repos are read from .apps[].repo
#   --namespace Kubernetes namespace for github-webhook-secret (default: tekton-pipelines)
#   --dry-run   Print what would be done without creating webhooks or K8s secret
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEKTON_DAG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STACKS_DIR="$TEKTON_DAG_ROOT/stacks"

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: $1 is required" >&2; exit 1; }; }
need yq

WEBHOOK_URL=""
WEBHOOK_SECRET=""
STACKS="stack-one.yaml"
NAMESPACE="${NAMESPACE:-tekton-pipelines}"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)        WEBHOOK_URL="$2"; shift 2 ;;
    --webhook-secret) WEBHOOK_SECRET="$2"; shift 2 ;;
    --stack)      STACKS="$2"; shift 2 ;;
    --namespace)  NAMESPACE="$2"; shift 2 ;;
    --dry-run)    DRY_RUN=true; shift ;;
    *)            echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Allow env override: EVENT_LISTENER_URL used if --url not passed
WEBHOOK_URL="${WEBHOOK_URL:-${EVENT_LISTENER_URL:-}}"
[[ -n "$WEBHOOK_URL" ]] || { echo "ERROR: --url is required (or set EVENT_LISTENER_URL). EventListener payload URL, e.g. https://el.example.com or http://localhost:8080" >&2; exit 1; }

# Ensure URL has no trailing slash for consistency
WEBHOOK_URL="${WEBHOOK_URL%/}"

if [[ -z "$WEBHOOK_SECRET" ]]; then
  WEBHOOK_SECRET=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | xxd -p -c 64)
  echo "Generated webhook key (use --webhook-secret to reuse): ${WEBHOOK_SECRET:0:8}..."
fi

# Collect unique repo slugs (owner/repo) from stack(s)
REPOS=()
for STACK in ${STACKS//,/ }; do
  [[ -f "$STACKS_DIR/$STACK" ]] || { echo "ERROR: Stack not found: $STACKS_DIR/$STACK" >&2; exit 1; }
  while IFS= read -r repo; do
    [[ -z "$repo" || "$repo" == "null" ]] && continue
    # dedupe
    if [[ " ${REPOS[*]} " != *" $repo "* ]]; then
      REPOS+=( "$repo" )
    fi
  done < <(yq -r '.apps[].repo' "$STACKS_DIR/$STACK" 2>/dev/null || true)
done

[[ ${#REPOS[@]} -gt 0 ]] || { echo "ERROR: No app repos found in stack(s): $STACKS" >&2; exit 1; }

echo "Webhook URL: $WEBHOOK_URL"
echo "Repos: ${REPOS[*]}"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "DRY RUN: no webhooks or secret will be created."
fi

# GitHub API: create or update webhook
# See https://docs.github.com/en/rest/repos/webhooks#create-a-repository-webhook
create_or_update_hook() {
  local repo_slug="$1"
  local owner="${repo_slug%%/*}"
  local repo="${repo_slug#*/}"
  local existing_id
  existing_id=$(curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$repo_slug/hooks" | jq -r --arg u "$WEBHOOK_URL" '.[] | select(.config.url == $u) | .id // empty')
  if [[ -n "$existing_id" ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "  [dry-run] Would update existing webhook id=$existing_id for $repo_slug"
      return 0
    fi
    curl -sS -X PATCH -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/repos/$repo_slug/hooks/$existing_id" \
      -d "{\"config\":{\"url\":\"$WEBHOOK_URL\",\"content_type\":\"json\",\"secret\":\"$WEBHOOK_SECRET\"},\"events\":[\"pull_request\"],\"active\":true}" >/dev/null || true
    echo "  Updated webhook for $repo_slug"
  else
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "  [dry-run] Would create webhook for $repo_slug"
      return 0
    fi
    local resp
    resp=$(curl -sS -w "\n%{http_code}" -X POST -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/repos/$repo_slug/hooks" \
      -d "{\"name\":\"web\",\"config\":{\"url\":\"$WEBHOOK_URL\",\"content_type\":\"json\",\"secret\":\"$WEBHOOK_SECRET\"},\"events\":[\"pull_request\"],\"active\":true}")
    local code="${resp##*$'\n'}"
    local body="${resp%$'\n'*}"
    if [[ "$code" -ge 200 && "$code" -lt 300 ]]; then
      echo "  Created webhook for $repo_slug"
    else
      echo "  Failed to create webhook for $repo_slug: HTTP $code" >&2
      echo "$body" | jq -r '.message // .' >&2
      return 1
    fi
  fi
}

# Resolve GITHUB_TOKEN (script accepts GH_TOKEN or GITHUB_TOKEN; source .env for GH_TOKEN)
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  GITHUB_TOKEN="${GH_TOKEN:-}"
fi
if [[ -z "${GITHUB_TOKEN:-}" ]] && command -v gh >/dev/null 2>&1; then
  GITHUB_TOKEN=$(gh auth token 2>/dev/null || true)
fi
[[ -n "${GITHUB_TOKEN:-}" ]] || { echo "ERROR: GITHUB_TOKEN or GH_TOKEN (e.g. in .env) or \`gh auth login\` required" >&2; exit 1; }

FAILED=0
for repo_slug in "${REPOS[@]}"; do
  create_or_update_hook "$repo_slug" || FAILED=$((FAILED + 1))
done

if [[ $FAILED -gt 0 ]]; then
  echo "WARNING: $FAILED repo(s) failed webhook setup."
fi

# Create or replace Kubernetes secret so the EventListener can validate webhook payloads
if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] Would create/replace secret github-webhook-secret in namespace $NAMESPACE"
else
  if kubectl get namespace "$NAMESPACE" &>/dev/null; then
    kubectl create secret generic github-webhook-secret --from-literal=secret="$WEBHOOK_SECRET" -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    echo "Applied secret github-webhook-secret in namespace $NAMESPACE"
  else
    echo "WARNING: Namespace $NAMESPACE not found; skip creating secret. Create it after installing Tekton Triggers:"
    echo "  kubectl create secret generic github-webhook-secret --from-literal=secret='<same-secret>' -n $NAMESPACE"
  fi
fi

echo ""
echo "Done. When a PR is merged in any of these repos, GitHub will POST to $WEBHOOK_URL and the pr-merged trigger will run the merge pipeline."
echo "Ensure the EventListener is reachable at that URL (e.g. kubectl port-forward svc/el-stack-event-listener 8080:8080 -n $NAMESPACE for local testing)."
