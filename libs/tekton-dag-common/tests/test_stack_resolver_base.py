"""Tests for stack_resolver_base."""

from pathlib import Path

import yaml

from tekton_dag_common.stack_resolver_base import (
    extract_repo_map,
    get_build_apps,
    load_stack_yaml,
    parse_apps,
)


def test_load_stack_yaml_valid(tmp_path: Path):
    f = tmp_path / "stack.yaml"
    data = {
        "name": "demo",
        "apps": [{"name": "api", "repo": "org/api", "role": "backend"}],
    }
    f.write_text(yaml.safe_dump(data), encoding="utf-8")
    loaded = load_stack_yaml(f)
    assert loaded == data


def test_load_stack_yaml_missing_file(tmp_path: Path):
    assert load_stack_yaml(tmp_path / "nope.yaml") is None


def test_load_stack_yaml_invalid_yaml(tmp_path: Path):
    f = tmp_path / "bad.yaml"
    f.write_text("{ not: valid yaml [[[\n", encoding="utf-8")
    assert load_stack_yaml(f) is None


def test_extract_repo_map():
    stack = {
        "apps": [
            {"name": "fe", "repo": "acme/tekton-dag-vue-fe", "role": "frontend"},
            {"name": "api", "repo": "acme/api-go", "role": "backend"},
        ]
    }
    m = extract_repo_map("stacks/demo.yaml", stack)
    assert m == {
        "tekton-dag-vue-fe": {
            "stack_file": "stacks/demo.yaml",
            "app_name": "fe",
            "repo": "acme/tekton-dag-vue-fe",
        },
        "api-go": {
            "stack_file": "stacks/demo.yaml",
            "app_name": "api",
            "repo": "acme/api-go",
        },
    }


def test_extract_repo_map_missing_repo():
    stack = {
        "apps": [
            {"name": "only-name", "role": "x"},
            {"name": "ok", "repo": "org/ok"},
        ]
    }
    m = extract_repo_map("stacks/x.yaml", stack)
    assert m == {
        "ok": {
            "stack_file": "stacks/x.yaml",
            "app_name": "ok",
            "repo": "org/ok",
        }
    }


def test_parse_apps():
    stack = {
        "apps": [
            {"name": "a", "repo": "o/a", "role": "r1"},
            {"name": "b", "repo": "o/b"},
        ]
    }
    assert parse_apps(stack) == [
        {"name": "a", "repo": "o/a", "role": "r1"},
        {"name": "b", "repo": "o/b", "role": ""},
    ]


def test_get_build_apps():
    stack = {
        "apps": [
            {"name": "first", "repo": "o/f"},
            {"name": "second", "repo": "o/s"},
        ]
    }
    assert get_build_apps(stack) == "first second"


def test_get_build_apps_empty():
    assert get_build_apps({}) == ""
    assert get_build_apps({"apps": []}) == ""
    assert get_build_apps({"apps": [{"repo": "o/x"}]}) == ""
