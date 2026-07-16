"""Tests for secrets/config Deployment injection helpers."""

from tekton_dag_common.deploy_injection import (
    build_env_from,
    build_volume_mounts_and_volumes,
    injection_summary,
    referenced_configmap_names,
    referenced_secret_names,
    sanitize_volume_name,
    validate_injection_refs,
)


def _app(**kwargs):
    base = {"name": "demo-bff"}
    base.update(kwargs)
    return base


def test_build_env_from_secrets_and_config():
    app = _app(
        secrets={"env-from": ["demo-bff-db", "demo-bff-api-keys"]},
        config={"env-from": ["demo-bff-config"]},
    )
    env = build_env_from(app)
    assert env == [
        {"secretRef": {"name": "demo-bff-db"}},
        {"secretRef": {"name": "demo-bff-api-keys"}},
        {"configMapRef": {"name": "demo-bff-config"}},
    ]


def test_build_env_from_empty():
    assert build_env_from(_app()) == []
    assert build_env_from(_app(secrets={}, config={})) == []


def test_volume_mounts_secrets_and_configmaps():
    app = _app(
        secrets={
            "volume-mounts": [
                {"secret": "demo-bff-tls", "mount-path": "/etc/tls"},
            ]
        },
        config={
            "volume-mounts": [
                {"configmap": "demo-bff-properties", "mount-path": "/etc/config"},
            ]
        },
    )
    mounts, volumes = build_volume_mounts_and_volumes(app)
    assert len(mounts) == 2
    assert mounts[0]["mountPath"] == "/etc/tls"
    assert mounts[0]["readOnly"] is True
    assert mounts[1]["mountPath"] == "/etc/config"
    assert volumes[0]["secret"]["secretName"] == "demo-bff-tls"
    assert volumes[1]["configMap"]["name"] == "demo-bff-properties"


def test_referenced_names():
    app = _app(
        secrets={
            "env-from": ["s1"],
            "volume-mounts": [{"secret": "s2", "mount-path": "/x"}],
        },
        config={
            "env-from": ["c1"],
            "volume-mounts": [{"configmap": "c2", "mount-path": "/y"}],
        },
    )
    assert referenced_secret_names(app) == ["s1", "s2"]
    assert referenced_configmap_names(app) == ["c1", "c2"]


def test_validate_injection_refs_missing():
    app = _app(secrets={"env-from": ["present", "missing"]})
    errs = validate_injection_refs(app, existing_secrets={"present"})
    assert len(errs) == 1
    assert "missing Secret missing" in errs[0]


def test_validate_injection_refs_ok():
    app = _app(
        secrets={"env-from": ["s1"]},
        config={"env-from": ["c1"]},
    )
    assert validate_injection_refs(
        app,
        existing_secrets={"s1"},
        existing_configmaps={"c1"},
    ) == []


def test_injection_summary():
    app = _app(secrets={"env-from": ["s1"]}, config={"env-from": ["c1"]})
    summary = injection_summary(app)
    assert summary["app"] == "demo-bff"
    assert summary["secrets"] == ["s1"]
    assert summary["configmaps"] == ["c1"]
    assert summary["envFrom_count"] == 2


def test_sanitize_volume_name_dns1123():
    name = sanitize_volume_name("secret", 0, "My_TLS.Cert")
    assert name == "secret-0-my-tls-cert"
    assert len(name) <= 63
    assert name == name.lower()


def test_sanitize_volume_name_truncates_long_names():
    long = "x" * 80
    name = sanitize_volume_name("secret", 0, long)
    assert len(name) <= 63
    assert name.startswith("secret-0-")


def test_unique_volume_name_disambiguates_collisions():
    from tekton_dag_common.deploy_injection import _unique_volume_name

    seen: set[str] = set()
    first = _unique_volume_name("secret", 0, "shared", seen)
    seen.add(first)
    # Pre-seed the natural name for index 1 so uniqueness kicks in
    natural_second = sanitize_volume_name("secret", 1, "shared")
    seen.add(natural_second)
    second = _unique_volume_name("secret", 1, "shared", seen)
    assert second != first
    assert second != natural_second
    assert len(second) <= 63
    assert second not in {first, natural_second} or second == natural_second + "-1" or "-1" in second


def test_skips_incomplete_volume_mount_entries():
    app = _app(
        secrets={
            "volume-mounts": [
                {"secret": "ok", "mount-path": "/etc/ok"},
                {"secret": "missing-path"},
                {"mount-path": "/no-secret"},
            ]
        },
        config={
            "volume-mounts": [
                {"configmap": "cm-ok", "mount-path": "/etc/cm"},
                {"configmap": "no-path"},
            ]
        },
    )
    mounts, volumes = build_volume_mounts_and_volumes(app)
    assert len(mounts) == 2
    assert len(volumes) == 2
    assert mounts[0]["mountPath"] == "/etc/ok"
    assert mounts[1]["mountPath"] == "/etc/cm"
