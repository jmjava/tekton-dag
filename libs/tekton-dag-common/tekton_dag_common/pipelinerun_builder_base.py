"""Shared Tekton PipelineRun manifest structure."""

from __future__ import annotations

import random
import string
from typing import Any

TEKTON_API_VERSION = "tekton.dev/v1"
STANDARD_LABELS = {"app.kubernetes.io/part-of": "tekton-job-standardization"}


def random_suffix(length: int = 5) -> str:
    """Random alphanumeric suffix (lowercase letters and digits)."""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def base_pipelinerun(
    name: str,
    pipeline_name: str,
    namespace: str,
    params: list[dict[str, Any]],
    workspaces: list[dict[str, Any]],
    service_account: str = "tekton-pr-sa",
) -> dict[str, Any]:
    """Build the common PipelineRun dict (metadata + spec shell)."""
    labels = {"tekton.dev/pipeline": pipeline_name, **STANDARD_LABELS}
    return {
        "apiVersion": TEKTON_API_VERSION,
        "kind": "PipelineRun",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": labels,
        },
        "spec": {
            "pipelineRef": {"name": pipeline_name},
            "params": params,
            "workspaces": workspaces,
            "taskRunTemplate": {
                "serviceAccountName": service_account,
            },
        },
    }


def default_workspaces(
    ssh_secret: str = "ssh-key-secret",
    cache_pvc: str = "build-cache",
    storage_size: str = "2Gi",
) -> list[dict[str, Any]]:
    """Standard workspace list (shared PVC template, SSH secret, build cache PVC)."""
    return [
        {
            "name": "shared-workspace",
            "volumeClaimTemplate": {
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": storage_size}},
                }
            },
        },
        {
            "name": "ssh-key",
            "secret": {"secretName": ssh_secret},
        },
        {
            "name": "build-cache",
            "persistentVolumeClaim": {"claimName": cache_pvc},
        },
    ]
