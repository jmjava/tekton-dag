"""Per-tool build resource profiles (M13 pillar 2).

Defines default CPU/memory requests and limits for compile and Kaniko steps.
Stack YAML may override via ``build.resources``; Helm may override via values.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# tool -> {requests, limits}
DEFAULT_PROFILES: dict[str, dict[str, dict[str, str]]] = {
    "maven": {
        "requests": {"cpu": "1", "memory": "2Gi"},
        "limits": {"cpu": "2", "memory": "4Gi"},
    },
    "gradle": {
        "requests": {"cpu": "1", "memory": "2Gi"},
        "limits": {"cpu": "4", "memory": "4Gi"},
    },
    "npm": {
        "requests": {"cpu": "500m", "memory": "512Mi"},
        "limits": {"cpu": "1", "memory": "1Gi"},
    },
    "pip": {
        "requests": {"cpu": "250m", "memory": "512Mi"},
        "limits": {"cpu": "1", "memory": "1Gi"},
    },
    "composer": {
        "requests": {"cpu": "250m", "memory": "512Mi"},
        "limits": {"cpu": "1", "memory": "1Gi"},
    },
    "kaniko": {
        "requests": {"cpu": "500m", "memory": "1Gi"},
        "limits": {"cpu": "2", "memory": "4Gi"},
    },
}


def get_profile(
    tool: str,
    *,
    overrides: dict[str, Any] | None = None,
    profiles: dict[str, dict[str, dict[str, str]]] | None = None,
) -> dict[str, dict[str, str]]:
    """
    Resolve a resource profile for a build tool.

    ``overrides`` may be a partial ``{requests: {...}, limits: {...}}`` from
    stack ``build.resources``.
    """
    base = deepcopy((profiles or DEFAULT_PROFILES).get(tool) or DEFAULT_PROFILES["npm"])
    if not overrides:
        return base
    for section in ("requests", "limits"):
        if section in overrides and isinstance(overrides[section], dict):
            base.setdefault(section, {}).update(
                {k: str(v) for k, v in overrides[section].items()}
            )
    return base


def resources_for_app(app: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Resolve compile resources for a stack app entry."""
    build = app.get("build") or {}
    tool = build.get("tool", "npm")
    return get_profile(tool, overrides=build.get("resources"))


def kaniko_resources(overrides: dict[str, Any] | None = None) -> dict[str, dict[str, str]]:
    """Resolve Kaniko/containerize resource profile."""
    return get_profile("kaniko", overrides=overrides)
