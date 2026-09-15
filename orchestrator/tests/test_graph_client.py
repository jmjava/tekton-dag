"""Behavioral tests for the Neo4j regression graph client."""

import json
from unittest.mock import MagicMock, call

import pytest

import graph_client


@pytest.fixture(autouse=True)
def reset_driver():
    graph_client._driver = None
    yield
    graph_client._driver = None


def _driver_and_session():
    driver = MagicMock()
    session = driver.session.return_value.__enter__.return_value
    return driver, session


def test_get_driver_uses_environment_and_caches(monkeypatch):
    driver = MagicMock()
    factory = MagicMock(return_value=driver)
    monkeypatch.setattr(graph_client.GraphDatabase, "driver", factory)
    monkeypatch.setenv("NEO4J_URI", "neo4j://example:7687")
    monkeypatch.setenv("NEO4J_USER", "alice")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")

    assert graph_client._get_driver() is driver
    assert graph_client._get_driver() is driver
    factory.assert_called_once_with(
        "neo4j://example:7687", auth=("alice", "secret")
    )


def test_get_driver_uses_defaults(monkeypatch):
    driver = object()
    factory = MagicMock(return_value=driver)
    monkeypatch.setattr(graph_client.GraphDatabase, "driver", factory)
    for name in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"):
        monkeypatch.delenv(name, raising=False)

    assert graph_client._get_driver() is driver
    factory.assert_called_once_with(
        "neo4j://graph-db:7687", auth=("neo4j", "changeme")
    )


def test_close_closes_driver_and_resets_singleton():
    driver = MagicMock()
    graph_client._driver = driver

    graph_client.close()

    driver.close.assert_called_once_with()
    assert graph_client._driver is None
    graph_client.close()  # Closing an already closed client is harmless.


def test_clear_graph_and_create_constraints(monkeypatch):
    driver, session = _driver_and_session()
    monkeypatch.setattr(graph_client, "_get_driver", lambda: driver)

    graph_client.clear_graph()
    graph_client.create_constraints()

    statements = [args[0] for args, _ in session.run.call_args_list]
    assert statements[0] == "MATCH (n) DETACH DELETE n"
    assert "Service" in statements[1]
    assert "Service" not in statements[2]
    assert "Test" in statements[2]


def test_ingest_traces_creates_tests_services_touches_and_calls(monkeypatch):
    driver, session = _driver_and_session()
    monkeypatch.setattr(graph_client, "_get_driver", lambda: driver)
    traces = [
        {
            "test_id": "e2e.checkout",
            "test_type": "e2e",
            "spans": [
                {"service": "frontend", "resource": "/checkout"},
                {"service": "frontend"},
                {"service": "payments", "resource": "/charge"},
            ],
        },
        {"test_id": "unit.empty"},
    ]

    graph_client.ingest_traces(traces)

    runs = session.run.call_args_list
    test_merges = [
        c
        for c in runs
        if c.args and "MERGE (t:Test" in c.args[0] and "MATCH" not in c.args[0]
    ]
    assert test_merges == [
        call(
            "MERGE (t:Test {id: $id}) SET t.type = $type",
            id="e2e.checkout",
            type="e2e",
        ),
        call(
            "MERGE (t:Test {id: $id}) SET t.type = $type",
            id="unit.empty",
            type="unknown",
        ),
    ]
    assert sum("MERGE (s:Service" in c.args[0] for c in runs) == 3
    assert sum("MERGE (t)-[:TOUCHES]" in c.args[0] for c in runs) == 3
    calls = [c for c in runs if "MERGE (a)-[:CALLS]" in c.args[0]]
    assert len(calls) == 1
    assert calls[0].kwargs == {"from": "frontend", "to": "payments"}


