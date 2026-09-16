#!/usr/bin/env python3
"""Fail when the documented support matrix drifts from automated jobs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs" / "support-matrix.yaml"
DOC_PATH = ROOT / "docs" / "SUPPORT-MATRIX.md"
COMPAT_WORKFLOW = ROOT / ".github" / "workflows" / "compatibility.yml"
LOCAL_WORKFLOW = ROOT / ".github" / "workflows" / "local-regression.yml"
WORKFLOWS_DIR = ROOT / ".github" / "workflows"

PYTHON_RE = re.compile(r'python-version:\s*"([^"]+)"')
NODE_RE = re.compile(r'node-version:\s*"([^"]+)"')
JAVA_RE = re.compile(r'java-version:\s*"([^"]+)"')
PHP_RE = re.compile(r'php-version:\s*"([^"]+)"')
GO_RE = re.compile(r'go-version:\s*"([^"]+)"')
KIND_ENV_RE = re.compile(r'KIND_VERSION:\s*"?(v[0-9.]+)"?')
KIND_URL_RE = re.compile(r"kind\.sigs\.k8s\.io/dl/(v[0-9.]+)/")
MATRIX_LIST_RE = re.compile(
    r"^\s+(python|node|java|php):\s*\[([^\]]+)\]",
    re.MULTILINE,
)


def _parse_list(raw: str) -> list[str]:
    return [item.strip().strip("\"'") for item in raw.split(",") if item.strip()]


def _workflow_text() -> dict[str, str]:
    return {path.name: path.read_text() for path in sorted(WORKFLOWS_DIR.glob("*.yml"))}


def main() -> int:
    matrix = yaml.safe_load(MATRIX_PATH.read_text())
    errors: list[str] = []
    workflows = _workflow_text()
    compat = workflows.get("compatibility.yml", "")
    local = workflows.get("local-regression.yml", "")
    doc = DOC_PATH.read_text()

    languages = {name: list(map(str, versions)) for name, versions in matrix["languages"].items()}
    primary = {name: str(value) for name, value in matrix["primary"].items()}
    cluster = {name: str(value) for name, value in matrix["cluster"].items()}

    compat_lists = {
        kind: _parse_list(raw) for kind, raw in MATRIX_LIST_RE.findall(compat)
    }
    for kind, expected in languages.items():
        found = compat_lists.get(kind, [])
        if found != expected:
            errors.append(
                f"compatibility.yml matrix.{kind}={found} does not match "
                f"support-matrix languages.{kind}={expected}"
            )

    for kind, field, regex in (
        ("python", "python-version", PYTHON_RE),
        ("node", "node-version", NODE_RE),
        ("java", "java-version", JAVA_RE),
        ("php", "php-version", PHP_RE),
    ):
        allowed = set(languages[kind])
        for name, text in workflows.items():
            for version in regex.findall(text):
                if version not in allowed:
                    errors.append(
                        f"{name} sets {field}: {version!r} which is not in "
                        f"support-matrix languages.{kind}={languages[kind]}"
                    )

    for kind, regex in (
        ("python", PYTHON_RE),
        ("node", NODE_RE),
        ("java", JAVA_RE),
        ("php", PHP_RE),
    ):
        versions = regex.findall(local)
        if primary[kind] not in versions:
            errors.append(
                f"local-regression.yml must use primary {kind} {primary[kind]}"
            )

    go_versions = []
    for name, text in workflows.items():
        go_versions.extend((name, version) for version in GO_RE.findall(text))
    for name, version in go_versions:
        if version != primary["go"]:
            errors.append(f"{name} sets go-version {version!r}, expected {primary['go']}")

    go_mod = (ROOT / "operator" / "go.mod").read_text().splitlines()
    module_line = next(line for line in go_mod if line.startswith("go "))
    if module_line != f"go {matrix['go_module']}":
        errors.append(f"operator/go.mod {module_line!r} != go {matrix['go_module']}")

    install_tekton = (ROOT / "scripts" / "install-tekton.sh").read_text()
    install_results = (ROOT / "scripts" / "install-tekton-results.sh").read_text()
    if f'TEKTON_PIPELINE_VERSION="${{TEKTON_PIPELINE_VERSION:-{cluster["tekton_pipelines"]}}}"' not in install_tekton:
        errors.append("install-tekton.sh pipeline pin does not match support-matrix")
    if f'TEKTON_TRIGGERS_VERSION="${{TEKTON_TRIGGERS_VERSION:-{cluster["tekton_triggers"]}}}"' not in install_tekton:
        errors.append("install-tekton.sh triggers pin does not match support-matrix")
    if f'TEKTON_RESULTS_VERSION="${{TEKTON_RESULTS_VERSION:-{cluster["tekton_results"]}}}"' not in install_results:
        errors.append("install-tekton-results.sh pin does not match support-matrix")

    kind_versions = set()
    for text in workflows.values():
        kind_versions.update(KIND_ENV_RE.findall(text))
        kind_versions.update(KIND_URL_RE.findall(text))
    if kind_versions and kind_versions != {cluster["kind"]}:
        errors.append(f"workflow Kind pins {sorted(kind_versions)} != {cluster['kind']}")

    required_doc_tokens = [
        *languages["python"],
        *languages["node"],
        *languages["java"],
        *languages["php"],
        primary["go"],
        matrix["go_module"],
        cluster["kind"],
        cluster["tekton_pipelines"],
        cluster["tekton_triggers"],
        cluster["tekton_results"],
        "compatibility.yml",
        "local-regression.yml",
    ]
    for token in required_doc_tokens:
        if str(token) not in doc:
            errors.append(f"SUPPORT-MATRIX.md is missing {token!r}")

    if 'workflow: ".github/workflows/compatibility.yml"' not in MATRIX_PATH.read_text():
        errors.append("support-matrix.yaml must name the compatibility workflow")
    if "schedule:" not in compat or "workflow_dispatch:" not in compat:
        errors.append("compatibility.yml must be scheduled and manually dispatchable")
    if "pull_request:" not in compat:
        errors.append("compatibility.yml must run on relevant pull requests")

    if errors:
        print("Support matrix drift:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("OK: documented support matrix matches automated jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
