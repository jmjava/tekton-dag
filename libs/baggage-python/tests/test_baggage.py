import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g

import tekton_dag_baggage as baggage

VECTORS = json.loads(
    (Path(__file__).resolve().parents[2] / "baggage-contract" / "vectors.json").read_text(
        encoding="utf-8"
    )
)


_BAGGAGE_ENV = (
    "BAGGAGE_ENABLED",
    "BAGGAGE_ROLE",
    "BAGGAGE_HEADER_NAME",
    "BAGGAGE_KEY",
    "BAGGAGE_SESSION_VALUE",
)


@pytest.fixture(autouse=True)
def _reset_instrumentation():
    baggage.reset_requests_instrumentation()
    saved = {key: os.environ.get(key) for key in _BAGGAGE_ENV}
    yield
    baggage.reset_requests_instrumentation()
    for key in _BAGGAGE_ENV:
        if saved[key] is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = saved[key]


class TestW3cCodec:
    def test_vectors(self):
        for case in VECTORS["codec"]:
            name = case["name"]
            if name == "parse-empty":
                for raw in case["parse"]:
                    assert baggage.parse_baggage(raw) == {}
            elif name.startswith("parse-"):
                assert baggage.parse_baggage(case["header"]) == case["expected"]
            elif name.startswith("merge-"):
                result = baggage.merge_baggage(case["existing"], case["key"], case["value"])
                if "equals" in case:
                    assert result == case["equals"]
                for part in case.get("contains", []):
                    assert part in result
                for part in case.get("excludes", []):
                    assert part not in result
            elif name == "round-trip":
                assert baggage.serialize_baggage(baggage.parse_baggage(case["header"])) == case[
                    "header"
                ]


class TestContractVectors:
    def test_incoming(self):
        for case in VECTORS["resolveIncoming"]:
            got = baggage.incoming_session(
                case.get("role"),
                case.get("header"),
                case.get("cookie"),
                case.get("query"),
                case.get("sessionValue"),
                enabled=case.get("enabled", True),
            )
            assert got == case["expected"], case["name"]

    def test_outgoing(self):
        for case in VECTORS["resolveOutgoing"]:
            got = baggage.outgoing_session(
                case.get("role"), case.get("context"), case.get("sessionValue")
            )
            assert got == case["expected"], case["name"]


def _make_app(env_overrides):
    os.environ.update(env_overrides)
    test_app = Flask(__name__)
    baggage.install(test_app)

    @test_app.route("/check")
    def _check():
        return getattr(g, "dev_session", None) or ""

    return test_app


class TestForwarderHook:
    def test_extracts_header(self):
        app = _make_app({"BAGGAGE_ENABLED": "true", "BAGGAGE_ROLE": "forwarder"})
        assert app.test_client().get("/check", headers={"x-dev-session": "sess-1"}).data == b"sess-1"

    def test_no_header_yields_empty(self):
        app = _make_app({"BAGGAGE_ENABLED": "true", "BAGGAGE_ROLE": "forwarder"})
        assert app.test_client().get("/check").data == b""

    def test_does_not_mint(self):
        app = _make_app(
            {
                "BAGGAGE_ENABLED": "true",
                "BAGGAGE_ROLE": "forwarder",
                "BAGGAGE_SESSION_VALUE": "must-not-mint",
            }
        )
        assert app.test_client().get("/check").data == b""


class TestOriginatorHook:
    def test_uses_configured_value_when_nothing_incoming(self):
        app = _make_app(
            {
                "BAGGAGE_ENABLED": "true",
                "BAGGAGE_ROLE": "originator",
                "BAGGAGE_SESSION_VALUE": "orig-123",
            }
        )
        assert app.test_client().get("/check").data == b"orig-123"

    def test_preserves_original_override_header(self):
        app = _make_app(
            {
                "BAGGAGE_ENABLED": "true",
                "BAGGAGE_ROLE": "originator",
                "BAGGAGE_SESSION_VALUE": "orig-123",
            }
        )
        resp = app.test_client().get("/check", headers={"x-dev-session": "pr-42"})
        assert resp.data == b"pr-42"

    def test_query_is_original_override_when_no_header(self):
        app = _make_app(
            {
                "BAGGAGE_ENABLED": "true",
                "BAGGAGE_ROLE": "originator",
                "BAGGAGE_SESSION_VALUE": "orig-123",
            }
        )
        resp = app.test_client().get("/check?x-dev-session=pr-99")
        assert resp.data == b"pr-99"


class TestTerminalHook:
    def test_extracts_header(self):
        app = _make_app({"BAGGAGE_ENABLED": "true", "BAGGAGE_ROLE": "terminal"})
        resp = app.test_client().get("/check", headers={"x-dev-session": "term-val"})
        assert resp.data == b"term-val"


class TestProductionGuard:
    def test_middleware_inactive_when_disabled(self):
        app = _make_app({"BAGGAGE_ENABLED": "false", "BAGGAGE_ROLE": "forwarder"})
        resp = app.test_client().get("/check", headers={"x-dev-session": "should-not-extract"})
        assert resp.data == b""

    def test_middleware_inactive_when_env_missing(self):
        env = os.environ.copy()
        env.pop("BAGGAGE_ENABLED", None)
        with patch.dict(os.environ, env, clear=True):
            app = Flask(__name__)
            baggage.install(app)

            @app.route("/check")
            def _check():
                return getattr(g, "dev_session", None) or ""

            resp = app.test_client().get("/check", headers={"x-dev-session": "nope"})
            assert resp.data == b""


def _send(session):
    adapter = MagicMock()
    resp_mock = MagicMock(status_code=200, headers={}, encoding="utf-8")
    resp_mock.is_redirect = False
    resp_mock.content = b""
    adapter.send.return_value = resp_mock
    session.mount("http://", adapter)
    session.get("http://downstream/api")
    return adapter.send.call_args[0][0]


class TestOutgoing:
    def test_originator_sets_headers_from_mint(self):
        with patch.dict(
            os.environ,
            {
                "BAGGAGE_ENABLED": "true",
                "BAGGAGE_ROLE": "originator",
                "BAGGAGE_SESSION_VALUE": "orig-sess",
            },
        ):
            prepared = _send(baggage.BaggageSession())
            assert prepared.headers.get("x-dev-session") == "orig-sess"
            assert "dev-session=orig-sess" in prepared.headers.get("baggage", "")

    def test_plain_requests_is_instrumented(self):
        with patch.dict(
            os.environ,
            {
                "BAGGAGE_ENABLED": "true",
                "BAGGAGE_ROLE": "originator",
                "BAGGAGE_SESSION_VALUE": "orig-sess",
            },
        ):
            baggage.install()
            import requests

            prepared = _send(requests.Session())
            assert prepared.headers.get("x-dev-session") == "orig-sess"

    def test_forwarder_copies_original_from_flask_context(self):
        app = _make_app({"BAGGAGE_ENABLED": "true", "BAGGAGE_ROLE": "forwarder"})

        @app.route("/proxy")
        def _proxy():
            import requests

            prepared = _send(requests.Session())
            return prepared.headers.get("x-dev-session") or ""

        resp = app.test_client().get("/proxy", headers={"x-dev-session": "pr-42"})
        assert resp.data == b"pr-42"

    def test_terminal_never_sets_headers(self):
        with patch.dict(
            os.environ,
            {"BAGGAGE_ENABLED": "true", "BAGGAGE_ROLE": "terminal"},
        ):
            prepared = _send(baggage.BaggageSession())
            assert "x-dev-session" not in prepared.headers
