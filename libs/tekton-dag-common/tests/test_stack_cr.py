"""Stack YAML → Stack CR conversion."""

from tekton_dag_common.stack_cr import stack_ref_from_file, stack_yaml_to_cr
from tekton_dag_common.stackrun_builder import build_stackrun
from tekton_dag_common.team_cr import team_yaml_to_cr


def test_stack_ref_from_file():
    assert stack_ref_from_file("stacks/stack-one.yaml") == "stack-one"
    assert stack_ref_from_file("stack-two-vendor.yml") == "stack-two-vendor"


def test_stack_yaml_to_cr_stack_one():
    doc = {
        "name": "stack-one",
        "description": "demo",
        "propagation": {"header-name": "x-dev-session", "strategy": "w3c-baggage"},
        "defaults": {"namespace": "staging", "image-registry": "localhost:5000"},
        "apps": [
            {
                "name": "demo-fe",
                "repo": "jmjava/tekton-dag-vue-fe",
                "role": "frontend",
                "propagation-role": "originator",
                "build": {"tool": "npm", "node-version": "22", "build-command": "npm ci"},
                "downstream": ["demo-api"],
                "secrets": {"env-from": ["fe-secrets"]},
            },
            {
                "name": "demo-api",
                "repo": "jmjava/api",
                "role": "persistence",
                "propagation-role": "terminal",
                "build": {"tool": "maven", "java-version": "21", "build-command": "mvn -B"},
            },
        ],
    }
    cr = stack_yaml_to_cr(doc, namespace="tekton-pipelines", stack_file="stacks/stack-one.yaml")
    assert cr["kind"] == "Stack"
    assert cr["metadata"]["name"] == "stack-one"
    assert cr["spec"]["stackFile"] == "stacks/stack-one.yaml"
    assert cr["spec"]["propagation"]["headerName"] == "x-dev-session"
    assert cr["spec"]["defaults"]["imageRegistry"] == "localhost:5000"
    assert cr["spec"]["apps"][0]["propagationRole"] == "originator"
    assert cr["spec"]["apps"][0]["build"]["nodeVersion"] == "22"
    assert cr["spec"]["apps"][0]["secrets"]["envFrom"] == ["fe-secrets"]


def test_build_stackrun_sets_stack_ref():
    sr = build_stackrun(mode="bootstrap", stack_file="stacks/stack-one.yaml")
    assert sr["spec"]["stackRef"] == "stack-one"
    assert sr["spec"]["mode"] == "bootstrap"


def test_team_yaml_to_cr():
    cr = team_yaml_to_cr(
        {
            "name": "default",
            "namespace": "tekton-pipelines",
            "imageRegistry": "localhost:5000",
            "stacks": ["stacks/stack-one.yaml"],
        },
        team_dir_name="default",
    )
    assert cr["kind"] == "Team"
    assert cr["spec"]["targetNamespace"] == "tekton-pipelines"
    assert cr["spec"]["stacks"] == ["stacks/stack-one.yaml"]
