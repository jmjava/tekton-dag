#!/usr/bin/env bash
# Ensure Kind (or similar) has a default StorageClass so PipelineRun PVCs can bind.
# Without a default, volumeClaimTemplate PVCs stay Pending and pods fail with
# "pod has unbound immediate PersistentVolumeClaims".
#
# Usage: ./scripts/install-kind-default-storage.sh
#
# If your cluster already has a default StorageClass, this is a no-op.
# Otherwise applies the local-path-provisioner and sets it as default.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for existing default StorageClass
DEFAULT_SC=$(kubectl get storageclass -o json 2>/dev/null | jq -r '.items[] | select(.metadata.annotations["storageclass.kubernetes.io/is-default-class"]=="true") | .metadata.name' 2>/dev/null || true)
if [[ -n "$DEFAULT_SC" ]]; then
  echo "Default StorageClass already set: $DEFAULT_SC"
  exit 0
fi

# Check for any StorageClass we can set as default
ANY_SC=$(kubectl get storageclass -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
if [[ -n "$ANY_SC" ]]; then
  echo "Setting existing StorageClass '$ANY_SC' as default..."
  kubectl patch storageclass "$ANY_SC" -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
  echo "Done. Default StorageClass: $ANY_SC"
  exit 0
fi

# No StorageClass at all — install local-path-provisioner (common for Kind)
echo "No StorageClass found. Installing local-path-provisioner as default..."
LOCAL_PATH_URL="${LOCAL_PATH_PROVISIONER_URL:-https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.28/deploy/local-path-storage.yaml}"
kubectl apply -f "$LOCAL_PATH_URL"
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}' 2>/dev/null || \
  kubectl patch storageclass standard -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}' 2>/dev/null || true
echo "Done. Run: kubectl get storageclass"
echo "If PVCs were already created (e.g. from a stuck PipelineRun), delete the PipelineRun so Tekton deletes the PVCs; then re-run your pipeline."
