#!/usr/bin/env bash
# Merge a GitHub PR by number. Uses `gh pr merge` or GitHub API.
# After merging, you can run the merge pipeline (stack-merge-release) with --git-revision main.
#
# Prerequisites: GITHUB_TOKEN in env, or `gh` CLI logged in with merge permission.
#
# Usage: ./merge-pr.sh PR_NUMBER [--squash|--merge|--rebase] [--repo OWNER/REPO] [--app APP] [--stack STACK]
#   Default merge method is --merge. Use --repo to merge a PR in another repo (e.g. app repo).
#   Or use --app demo-fe (and optional --stack stack-one.yaml) to resolve repo from the stack; --repo wins if both given.
#   Without --repo/--app, uses the current git repo (e.g. run from app repo or from tekton-dag).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STACKS_DIR="$REPO_ROOT/stacks"
cd "$REPO_ROOT"

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: $1 is required" >&2; exit 1; }; }
need yq

[[ $# -ge 1 ]] || { echo "Usage: $0 PR_NUMBER [--squash|--merge|--rebase] [--repo OWNER/REPO] [--app APP] [--stack STACK]" >&2; exit 1; }
PR_NUMBER="$1"
shift
METHOD=""
REPO_OVERRIDE=""
APP=""
STACK="stack-one.yaml"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --squash) METHOD="squash"; shift ;;
    --merge)  METHOD="merge"; shift ;;
    --rebase) METHOD="rebase"; shift ;;
    --repo)   REPO_OVERRIDE="$2"; shift 2 ;;
    --app)    APP="$2"; shift 2 ;;
    --stack)  STACK="$2"; shift 2 ;;
    *)        echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done
[[ -z "$METHOD" ]] && METHOD="merge"

REPO_SLUG="$REPO_OVERRIDE"
if [[ -z "$REPO_SLUG" && -n "$APP" ]]; then
  [[ -f "$STACKS_DIR/$STACK" ]] || { echo "Stack file not found: $STACKS_DIR/$STACK" >&2; exit 1; }
  REPO_SLUG=$(yq -r ".apps[] | select(.name == \"$APP\") | .repo" "$STACKS_DIR/$STACK" 2>/dev/null || true)
  [[ -n "$REPO_SLUG" && "$REPO_SLUG" != "null" ]] || { echo "App '$APP' not found in stack $STACK" >&2; exit 1; }
fi
if [[ -z "$REPO_SLUG" ]]; then
  if command -v gh >/dev/null 2>&1; then
    REPO_SLUG=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
  fi
  if [[ -z "$REPO_SLUG" ]]; then
    REPO_SLUG=$(git remote get-url origin | sed -n 's|.*github\.com[:/]\([^.]*\)\.git|\1|p' | sed 's|/|/|')
    [[ -z "$REPO_SLUG" ]] && REPO_SLUG=$(git remote get-url origin | sed -n 's|.*github\.com[:/]\([^/]*\)/\([^/]*\)\.*|\1/\2|p')
  fi
fi
[[ -n "$REPO_SLUG" ]] || { echo "Could not determine repo. Use --repo OWNER/REPO." >&2; exit 1; }

if command -v gh >/dev/null 2>&1; then
  if [[ -n "$REPO_OVERRIDE" ]]; then
    gh pr merge "$PR_NUMBER" --repo "$REPO_SLUG" --"$METHOD" --delete-branch 2>/dev/null || gh pr merge "$PR_NUMBER" --repo "$REPO_SLUG" --"$METHOD"
  else
    gh pr merge "$PR_NUMBER" --"$METHOD" --delete-branch 2>/dev/null || gh pr merge "$PR_NUMBER" --"$METHOD"
  fi
  echo "Merged PR #$PR_NUMBER in $REPO_SLUG."
  echo "Run merge pipeline: ./scripts/generate-run.sh --mode merge --stack stack-one.yaml --app <app> --apply"
  exit 0
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "Need gh CLI or GITHUB_TOKEN to merge PR." >&2
  exit 1
fi

# GitHub API: merge pull request
RESP=$(curl -sS -X PUT \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO_SLUG/pulls/$PR_NUMBER/merge" \
  -d "{\"merge_method\":\"$METHOD\"}")
if echo "$RESP" | grep -q '"merged":true'; then
  echo "Merged PR #$PR_NUMBER in $REPO_SLUG."
  echo "Run merge pipeline: ./scripts/generate-run.sh --mode merge --stack stack-one.yaml --app <app> --apply"
else
  echo "Merge failed: $RESP" >&2
  exit 1
fi
