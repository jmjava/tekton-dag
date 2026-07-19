"""
Kubernetes client wrapper for creating PipelineRuns and querying status.

Uses in-cluster config when running as a pod, falls back to kubeconfig for local dev.
"""

import base64
import logging

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger("orchestrator.k8s")

_api = None
_core_api = None


def _ensure_config():
    try:
        config.load_incluster_config()
        logger.info("Using in-cluster Kubernetes config")
    except config.ConfigException:
        config.load_kube_config()
        logger.info("Using kubeconfig (local dev)")


def _get_api():
    global _api
    if _api is None:
        _ensure_config()
        _api = client.CustomObjectsApi()
    return _api


def _get_core_api():
    global _core_api
    if _core_api is None:
        _ensure_config()
        _core_api = client.CoreV1Api()
    return _core_api


def create_pipelinerun(run_manifest, namespace="tekton-pipelines"):
    """
    Create a Tekton PipelineRun in the cluster.

    Returns the created resource name, or raises on failure.
    """
    api = _get_api()
    try:
        result = api.create_namespaced_custom_object(
            group="tekton.dev",
            version="v1",
            namespace=namespace,
            plural="pipelineruns",
            body=run_manifest,
        )
        name = result["metadata"]["name"]
        logger.info("Created PipelineRun: %s in %s", name, namespace)
        return name
    except ApiException as e:
        logger.error("Failed to create PipelineRun: %s", e.reason)
        raise


def get_pipelinerun(name, namespace="tekton-pipelines"):
    """Get a PipelineRun by name."""
    api = _get_api()
    try:
        return api.get_namespaced_custom_object(
            group="tekton.dev",
            version="v1",
            namespace=namespace,
            plural="pipelineruns",
            name=name,
        )
    except ApiException as e:
        if e.status == 404:
            return None
        raise


def list_pipelineruns(namespace="tekton-pipelines", limit=20, label_selector=""):
    """List recent PipelineRuns."""
    api = _get_api()
    try:
        result = api.list_namespaced_custom_object(
            group="tekton.dev",
            version="v1",
            namespace=namespace,
            plural="pipelineruns",
            limit=limit,
            label_selector=label_selector,
        )
        return result.get("items", [])
    except ApiException as e:
        logger.error("Failed to list PipelineRuns: %s", e.reason)
        return []


# M14 CRDs (tektondag.io/v1alpha1)
STACKRUN_GROUP = "tektondag.io"
STACKRUN_VERSION = "v1alpha1"
STACKRUN_PLURAL = "stackruns"


def create_stackrun(run_manifest, namespace="tekton-pipelines"):
    """
    Create a StackRun custom resource.

    Returns the created resource name, or raises on failure.
    """
    api = _get_api()
    try:
        result = api.create_namespaced_custom_object(
            group=STACKRUN_GROUP,
            version=STACKRUN_VERSION,
            namespace=namespace,
            plural=STACKRUN_PLURAL,
            body=run_manifest,
        )
        name = result["metadata"]["name"]
        logger.info("Created StackRun: %s in %s", name, namespace)
        return name
    except ApiException as e:
        logger.error("Failed to create StackRun: %s", e.reason)
        raise


def list_stackruns(namespace="tekton-pipelines", limit=20):
    """List recent StackRun CRs."""
    api = _get_api()
    try:
        result = api.list_namespaced_custom_object(
            group=STACKRUN_GROUP,
            version=STACKRUN_VERSION,
            namespace=namespace,
            plural=STACKRUN_PLURAL,
            limit=limit,
        )
        return result.get("items", [])
    except ApiException as e:
        logger.error("Failed to list StackRuns: %s", e.reason)
        return []


def get_stackrun(name, namespace="tekton-pipelines"):
    """Get a StackRun by name, or None if missing."""
    api = _get_api()
    try:
        return api.get_namespaced_custom_object(
            group=STACKRUN_GROUP,
            version=STACKRUN_VERSION,
            namespace=namespace,
            plural=STACKRUN_PLURAL,
            name=name,
        )
    except ApiException as e:
        if e.status == 404:
            return None
        raise


def get_secret_data(name, namespace="tekton-pipelines"):
    """
    Return decoded string data from a Secret, or None if missing.

    Values are UTF-8 decoded; binary secrets that are not valid UTF-8 are skipped.
    """
    api = _get_core_api()
    try:
        secret = api.read_namespaced_secret(name=name, namespace=namespace)
    except ApiException as e:
        if e.status == 404:
            logger.warning("Secret %s/%s not found", namespace, name)
            return None
        raise
    out = {}
    for key, raw in (secret.data or {}).items():
        try:
            out[key] = base64.b64decode(raw).decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            continue
    return out


def list_secret_names(namespace="tekton-pipelines"):
    """
    Return a set of Secret names in the namespace.

    Raises ApiException on API/RBAC failures so callers do not treat errors
    as an empty namespace (which would mark every ref as missing).
    """
    api = _get_core_api()
    result = api.list_namespaced_secret(namespace=namespace)
    return {item.metadata.name for item in result.items}


def list_configmap_names(namespace="tekton-pipelines"):
    """
    Return a set of ConfigMap names in the namespace.

    Raises ApiException on API/RBAC failures (same rationale as list_secret_names).
    """
    api = _get_core_api()
    result = api.list_namespaced_config_map(namespace=namespace)
    return {item.metadata.name for item in result.items}
