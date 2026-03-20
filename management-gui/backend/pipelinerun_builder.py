"""
PipelineRun manifest builder for the management GUI trigger form.

Builds YAML dicts (not strings) for pr, bootstrap, and merge PipelineRuns,
ready to pass to k8s_client.create_pipelinerun().
"""


def build_bootstrap(*, git_url, git_revision, stack_file, image_registry,
                    namespace="tekton-pipelines", git_ssh_secret="git-ssh-key",
                    cache_pvc="build-cache"):
    stack_path = stack_file if stack_file.startswith("stacks/") else f"stacks/{stack_file}"
    return {
        "apiVersion": "tekton.dev/v1",
        "kind": "PipelineRun",
        "metadata": {
            "generateName": "stack-bootstrap-",
            "namespace": namespace,
        },
        "spec": {
            "pipelineRef": {"name": "stack-bootstrap"},
            "taskRunTemplate": {"serviceAccountName": "tekton-pr-sa"},
            "params": [
                {"name": "git-url", "value": git_url},
                {"name": "git-revision", "value": git_revision},
                {"name": "stack-file", "value": stack_path},
                {"name": "image-registry", "value": image_registry},
                {"name": "image-tag", "value": "base-1"},
            ],
            "workspaces": [
                {
                    "name": "shared-workspace",
                    "volumeClaimTemplate": {
                        "spec": {
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "10Gi"}},
                        },
                    },
                },
                {"name": "ssh-key", "secret": {"secretName": git_ssh_secret}},
                {"name": "build-cache", "persistentVolumeClaim": {"claimName": cache_pvc}},
            ],
        },
    }


def build_pr(*, stack_file, changed_app, pr_number, git_url, git_revision,
             image_registry, namespace="tekton-pipelines",
             version_overrides=None, intercept_backend="telepresence",
             storage_class="", build_images=False,
             git_ssh_secret="git-ssh-key", cache_pvc="build-cache"):
    stack_path = stack_file if stack_file.startswith("stacks/") else f"stacks/{stack_file}"
    params = [
        {"name": "git-url", "value": git_url},
        {"name": "git-revision", "value": git_revision},
        {"name": "stack-file", "value": stack_path},
        {"name": "changed-app", "value": changed_app},
        {"name": "pr-number", "value": str(pr_number)},
        {"name": "image-registry", "value": image_registry},
        {"name": "intercept-backend", "value": intercept_backend},
    ]
    if version_overrides:
        params.append({"name": "version-overrides", "value": version_overrides})
    if storage_class:
        params.append({"name": "storage-class", "value": storage_class})

    return {
        "apiVersion": "tekton.dev/v1",
        "kind": "PipelineRun",
        "metadata": {
            "generateName": f"stack-pr-{pr_number}-",
            "namespace": namespace,
        },
        "spec": {
            "pipelineRef": {"name": "stack-pr-test"},
            "taskRunTemplate": {"serviceAccountName": "tekton-pr-sa"},
            "params": params,
            "workspaces": [
                {
                    "name": "shared-workspace",
                    "volumeClaimTemplate": {
                        "spec": {
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "10Gi"}},
                        },
                    },
                },
                {"name": "ssh-key", "secret": {"secretName": git_ssh_secret}},
                {"name": "build-cache", "persistentVolumeClaim": {"claimName": cache_pvc}},
            ],
        },
    }


def build_merge(*, stack_file, changed_app, git_url, git_revision,
                image_registry, namespace="tekton-pipelines",
                git_ssh_secret="git-ssh-key", cache_pvc="build-cache"):
    stack_path = stack_file if stack_file.startswith("stacks/") else f"stacks/{stack_file}"
    return {
        "apiVersion": "tekton.dev/v1",
        "kind": "PipelineRun",
        "metadata": {
            "generateName": "stack-merge-",
            "namespace": namespace,
        },
        "spec": {
            "pipelineRef": {"name": "stack-merge-release"},
            "taskRunTemplate": {"serviceAccountName": "tekton-pr-sa"},
            "params": [
                {"name": "git-url", "value": git_url},
                {"name": "git-revision", "value": git_revision},
                {"name": "stack-file", "value": stack_path},
                {"name": "changed-app", "value": changed_app},
                {"name": "image-registry", "value": image_registry},
            ],
            "workspaces": [
                {
                    "name": "shared-workspace",
                    "volumeClaimTemplate": {
                        "spec": {
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "10Gi"}},
                        },
                    },
                },
                {"name": "ssh-key", "secret": {"secretName": git_ssh_secret}},
                {"name": "build-cache", "persistentVolumeClaim": {"claimName": cache_pvc}},
            ],
        },
    }
