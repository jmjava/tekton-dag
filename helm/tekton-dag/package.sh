#!/bin/bash
set -e

CHART_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$CHART_DIR/../.." && pwd)"

echo "Packaging tekton-dag Helm chart..."
echo "  Chart dir: $CHART_DIR"
echo "  Repo root: $REPO_ROOT"

rm -rf "$CHART_DIR/raw"
mkdir -p "$CHART_DIR/raw/tasks" "$CHART_DIR/raw/pipelines" "$CHART_DIR/raw/stacks"

echo "  Copying tasks..."
cp "$REPO_ROOT"/tasks/*.yaml "$CHART_DIR/raw/tasks/"

echo "  Copying pipelines and triggers..."
cp "$REPO_ROOT"/pipeline/*.yaml "$CHART_DIR/raw/pipelines/"

echo "  Copying stacks..."
cp "$REPO_ROOT"/stacks/*.yaml "$CHART_DIR/raw/stacks/"

echo "Done. Raw files staged in $CHART_DIR/raw/"
echo ""
echo "To template:  helm template tekton-dag $CHART_DIR"
echo "To install:   helm install tekton-dag $CHART_DIR -n tekton-pipelines"
echo "To package:   helm package $CHART_DIR"
