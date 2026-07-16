"""Resolve promote targets from stacks/registries.yaml (M13)."""

from __future__ import annotations

import logging
import os
from typing import Any

import yaml

logger = logging.getLogger("orchestrator.registries")


def load_registries(path: str) -> list[dict[str, Any]]:
    """Load registry entries from a YAML file. Missing/invalid → []."""
    if not path or not os.path.isfile(path):
        return []
    try:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:
        logger.error("Failed to load registries from %s: %s", path, exc)
        return []
    entries = data.get("registries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return []
    return [e for e in entries if isinstance(e, dict) and e.get("name")]


def resolve_promote_target(
    *,
    target_environment: str,
    target_registry: str = "",
    credentials_secret: str = "",
    registries: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    """
    Resolve registry URL and credentials for a promote request.

    Explicit request fields win; otherwise match ``environment`` (then ``name``)
    in the registries list.
    """
    env = (target_environment or "").strip()
    url = (target_registry or "").strip()
    creds = (credentials_secret or "").strip()
    matched = None
    for entry in registries or []:
        entry_env = str(entry.get("environment") or entry.get("name") or "")
        if env and entry_env == env:
            matched = entry
            break
    if matched is None and env:
        for entry in registries or []:
            if str(entry.get("name") or "") == env:
                matched = entry
                break
    if matched:
        if not url:
            url = str(matched.get("url") or "")
        if not creds:
            creds = str(matched.get("credentials-secret") or "")
    return {
        "target_environment": env,
        "target_registry": url,
        "credentials_secret": creds,
        "registry_name": str((matched or {}).get("name") or ""),
    }
