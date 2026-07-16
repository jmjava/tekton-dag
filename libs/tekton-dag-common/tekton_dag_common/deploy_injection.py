"""Build Kubernetes Deployment injection fragments from stack app secrets/config.

M13 pillars 6–7: stack YAML ``secrets`` and ``config`` blocks are converted into
``envFrom``, ``volumeMounts``, and ``volumes`` for generated Deployments.
"""

from __future__ import annotations

import re
from typing import Any

_DNS1123_RE = re.compile(r"[^a-z0-9-]+")


def sanitize_volume_name(prefix: str, index: int, resource_name: str) -> str:
    """Build a DNS-1123-ish volume name (lowercase, alnum/dash, <= 63 chars)."""
    raw = f"{prefix}-{index}-{resource_name}".lower().replace("_", "-")
    cleaned = _DNS1123_RE.sub("-", raw).strip("-")
    if not cleaned:
        cleaned = f"{prefix}-{index}"
    return cleaned[:63].strip("-") or f"{prefix}-{index}"


def _env_from_secret(name: str) -> dict[str, Any]:
    return {"secretRef": {"name": name}}


def _env_from_configmap(name: str) -> dict[str, Any]:
    return {"configMapRef": {"name": name}}


def build_env_from(app: dict[str, Any]) -> list[dict[str, Any]]:
    """Return envFrom entries from app secrets.env-from and config.env-from."""
    env_from: list[dict[str, Any]] = []
    secrets = app.get("secrets") or {}
    for name in secrets.get("env-from") or []:
        if name:
            env_from.append(_env_from_secret(str(name)))
    config = app.get("config") or {}
    for name in config.get("env-from") or []:
        if name:
            env_from.append(_env_from_configmap(str(name)))
    return env_from


def build_volume_mounts_and_volumes(
    app: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (volumeMounts, volumes) from secrets/config volume-mounts."""
    mounts: list[dict[str, Any]] = []
    volumes: list[dict[str, Any]] = []
    seen: set[str] = set()

    secrets = app.get("secrets") or {}
    for i, entry in enumerate(secrets.get("volume-mounts") or []):
        secret_name = entry.get("secret") if isinstance(entry, dict) else None
        mount_path = entry.get("mount-path") if isinstance(entry, dict) else None
        if not secret_name or not mount_path:
            continue
        vol_name = sanitize_volume_name("secret", i, str(secret_name))
        if vol_name in seen:
            continue
        seen.add(vol_name)
        mounts.append({"name": vol_name, "mountPath": mount_path, "readOnly": True})
        volumes.append({"name": vol_name, "secret": {"secretName": secret_name}})

    config = app.get("config") or {}
    for i, entry in enumerate(config.get("volume-mounts") or []):
        cm_name = entry.get("configmap") if isinstance(entry, dict) else None
        mount_path = entry.get("mount-path") if isinstance(entry, dict) else None
        if not cm_name or not mount_path:
            continue
        vol_name = sanitize_volume_name("cm", i, str(cm_name))
        if vol_name in seen:
            continue
        seen.add(vol_name)
        mounts.append({"name": vol_name, "mountPath": mount_path, "readOnly": True})
        volumes.append({"name": vol_name, "configMap": {"name": cm_name}})

    return mounts, volumes


def referenced_secret_names(app: dict[str, Any]) -> list[str]:
    """Secret names referenced by an app (env-from + volume mounts)."""
    names: list[str] = []
    secrets = app.get("secrets") or {}
    for name in secrets.get("env-from") or []:
        if name:
            names.append(str(name))
    for entry in secrets.get("volume-mounts") or []:
        if isinstance(entry, dict) and entry.get("secret"):
            names.append(str(entry["secret"]))
    return names


def referenced_configmap_names(app: dict[str, Any]) -> list[str]:
    """ConfigMap names referenced by an app (env-from + volume mounts)."""
    names: list[str] = []
    config = app.get("config") or {}
    for name in config.get("env-from") or []:
        if name:
            names.append(str(name))
    for entry in config.get("volume-mounts") or []:
        if isinstance(entry, dict) and entry.get("configmap"):
            names.append(str(entry["configmap"]))
    return names


def validate_injection_refs(
    app: dict[str, Any],
    *,
    existing_secrets: set[str] | None = None,
    existing_configmaps: set[str] | None = None,
) -> list[str]:
    """
    Return human-readable errors for missing Secrets/ConfigMaps.

    When existing_* is None, that resource type is not checked.
    """
    errors: list[str] = []
    app_name = app.get("name", "<unknown>")
    if existing_secrets is not None:
        for name in referenced_secret_names(app):
            if name not in existing_secrets:
                errors.append(f"app {app_name}: missing Secret {name}")
    if existing_configmaps is not None:
        for name in referenced_configmap_names(app):
            if name not in existing_configmaps:
                errors.append(f"app {app_name}: missing ConfigMap {name}")
    return errors


def injection_summary(app: dict[str, Any]) -> dict[str, Any]:
    """Compact summary for API/GUI status panels."""
    env_from = build_env_from(app)
    mounts, volumes = build_volume_mounts_and_volumes(app)
    return {
        "app": app.get("name"),
        "secrets": referenced_secret_names(app),
        "configmaps": referenced_configmap_names(app),
        "envFrom_count": len(env_from),
        "volumeMount_count": len(mounts),
        "volume_count": len(volumes),
        "envFrom": env_from,
        "volumeMounts": mounts,
        "volumes": volumes,
    }
