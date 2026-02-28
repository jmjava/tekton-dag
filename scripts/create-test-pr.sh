#!/usr/bin/env bash
# Create a real GitHub PR in the **app repo** (the app being tested with the intercept).
# This is the correct flow for validating the PR pipeline: PR lives in the app repo
# (e.g. jmjava/tekton-dag-vue-fe for demo-fe), not in the platform repo (tekton-dag).
#
# From the app repo: create a new branch, make a small change, push, open PR.
# Output: PR_NUMBER, BRANCH_NAME, APP so you can run the PR pipeline with
# --app-revision <app>:<BRANCH_NAME>.
#
# Prerequisites:
#   - App repo cloned under APP_REPOS_ROOT (default $HOME/github), e.g. $HOME/github/jmjava/tekton-dag-vue-fe
#   - git remote in app repo points at GitHub; push access
#   - GITHUB_TOKEN in env or `gh` CLI logged in to open the PR
#
# Usage:
#   ./scripts/create-test-pr.sh --app demo-fe [--stack stack-one.yaml] [--app-repo-root /path/to/github]
#   --branch NAME   Branch name (default: test-pr-<timestamp>)
#   --title "..."   PR title (default: "Test PR for pipeline")
#
# Example:
#   ./scripts/create-test-pr.sh --app demo-fe
#   # outputs: APP=demo-fe PR_NUMBER=3 BRANCH_NAME=test-pr-20260226120000
#   ./scripts/generate-run.sh --mode pr --stack stack-one.yaml --app demo-fe --pr 3 \
#     --app-revision demo-fe:test-pr-20260226120000 --apply
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEKTON_DAG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STACKS_DIR="$TEKTON_DAG_ROOT/stacks"

need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: $1 is required" >&2; exit 1; }; }
need yq

APP=""
STACK="stack-one.yaml"
APP_REPOS_ROOT="${APP_REPOS_ROOT:-$HOME/github}"
BRANCH_NAME=""
TITLE="Test PR for pipeline"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)            APP="$2"; shift 2 ;;
    --stack)          STACK="$2"; shift 2 ;;
    --app-repo-root)  APP_REPOS_ROOT="$2"; shift 2 ;;
    --branch)         BRANCH_NAME="$2"; shift 2 ;;
    --title)          TITLE="$2"; shift 2 ;;
    *)                echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$APP" ]] || { echo "ERROR: --app is required (e.g. demo-fe). The PR will be created in that app's repo." >&2; exit 1; }
[[ -f "$STACKS_DIR/$STACK" ]] || { echo "ERROR: Stack file not found: $STACKS_DIR/$STACK" >&2; exit 1; }

# Resolve app repo from stack (e.g. jmjava/tekton-dag-vue-fe)
REPO_SLUG=$(yq -r ".apps[] | select(.name == \"$APP\") | .repo" "$STACKS_DIR/$STACK")
[[ -n "$REPO_SLUG" && "$REPO_SLUG" != "null" ]] || { echo "ERROR: App '$APP' not found in stack $STACK" >&2; exit 1; }

# App repo path: e.g. $HOME/github/jmjava/tekton-dag-vue-fe
APP_REPO_DIR="$APP_REPOS_ROOT/$REPO_SLUG"
[[ -d "$APP_REPO_DIR" ]] || { echo "ERROR: App repo not found at $APP_REPO_DIR. Clone it (e.g. git clone git@github.com:${REPO_SLUG}.git $APP_REPO_DIR) or set APP_REPOS_ROOT." >&2; exit 1; }
[[ -d "$APP_REPO_DIR/.git" ]] || { echo "ERROR: Not a git repo: $APP_REPO_DIR" >&2; exit 1; }

cd "$APP_REPO_DIR"

if [[ -z "$BRANCH_NAME" ]]; then
  BRANCH_NAME="test-pr-$(date +%Y%m%d%H%M%S)"
fi

git fetch origin 2>/dev/null || true
DEFAULT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")

# Create branch from origin/main (or main) and make a trivial change
git checkout -B "$BRANCH_NAME" origin/main 2>/dev/null || git checkout -B "$BRANCH_NAME" main 2>/dev/null || git checkout -b "$BRANCH_NAME"

TRIGGER_FILE=".test-pr-branch"
echo "Test PR branch: $BRANCH_NAME at $(date -Iseconds)" >> "$TRIGGER_FILE"
git add "$TRIGGER_FILE"
if ! git commit -m "chore: test PR for pipeline (branch $BRANCH_NAME)"; then
  git commit --allow-empty -m "chore: test PR branch $BRANCH_NAME"
fi

# Push branch (SSH preferred)
ORIGIN_URL=$(git remote get-url origin 2>/dev/null)
if [[ "$ORIGIN_URL" != *"github.com"* ]]; then
  echo "ERROR: Remote origin does not look like GitHub: $ORIGIN_URL" >&2
  exit 1
fi
git push -u origin "$BRANCH_NAME" || { echo "Push failed. Fix remote (SSH?) and retry." >&2; exit 1; }

# Open PR via gh or GitHub API (in the app repo)
PR_NUMBER=""
if command -v gh >/dev/null 2>&1; then
  PR_NUMBER=$(gh pr create --base main --head "$BRANCH_NAME" --title "$TITLE" --body "Automated test PR for Tekton PR pipeline (app: $APP). Branch: $BRANCH_NAME" --json number -q .number 2>/dev/null || true)
fi
if [[ -z "$PR_NUMBER" && -n "${GITHUB_TOKEN:-}" ]]; then
  RESP=$(curl -sS -X POST \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO_SLUG/pulls" \
    -d "{\"title\":\"$TITLE\",\"head\":\"$BRANCH_NAME\",\"base\":\"main\",\"body\":\"Test PR for pipeline (app: $APP). Branch: $BRANCH_NAME\"}")
  PR_NUMBER=$(echo "$RESP" | sed -n 's/.*"number": *\([0-9]*\).*/\1/p')
  [[ -z "$PR_NUMBER" ]] && echo "API response: $RESP" >&2
fi

if [[ -z "$PR_NUMBER" ]]; then
  echo "Could not create PR. Push succeeded; create the PR manually on GitHub for repo $REPO_SLUG branch: $BRANCH_NAME" >&2
  echo "APP=$APP"
  echo "BRANCH_NAME=$BRANCH_NAME"
  echo "PR_NUMBER="
  exit 0
fi

echo "APP=$APP"
echo "PR_NUMBER=$PR_NUMBER"
echo "BRANCH_NAME=$BRANCH_NAME"
echo ""
echo "Next: run the PR pipeline with this app, PR number, and app branch (platform stays at main or your choice):"
echo "  ./scripts/generate-run.sh --mode pr --stack $STACK --app $APP --pr $PR_NUMBER --app-revision $APP:$BRANCH_NAME --apply"
echo ""
echo "After pipeline succeeds, merge the app PR and run the merge pipeline:"
echo "  ./scripts/merge-pr.sh $PR_NUMBER --repo $REPO_SLUG"
echo "  ./scripts/generate-run.sh --mode merge --stack $STACK --app $APP --apply"
