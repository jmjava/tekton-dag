#!/usr/bin/env bash
# Create the ServiceAccount + Role the in-cluster mirrord proxy pod runs as.
#
# `mirrord exec` inside the proxy pod must resolve its target Deployment and
# create the mirrord-agent Job in the same namespace. The pipeline SA cannot
# create ServiceAccounts, so a cluster admin runs this once per namespace
# (run-cluster-ci.sh / run-product-intercept-e2e.sh do it for CI).
#
# Usage: ./scripts/install-mirrord-intercept-rbac.sh [--namespace staging] [--name mirrord-intercept]
set -euo pipefail

NAMESPACE="${MIRRORD_INTERCEPT_NAMESPACE:-staging}"
SA_NAME="${MIRRORD_INTERCEPT_SA:-mirrord-intercept}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --namespace) NAMESPACE="$2"; shift 2 ;;
    --name) SA_NAME="$2"; shift 2 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 64 ;;
  esac
done

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${SA_NAME}
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/part-of: tekton-job-standardization
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ${SA_NAME}
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/part-of: tekton-job-standardization
rules:
  # Target resolution (deployment -> replicaset -> pod) and agent placement.
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "endpoints"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets", "statefulsets"]
    verbs: ["get", "list", "watch"]
  # The mirrord-agent runs as a Job in the target namespace.
  - apiGroups: ["batch"]
    resources: ["jobs"]
    verbs: ["get", "list", "watch", "create", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ${SA_NAME}
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/part-of: tekton-job-standardization
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ${SA_NAME}
subjects:
  - kind: ServiceAccount
    name: ${SA_NAME}
    namespace: ${NAMESPACE}
EOF

echo "OK: ServiceAccount ${NAMESPACE}/${SA_NAME} ready for the mirrord intercept proxy"
