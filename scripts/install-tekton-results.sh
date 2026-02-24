#!/usr/bin/env bash
# Install Tekton Results (API + Watcher) so pipeline/task run history is stored in the DB.
# Run after install-postgres-kind.sh so Postgres and secret tekton-results-postgres exist.
#
# Creates the TLS secret expected by the API, then applies the official release.
# Usage: ./install-tekton-results.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NAMESPACE="${NAMESPACE:-tekton-pipelines}"
RESULTS_RELEASE="${RESULTS_RELEASE:-https://storage.googleapis.com/tekton-releases/results/latest/release.yaml}"
API_CN="tekton-results-api-service.tekton-pipelines.svc.cluster.local"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need kubectl
need openssl
need yq

echo "=============================================="
echo "  Install Tekton Results (API + Watcher)"
echo "  Namespace: $NAMESPACE"
echo "=============================================="

kubectl get namespace "$NAMESPACE" &>/dev/null || { echo "Namespace $NAMESPACE not found. Run install-tekton.sh first." >&2; exit 1; }
kubectl get secret tekton-results-postgres -n "$NAMESPACE" &>/dev/null || { echo "Secret tekton-results-postgres not found. Run install-postgres-kind.sh first." >&2; exit 1; }

# TLS secret for the API (self-signed)
if kubectl get secret tekton-results-tls -n "$NAMESPACE" &>/dev/null; then
  echo "  TLS secret tekton-results-tls already exists; skipping."
else
  echo "  Creating TLS secret for Results API..."
  TMPDIR="${TMPDIR:-/tmp}"
  CERT="$TMPDIR/tekton-results-cert.pem"
  KEY="$TMPDIR/tekton-results-key.pem"
  openssl req -x509 -newkey rsa:4096 -keyout "$KEY" -out "$CERT" -days 365 -nodes \
    -subj "/CN=${API_CN}" \
    -addext "subjectAltName=DNS:${API_CN},DNS:tekton-results-api-service,DNS:localhost"
  kubectl create secret tls tekton-results-tls -n "$NAMESPACE" --cert="$CERT" --key="$KEY"
  rm -f "$CERT" "$KEY"
  echo "  TLS secret created."
fi

# Apply release but exclude the release's Postgres (StatefulSet, Service, ConfigMap) so we use our own Postgres
echo "  Fetching Tekton Results release and excluding its Postgres (using our Postgres)..."
TMP_RELEASE=$(mktemp)
curl -sL "$RESULTS_RELEASE" -o "$TMP_RELEASE"
yq eval-all '
  select(
    ( (.kind == "StatefulSet" and .metadata.name == "tekton-results-postgres") or
      (.kind == "Service" and .metadata.name == "tekton-results-postgres-service") or
      (.kind == "ConfigMap" and .metadata.name == "tekton-results-postgres") )
    | not
  )
' "$TMP_RELEASE" | kubectl apply -f -
rm -f "$TMP_RELEASE"

echo "  Waiting for Results API and Watcher to be ready..."
kubectl wait --for=condition=Available deployment/tekton-results-api -n "$NAMESPACE" --timeout=120s 2>/dev/null || echo "  (API may still be rolling out.)"
kubectl wait --for=condition=Available deployment/tekton-results-watcher -n "$NAMESPACE" --timeout=120s 2>/dev/null || echo "  (Watcher may still be rolling out.)"

echo ""
echo "  Done. Tekton Results is installed; the Watcher will store PipelineRun/TaskRun data in Postgres."
echo "  Verify with: ./scripts/verify-results-in-db.sh (after running a pipeline)."
echo ""
