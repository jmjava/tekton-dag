"""Build tektondag.io/v1alpha1 StackRun manifests (M14 CRD-primary path)."""

from __future__ import annotations

import random
import string


def _suffix(length: int = 5) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def build_stackrun(
    *,
    mode: str,
    namespace: str = "tekton-pipelines",
    stack_file: str = "",
    stack_ref: str = "",
    git_url: str = "",
    git_revision: str = "",
    image_registry: str = "",
    cache_repo: str = "",
    changed_app: str = "",
    pr_number: int = 0,
    app_revisions: str = "",
    intercept_backend: str = "",
    dashboard_url: str = "",
    pr_repo_url: str = "",
    release_version: str = "",
    target_environment: str = "",
    target_registry: str = "",
    credentials_secret: str = "",
    require_approval: bool = False,
    approved_by: str = "",
    timeout: str = "2h",
    max_retries: int = 2,
) -> dict:
    """Return a StackRun CR dict ready for the API."""
    name = f"stackrun-{mode}-{_suffix()}"
    spec: dict = {
        "mode": mode,
        "stackFile": stack_file,
        "gitUrl": git_url,
        "gitRevision": git_revision,
        "imageRegistry": image_registry,
        "cacheRepo": cache_repo,
        "timeout": timeout,
        "maxRetries": int(max_retries),
    }
    if stack_ref:
        spec["stackRef"] = stack_ref
    if changed_app:
        spec["changedApp"] = changed_app
    if pr_number:
        spec["prNumber"] = int(pr_number)
    if app_revisions:
        spec["appRevisions"] = app_revisions
    if intercept_backend:
        spec["interceptBackend"] = intercept_backend
    if dashboard_url:
        spec["dashboardUrl"] = dashboard_url
    if pr_repo_url:
        spec["prRepoUrl"] = pr_repo_url
    if release_version:
        spec["releaseVersion"] = str(release_version)
    if target_environment:
        spec["targetEnvironment"] = target_environment
    if target_registry:
        spec["targetRegistry"] = target_registry
    if credentials_secret:
        spec["credentialsSecret"] = credentials_secret
    if require_approval:
        spec["requireApproval"] = True
    if approved_by:
        spec["approvedBy"] = approved_by

    return {
        "apiVersion": "tektondag.io/v1alpha1",
        "kind": "StackRun",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/part-of": "tekton-job-standardization",
                "tektondag.io/mode": mode,
            },
        },
        "spec": spec,
    }
