#!/usr/bin/env python3
"""Fail if Dependabot can still open breaking updates, or operator Go pins drift."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MAJOR = "version-update:semver-major"
MINOR = "version-update:semver-minor"


def _fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def check_dependabot() -> None:
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())
    for entry in config["updates"]:
        eco = entry["package-ecosystem"]
        loc = f"{eco}:{entry.get('directory', '/')}"
        if entry.get("rebase-strategy") != "disabled":
            _fail(f"{loc} must set rebase-strategy: disabled")

        groups = entry.get("groups") or {}
        if not groups:
            _fail(f"{loc} must group updates")
        for name, group in groups.items():
            types = set(group.get("update-types") or [])
            if "major" in types:
                _fail(f"{name} must not auto-open majors")
            if not types <= {"minor", "patch"}:
                _fail(f"{name} has unexpected update-types: {types}")
            if eco == "gomod" and types != {"patch"}:
                _fail(f"{name} must be patch-only")

        ignore_types: set[str] = set()
        for rule in entry.get("ignore") or []:
            if rule.get("dependency-name") == "*":
                ignore_types.update(rule.get("update-types") or [])
        if MAJOR not in ignore_types:
            _fail(f"{loc} must ignore * semver-major (groups do not block ungrouped majors)")
        if eco == "gomod" and MINOR not in ignore_types:
            _fail(f"{loc} must ignore * semver-minor (ginkgo/gomega minors bump Go)")


def check_operator_go_pin() -> None:
    dockerfile = (ROOT / "operator/Dockerfile").read_text()
    gomod = (ROOT / "operator/go.mod").read_text()
    workflow = (ROOT / ".github/workflows/operator.yml").read_text()

    image = re.search(r"FROM docker.io/golang:([0-9]+\.[0-9]+)", dockerfile)
    module = re.search(r"^go ([0-9]+\.[0-9]+)", gomod, re.M)
    if not image or not module:
        _fail("could not parse operator Dockerfile / go.mod Go versions")
    if image.group(1) != module.group(1):
        _fail(
            f"operator Dockerfile golang:{image.group(1)} != go.mod {module.group(1)}"
        )
    if "Builder Go matches go.mod" not in workflow:
        _fail("operator workflow must check Dockerfile Go against go.mod")


def main() -> None:
    check_dependabot()
    check_operator_go_pin()
    print("CI policy checks passed")


if __name__ == "__main__":
    main()