def test_ingest_from_file_replaces_graph_and_returns_count(tmp_path, monkeypatch):
    path = tmp_path / "traces.json"
    path.write_text(json.dumps({"traces": [{"test_id": "one"}, {"test_id": "two"}]}))
    clear = MagicMock()
    constraints = MagicMock()
    ingest = MagicMock()
    monkeypatch.setattr(graph_client, "clear_graph", clear)
    monkeypatch.setattr(graph_client, "create_constraints", constraints)
    monkeypatch.setattr(graph_client, "ingest_traces", ingest)

    assert graph_client.ingest_from_file(path) == 2
    clear.assert_called_once_with()
    constraints.assert_called_once_with()
    ingest.assert_called_once_with([{"test_id": "one"}, {"test_id": "two"}])


def test_query_test_plan_reports_unknown_service(monkeypatch):
    driver, session = _driver_and_session()
    service_check = MagicMock()
    service_check.single.return_value = None
    session.run.return_value = service_check
    monkeypatch.setattr(graph_client, "_get_driver", lambda: driver)

    plan = graph_client.query_test_plan("missing")

    assert plan == {
        "tests": [],
        "unmapped_area": "missing",
        "message": "No mapped regression; area 'missing' needs tests",
    }
    assert session.run.call_count == 1


def test_query_test_plan_reports_known_service_without_tests(monkeypatch):
    driver, session = _driver_and_session()
    service_check = MagicMock()
    service_check.single.return_value = {"s": object()}
    session.run.side_effect = [service_check, iter(())]
    monkeypatch.setattr(graph_client, "_get_driver", lambda: driver)

    plan = graph_client.query_test_plan("orphan", radius=1)

    assert plan["tests"] == []
    assert plan["unmapped_area"] == "orphan"
    assert session.run.call_count == 2
    assert "TOUCHES" in session.run.call_args_list[1].args[0]
    assert "apoc.path" not in session.run.call_args_list[1].args[0]


def test_query_test_plan_direct_returns_tests_services_and_summary(monkeypatch):
    driver, session = _driver_and_session()
    service_check = MagicMock()
    service_check.single.return_value = {"s": object()}
    session.run.side_effect = [
        service_check,
        iter(
            [
                {"id": "checkout", "type": "e2e"},
                {"id": "payment-unit", "type": "individual"},
            ]
        ),
        iter([{"name": "frontend"}, {"name": "payments"}]),
    ]
    monkeypatch.setattr(graph_client, "_get_driver", lambda: driver)

    plan = graph_client.query_test_plan("frontend")

    assert plan == {
        "tests": [
            {"id": "checkout", "type": "e2e"},
            {"id": "payment-unit", "type": "individual"},
        ],
        "services": ["frontend", "payments"],
        "unmapped_area": "",
        "message": "2 tests selected (1 e2e, 1 individual)",
    }
    assert session.run.call_args_list[2].kwargs == {
        "ids": ["checkout", "payment-unit"]
    }


def test_query_test_plan_radius_uses_apoc_subgraph(monkeypatch):
    driver, session = _driver_and_session()
    service_check = MagicMock()
    service_check.single.return_value = {"s": object()}
    session.run.side_effect = [
        service_check,
        iter([{"id": "blast", "type": "e2e"}]),
        iter([{"name": "api"}]),
    ]
    monkeypatch.setattr(graph_client, "_get_driver", lambda: driver)

    plan = graph_client.query_test_plan("frontend", radius=3)

    radius_query = session.run.call_args_list[1]
    assert "apoc.path.subgraphNodes" in radius_query.args[0]
    assert radius_query.kwargs == {"app": "frontend", "radius": 3}
    assert plan["message"] == "1 tests selected (1 e2e, 0 individual)"


def test_graph_stats_returns_all_counts(monkeypatch):
    driver, session = _driver_and_session()
    results = []
    for count in (4, 7, 9, 3):
        result = MagicMock()
        result.single.return_value = {"c": count}
        results.append(result)
    session.run.side_effect = results
    monkeypatch.setattr(graph_client, "_get_driver", lambda: driver)

    assert graph_client.graph_stats() == {
        "services": 4,
        "tests": 7,
        "touches_edges": 9,
        "calls_edges": 3,
    }
    assert session.run.call_count == 4
