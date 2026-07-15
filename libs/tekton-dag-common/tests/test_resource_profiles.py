"""Tests for per-tool resource profiles."""

from tekton_dag_common.resource_profiles import (
    get_profile,
    kaniko_resources,
    resources_for_app,
)


def test_maven_default_larger_than_npm():
    maven = get_profile("maven")
    npm = get_profile("npm")
    assert maven["requests"]["memory"] == "2Gi"
    assert npm["requests"]["memory"] == "512Mi"


def test_stack_override_merges():
    profile = get_profile(
        "npm",
        overrides={"requests": {"memory": "1Gi"}, "limits": {"cpu": "2"}},
    )
    assert profile["requests"]["memory"] == "1Gi"
    assert profile["requests"]["cpu"] == "500m"  # preserved
    assert profile["limits"]["cpu"] == "2"


def test_resources_for_app():
    app = {
        "name": "api",
        "build": {
            "tool": "maven",
            "build-command": "mvn package",
            "resources": {"limits": {"memory": "8Gi"}},
        },
    }
    res = resources_for_app(app)
    assert res["limits"]["memory"] == "8Gi"
    assert res["requests"]["cpu"] == "1"


def test_kaniko_resources():
    res = kaniko_resources({"requests": {"cpu": "1"}})
    assert res["requests"]["cpu"] == "1"
    assert res["limits"]["memory"] == "4Gi"
