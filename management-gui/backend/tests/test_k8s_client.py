"""Tests for k8s_client.py — mocks the Kubernetes Python client."""

from unittest.mock import patch, MagicMock

import k8s_client


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
def test_create_pipelinerun(mock_get_api):
    mock_api = MagicMock()
    mock_api.create_namespaced_custom_object.return_value = {
        "metadata": {"name": "run-xyz"}
    }
    mock_get_api.return_value = mock_api

    manifest = {"kind": "PipelineRun", "metadata": {"generateName": "test-"}}
    name = k8s_client.create_pipelinerun("ctx", "ns", manifest)
    assert name == "run-xyz"


@patch("k8s_client.get_api")
def test_create_pipelinerun_error(mock_get_api):
    from kubernetes.client.rest import ApiException
    mock_api = MagicMock()
    mock_api.create_namespaced_custom_object.side_effect = ApiException(status=403, reason="Forbidden")
    mock_get_api.return_value = mock_api

    import pytest
    with pytest.raises(ApiException):
        k8s_client.create_pipelinerun("ctx", "ns", {})


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
