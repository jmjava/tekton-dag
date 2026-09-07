#!/bin/bash
set -e

CHART_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$CHART_DIR/../.." && pwd)"

echo "Packaging tekton-dag Helm chart..."
echo "  Chart dir: $CHART_DIR"
echo "  Repo root: $REPO_ROOT"

rm -rf "$CHART_DIR/raw"
mkdir -p "$CHART_DIR/raw/tasks" "$CHART_DIR/raw/pipelines" "$CHART_DIR/raw/stacks" \
  "$CHART_DIR/raw/stack-crs" "$CHART_DIR/raw/team-crs"

echo "  Copying tasks..."
cp "$REPO_ROOT"/tasks/*.yaml "$CHART_DIR/raw/tasks/"

echo "  Copying pipelines and triggers..."
cp "$REPO_ROOT"/pipeline/*.yaml "$CHART_DIR/raw/pipelines/"

echo "  Copying stacks..."
cp "$REPO_ROOT"/stacks/*.yaml "$CHART_DIR/raw/stacks/"

echo "  Rendering Stack + Team CRs..."
PYTHONPATH="$REPO_ROOT/libs/tekton-dag-common${PYTHONPATH:+:$PYTHONPATH}" \
  python3 - "$REPO_ROOT" "$CHART_DIR" <<'PY'
import sys
from pathlib import Path
import yaml

repo, chart = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo / "libs" / "tekton-dag-common"))
from tekton_dag_common.stack_cr import iter_stack_files, stack_yaml_to_cr
from tekton_dag_common.team_cr import iter_team_files, team_yaml_to_cr

ns = "tekton-pipelines"
out_s = chart / "raw" / "stack-crs"
out_t = chart / "raw" / "team-crs"
for path in iter_stack_files(repo / "stacks"):
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data.get("apps"), list):
        continue
    cr = stack_yaml_to_cr(
        data,
        namespace=ns,
        stack_file=f"stacks/{path.name}",
        git_url="https://github.com/jmjava/tekton-dag.git",
    )
    (out_s / f"{cr['metadata']['name']}.yaml").write_text(yaml.safe_dump(cr, sort_keys=False))
for team_name, path in iter_team_files(repo / "teams"):
    data = yaml.safe_load(path.read_text()) or {}
    cr = team_yaml_to_cr(data, team_dir_name=team_name, namespace=ns)
    (out_t / f"{cr['metadata']['name']}.yaml").write_text(yaml.safe_dump(cr, sort_keys=False))
PY

echo "Done. Raw files staged in $CHART_DIR/raw/"
echo ""
echo "To template:  helm template tekton-dag $CHART_DIR"
echo "To install:   helm install tekton-dag $CHART_DIR -n tekton-pipelines"
echo "To package:   helm package $CHART_DIR"
