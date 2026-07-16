"""Validate M13 stack fixture against stacks/schema.json (requires jsonschema)."""

import json
from pathlib import Path

import pytest
import yaml

jsonschema = pytest.importorskip("jsonschema")

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = ROOT / "stacks" / "schema.json"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "app_with_secrets_config.yaml"


def test_fixture_validates_against_stack_schema():
    schema = json.loads(SCHEMA.read_text())
    data = yaml.safe_load(FIXTURE.read_text())
    jsonschema.validate(instance=data, schema=schema)


def test_fixture_injection_helpers_match_schema_app():
    from tekton_dag_common.deploy_injection import (
        build_env_from,
        referenced_configmap_names,
        referenced_secret_names,
    )
    from tekton_dag_common.resource_profiles import resources_for_app

    data = yaml.safe_load(FIXTURE.read_text())
    app = data["apps"][0]
    assert referenced_secret_names(app) == ["demo-bff-db", "demo-bff-api-keys", "demo-bff-tls"]
    assert referenced_configmap_names(app) == ["demo-bff-config", "demo-bff-properties"]
    env = build_env_from(app)
    assert {"secretRef": {"name": "demo-bff-db"}} in env
    assert {"configMapRef": {"name": "demo-bff-config"}} in env
    res = resources_for_app(app)
    assert res["requests"]["memory"] == "3Gi"
    assert res["limits"]["memory"] == "6Gi"


def test_invalid_secrets_block_rejected():
    schema = json.loads(SCHEMA.read_text())
    bad = {
        "name": "bad",
        "apps": [
            {
                "name": "x",
                "repo": "o/r",
                "role": "standalone",
                "build": {"tool": "npm", "build-command": "npm ci"},
                "secrets": {
                    "volume-mounts": [{"secret": "only-secret"}],  # missing mount-path
                },
            }
        ],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=schema)
