#!/usr/bin/env bash
# Install PostgreSQL in the Kind (or any) cluster for Tekton Results.
# Creates the secret Tekton Results expects, then deploys Postgres with a PVC.
# Run after install-tekton.sh so tekton-pipelines namespace exists.
#
# Usage: ./install-postgres-kind.sh [--storage-class CLASS] [--ephemeral]
#   --storage-class  PVC storage class (default: "" for Kind's default; use "standard" for some clusters)
#   --ephemeral      Use emptyDir instead of PVC (Kind with no StorageClass; data not persistent)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$REPO_ROOT/config/postgres"
NAMESPACE="${NAMESPACE:-tekton-pipelines}"
STORAGE_CLASS=""
EPHEMERAL=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --storage-class) STORAGE_CLASS="$2"; shift 2 ;;
    --ephemeral)     EPHEMERAL=true; shift ;;
    *)               echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need kubectl

echo "=============================================="
echo "  PostgreSQL for Tekton Results (Kind cluster)"
echo "  Namespace: $NAMESPACE"
echo "=============================================="

# Ensure namespace exists (e.g. from install-tekton.sh)
kubectl get namespace "$NAMESPACE" &>/dev/null || kubectl create namespace "$NAMESPACE"

# 1. Secret expected by Tekton Results (and by our Postgres deployment)
if kubectl get secret tekton-results-postgres -n "$NAMESPACE" &>/dev/null; then
  echo "  Secret tekton-results-postgres already exists; skipping creation."
else
  echo "  Creating secret tekton-results-postgres..."
  kubectl create secret generic tekton-results-postgres --namespace="$NAMESPACE" \
    --from-literal=POSTGRES_USER=postgres \
    --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 24)
  echo "  Secret created."
fi

# 2. Apply Postgres manifest (PVC or ephemeral)
if [[ "$EPHEMERAL" == "true" ]]; then
  echo "  Deploying PostgreSQL (ephemeral emptyDir — no PVC)..."
  kubectl apply -f "$CONFIG_DIR/postgres-ephemeral.yaml" -n "$NAMESPACE"
else
  echo "  Deploying PostgreSQL (PVC + Deployment + Service)..."
  if [[ -n "$STORAGE_CLASS" ]]; then
    sed "s/storageClassName: \"\"/storageClassName: $STORAGE_CLASS/" "$CONFIG_DIR/postgres.yaml" | kubectl apply -f - -n "$NAMESPACE"
  else
    kubectl apply -f "$CONFIG_DIR/postgres.yaml" -n "$NAMESPACE"
  fi
fi
# On Kind without --ephemeral and no default StorageClass, PVC may stay Pending; use --ephemeral or install a provisioner

# 3. Wait for Postgres to be ready (resilient: PVC may stay Pending on Kind without StorageClass)
echo "  Waiting for PostgreSQL pod to be ready..."
if kubectl wait --for=condition=Ready pod -l app=tekton-results-postgres -n "$NAMESPACE" --timeout=120s 2>/dev/null; then
  echo "  PostgreSQL is ready."
else
  echo "  WARN: PostgreSQL pod not ready (PVC may be Pending; install a StorageClass or use --storage-class)."
  echo "  Continuing; Tekton Results may fail until Postgres is up."
fi

echo ""
echo "  Done. PostgreSQL (or PVC) is in $NAMESPACE."
echo "  Service: tekton-results-postgres-service.${NAMESPACE}.svc.cluster.local:5432"
echo "  Database: tekton-results"
echo ""
echo "  Next (optional): install Tekton Results to persist pipeline/task run history:"
echo "    1. Create TLS secret for the Results API (see Tekton Results install docs)."
echo "    2. kubectl apply -f https://storage.googleapis.com/tekton-releases/results/latest/release.yaml"
echo ""
