"""
Kubernetes client wrapper for creating PipelineRuns and querying status.

Uses in-cluster config when running as a pod, falls back to kubeconfig for local dev.
"""

import logging

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger("orchestrator.k8s")

_api = None


def _get_api():
    global _api
    if _api is None:
        try:
            config.load_incluster_config()
            logger.info("Using in-cluster Kubernetes config")
        except config.ConfigException:
            config.load_kube_config()
            logger.info("Using kubeconfig (local dev)")
        _api = client.CustomObjectsApi()
    return _api


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
