#!/usr/bin/env python3
"""Strictly parse every tracked JSON and YAML file in the repository."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode
from yaml.resolver import BaseResolver

REPO_ROOT = Path(__file__).resolve().parent.parent
HELM_TEMPLATE_PREFIX = Path("helm/tekton-dag/templates")
STRUCTURED_SUFFIXES = {".json", ".yaml", ".yml"}


class DuplicateJsonKeyError(ValueError):
    """Raised when a JSON object defines the same key more than once."""


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeySafeLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeySafeLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping
)


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard numeric constant {value!r}")


def tracked_structured_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    paths = (
        Path(raw.decode("utf-8"))
        for raw in result.stdout.split(b"\0")
        if raw
    )
    return sorted(
        path
        for path in paths
        if path.suffix.lower() in STRUCTURED_SUFFIXES
        and HELM_TEMPLATE_PREFIX not in path.parents
    )


def parse_json(content: str) -> None:
    json.loads(
        content,
        object_pairs_hook=reject_duplicate_json_keys,
        parse_constant=reject_json_constant,
    )


def parse_yaml(content: str) -> None:
    list(yaml.load_all(content, Loader=UniqueKeySafeLoader))


def main() -> int:
    failures: list[tuple[Path, Exception]] = []
    paths = tracked_structured_files()
    for relative_path in paths:
        try:
            content = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            if relative_path.suffix.lower() == ".json":
                parse_json(content)
            else:
                parse_yaml(content)
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            failures.append((relative_path, exc))

    if failures:
        for path, error in failures:
            print(f"{path}: {error}", file=sys.stderr)
        print(
            f"Structured-file validation failed for {len(failures)} file(s).",
            file=sys.stderr,
        )
        return 1

    print(f"Validated {len(paths)} tracked JSON/YAML file(s).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as exc:
        print(f"Unable to enumerate tracked files: {exc}", file=sys.stderr)
        sys.exit(2)
