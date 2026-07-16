"""Tests for promote target resolution from registries.yaml."""

from pathlib import Path

import registry_resolver as rr


def test_load_registries_from_repo_file():
    path = Path(__file__).resolve().parents[2] / "stacks" / "registries.yaml"
    entries = rr.load_registries(str(path))
    assert len(entries) >= 2
    names = {e["name"] for e in entries}
    assert "staging" in names
    assert "production" in names


def test_load_registries_missing_file():
    assert rr.load_registries("/no/such/registries.yaml") == []


def test_resolve_promote_target_from_environment():
    registries = [
        {
            "name": "prod",
            "url": "reg.example/prod",
            "credentials-secret": "prod-creds",
            "environment": "production",
        }
    ]
    target = rr.resolve_promote_target(
        target_environment="production",
        registries=registries,
    )
    assert target["target_registry"] == "reg.example/prod"
    assert target["credentials_secret"] == "prod-creds"
    assert target["registry_name"] == "prod"


def test_resolve_promote_target_request_overrides_file():
    registries = [
        {
            "name": "staging",
            "url": "from-file",
            "credentials-secret": "file-creds",
            "environment": "staging",
        }
    ]
    target = rr.resolve_promote_target(
        target_environment="staging",
        target_registry="explicit-reg",
        credentials_secret="explicit-creds",
        registries=registries,
    )
    assert target["target_registry"] == "explicit-reg"
    assert target["credentials_secret"] == "explicit-creds"
