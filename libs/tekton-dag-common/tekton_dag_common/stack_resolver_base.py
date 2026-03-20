"""Shared stack YAML parsing and app/repo helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_stack_yaml(path: str | Path) -> dict[str, Any] | None:
    """
    Load a single stack YAML file.

    Returns the parsed mapping, or None if the file is missing, invalid YAML,
    or does not parse to a dict.
    """
    p = Path(path)
    if not p.is_file():
        return None
    try:
        with p.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.debug("Invalid YAML in %s: %s", p, e)
        return None
    except OSError as e:
        logger.debug("Could not read %s: %s", p, e)
        return None
    if not isinstance(data, dict):
        return None
    return data


def extract_repo_map(
    stack_file_key: str, stack_dict: dict[str, Any]
) -> dict[str, dict[str, str]]:
    """
    Build repo short name -> {stack_file, app_name, repo} from a stack's apps.

    Apps without both ``repo`` and ``name`` are skipped (same rules as StackResolver).
    """
    out: dict[str, dict[str, str]] = {}
    for app in stack_dict.get("apps", []) or []:
        if not isinstance(app, dict):
            continue
        repo = app.get("repo", "") or ""
        app_name = app.get("name", "") or ""
        if not repo or not app_name:
            continue
        repo_short = repo.split("/")[-1] if "/" in repo else repo
        out[repo_short] = {
            "stack_file": stack_file_key,
            "app_name": app_name,
            "repo": repo,
        }
    return out


def parse_apps(stack_dict: dict[str, Any]) -> list[dict[str, str]]:
    """Return app summaries: ``[{name, repo, role}, ...]``."""
    result: list[dict[str, str]] = []
    for app in stack_dict.get("apps", []) or []:
        if not isinstance(app, dict):
            continue
        result.append(
            {
                "name": app.get("name", "") or "",
                "repo": app.get("repo", "") or "",
                "role": app.get("role", "") or "",
            }
        )
    return result


def get_build_apps(stack_dict: dict[str, Any]) -> str:
    """Space-separated app names from the stack's apps list (or empty string)."""
    names: list[str] = []
    for app in stack_dict.get("apps", []) or []:
        if not isinstance(app, dict):
            continue
        n = app.get("name")
        if n:
            names.append(str(n))
    return " ".join(names)
