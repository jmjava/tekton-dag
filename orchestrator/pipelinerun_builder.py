"""
PipelineRun builder: generates and applies Tekton PipelineRun manifests.

Replaces generate-run.sh for the orchestration service path.
"""

import logging
import random
import string

logger = logging.getLogger("orchestrator.builder")

try:
    from tekton_dag_common.reliability import (
        DEFAULT_MAX_RETRIES,
        DEFAULT_PIPELINE_TIMEOUT,
        apply_reliability,
    )
except ImportError:  # pragma: no cover - package may be absent in slim images
    apply_reliability = None
    DEFAULT_PIPELINE_TIMEOUT = "2h"
    DEFAULT_MAX_RETRIES = 2


def _random_suffix(length=5):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _with_reliability(run, timeout=None, max_retries=None):
    """Attach pipeline timeout and max-retries (M13 defaults when unset)."""
    if apply_reliability is None:
        return run
    return apply_reliability(
        run,
        timeout=DEFAULT_PIPELINE_TIMEOUT if timeout is None else timeout,
        max_retries=DEFAULT_MAX_RETRIES if max_retries is None else max_retries,
    )


def build_pr_pipelinerun(
    *,
    stack_file,
    changed_app,
    pr_number,
    git_url,
    git_revision,
    image_registry,
    cache_repo="",
    intercept_backend="telepresence",
    app_revisions=None,
    namespace="tekton-pipelines",
    compile_images=None,
    dashboard_url="",
    pr_repo_url="",
    timeout=None,
    max_retries=None,
):
    """Build a stack-pr-test PipelineRun manifest."""
    name = f"stack-pr-{pr_number}-{_random_suffix()}"
    app_revisions = app_revisions or "{}"
    compile_images = compile_images or {}

    run = {
        "apiVersion": "tekton.dev/v1",
        "kind": "PipelineRun",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "tekton.dev/pipeline": "stack-pr-test",
                "app.kubernetes.io/part-of": "tekton-job-standardization",
            },
        },
        "spec": {
            "pipelineRef": {"name": "stack-pr-test"},
            "params": [
                {"name": "git-url", "value": git_url},
                {"name": "git-revision", "value": git_revision},
                {"name": "stack-file", "value": stack_file},
                {"name": "changed-app", "value": changed_app},
                {"name": "pr-number", "value": str(pr_number)},
                {"name": "app-revisions", "value": app_revisions},
                {"name": "image-registry", "value": image_registry},
                {"name": "cache-repo", "value": cache_repo},
                {"name": "intercept-backend", "value": intercept_backend},
                {"name": "dashboard-url", "value": dashboard_url},
                {"name": "pr-repo-url", "value": pr_repo_url},
            ],
            "workspaces": [
                {
                    "name": "shared-workspace",
                    "volumeClaimTemplate": {
                        "spec": {
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "2Gi"}},
                        }
                    },
                },
                {
                    "name": "ssh-key",
                    "secret": {"secretName": "ssh-key-secret"},
                },
                {
                    "name": "build-cache",
                    "persistentVolumeClaim": {"claimName": "build-cache-pvc"},
                },
            ],
            "taskRunTemplate": {
                "serviceAccountName": "tekton-pr-sa",
            },
        },
    }

    for key, param_name in [
        ("npm", "compile-image-npm"),
        ("maven", "compile-image-maven"),
        ("gradle", "compile-image-gradle"),
        ("pip", "compile-image-pip"),
        ("php", "compile-image-php"),
        ("mirrord", "compile-image-mirrord"),
    ]:
        if key in compile_images:
            run["spec"]["params"].append({"name": param_name, "value": compile_images[key]})

    return _with_reliability(run, timeout=timeout, max_retries=max_retries)


def build_bootstrap_pipelinerun(
    *,
    git_url,
    git_revision,
    stack_file,
    image_registry,
    cache_repo="",
    namespace="tekton-pipelines",
    compile_images=None,
    timeout=None,
    max_retries=None,
):
    """Build a stack-bootstrap PipelineRun manifest."""
    name = f"stack-bootstrap-{_random_suffix()}"
    compile_images = compile_images or {}

    run = {
        "apiVersion": "tekton.dev/v1",
        "kind": "PipelineRun",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "tekton.dev/pipeline": "stack-bootstrap",
                "app.kubernetes.io/part-of": "tekton-job-standardization",
            },
        },
        "spec": {
            "pipelineRef": {"name": "stack-bootstrap"},
            "params": [
                {"name": "git-url", "value": git_url},
                {"name": "git-revision", "value": git_revision},
                {"name": "stack-file", "value": stack_file},
                {"name": "image-registry", "value": image_registry},
                {"name": "cache-repo", "value": cache_repo},
            ],
            "workspaces": [
                {
                    "name": "shared-workspace",
                    "volumeClaimTemplate": {
                        "spec": {
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "2Gi"}},
                        }
                    },
                },
                {
                    "name": "ssh-key",
                    "secret": {"secretName": "ssh-key-secret"},
                },
                {
                    "name": "build-cache",
                    "persistentVolumeClaim": {"claimName": "build-cache-pvc"},
                },
            ],
            "taskRunTemplate": {
                "serviceAccountName": "tekton-pr-sa",
            },
        },
    }

    for key, param_name in [
        ("npm", "compile-image-npm"),
        ("maven", "compile-image-maven"),
        ("gradle", "compile-image-gradle"),
        ("pip", "compile-image-pip"),
        ("php", "compile-image-php"),
    ]:
        if key in compile_images:
            run["spec"]["params"].append({"name": param_name, "value": compile_images[key]})

    return _with_reliability(run, timeout=timeout, max_retries=max_retries)


