#!/usr/bin/env bash
# Create the git-ssh-key secret in tekton-pipelines from ~/.ssh if not already present.
# Required for clone-app-repos (SSH pull). Idempotent: skips if secret exists.
#
# Usage: ./ensure-git-ssh-secret.sh [--secret-name NAME] [--namespace NS]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="${NAMESPACE:-tekton-pipelines}"
SECRET_NAME="${GIT_SSH_SECRET_NAME:-git-ssh-key}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --secret-name) SECRET_NAME="$2"; shift 2 ;;
    --namespace)   NAMESPACE="$2"; shift 2 ;;
    *)             echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need kubectl

if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" &>/dev/null; then
  echo "  Secret $SECRET_NAME already exists in $NAMESPACE; skipping."
  exit 0
fi

SSH_DIR="${HOME}/.ssh"
if [ -f "$SSH_DIR/id_ed25519" ]; then
  echo "  Creating secret $SECRET_NAME from $SSH_DIR/id_ed25519..."
  kubectl create secret generic "$SECRET_NAME" --from-file=id_ed25519="$SSH_DIR/id_ed25519" -n "$NAMESPACE"
elif [ -f "$SSH_DIR/id_rsa" ]; then
  echo "  Creating secret $SECRET_NAME from $SSH_DIR/id_rsa..."
  kubectl create secret generic "$SECRET_NAME" --from-file=id_rsa="$SSH_DIR/id_rsa" -n "$NAMESPACE"
else
  echo "  No SSH key found at $SSH_DIR/id_ed25519 or $SSH_DIR/id_rsa." >&2
  echo "  Create a key (e.g. ssh-keygen -t ed25519 -C your@email) and add the public key to GitHub." >&2
  exit 1
fi

echo "  Done. Secret $SECRET_NAME is in $NAMESPACE."
