#!/usr/bin/env python3
"""Fail when duplicated Helm, CRD, Stack, or PipelineRun representations drift."""

from __future__ import annotations

import argparse
import filecmp
import re
import sys
from pathlib import Path

import yaml
from tekton_dag_common.stack_cr import iter_stack_files, stack_yaml_to_cr
from tekton_dag_common.team_cr import iter_team_files, team_yaml_to_cr

CRD_NAMES = (
    "tektondag.io_stackruns.yaml",
    "tektondag.io_stacks.yaml",
    "tektondag.io_teams.yaml",
)

GO_BUILDERS = {
    "BuildPR": "stack-pr-test",
    "BuildBootstrap": "stack-bootstrap",
    "BuildMerge": "stack-merge-release",
    "BuildPromote": "stack-promote",
    "BuildPRContinue": "stack-pr-continue",
}

PYTHON_BUILDERS = {
    "build_pr_pipelinerun": "stack-pr-test",
    "build_bootstrap_pipelinerun": "stack-bootstrap",
    "build_merge_pipelinerun": "stack-merge-release",
    "build_promote_pipelinerun": "stack-promote",
}

PARAM_RE = re.compile(r'param\("([^"]+)"')
PY_PARAM_RE = re.compile(r'\{"name": "([^"]+)", "value":')
FUNC_RE = re.compile(r"^func (Build[A-Za-z]+)\(")
PY_FUNC_RE = re.compile(r"^def (build_[a-z_]+)\(")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def check_crd_copies(root: Path) -> list[str]:
    errors: list[str] = []
    generated = root / "operator" / "config" / "crd" / "bases"
    packaged = root / "helm" / "tekton-dag" / "crds"
    for name in CRD_NAMES:
        left = generated / name
        right = packaged / name
        if not left.is_file():
            errors.append(f"missing generated CRD: {left}")
            continue
        if not right.is_file():
            errors.append(f"missing Helm CRD copy: {right}")
            continue
        if not filecmp.cmp(left, right, shallow=False):
            errors.append(f"CRD drift: {left} != {right}")
    return errors


def check_stack_and_team_conversion(root: Path) -> list[str]:
    errors: list[str] = []
    stacks = root / "stacks"
    converted = 0
    for path in iter_stack_files(stacks):
        data = yaml.safe_load(path.read_text()) or {}
        if not isinstance(data.get("apps"), list):
            continue
        cr = stack_yaml_to_cr(
            data,
            namespace="tekton-pipelines",
            stack_file=f"stacks/{path.name}",
            git_url="https://github.com/jmjava/tekton-dag.git",
        )
        if cr.get("kind") != "Stack":
            errors.append(f"{path}: conversion did not produce kind Stack")
            continue
        if not cr.get("metadata", {}).get("name"):
            errors.append(f"{path}: Stack CR is missing metadata.name")
            continue
        if not cr.get("spec", {}).get("apps"):
            errors.append(f"{path}: Stack CR has no spec.apps")
            continue
        converted += 1
    if converted == 0:
        errors.append("no stack YAML files converted to Stack CRs")

    teams = 0
    for team_name, path in iter_team_files(root / "teams"):
        data = yaml.safe_load(path.read_text()) or {}
        cr = team_yaml_to_cr(data, team_dir_name=team_name, namespace="tekton-pipelines")
        if cr.get("kind") != "Team" or not cr.get("metadata", {}).get("name"):
            errors.append(f"{path}: Team conversion failed")
            continue
        teams += 1
    if teams == 0:
        errors.append("no team YAML files converted to Team CRs")
    return errors


def _pipeline_params(path: Path) -> tuple[set[str], set[str]]:
    docs = list(yaml.safe_load_all(path.read_text()))
    pipeline = next(
        (
            doc
            for doc in docs
            if isinstance(doc, dict) and doc.get("kind") == "Pipeline"
        ),
        None,
    )
    if pipeline is None:
        return set(), set()
    required: set[str] = set()
    declared: set[str] = set()
    for param in pipeline.get("spec", {}).get("params") or []:
        name = param.get("name")
        if not name:
            continue
        declared.add(name)
        if "default" not in param:
            required.add(name)
    return required, declared


def _go_builder_params(source: str) -> dict[str, set[str]]:
    current = None
    params: dict[str, set[str]] = {name: set() for name in GO_BUILDERS}
    for line in source.splitlines():
        match = FUNC_RE.match(line)
        if match:
            current = match.group(1) if match.group(1) in GO_BUILDERS else None
            continue
        if current is None:
            continue
        params[current].update(PARAM_RE.findall(line))
        if line.startswith("func "):
            current = None
    return params


def _python_builder_params(source: str) -> dict[str, set[str]]:
    current = None
    params: dict[str, set[str]] = {name: set() for name in PYTHON_BUILDERS}
    for line in source.splitlines():
        match = PY_FUNC_RE.match(line)
        if match:
            current = match.group(1) if match.group(1) in PYTHON_BUILDERS else None
            continue
        if current is None:
            continue
        if line.startswith("def "):
            current = None
            continue
        params[current].update(PY_PARAM_RE.findall(line))
    return params


def check_pipeline_param_compatibility(root: Path) -> list[str]:
    errors: list[str] = []
    pipelines = {
        "stack-pr-test": root / "pipeline" / "stack-pr-pipeline.yaml",
        "stack-bootstrap": root / "pipeline" / "stack-bootstrap-pipeline.yaml",
        "stack-merge-release": root / "pipeline" / "stack-merge-pipeline.yaml",
        "stack-promote": root / "pipeline" / "stack-promote-pipeline.yaml",
        "stack-pr-continue": root / "pipeline" / "stack-pr-continue-pipeline.yaml",
    }
    declared: dict[str, tuple[set[str], set[str]]] = {}
    for name, path in pipelines.items():
        if not path.is_file():
            errors.append(f"missing pipeline: {path}")
            continue
        declared[name] = _pipeline_params(path)

    go_params = _go_builder_params((root / "operator" / "internal" / "pipeline" / "builder.go").read_text())
    py_params = _python_builder_params((root / "orchestrator" / "pipelinerun_builder.py").read_text())

    for builder, pipeline in GO_BUILDERS.items():
        required, all_declared = declared.get(pipeline, (set(), set()))
        emitted = go_params.get(builder, set())
        missing = required - emitted
        extra = emitted - all_declared
        if missing:
            errors.append(
                f"{builder} does not set required {pipeline} params: {sorted(missing)}"
            )
        if extra:
            errors.append(
                f"{builder} sets unknown {pipeline} params: {sorted(extra)}"
            )

    for builder, pipeline in PYTHON_BUILDERS.items():
        go_builder = next(name for name, target in GO_BUILDERS.items() if target == pipeline)
        # Compile-image overrides are optional and only emitted when provided.
        comparable = py_params[builder] - {
            name for name in py_params[builder] if name.startswith("compile-image-")
        }
        go_comparable = go_params[go_builder] - {
            name for name in go_params[go_builder] if name.startswith("compile-image-")
        }
        if comparable != go_comparable:
            errors.append(
                f"{builder} params {sorted(comparable)} != {go_builder} params {sorted(go_comparable)}"
            )
    return errors


def run_checks(root: Path | None = None) -> list[str]:
    repo = root or _repo_root()
    errors = []
    errors.extend(check_crd_copies(repo))
    errors.extend(check_stack_and_team_conversion(repo))
    errors.extend(check_pipeline_param_compatibility(repo))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    errors = run_checks()
    if errors:
        print("ERROR: representation drift detected", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("OK: Helm CRDs, Stack/Team conversion, and PipelineRun params are in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
