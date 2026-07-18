"""Lightweight checks that stacks/schema.json exposes M13 fields."""

import json
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[3] / "stacks" / "schema.json"


def test_schema_has_secrets_config_resources_registries():
    schema = json.loads(SCHEMA.read_text())
    app_props = schema["properties"]["apps"]["items"]["properties"]
    assert "secrets" in app_props
    assert "config" in app_props
    assert "env-from" in app_props["secrets"]["properties"]
    assert "volume-mounts" in app_props["secrets"]["properties"]
    assert "env-from" in app_props["config"]["properties"]
    assert "resources" in app_props["build"]["properties"]
    assert "registries" in schema["properties"]
