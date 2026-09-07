"""Team YAML → tektondag.io/v1alpha1 Team CR."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def team_yaml_to_cr(
    doc: dict[str, Any],
    *,
    team_dir_name: str,
    namespace: str = "tekton-pipelines",
) -> dict[str, Any]:
    name = str(doc.get("name") or team_dir_name)
    spec: dict[str, Any] = {"name": name}
    for src, dst in (
        ("namespace", "targetNamespace"),
        ("cluster", "cluster"),
        ("imageRegistry", "imageRegistry"),
        ("cacheRepo", "cacheRepo"),
        ("interceptBackend", "interceptBackend"),
    ):
        if doc.get(src):
            spec[dst] = str(doc[src])
    if doc.get("maxConcurrentRuns") is not None:
        spec["maxConcurrentRuns"] = int(doc["maxConcurrentRuns"])
    if doc.get("maxParallelBuilds") is not None:
        spec["maxParallelBuilds"] = int(doc["maxParallelBuilds"])
    stacks = doc.get("stacks") or []
    if stacks:
        spec["stacks"] = [str(s) for s in stacks]
    return {
        "apiVersion": "tektondag.io/v1alpha1",
        "kind": "Team",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/part-of": "tekton-job-standardization",
            },
        },
        "spec": spec,
    }


def iter_team_files(teams_dir: Path) -> list[tuple[str, Path]]:
    found = []
    if not teams_dir.is_dir():
        return found
    for team_dir in sorted(p for p in teams_dir.iterdir() if p.is_dir()):
        cfg = team_dir / "team.yaml"
        if cfg.is_file():
            found.append((team_dir.name, cfg))
    return found
