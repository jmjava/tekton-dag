"""
PipelineRun builder: generates and applies Tekton PipelineRun manifests.

Replaces generate-run.sh for the orchestration service path.
"""

import logging
import random
import string

logger = logging.getLogger("orchestrator.builder")


def _random_suffix(length=5):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


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

    return run


def build_bootstrap_pipelinerun(
    *,
    git_url,
    git_revision,
    stack_file,
    image_registry,
    cache_repo="",
    namespace="tekton-pipelines",
    compile_images=None,
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

    return run


def build_merge_pipelinerun(
    *,
    changed_app,
    git_url,
    git_revision,
    stack_file,
    image_registry,
    cache_repo="",
    namespace="tekton-pipelines",
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

    return run
