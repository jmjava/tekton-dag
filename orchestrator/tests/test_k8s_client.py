"""Kubernetes client wrapper tests with mocked kubernetes.client and config."""

import pytest
from kubernetes.client.rest import ApiException

import k8s_client


@pytest.fixture(autouse=True)
def reset_k8s_singleton():
    k8s_client._api = None
    k8s_client._core_api = None
    yield
    k8s_client._api = None
    k8s_client._core_api = None


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


def test_get_core_api_initializes_then_caches():
    from unittest.mock import MagicMock

    core_api = object()
    ensure_config = MagicMock()
    mock_client = MagicMock()
    mock_client.CoreV1Api.return_value = core_api
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_ensure_config", ensure_config)
        mp.setattr(k8s_client, "client", mock_client)

        assert k8s_client._get_core_api() is core_api
        assert k8s_client._get_core_api() is core_api

    ensure_config.assert_called_once_with()
    mock_client.CoreV1Api.assert_called_once_with()


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


def test_list_teams_returns_items_and_uses_team_crd():
    from unittest.mock import MagicMock

    teams = [{"metadata": {"name": "alpha"}}]
    api = MagicMock()
    api.list_namespaced_custom_object.return_value = {"items": teams}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.list_teams("teams-ns") == teams

    api.list_namespaced_custom_object.assert_called_once_with(
        group=k8s_client.STACKRUN_GROUP,
        version=k8s_client.STACKRUN_VERSION,
        namespace="teams-ns",
        plural=k8s_client.TEAM_PLURAL,
    )


def test_list_teams_returns_empty_for_missing_items_or_any_error():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.list_namespaced_custom_object.return_value = {}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.list_teams() == []

    api.list_namespaced_custom_object.side_effect = RuntimeError("discovery failed")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.list_teams() == []


def test_create_stackrun_returns_created_name():
    from unittest.mock import MagicMock

    manifest = {"metadata": {"generateName": "demo-"}}
    api = MagicMock()
    api.create_namespaced_custom_object.return_value = {
        "metadata": {"name": "demo-abc"}
    }
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.create_stackrun(manifest, "runs") == "demo-abc"

    api.create_namespaced_custom_object.assert_called_once_with(
        group=k8s_client.STACKRUN_GROUP,
        version=k8s_client.STACKRUN_VERSION,
        namespace="runs",
        plural=k8s_client.STACKRUN_PLURAL,
        body=manifest,
    )


def test_create_stackrun_propagates_api_error():
    from unittest.mock import MagicMock

    error = ApiException(status=422, reason="Invalid")
    api = MagicMock()
    api.create_namespaced_custom_object.side_effect = error
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        with pytest.raises(ApiException) as caught:
            k8s_client.create_stackrun({}, "runs")
    assert caught.value is error


def test_list_stackruns_returns_items_and_request_parameters():
    from unittest.mock import MagicMock

    runs = [{"metadata": {"name": "run-1"}}]
    api = MagicMock()
    api.list_namespaced_custom_object.return_value = {"items": runs}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.list_stackruns("runs", limit=4) == runs

    api.list_namespaced_custom_object.assert_called_once_with(
        group=k8s_client.STACKRUN_GROUP,
        version=k8s_client.STACKRUN_VERSION,
        namespace="runs",
        plural=k8s_client.STACKRUN_PLURAL,
        limit=4,
    )


def test_list_stackruns_handles_missing_items_and_api_error():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.list_namespaced_custom_object.return_value = {}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.list_stackruns() == []

    api.list_namespaced_custom_object.side_effect = ApiException(
        status=403, reason="Forbidden"
    )
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.list_stackruns() == []


def test_get_stackrun_returns_body_and_uses_stackrun_crd():
    from unittest.mock import MagicMock

    body = {"metadata": {"name": "run-1"}}
    api = MagicMock()
    api.get_namespaced_custom_object.return_value = body
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        assert k8s_client.get_stackrun("run-1", "runs") is body

    api.get_namespaced_custom_object.assert_called_once_with(
        group=k8s_client.STACKRUN_GROUP,
        version=k8s_client.STACKRUN_VERSION,
        namespace="runs",
        plural=k8s_client.STACKRUN_PLURAL,
        name="run-1",
    )


@pytest.mark.parametrize("status, expected_none", [(404, True), (500, False)])
def test_get_stackrun_error_semantics(status, expected_none):
    from unittest.mock import MagicMock

    api = MagicMock()
    api.get_namespaced_custom_object.side_effect = ApiException(
        status=status, reason="failure"
    )
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_api", lambda: api)
        if expected_none:
            assert k8s_client.get_stackrun("missing") is None
        else:
            with pytest.raises(ApiException):
                k8s_client.get_stackrun("broken")


def test_get_secret_data_decodes():
    import base64
    from unittest.mock import MagicMock

    secret = MagicMock()
    secret.data = {
        "secret": base64.b64encode(b"webhook-value").decode("ascii"),
        "bin": base64.b64encode(b"\xff\xfe").decode("ascii"),
    }
    api = MagicMock()
    api.read_namespaced_secret.return_value = secret
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_core_api", lambda: api)
        data = k8s_client.get_secret_data("github-webhook-secret", namespace="ns")
    assert data["secret"] == "webhook-value"
    assert "bin" not in data


def test_get_secret_data_404():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.read_namespaced_secret.side_effect = ApiException(status=404, reason="Not Found")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_core_api", lambda: api)
        assert k8s_client.get_secret_data("missing") is None


def test_get_secret_data_handles_empty_data():
    from unittest.mock import MagicMock

    secret = MagicMock()
    secret.data = None
    api = MagicMock()
    api.read_namespaced_secret.return_value = secret
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_core_api", lambda: api)
        assert k8s_client.get_secret_data("empty", "ns") == {}
    api.read_namespaced_secret.assert_called_once_with(name="empty", namespace="ns")


def test_get_secret_data_non_404_propagates():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.read_namespaced_secret.side_effect = ApiException(
        status=403, reason="Forbidden"
    )
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_core_api", lambda: api)
        with pytest.raises(ApiException):
            k8s_client.get_secret_data("denied", "ns")


def test_list_secret_and_configmap_names():
    from unittest.mock import MagicMock

    s1 = MagicMock()
    s1.metadata.name = "a"
    s2 = MagicMock()
    s2.metadata.name = "b"
    c1 = MagicMock()
    c1.metadata.name = "c"
    api = MagicMock()
    api.list_namespaced_secret.return_value = MagicMock(items=[s1, s2])
    api.list_namespaced_config_map.return_value = MagicMock(items=[c1])
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_core_api", lambda: api)
        assert k8s_client.list_secret_names("ns") == {"a", "b"}
        assert k8s_client.list_configmap_names("ns") == {"c"}


def test_list_secret_names_propagates_api_error():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.list_namespaced_secret.side_effect = ApiException(status=403, reason="Forbidden")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_core_api", lambda: api)
        with pytest.raises(ApiException):
            k8s_client.list_secret_names("ns")


def test_list_configmap_names_propagates_api_error():
    from unittest.mock import MagicMock

    api = MagicMock()
    api.list_namespaced_config_map.side_effect = ApiException(
        status=403, reason="Forbidden"
    )
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(k8s_client, "_get_core_api", lambda: api)
        with pytest.raises(ApiException):
            k8s_client.list_configmap_names("ns")
