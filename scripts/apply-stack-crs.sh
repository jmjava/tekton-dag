#!/usr/bin/env bash
# Render stacks/*.yaml and teams/*/team.yaml as tektondag.io CRs and apply them.
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

APPLY=true
KIND=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) APPLY=false; shift ;;
    --stacks) KIND="stacks"; shift ;;
    --teams) KIND="teams"; shift ;;
    --help|-h)
      echo "Usage: $0 [--dry-run] [--stacks|--teams]"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

PY="${REPO_ROOT}/.venv/bin/python3"
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi
export PYTHONPATH="${REPO_ROOT}/libs/tekton-dag-common${PYTHONPATH:+:$PYTHONPATH}"

render() {
  "$PY" - "$REPO_ROOT" "$NAMESPACE" "$KIND" <<'PY'
import sys
from pathlib import Path

import yaml

repo, namespace, kind = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
sys.path.insert(0, str(repo / "libs" / "tekton-dag-common"))
from tekton_dag_common.stack_cr import iter_stack_files, stack_yaml_to_cr
from tekton_dag_common.team_cr import iter_team_files, team_yaml_to_cr

docs = []
if kind in ("", "stacks"):
    for path in iter_stack_files(repo / "stacks"):
        data = yaml.safe_load(path.read_text()) or {}
        if not isinstance(data.get("apps"), list):
            continue
        docs.append(stack_yaml_to_cr(
            data,
            namespace=namespace,
            stack_file=f"stacks/{path.name}",
            git_url="https://github.com/jmjava/tekton-dag.git",
        ))
if kind in ("", "teams"):
    for team_name, path in iter_team_files(repo / "teams"):
        data = yaml.safe_load(path.read_text()) or {}
        docs.append(team_yaml_to_cr(data, team_dir_name=team_name, namespace=namespace))
for i, doc in enumerate(docs):
    if i:
        print("---")
    yaml.safe_dump(doc, sys.stdout, sort_keys=False)
PY
}

YAML="$(render)"
if [[ -z "$YAML" ]]; then
  echo "No Stack/Team CRs to apply"
  exit 0
fi
if [[ "$APPLY" != "true" ]]; then
  printf '%s\n' "$YAML"
  exit 0
fi
need kubectl
printf '%s\n' "$YAML" | kubectl apply -f -
echo "OK: applied Stack/Team CRs in $NAMESPACE"
