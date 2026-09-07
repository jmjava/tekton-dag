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


def cr_to_team_config(cr: dict[str, Any]) -> dict[str, Any]:
    """Map a Team CR object to the Git team.yaml dict shape used by Flask/GUI."""
    spec = cr.get("spec") or {}
    name = str(spec.get("name") or (cr.get("metadata") or {}).get("name") or "")
    cfg: dict[str, Any] = {"name": name}
    if spec.get("targetNamespace"):
        cfg["namespace"] = str(spec["targetNamespace"])
    if spec.get("cluster"):
        cfg["cluster"] = str(spec["cluster"])
    if spec.get("imageRegistry"):
        cfg["imageRegistry"] = str(spec["imageRegistry"])
    if spec.get("cacheRepo"):
        cfg["cacheRepo"] = str(spec["cacheRepo"])
    if spec.get("interceptBackend"):
        cfg["interceptBackend"] = str(spec["interceptBackend"])
    if spec.get("maxConcurrentRuns") is not None:
        cfg["maxConcurrentRuns"] = int(spec["maxConcurrentRuns"])
    if spec.get("maxParallelBuilds") is not None:
        cfg["maxParallelBuilds"] = int(spec["maxParallelBuilds"])
    stacks = spec.get("stacks") or []
    if stacks:
        cfg["stacks"] = [str(s) for s in stacks]
    return cfg


def overlay_team_configs(
    teams: dict[str, dict[str, Any]],
    crs: list[dict[str, Any]],
    *,
    team_filter: str = "*",
) -> dict[str, dict[str, Any]]:
    """Merge Team CRs onto YAML-loaded teams. CR fields win when set."""
    out = dict(teams)
    for cr in crs:
        cfg = cr_to_team_config(cr)
        name = cfg.get("name") or ""
        if not name:
            continue
        if team_filter != "*" and name != team_filter:
            continue
        merged = dict(out.get(name) or {})
        for key, val in cfg.items():
            if val is not None and val != "" and val != []:
                merged[key] = val
        out[name] = merged
    return out


def iter_team_files(teams_dir: Path) -> list[tuple[str, Path]]:
    found = []
    if not teams_dir.is_dir():
        return found
    for team_dir in sorted(p for p in teams_dir.iterdir() if p.is_dir()):
        cfg = team_dir / "team.yaml"
        if cfg.is_file():
            found.append((team_dir.name, cfg))
    return found
