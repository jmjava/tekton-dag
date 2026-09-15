#!/usr/bin/env bash
# Stage, package, render, and parse the distributable Helm chart.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

need helm
need python3

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$REPO_ROOT/helm/tekton-dag/package.sh"
helm lint --strict "$REPO_ROOT/helm/tekton-dag"
helm package "$REPO_ROOT/helm/tekton-dag" --destination "$TMP_DIR"

mapfile -t charts < <(compgen -G "$TMP_DIR/tekton-dag-*.tgz" || true)
((${#charts[@]} == 1)) ||
  die "expected one packaged chart, found ${#charts[@]}"
chart="${charts[0]}"

helm lint --strict "$chart"
helm template static-quality-default "$chart" --include-crds \
  >"$TMP_DIR/rendered-default.yaml"
helm template static-quality-cluster-admin "$chart" --include-crds \
  --set rbac.clusterAdmin=true \
  >"$TMP_DIR/rendered-cluster-admin.yaml"

python3 - "$TMP_DIR/rendered-default.yaml" "$TMP_DIR/rendered-cluster-admin.yaml" <<'PY'
import sys
from pathlib import Path

import yaml

for filename in sys.argv[1:]:
    path = Path(filename)
    documents = [document for document in yaml.safe_load_all(path.read_text()) if document]
    if not documents:
        raise SystemExit(f"{path}: rendered no resources")
    print(f"{path.name}: parsed {len(documents)} resource(s)")
PY
