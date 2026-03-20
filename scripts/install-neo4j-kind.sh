#!/usr/bin/env bash
# Install Neo4j Community in the Kind cluster for M9 test-trace graph.
# Deploys a single-node Neo4j with ephemeral storage (sufficient for dev/PoC).
#
# Usage: ./scripts/install-neo4j-kind.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

NEO4J_PASSWORD="${NEO4J_PASSWORD:-changeme}"

need kubectl

echo "=============================================="
echo "  Neo4j Community for test-trace graph (M9)"
echo "  Namespace: $NAMESPACE"
echo "=============================================="

kubectl get namespace "$NAMESPACE" &>/dev/null || kubectl create namespace "$NAMESPACE"

if kubectl get secret neo4j-auth -n "$NAMESPACE" &>/dev/null; then
  echo "  Secret neo4j-auth already exists; skipping."
else
  echo "  Creating secret neo4j-auth..."
  kubectl create secret generic neo4j-auth --namespace="$NAMESPACE" \
    --from-literal=NEO4J_AUTH="neo4j/${NEO4J_PASSWORD}"
fi

echo "  Applying Neo4j deployment..."
cat <<'MANIFEST' | kubectl apply -n "$NAMESPACE" -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graph-db
  labels:
    app: graph-db
    app.kubernetes.io/part-of: tekton-job-standardization
spec:
  replicas: 1
  selector:
    matchLabels:
      app: graph-db
  template:
    metadata:
      labels:
        app: graph-db
    spec:
      containers:
        - name: neo4j
          image: neo4j:5-community
          ports:
            - containerPort: 7474
              name: http
            - containerPort: 7687
              name: bolt
          env:
            - name: NEO4J_AUTH
              valueFrom:
                secretKeyRef:
                  name: neo4j-auth
                  key: NEO4J_AUTH
            - name: NEO4J_PLUGINS
              value: "[]"
            - name: NEO4J_server_config_strict__validation_enabled
              value: "false"
            - name: NEO4J_server_memory_heap_initial__size
              value: "256m"
            - name: NEO4J_server_memory_heap_max__size
              value: "512m"
          resources:
            requests:
              cpu: 200m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 1Gi
          readinessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 60
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 90
            periodSeconds: 30
            failureThreshold: 5
---
apiVersion: v1
kind: Service
metadata:
  name: graph-db
  labels:
    app: graph-db
spec:
  type: ClusterIP
  ports:
    - port: 7474
      targetPort: http
      protocol: TCP
      name: http
    - port: 7687
      targetPort: bolt
      protocol: TCP
      name: bolt
  selector:
    app: graph-db
MANIFEST

echo "  Waiting for Neo4j pod to be ready..."
if kubectl wait --for=condition=Ready pod -l app=graph-db -n "$NAMESPACE" --timeout=120s 2>/dev/null; then
  echo "  Neo4j is ready."
else
  echo "  WARN: Neo4j pod not ready within 120s. Check: kubectl get pods -n $NAMESPACE -l app=graph-db"
fi

echo ""
echo "  Done. Neo4j in $NAMESPACE."
  echo "  Bolt:  neo4j://graph-db.${NAMESPACE}.svc.cluster.local:7687"
echo "  HTTP:  http://graph-db.${NAMESPACE}.svc.cluster.local:7474"
echo "  Auth:  neo4j / ${NEO4J_PASSWORD}"
echo ""
