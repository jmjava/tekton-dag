from pathlib import Path

from tekton_dag_common.baggage_contract import (
    apply_outgoing_headers,
    doctor_stack,
    emit_env,
    find_app,
    incoming_session,
    infer_role,
    load_stack_yaml,
    load_vectors,
    merge_baggage,
    outgoing_session,
    parse_baggage,
    serialize_baggage,
    stack_propagation,
)

VECTORS = load_vectors()
ROOT = Path(__file__).resolve().parents[3]


def test_codec_vectors():
    for case in VECTORS["codec"]:
        name = case["name"]
        if name == "parse-empty":
            for raw in case["parse"]:
                assert parse_baggage(raw) == {}
        elif name.startswith("parse-"):
            assert parse_baggage(case["header"]) == case["expected"]
        elif name.startswith("merge-"):
            result = merge_baggage(case["existing"], case["key"], case["value"])
            if "equals" in case:
                assert result == case["equals"]
            for part in case.get("contains", []):
                assert part in result
            for part in case.get("excludes", []):
                assert part not in result
        elif name == "round-trip":
            assert serialize_baggage(parse_baggage(case["header"])) == case["header"]


def test_incoming_vectors_preserve_original_override():
    for case in VECTORS["resolveIncoming"]:
        got = incoming_session(
            case.get("role"),
            case.get("header"),
            case.get("cookie"),
            case.get("query"),
            case.get("sessionValue"),
            enabled=case.get("enabled", True),
        )
        assert got == case["expected"], case["name"]


def test_outgoing_vectors_never_rewrite():
    for case in VECTORS["resolveOutgoing"]:
        got = outgoing_session(case.get("role"), case.get("context"), case.get("sessionValue"))
        assert got == case["expected"], case["name"]


def test_apply_outgoing_copies_original_header():
    headers = apply_outgoing_headers(
        {"baggage": "traceId=abc"},
        role="forwarder",
        context_value="pr-42",
    )
    assert headers["x-dev-session"] == "pr-42"
    assert "dev-session=pr-42" in headers["baggage"]
    assert "traceId=abc" in headers["baggage"]


def test_infer_role_matches_resolve_stack():
    assert infer_role({"role": "frontend", "downstream": ["api"]}) == "originator"
    assert infer_role({"role": "middleware", "downstream": ["api"]}) == "forwarder"
    assert infer_role({"role": "persistence", "downstream": []}) == "terminal"
    assert infer_role({"propagation-role": "originator", "downstream": []}) == "originator"


def test_stack_one_emit_and_doctor():
    stack = load_stack_yaml(ROOT / "stacks" / "stack-one.yaml")
    assert stack is not None
    report = doctor_stack(stack, stack_label="stack-one")
    assert report["ok"]
    by_name = {c["app"]: c["role"] for c in report["apps"]}
    assert by_name == {
        "demo-fe": "originator",
        "release-lifecycle-demo": "forwarder",
        "demo-api": "terminal",
    }
    assert stack_propagation(stack)["header_name"] == "x-dev-session"
    fe = emit_env(
        {
            "role": "originator",
            "header_name": "x-dev-session",
            "baggage_key": "dev-session",
        },
        "vite",
    )
    assert "VITE_BAGGAGE_ROLE=originator" in fe
    assert find_app(stack, "demo-api")["name"] == "demo-api"


def test_originator_must_not_overwrite_incoming_pr_header():
    """The override for a container in the stack is the incoming value."""
    assert incoming_session("originator", header="pr-42", session_value="local-debug") == "pr-42"
    assert outgoing_session("originator", "pr-42", "local-debug") == "pr-42"
