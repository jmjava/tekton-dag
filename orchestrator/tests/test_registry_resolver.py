"""Tests for promote target resolution from registries.yaml."""

from pathlib import Path

import yaml

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


def test_load_registries_invalid_yaml_returns_empty(tmp_path, monkeypatch):
    path = tmp_path / "registries.yaml"
    path.write_text("registries: []")
    monkeypatch.setattr(
        yaml, "safe_load", lambda _stream: (_ for _ in ()).throw(ValueError("bad yaml"))
    )

    assert rr.load_registries(str(path)) == []


def test_load_registries_filters_invalid_entries(tmp_path):
    path = tmp_path / "registries.yaml"
    path.write_text(
        """
registries:
  - name: production
    url: registry.example/production
  - url: registry.example/unnamed
  - plain-string
  - {}
"""
    )

    assert rr.load_registries(str(path)) == [
        {"name": "production", "url": "registry.example/production"}
    ]


def test_load_registries_rejects_non_mapping_and_non_list(tmp_path):
    path = tmp_path / "registries.yaml"
    path.write_text("- production\n- staging\n")
    assert rr.load_registries(str(path)) == []

    path.write_text("registries: production\n")
    assert rr.load_registries(str(path)) == []


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


def test_resolve_promote_target_falls_back_to_registry_name():
    registries = [
        {
            "name": "prod",
            "environment": "production",
            "url": "registry.example/prod",
        },
        {
            "name": "staging",
            "url": "registry.example/staging",
            "credentials-secret": "staging-creds",
        },
    ]

    target = rr.resolve_promote_target(
        target_environment=" staging ",
        registries=registries,
    )

    assert target == {
        "target_environment": "staging",
        "target_registry": "registry.example/staging",
        "credentials_secret": "staging-creds",
        "registry_name": "staging",
    }


def test_resolve_promote_target_unmatched_environment():
    assert rr.resolve_promote_target(
        target_environment="unknown",
        registries=[{"name": "production", "url": "registry.example/prod"}],
    ) == {
        "target_environment": "unknown",
        "target_registry": "",
        "credentials_secret": "",
        "registry_name": "",
    }
