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
    assert found == HOOK_TASKS
