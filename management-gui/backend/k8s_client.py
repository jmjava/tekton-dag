"""
Multi-cluster Kubernetes client for the management GUI.

Caches one ApiClient per kubeconfig context so a single backend process
can query Tekton PipelineRuns/TaskRuns across multiple clusters.

Adapted from orchestrator/k8s_client.py (single-cluster version).
"""

import logging

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger("mgmt.k8s")

_clients = {}


def get_api(context=None):
    """Return a CustomObjectsApi for the given kubeconfig context (cached)."""
    if context not in _clients:
        try:
            api_client = config.new_client_from_config(context=context)
        except config.ConfigException:
            config.load_incluster_config()
            api_client = client.ApiClient()
        _clients[context] = client.CustomObjectsApi(api_client)
        logger.info("Created k8s client for context=%s", context or "(default)")
    return _clients[context]


def list_pipelineruns(context, namespace, limit=50, label_selector=""):
    """List recent PipelineRuns in a namespace."""
    api = get_api(context)
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


def get_pipelinerun(context, namespace, name):
    """Get a single PipelineRun by name."""
    api = get_api(context)
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


def list_taskruns(context, namespace, pipelinerun_name=None):
    """List TaskRuns, optionally filtered by PipelineRun label."""
    api = get_api(context)
    label_selector = ""
    if pipelinerun_name:
        label_selector = f"tekton.dev/pipelineRun={pipelinerun_name}"
    try:
        result = api.list_namespaced_custom_object(
            group="tekton.dev",
            version="v1",
            namespace=namespace,
            plural="taskruns",
            label_selector=label_selector,
        )
        return result.get("items", [])
    except ApiException as e:
        logger.error("Failed to list TaskRuns: %s", e.reason)
        return []


def create_pipelinerun(context, namespace, manifest):
    """Create a PipelineRun and return the created resource name."""
    api = get_api(context)
    try:
        result = api.create_namespaced_custom_object(
            group="tekton.dev",
            version="v1",
            namespace=namespace,
            plural="pipelineruns",
            body=manifest,
        )
        name = result["metadata"]["name"]
        logger.info("Created PipelineRun: %s in %s", name, namespace)
        return name
    except ApiException as e:
        logger.error("Failed to create PipelineRun: %s", e.reason)
        raise
