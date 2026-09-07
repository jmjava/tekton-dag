#!/usr/bin/env bash
# Enable the Stack validating webhook on Kind: TLS secret, Service, and
# ValidatingWebhookConfiguration. Do not apply operator/config/webhook/manifests.yaml
# (that file points at namespace "system").
#
# Usage:
#   ./scripts/install-operator-webhook-kind.sh
#
# Requires the operator Deployment already installed (install-operator-kind.sh).
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

need kubectl
need openssl

NAMESPACE="${NAMESPACE:-tekton-pipelines}"
SVC="tekton-dag-operator-webhook"
SECRET="webhook-server-cert"
CFG="tektondag-stack-validating"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

CN="${SVC}.${NAMESPACE}.svc"
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -subj "/CN=${CN}" \
  -addext "subjectAltName=DNS:${CN},DNS:${SVC},DNS:${SVC}.${NAMESPACE}.svc.cluster.local" \
  -keyout "$TMP/tls.key" -out "$TMP/tls.crt" >/dev/null 2>&1

kubectl create secret tls "$SECRET" -n "$NAMESPACE" \
  --cert="$TMP/tls.crt" --key="$TMP/tls.key" \
  --dry-run=client -o yaml | kubectl apply -f -

CA_BUNDLE="$(base64 -w0 < "$TMP/tls.crt" 2>/dev/null || base64 < "$TMP/tls.crt" | tr -d '\n')"

kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: ${SVC}
  namespace: ${NAMESPACE}
  labels:
    app: tekton-dag-operator
spec:
  selector:
    app: tekton-dag-operator
  ports:
    - name: webhook
      port: 443
      targetPort: 9443
EOF

kubectl apply -f - <<EOF
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: ${CFG}
webhooks:
  - name: vstack.tektondag.io
    admissionReviewVersions: ["v1"]
    clientConfig:
      service:
        name: ${SVC}
        namespace: ${NAMESPACE}
        path: /validate-tektondag-io-v1alpha1-stack
        port: 443
      caBundle: ${CA_BUNDLE}
    failurePolicy: Fail
    sideEffects: None
    rules:
      - apiGroups: ["tektondag.io"]
        apiVersions: ["v1alpha1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["stacks"]
EOF

kubectl set env deployment/tekton-dag-operator -n "$NAMESPACE" ENABLE_WEBHOOKS=true
kubectl patch deployment tekton-dag-operator -n "$NAMESPACE" --type=strategic -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "manager",
          "ports": [{"containerPort": 9443, "name": "webhook"}],
          "volumeMounts": [{
            "name": "webhook-certs",
            "mountPath": "/tmp/k8s-webhook-server/serving-certs",
            "readOnly": true
          }]
        }],
        "volumes": [{
          "name": "webhook-certs",
          "secret": {"secretName": "'"${SECRET}"'"}
        }]
      }
    }
  }
}'

kubectl rollout status deployment/tekton-dag-operator -n "$NAMESPACE" --timeout=180s
kubectl wait --for=condition=Available deployment/tekton-dag-operator -n "$NAMESPACE" --timeout=60s
echo "Stack validating webhook enabled (failurePolicy=Fail). Cert secret: ${SECRET}"
