#!/usr/bin/env bash
# Create/push each sample app as its own GitHub repo under jmjava.
# The Tekton pipeline clones these repos via SSH (e.g. git@github.com:jmjava/tekton-dag-vue-fe.git).
#
# Prerequisites:
#   - gh CLI installed and authenticated (gh auth login)
#   - Push access to github.com/jmjava
#
# Usage: ./scripts/create-and-push-sample-repos.sh [--dry-run] [name1 name2 ...]
#   With no names, processes all tekton-dag-* directories under SAMPLE_REPOS_ROOT.
#   SAMPLE_REPOS_ROOT defaults to repo/sample-repos; set to e.g. ~/github/jmjava to use clones.
#   With names (e.g. tekton-dag-vue-fe), only those are created/pushed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SAMPLE_ROOT="${SAMPLE_REPOS_ROOT:-$REPO_ROOT/sample-repos}"
DRY_RUN=false
NAMES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    *)         NAMES+=("$1"); shift ;;
  esac
done

if [[ ${#NAMES[@]} -eq 0 ]]; then
  for d in "$SAMPLE_ROOT"/tekton-dag-*; do
    [[ -d "$d" ]] || continue
    NAMES+=("$(basename "$d")")
  done
fi

if [[ ${#NAMES[@]} -eq 0 ]]; then
  echo "No sample directories found under $SAMPLE_ROOT"
  echo "Clone the repos to ~/github/jmjava (see sample-repos/README.md) and push from each repo, or set SAMPLE_REPOS_ROOT."
  exit 0
fi

echo "Sample repos to create/push: ${NAMES[*]}"
echo ""

for name in "${NAMES[@]}"; do
  src="$SAMPLE_ROOT/$name"
  if [[ ! -d "$src" ]]; then
    echo "  Skip $name: not found at $src"
    continue
  fi
  repo_url="git@github.com:jmjava/$name.git"
  echo "--- $name -> jmjava/$name ---"
  if [[ "$DRY_RUN" == true ]]; then
    echo "  [dry-run] would create repo and push $src"
    continue
  fi
  tmp=""
  trap '[[ -n "$tmp" ]] && rm -rf "$tmp"' EXIT
  tmp="$(mktemp -d)"
  cp -a "$src"/. "$tmp/"
  ( cd "$tmp"
    git init -b main
    git add .
    git commit -m "Initial commit: sample app for tekton-dag"
    if gh repo view "jmjava/$name" --json name &>/dev/null; then
      git remote add origin "$repo_url"
      git push -u origin main --force
    else
      gh repo create "jmjava/$name" --public --source=. --remote=origin --push
      git remote set-url origin "$repo_url"
    fi
  )
  trap - EXIT
  echo "  Done: $repo_url"
  echo ""
done

echo "All done. Tekton clones via SSH, e.g.:"
for name in "${NAMES[@]}"; do
  echo "  git@github.com:jmjava/$name.git"
done
