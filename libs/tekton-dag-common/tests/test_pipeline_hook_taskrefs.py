"""S38: Tekton v1.6 rejects taskRef.name: $(params.*) at apply time."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
PIPELINES = [
    "pipeline/stack-bootstrap-pipeline.yaml",
    "pipeline/stack-merge-pipeline.yaml",
    "pipeline/stack-pr-pipeline.yaml",
]
HOOK_TASKS = {"hook-pre-build", "hook-post-build", "hook-pre-test", "hook-post-test"}


def _iter_pipeline_tasks(spec: dict):
    yield from spec.get("tasks") or []
    yield from spec.get("finally") or []


def test_no_param_substitution_in_taskref_name():
    for rel in sorted((ROOT / "pipeline").glob("*.yaml")):
        for data in yaml.safe_load_all(rel.read_text()):
            if not isinstance(data, dict) or data.get("kind") != "Pipeline":
                continue
            for task in _iter_pipeline_tasks(data.get("spec") or {}):
                ref = task.get("taskRef") or {}
                name = ref.get("name")
                if isinstance(name, str):
                    assert "$(params." not in name, (
                        f"{rel.name} task {task.get('name')}: "
                        "taskRef.name cannot be $(params.*) on Tekton v1.6+"
                    )


def test_hook_tasks_use_cluster_resolver():
    found = set()
    for rel in PIPELINES:
        data = yaml.safe_load((ROOT / rel).read_text())
        hook_params = {
            param["name"]: param.get("default")
            for param in data["spec"].get("params") or []
            if param["name"] in {
                "pre-build-task",
                "post-build-task",
                "pre-test-task",
                "post-test-task",
            }
        }
        assert all(value == "tekton-dag-hook-noop" for value in hook_params.values())
        for task in _iter_pipeline_tasks(data.get("spec") or {}):
            if task.get("name") not in HOOK_TASKS:
                continue
            found.add(task["name"])
            ref = task.get("taskRef") or {}
            assert ref.get("resolver") == "cluster", (
                f"{rel} {task['name']} must use cluster resolver"
            )
            params = {p["name"]: p.get("value") for p in ref.get("params") or []}
            assert params.get("kind") == "task"
            assert params.get("name", "").startswith("$(params.")
            assert task["when"][0]["values"] == ["tekton-dag-hook-noop"]
    assert found == HOOK_TASKS


def test_hook_noop_sentinel_is_installed_and_accepts_all_hook_inputs():
    task = yaml.safe_load((ROOT / "tasks/tekton-dag-hook-noop.yaml").read_text())

    assert task["metadata"]["name"] == "tekton-dag-hook-noop"
    assert {param["name"] for param in task["spec"]["params"]} == {
        "stack-json",
        "build-apps",
        "built-images",
        "image-registry",
    }
    assert task["spec"]["workspaces"] == [{"name": "source", "optional": True}]
