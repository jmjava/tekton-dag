#!/usr/bin/env bash
# Uninstall the Tekton Dashboard (same manifest used by install-tekton-dashboard.sh).
#
# Usage: ./uninstall-tekton-dashboard.sh [--read-write]
# Use --read-write if you installed with release-full.yaml (read/write mode).
set -euo pipefail

READ_WRITE=false
RELEASE_URL="https://infra.tekton.dev/tekton-releases/dashboard/latest/release.yaml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --read-write) READ_WRITE=true; shift ;;
    *)            echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ "$READ_WRITE" == "true" ]]; then
  RELEASE_URL="https://infra.tekton.dev/tekton-releases/dashboard/latest/release-full.yaml"
fi

echo "Uninstalling Tekton Dashboard..."
kubectl delete -f "$RELEASE_URL" --ignore-not-found 2>/dev/null || true
echo "Done."
