"""Kubernetes client wrapper tests with mocked kubernetes.client and config."""

import pytest
from kubernetes.client.rest import ApiException

import k8s_client


@pytest.fixture(autouse=True)
def reset_k8s_singleton():
    k8s_client._api = None
    yield
    k8s_client._api = None


def test_get_api_uses_incluster_then_caches():
    mock_api = object()
    with pytest.MonkeyPatch.context() as mp:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.CustomObjectsApi.return_value = mock_api
        mock_config = MagicMock()
        mock_config.load_incluster_config.side_effect = None
        mp.setattr(k8s_client, "client", mock_client)
        mp.setattr(k8s_client, "config", mock_config)

        k8s_client._api = None
        a1 = k8s_client._get_api()
        a2 = k8s_client._get_api()
        assert a1 is mock_api is a2
        mock_config.load_incluster_config.assert_called_once()
        mock_config.load_kube_config.assert_not_called()


def test_get_api_falls_back_to_kubeconfig():
    mock_api = object()
    with pytest.MonkeyPatch.context() as mp:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.CustomObjectsApi.return_value = mock_api
        mock_config = MagicMock()
        from kubernetes import config as kconfig

        mock_config.ConfigException = kconfig.ConfigException
        mock_config.load_incluster_config.side_effect = kconfig.ConfigException()
        mp.setattr(k8s_client, "client", mock_client)
        mp.setattr(k8s_client, "config", mock_config)

        k8s_client._api = None
        assert k8s_client._get_api() is mock_api
        mock_config.load_kube_config.assert_called_once()


def test_create_pipelinerun_returns_name():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.create_namespaced_custom_object.return_value = {
        "metadata": {"name": "run-xyz"},
    }
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        name = k8s_client.create_pipelinerun({"kind": "PipelineRun"}, namespace="ns1")
    assert name == "run-xyz"
    api.create_namespaced_custom_object.assert_called_once()
    call_kw = api.create_namespaced_custom_object.call_args.kwargs
    assert call_kw["namespace"] == "ns1"
    assert call_kw["group"] == "tekton.dev"
    assert call_kw["version"] == "v1"
    assert call_kw["plural"] == "pipelineruns"


def test_create_pipelinerun_propagates_api_exception():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.create_namespaced_custom_object.side_effect = ApiException(status=409, reason="Conflict")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        with pytest.raises(ApiException):
            k8s_client.create_pipelinerun({}, namespace="ns")


def test_get_pipelinerun_returns_body():
    from unittest.mock import MagicMock

    body = {"metadata": {"name": "pr-1"}}
    api = MagicMock()
    api.get_namespaced_custom_object.return_value = body
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.get_pipelinerun("pr-1", namespace="n") is body


def test_get_pipelinerun_404_returns_none():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.get_namespaced_custom_object.side_effect = ApiException(status=404, reason="Not Found")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.get_pipelinerun("missing", namespace="n") is None


def test_get_pipelinerun_other_status_raises():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.get_namespaced_custom_object.side_effect = ApiException(status=500, reason="Error")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        with pytest.raises(ApiException):
            k8s_client.get_pipelinerun("x", namespace="n")


def test_list_pipelineruns_returns_items():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.list_namespaced_custom_object.return_value = {
        "items": [{"metadata": {"name": "a"}}],
    }
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        items = k8s_client.list_pipelineruns(namespace="n", limit=5, label_selector="k=v")
    assert items == [{"metadata": {"name": "a"}}]
    api.list_namespaced_custom_object.assert_called_once()
    kw = api.list_namespaced_custom_object.call_args.kwargs
    assert kw["limit"] == 5
    assert kw["label_selector"] == "k=v"


def test_list_pipelineruns_missing_items_key():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.list_namespaced_custom_object.return_value = {}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.list_pipelineruns() == []


def test_list_pipelineruns_api_error_returns_empty():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.list_namespaced_custom_object.side_effect = ApiException(status=403, reason="Forbidden")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.list_pipelineruns(namespace="n") == []
