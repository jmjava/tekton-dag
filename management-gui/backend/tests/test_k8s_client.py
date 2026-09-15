"""Tests for k8s_client.py — mocks the Kubernetes Python client."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import k8s_client
import pytest


@patch("k8s_client.get_api")
def test_list_pipelineruns(mock_get_api):
    mock_api = MagicMock()
    mock_api.list_namespaced_custom_object.return_value = {
        "items": [
            {"metadata": {"name": "run-1"}},
            {"metadata": {"name": "run-2"}},
        ]
    }
    mock_get_api.return_value = mock_api

    result = k8s_client.list_pipelineruns("ctx", "ns")
    assert len(result) == 2
    assert result[0]["metadata"]["name"] == "run-1"
    mock_api.list_namespaced_custom_object.assert_called_once_with(
        group="tekton.dev", version="v1", namespace="ns",
        plural="pipelineruns", limit=50, label_selector="",
    )


@patch("k8s_client.get_api")
def test_list_pipelineruns_api_error(mock_get_api):
    from kubernetes.client.rest import ApiException
    mock_api = MagicMock()
    mock_api.list_namespaced_custom_object.side_effect = ApiException(status=500, reason="Internal")
    mock_get_api.return_value = mock_api

    result = k8s_client.list_pipelineruns("ctx", "ns")
    assert result == []


@patch("k8s_client.get_api")
def test_get_pipelinerun(mock_get_api):
    mock_api = MagicMock()
    mock_api.get_namespaced_custom_object.return_value = {
        "metadata": {"name": "run-abc"},
        "status": {"conditions": [{"reason": "Succeeded"}]},
    }
    mock_get_api.return_value = mock_api

    result = k8s_client.get_pipelinerun("ctx", "ns", "run-abc")
    assert result["metadata"]["name"] == "run-abc"


@patch("k8s_client.get_api")
def test_get_pipelinerun_not_found(mock_get_api):
    from kubernetes.client.rest import ApiException
    mock_api = MagicMock()
    mock_api.get_namespaced_custom_object.side_effect = ApiException(status=404, reason="Not Found")
    mock_get_api.return_value = mock_api

    result = k8s_client.get_pipelinerun("ctx", "ns", "no-such-run")
    assert result is None


@patch("k8s_client.get_api")
def test_list_taskruns_with_filter(mock_get_api):
    mock_api = MagicMock()
    mock_api.list_namespaced_custom_object.return_value = {"items": [{"metadata": {"name": "tr-1"}}]}
    mock_get_api.return_value = mock_api

    result = k8s_client.list_taskruns("ctx", "ns", pipelinerun_name="run-abc")
    assert len(result) == 1
    mock_api.list_namespaced_custom_object.assert_called_once_with(
        group="tekton.dev", version="v1", namespace="ns",
        plural="taskruns", label_selector="tekton.dev/pipelineRun=run-abc",
    )


@patch("k8s_client.get_api")
def test_list_stackruns(mock_get_api):
    mock_api = MagicMock()
    mock_api.list_namespaced_custom_object.return_value = {
        "items": [{"metadata": {"name": "sr-1"}}]
    }
    mock_get_api.return_value = mock_api
    result = k8s_client.list_stackruns("ctx", "ns")
    assert result[0]["metadata"]["name"] == "sr-1"
    mock_api.list_namespaced_custom_object.assert_called_once_with(
        group="tektondag.io", version="v1alpha1", namespace="ns",
        plural="stackruns", limit=50, label_selector="",
    )


@patch("k8s_client.get_api")
def test_get_stackrun_not_found(mock_get_api):
    from kubernetes.client.rest import ApiException
    mock_api = MagicMock()
    mock_api.get_namespaced_custom_object.side_effect = ApiException(status=404, reason="Not Found")
    mock_get_api.return_value = mock_api
    assert k8s_client.get_stackrun("ctx", "ns", "missing") is None


@patch("k8s_client.get_api")
def test_patch_stackrun(mock_get_api):
    mock_api = MagicMock()
    mock_api.patch_namespaced_custom_object.return_value = {
        "metadata": {"name": "sr-1"},
        "spec": {"approvedBy": "alice"},
    }
    mock_get_api.return_value = mock_api
    result = k8s_client.patch_stackrun("ctx", "ns", "sr-1", {"spec": {"approvedBy": "alice"}})
    assert result["spec"]["approvedBy"] == "alice"


def test_get_api_caches_client():
    k8s_client._clients.clear()
    with patch("k8s_client.config") as mock_config, \
         patch("k8s_client.client") as mock_client:
        mock_config.new_client_from_config.return_value = MagicMock()
        mock_client.CustomObjectsApi.return_value = MagicMock()

        api1 = k8s_client.get_api("test-ctx")
        api2 = k8s_client.get_api("test-ctx")
        assert api1 is api2
        mock_config.new_client_from_config.assert_called_once_with(context="test-ctx")

    k8s_client._clients.clear()


def test_api_client_uses_incluster_config_when_kubeconfig_is_unavailable():
    fallback_client = MagicMock()
    config_error = k8s_client.config.ConfigException("no kubeconfig")

    with patch.object(
        k8s_client.config,
        "new_client_from_config",
        side_effect=config_error,
    ) as mock_new_client, patch.object(
        k8s_client.config, "load_incluster_config"
    ) as mock_load_incluster, patch.object(
        k8s_client.client, "ApiClient", return_value=fallback_client
    ) as mock_api_client:
        result = k8s_client._api_client("missing-context")

    assert result is fallback_client
    mock_new_client.assert_called_once_with(context="missing-context")
    mock_load_incluster.assert_called_once_with()
    mock_api_client.assert_called_once_with()


def test_get_core_api_caches_client_by_context():
    k8s_client._core_clients.clear()
    api_client = MagicMock()
    core_api = MagicMock()

    try:
        with patch("k8s_client._api_client", return_value=api_client) as mock_factory, \
             patch("k8s_client.client.CoreV1Api", return_value=core_api) as mock_core:
            first = k8s_client.get_core_api("cluster-a")
            second = k8s_client.get_core_api("cluster-a")

        assert first is core_api
        assert second is core_api
        mock_factory.assert_called_once_with("cluster-a")
        mock_core.assert_called_once_with(api_client)
    finally:
        k8s_client._core_clients.clear()


@patch("k8s_client.get_core_api")
def test_list_secret_and_configmap_names(mock_get_core_api):
    core_api = mock_get_core_api.return_value
    core_api.list_namespaced_secret.return_value.items = [
        SimpleNamespace(metadata=SimpleNamespace(name="registry-auth")),
        SimpleNamespace(metadata=SimpleNamespace(name="database")),
    ]
    core_api.list_namespaced_config_map.return_value.items = [
        SimpleNamespace(metadata=SimpleNamespace(name="app-config")),
    ]

    assert k8s_client.list_secret_names("ctx", "apps") == {
        "registry-auth",
        "database",
    }
    assert k8s_client.list_configmap_names("ctx", "apps") == {"app-config"}
    core_api.list_namespaced_secret.assert_called_once_with(namespace="apps")
    core_api.list_namespaced_config_map.assert_called_once_with(namespace="apps")


@patch("k8s_client.get_api")
def test_get_pipelinerun_reraises_non_not_found_api_error(mock_get_api):
    from kubernetes.client.rest import ApiException

    error = ApiException(status=403, reason="Forbidden")
    mock_get_api.return_value.get_namespaced_custom_object.side_effect = error

    with pytest.raises(ApiException) as exc_info:
        k8s_client.get_pipelinerun("ctx", "apps", "run-1")

    assert exc_info.value is error


@patch("k8s_client.get_api")
def test_list_taskruns_without_filter(mock_get_api):
    mock_get_api.return_value.list_namespaced_custom_object.return_value = {
        "items": []
    }

    assert k8s_client.list_taskruns("ctx", "apps") == []
    mock_get_api.return_value.list_namespaced_custom_object.assert_called_once_with(
        group="tekton.dev",
        version="v1",
        namespace="apps",
        plural="taskruns",
        label_selector="",
    )


@patch("k8s_client.get_api")
def test_list_taskruns_returns_empty_on_api_error(mock_get_api):
    from kubernetes.client.rest import ApiException

    mock_get_api.return_value.list_namespaced_custom_object.side_effect = ApiException(
        status=500, reason="Unavailable"
    )

    assert k8s_client.list_taskruns("ctx", "apps", "run-1") == []


@patch("k8s_client.get_api")
def test_create_stackrun_returns_created_name(mock_get_api):
    manifest = {"metadata": {"generateName": "stackrun-"}}
    mock_get_api.return_value.create_namespaced_custom_object.return_value = {
        "metadata": {"name": "stackrun-abc"}
    }

    assert (
        k8s_client.create_stackrun("ctx", "apps", manifest)
        == "stackrun-abc"
    )
    mock_get_api.return_value.create_namespaced_custom_object.assert_called_once_with(
        group="tektondag.io",
        version="v1alpha1",
        namespace="apps",
        plural="stackruns",
        body=manifest,
    )


@patch("k8s_client.get_api")
def test_create_stackrun_reraises_api_error(mock_get_api):
    from kubernetes.client.rest import ApiException

    error = ApiException(status=422, reason="Invalid")
    mock_get_api.return_value.create_namespaced_custom_object.side_effect = error

    with pytest.raises(ApiException) as exc_info:
        k8s_client.create_stackrun("ctx", "apps", {})

    assert exc_info.value is error


@patch("k8s_client.get_api")
def test_list_stackruns_returns_empty_on_api_error(mock_get_api):
    from kubernetes.client.rest import ApiException

    mock_get_api.return_value.list_namespaced_custom_object.side_effect = ApiException(
        status=403, reason="Forbidden"
    )

    assert k8s_client.list_stackruns("ctx", "apps") == []


@patch("k8s_client.get_api")
def test_get_stackrun_reraises_non_not_found_api_error(mock_get_api):
    from kubernetes.client.rest import ApiException

    error = ApiException(status=500, reason="Unavailable")
    mock_get_api.return_value.get_namespaced_custom_object.side_effect = error

    with pytest.raises(ApiException) as exc_info:
        k8s_client.get_stackrun("ctx", "apps", "stackrun-1")

    assert exc_info.value is error


@patch("k8s_client.get_api")
def test_list_teams_returns_items(mock_get_api):
    teams = [{"metadata": {"name": "platform"}}]
    mock_get_api.return_value.list_namespaced_custom_object.return_value = {
        "items": teams
    }

    assert k8s_client.list_teams("ctx", "control", limit=12) == teams
    mock_get_api.return_value.list_namespaced_custom_object.assert_called_once_with(
        group="tektondag.io",
        version="v1alpha1",
        namespace="control",
        plural="teams",
        limit=12,
    )


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(
            k8s_client.ApiException(status=500, reason="Unavailable"),
            id="api-error",
        ),
        pytest.param(RuntimeError("client setup failed"), id="unexpected-error"),
    ],
)
@patch("k8s_client.get_api")
def test_list_teams_returns_empty_on_errors(mock_get_api, error):
    mock_get_api.return_value.list_namespaced_custom_object.side_effect = error

    assert k8s_client.list_teams("ctx", "control") == []