def build_merge_pipelinerun(
    *,
    changed_app,
    git_url,
    git_revision,
    stack_file,
    image_registry,
    cache_repo="",
    namespace="tekton-pipelines",
    timeout=None,
    max_retries=None,
):
    """Build a stack-merge-release PipelineRun manifest."""
    name = f"stack-merge-{_random_suffix()}"

    run = {
        "apiVersion": "tekton.dev/v1",
        "kind": "PipelineRun",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "tekton.dev/pipeline": "stack-merge-release",
                "app.kubernetes.io/part-of": "tekton-job-standardization",
            },
        },
        "spec": {
            "pipelineRef": {"name": "stack-merge-release"},
            "params": [
                {"name": "git-url", "value": git_url},
                {"name": "git-revision", "value": git_revision},
                {"name": "stack-file", "value": stack_file},
                {"name": "changed-app", "value": changed_app},
                {"name": "image-registry", "value": image_registry},
                {"name": "cache-repo", "value": cache_repo},
            ],
            "workspaces": [
                {
                    "name": "shared-workspace",
                    "volumeClaimTemplate": {
                        "spec": {
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "2Gi"}},
                        }
                    },
                },
                {
                    "name": "ssh-key",
                    "secret": {"secretName": "ssh-key-secret"},
                },
                {
                    "name": "build-cache",
                    "persistentVolumeClaim": {"claimName": "build-cache-pvc"},
                },
            ],
            "taskRunTemplate": {
                "serviceAccountName": "tekton-pr-sa",
            },
        },
    }

    return _with_reliability(run, timeout=timeout, max_retries=max_retries)


def build_promote_pipelinerun(
    *,
    stack_file,
    release_version,
    target_environment,
    image_registry,
    target_registry="",
    credentials_secret="",
    changed_app="",
    namespace="tekton-pipelines",
    timeout=None,
    max_retries=None,
    require_approval=False,
    approved_by="",
):
    """
    Build a stack-promote PipelineRun manifest (M13 multi-cluster push).

    Pulls release-tagged images from the build registry and pushes them to a
    target registry / environment.
    """
    name = f"stack-promote-{target_environment}-{_random_suffix()}"

    workspaces = [
        {
            "name": "shared-workspace",
            "volumeClaimTemplate": {
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": "1Gi"}},
                }
            },
        },
    ]
    # Mount dockerconfigjson Secret for private registry auth (crane DOCKER_CONFIG).
    if credentials_secret:
        workspaces.append(
            {
                "name": "dockerconfig",
                "secret": {
                    "secretName": credentials_secret,
                    "items": [{"key": ".dockerconfigjson", "path": "config.json"}],
                },
            }
        )

    run = {
        "apiVersion": "tekton.dev/v1",
        "kind": "PipelineRun",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "tekton.dev/pipeline": "stack-promote",
                "app.kubernetes.io/part-of": "tekton-job-standardization",
                "tekton-dag.io/environment": target_environment,
            },
            "annotations": {
                "tekton-dag.io/release-version": str(release_version),
                "tekton-dag.io/approved-by": approved_by or "",
                "tekton-dag.io/require-approval": "true" if require_approval else "false",
                "tekton-dag.io/max-retries-note": (
                    "PipelineRun param max-retries is for audit; Tekton task "
                    "retries on promote remain fixed at 2"
                ),
            },
        },
        "spec": {
            "pipelineRef": {"name": "stack-promote"},
            "params": [
                {"name": "stack-file", "value": stack_file},
                {"name": "release-version", "value": str(release_version)},
                {"name": "target-environment", "value": target_environment},
                {"name": "image-registry", "value": image_registry},
                {"name": "target-registry", "value": target_registry},
                {"name": "credentials-secret", "value": credentials_secret},
                {"name": "changed-app", "value": changed_app},
                {"name": "apps", "value": changed_app},
            ],
            "workspaces": workspaces,
            "taskRunTemplate": {
                "serviceAccountName": "tekton-pr-sa",
            },
        },
    }

    return _with_reliability(run, timeout=timeout, max_retries=max_retries)
