"""Convert Git stack YAML (kebab-case) to tektondag.io/v1alpha1 Stack CRs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

SKIP_FILES = frozenset({"registries.yaml", "registry.yaml", "versions.yaml"})


def stack_ref_from_file(stack_file: str) -> str:
    """stacks/stack-one.yaml -> stack-one."""
    if not stack_file:
        return ""
    base = stack_file.rsplit("/", 1)[-1]
    if base.endswith(".yaml"):
        return base[: -len(".yaml")]
    if base.endswith(".yml"):
        return base[: -len(".yml")]
    return base


def _injection(block: dict | None, *, secret: bool) -> dict | None:
    if not isinstance(block, dict):
        return None
    out: dict[str, Any] = {}
    env_from = block.get("env-from") or []
    if env_from:
        out["envFrom"] = [str(n) for n in env_from if n]
    mounts = []
    for entry in block.get("volume-mounts") or []:
        if not isinstance(entry, dict):
            continue
        mount_path = entry.get("mount-path")
        if not mount_path:
            continue
        item: dict[str, str] = {"mountPath": str(mount_path)}
        if secret and entry.get("secret"):
            item["secret"] = str(entry["secret"])
        if not secret and entry.get("configmap"):
            item["configMap"] = str(entry["configmap"])
        mounts.append(item)
    if mounts:
        out["volumeMounts"] = mounts
    return out or None


def stack_yaml_to_cr(
    doc: dict[str, Any],
    *,
    namespace: str = "tekton-pipelines",
    stack_file: str = "",
    git_url: str = "",
) -> dict[str, Any]:
    """Build a Stack CR dict from a parsed stacks/*.yaml document."""
    name = str(doc.get("name") or stack_ref_from_file(stack_file) or "stack")
    spec: dict[str, Any] = {"name": name, "apps": []}
    if stack_file:
        spec["stackFile"] = stack_file
    if git_url:
        spec["gitUrl"] = git_url
    if doc.get("description"):
        spec["description"] = str(doc["description"])

    prop = doc.get("propagation") or {}
    if isinstance(prop, dict) and prop:
        spec["propagation"] = {
            k: v
            for k, v in {
                "headerName": prop.get("header-name"),
                "baggageKey": prop.get("baggage-key"),
                "strategy": prop.get("strategy"),
            }.items()
            if v
        }

    defaults = doc.get("defaults") or {}
    if isinstance(defaults, dict) and defaults:
        spec["defaults"] = {
            k: str(v)
            for k, v in {
                "namespace": defaults.get("namespace"),
                "imageRegistry": defaults.get("image-registry"),
                "servicePort": defaults.get("service-port"),
                "containerPort": defaults.get("container-port"),
            }.items()
            if v is not None and str(v) != ""
        }

    for app in doc.get("apps") or []:
        if not isinstance(app, dict):
            continue
        item: dict[str, Any] = {
            "name": str(app.get("name") or ""),
            "repo": str(app.get("repo") or ""),
            "role": str(app.get("role") or ""),
        }
        if app.get("propagation-role"):
            item["propagationRole"] = str(app["propagation-role"])
        if app.get("container-port"):
            item["containerPort"] = str(app["container-port"])
        if app.get("context-dir"):
            item["contextDir"] = str(app["context-dir"])
        if app.get("dockerfile"):
            item["dockerfile"] = str(app["dockerfile"])
        build = app.get("build") or {}
        if isinstance(build, dict) and build:
            b: dict[str, Any] = {}
            if build.get("tool"):
                b["tool"] = str(build["tool"])
            if build.get("runtime"):
                b["runtime"] = str(build["runtime"])
            if build.get("java-version"):
                b["javaVersion"] = str(build["java-version"])
            if build.get("node-version"):
                b["nodeVersion"] = str(build["node-version"])
            if build.get("python-version"):
                b["pythonVersion"] = str(build["python-version"])
            if build.get("php-version"):
                b["phpVersion"] = str(build["php-version"])
            if build.get("build-command"):
                b["buildCommand"] = str(build["build-command"])
            if b:
                item["build"] = b
        if app.get("downstream"):
            item["downstream"] = [str(d) for d in app["downstream"]]
        if app.get("tests"):
            item["tests"] = app["tests"]
        secrets = _injection(app.get("secrets"), secret=True)
        if secrets:
            item["secrets"] = secrets
        config = _injection(app.get("config"), secret=False)
        if config:
            item["config"] = config
        spec["apps"].append(item)

    return {
        "apiVersion": "tektondag.io/v1alpha1",
        "kind": "Stack",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/part-of": "tekton-job-standardization",
            },
        },
        "spec": spec,
    }


def iter_stack_files(stacks_dir: Path) -> list[Path]:
    files = []
    for path in sorted(stacks_dir.glob("*.yaml")):
        if path.name in SKIP_FILES:
            continue
        files.append(path)
    return files
