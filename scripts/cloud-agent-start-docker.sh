#!/usr/bin/env bash
# Per-boot Docker daemon for Cloud Agent VMs (nested overlay → fuse-overlayfs).
# Idempotent: returns once `docker info` works. Does not create a Kind cluster.
set -euo pipefail

DOCKER_LOG="${DOCKER_LOG:-/tmp/dockerd.log}"
DOCKER_SOCK="${DOCKER_SOCK:-/var/run/docker.sock}"

if docker info >/dev/null 2>&1; then
  echo "docker already running"
  exit 0
fi

if [[ ! -x /usr/bin/dockerd ]]; then
  echo "ERROR: dockerd not installed (expected on the environment snapshot)" >&2
  exit 1
fi

sudo mkdir -p /etc/docker /var/lib/docker /var/run
if [[ ! -f /etc/docker/daemon.json ]]; then
  sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{
  "storage-driver": "fuse-overlayfs",
  "iptables": true,
  "ip6tables": false,
  "live-restore": false,
  "log-level": "warn"
}
EOF
fi

if ! pgrep -x dockerd >/dev/null 2>&1; then
  sudo dockerd >"$DOCKER_LOG" 2>&1 &
fi

for i in $(seq 1 40); do
  if docker info >/dev/null 2>&1 || sudo docker info >/dev/null 2>&1; then
    sudo chmod 666 "$DOCKER_SOCK" 2>/dev/null || true
    echo "docker ready (${i}s)"
    docker info >/dev/null
    exit 0
  fi
  sleep 1
done

echo "ERROR: dockerd did not become ready; last log:" >&2
tail -50 "$DOCKER_LOG" >&2 || true
exit 1
