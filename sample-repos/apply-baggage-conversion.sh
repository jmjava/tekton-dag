#!/usr/bin/env bash
# Copy contract conversion files into cloned jmjava sample app repos.
# Usage: ./sample-repos/apply-baggage-conversion.sh /path/to/sample-apps
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC="$SCRIPT_DIR/conversion"
DEST="${1:-}"

if [[ -z "$DEST" || ! -d "$DEST" ]]; then
  echo "Usage: $0 /path/to/dir-containing-tekton-dag-* clones" >&2
  exit 1
fi

copied=0
missing=0
while IFS= read -r -d '' file; do
  rel="${file#$SRC/}"
  repo="${rel%%/*}"
  rest="${rel#*/}"
  target_root="$DEST/$repo"
  if [[ ! -d "$target_root/.git" && ! -d "$target_root" ]]; then
    echo "SKIP $repo (not found under $DEST)"
    missing=$((missing + 1))
    continue
  fi
  dest_file="$target_root/$rest"
  mkdir -p "$(dirname "$dest_file")"
  cp "$file" "$dest_file"
  echo "COPIED $repo/$rest"
  copied=$((copied + 1))
done < <(find "$SRC" -type f -print0)

echo ""
echo "Copied $copied files. Missing repos: $missing"
echo "Next: emit env from the stack and commit each sample repo."
echo "  $REPO_ROOT/scripts/emit-baggage-env.sh --stack $REPO_ROOT/stacks/stack-one.yaml --all"
