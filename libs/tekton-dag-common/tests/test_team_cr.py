"""Team YAML ↔ CR conversion."""

from tekton_dag_common.team_cr import cr_to_team_config, overlay_team_configs, team_yaml_to_cr


def test_round_trip_overlay():
    yaml_doc = {
        "name": "default",
        "namespace": "tekton-pipelines",
        "cluster": "kind-tekton-stack",
        "imageRegistry": "localhost:5000",
        "stacks": ["stacks/stack-one.yaml"],
    }
    cr = team_yaml_to_cr(yaml_doc, team_dir_name="default")
    assert cr["kind"] == "Team"
    assert cr["spec"]["targetNamespace"] == "tekton-pipelines"
    cfg = cr_to_team_config(cr)
    assert cfg["namespace"] == "tekton-pipelines"
    assert cfg["imageRegistry"] == "localhost:5000"

    teams = {"default": {"name": "default", "imageRegistry": "old"}}
    cr["spec"]["imageRegistry"] = "localhost:5000"
    out = overlay_team_configs(teams, [cr])
    assert out["default"]["imageRegistry"] == "localhost:5000"


def test_overlay_adds_cr_only_team():
    cr = {
        "metadata": {"name": "east"},
        "spec": {"name": "east", "cluster": "staging-east", "targetNamespace": "team-east"},
    }
    out = overlay_team_configs({}, [cr])
    assert out["east"]["cluster"] == "staging-east"
    assert out["east"]["namespace"] == "team-east"


def test_overlay_filter():
    cr = {"spec": {"name": "east", "cluster": "x"}}
    out = overlay_team_configs({}, [cr], team_filter="default")
    assert out == {}
