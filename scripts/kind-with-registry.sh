#!/usr/bin/env bash
# Create a kind cluster with a local container registry for Tekton build pipelines.
# Registry is available as localhost:5000 on the host and to the cluster.
# Usage: ./kind-with-registry.sh [--name CLUSTER_NAME] [--port REGISTRY_PORT]
# Example: ./kind-with-registry.sh --name tekton-stack
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIND_CLUSTER_NAME="${KIND_CLUSTER_NAME:-tekton-stack}"
REG_PORT="${REG_PORT:-5000}"
reg_name="kind-registry"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)   KIND_CLUSTER_NAME="$2"; shift 2 ;;
    --port)   REG_PORT="$2"; shift 2 ;;
    *)        echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

need() { command -v "$1" >/dev/null 2>&1 || { echo "Required: $1" >&2; exit 1; }; }
need docker
need kind
need kubectl

echo "=============================================="
echo "  Kind cluster + local registry"
echo "  Cluster name: $KIND_CLUSTER_NAME"
echo "  Registry:      localhost:${REG_PORT}"
echo "=============================================="

# 1. Create registry container unless it already exists
if [ "$(docker inspect -f '{{.State.Running}}' "${reg_name}" 2>/dev/null || true)" != 'true' ]; then
  echo "  Creating local registry container (${reg_name})..."
  docker run -d --restart=always \
    -p "127.0.0.1:${REG_PORT}:5000" \
    --network bridge \
    --name "${reg_name}" \
    registry:2
else
  echo "  Registry ${reg_name} already running."
fi

# 2. Create kind cluster with containerd config (skip if already exists)
if kind get clusters 2>/dev/null | grep -qx "${KIND_CLUSTER_NAME}"; then
  echo "  Cluster $KIND_CLUSTER_NAME already exists; skipping creation."
else
  echo "  Creating kind cluster: $KIND_CLUSTER_NAME ..."
  cat <<EOF | kind create cluster --name "${KIND_CLUSTER_NAME}" --config=-
kind: Cluster
apiVersion: kind.x.k8s.io/v1alpha4
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry]
    config_path = "/etc/containerd/certs.d"
EOF
fi

# 3. Tell containerd on each node to use the registry for localhost:REG_PORT
#    (localhost in a node is not the host; we alias it to the registry container)
REGISTRY_DIR="/etc/containerd/certs.d/localhost:${REG_PORT}"
for node in $(kind get nodes --name "${KIND_CLUSTER_NAME}"); do
  docker exec "${node}" mkdir -p "${REGISTRY_DIR}"
  cat <<TOML | docker exec -i "${node}" cp /dev/stdin "${REGISTRY_DIR}/hosts.toml"
[host."http://${reg_name}:5000"]
  capabilities = ["pull", "resolve"]
  skip_verify = true
TOML
done

# 4. Connect the registry to the kind network so nodes can reach it
if [ "$(docker inspect -f '{{json .NetworkSettings.Networks.kind}}' "${reg_name}" 2>/dev/null)" = 'null' ]; then
  echo "  Connecting registry to kind network..."
  docker network connect "kind" "${reg_name}" 2>/dev/null || true
fi

# 5. Document the local registry (for tooling that reads this ConfigMap)
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:${REG_PORT}"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF

echo ""
echo "  Done. Use the registry like this:"
echo "    docker tag myimage:latest localhost:${REG_PORT}/myimage:latest"
echo "    docker push localhost:${REG_PORT}/myimage:latest"
echo "    kubectl run foo --image=localhost:${REG_PORT}/myimage:latest"
echo ""
echo "  For Tekton pipelines, pass:  --registry localhost:${REG_PORT}"
echo "  Next: install Tekton and apply tasks/pipelines (see docs or run scripts/install-tekton.sh if present)."
echo ""
