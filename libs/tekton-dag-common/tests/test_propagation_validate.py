from pathlib import Path

from tekton_dag_common.baggage_contract import apply_outgoing_headers, incoming_session, outgoing_session
from tekton_dag_common.propagation_validate import (
    aliases_from_stack,
    evaluate_propagation,
    format_report,
    simulate_chain,
)

ROOT = Path(__file__).resolve().parents[3]


NESTED_OK = {
    "app": "demo-fe",
    "session": "pr-42",
    "hops": [
        {
            "app": "release-lifecycle-demo",
            "session": "pr-42",
            "hops": [{"app": "demo-api", "session": "pr-42"}],
        }
    ],
}

CHAIN = "demo-fe release-lifecycle-demo demo-api"


def test_nested_hop_report_passes_when_original_is_copied():
    report = evaluate_propagation(
        NESTED_OK,
        chain=CHAIN,
        header_value="pr-42",
        build_apps="demo-api",
        roles={
            "demo-fe": "originator",
            "release-lifecycle-demo": "forwarder",
            "demo-api": "terminal",
        },
    )
    assert report.ok, report.failures
    assert report.header_found
    assert not report.rewritten
    assert [h.status for h in report.hops] == ["PASS", "PASS", "PASS"]
    assert all(h.session == "pr-42" for h in report.hops)


def test_missing_original_header_fails_closed():
    body = {
        "app": "demo-fe",
        "hops": [{"app": "release-lifecycle-demo"}, {"app": "demo-api"}],
    }
    report = evaluate_propagation(body, chain=CHAIN, header_value="pr-42", build_apps="demo-api")
    assert not report.ok
    assert any("missing" in f for f in report.failures)


def test_rewritten_header_fails_closed():
    body = {
        "app": "demo-fe",
        "session": "pr-42",
        "hops": [
            {
                "app": "release-lifecycle-demo",
                "session": "local-debug",
                "hops": [{"app": "demo-api", "session": "local-debug"}],
            }
        ],
    }
    report = evaluate_propagation(body, chain=CHAIN, header_value="pr-42", build_apps="demo-api")
    assert not report.ok
    assert report.rewritten
    assert any("rewritten" in f for f in report.failures)


def test_unreached_required_hop_fails():
    body = {"app": "demo-fe", "session": "pr-42"}
    report = evaluate_propagation(body, chain=CHAIN, header_value="pr-42", build_apps="demo-api")
    assert not report.ok
    assert any("demo-api" in f for f in report.failures)


def test_beyond_deepest_intercept_does_not_require_header():
    body = {
        "app": "demo-fe",
        "session": "pr-42",
        "hops": [{"app": "release-lifecycle-demo", "session": "pr-42"}],
    }
    report = evaluate_propagation(
        body,
        chain=CHAIN,
        header_value="pr-42",
        build_apps="release-lifecycle-demo",
    )
    assert report.ok, report.failures
    assert report.hops[2].status == "OK"
    assert not report.hops[2].required


def test_unstructured_text_still_requires_original_value():
    report = evaluate_propagation(
        "tekton-dag-vue-fe release-lifecycle-demo demo-api",
        chain=CHAIN,
        header_value="pr-42",
        build_apps="demo-api",
    )
    assert not report.ok
    assert any("missing" in f for f in report.failures)

    ok = evaluate_propagation(
        "demo-fe release-lifecycle-demo demo-api pr-42",
        chain=CHAIN,
        header_value="pr-42",
        build_apps="demo-api",
    )
    assert ok.ok, ok.failures


def test_unreachable_originator_fails_on_multi_hop():
    report = evaluate_propagation(
        '{"error":"unreachable"}',
        chain=CHAIN,
        header_value="pr-42",
        build_apps="demo-api",
    )
    assert not report.ok
    assert any("unreachable" in f for f in report.failures)


def test_single_app_health_does_not_require_header():
    report = evaluate_propagation("tekton-dag-flask", chain="demo-api", header_value="pr-42")
    assert report.ok, report.failures


def test_simulate_chain_never_rewrites_pr_header():
    apps = [
        {"name": "demo-fe", "role": "frontend", "downstream": ["bff"], "propagation-role": "originator"},
        {"name": "bff", "role": "middleware", "downstream": ["api"], "propagation-role": "forwarder"},
        {"name": "api", "role": "persistence", "downstream": [], "propagation-role": "terminal"},
    ]
    simulated = simulate_chain(apps, incoming_header="pr-42", mint_value="local-debug")
    assert [h["session"] for h in simulated["hops"]] == ["pr-42", "pr-42", "pr-42"]
    assert simulated["hops"][0]["outgoing"] == "pr-42"
    assert simulated["hops"][1]["outgoing"] == "pr-42"
    assert simulated["hops"][2]["outgoing"] is None
    assert simulated["final_outgoing"] == {}

    report = evaluate_propagation(
        simulated["report"],
        chain="demo-fe bff api",
        header_value="pr-42",
        build_apps="api",
    )
    assert report.ok, report.failures


def test_contract_helpers_match_simulate_invariant():
    adopted = incoming_session("originator", header="pr-42", session_value="minted")
    assert adopted == "pr-42"
    headers = apply_outgoing_headers({}, role="forwarder", context_value=adopted)
    assert headers["x-dev-session"] == "pr-42"
    assert outgoing_session("terminal", adopted) is None


def test_format_report_mentions_fail_closed_and_original():
    report = evaluate_propagation("{}", chain=CHAIN, header_value="pr-42", build_apps="demo-api")
    text = format_report(report)
    assert "FAIL:" in text
    assert "pr-42" in text


def test_task_is_fail_closed():
    task = (ROOT / "tasks/validate-propagation.yaml").read_text()
    assert "exit 1" in task
    assert "original override" in task
    assert "rewritten" in task
    assert "/propagation" in task
    assert "FAIL:" in task


def test_repo_basename_alias_counts_as_reached():
    body = {
        "app": "tekton-dag-vue-fe",
        "session": "pr-42",
        "hops": [{"app": "tekton-dag-spring-boot", "session": "pr-42"}],
    }
    report = evaluate_propagation(
        body,
        chain="demo-fe release-lifecycle-demo",
        header_value="pr-42",
        build_apps="release-lifecycle-demo",
        aliases={
            "demo-fe": ["demo-fe", "tekton-dag-vue-fe"],
            "release-lifecycle-demo": ["release-lifecycle-demo", "tekton-dag-spring-boot"],
        },
    )
    assert report.ok, report.failures


def test_aliases_from_stack_one():
    from tekton_dag_common.stack_resolver_base import load_stack_yaml

    stack = load_stack_yaml(ROOT / "stacks" / "stack-one.yaml")
    aliases = aliases_from_stack(stack)
    assert "tekton-dag-vue-fe" in aliases["demo-fe"]
    assert "tekton-dag-spring-boot" in aliases["release-lifecycle-demo"]


def test_stack_one_simulate_cli_shape():
    stack_apps = [
        {"name": "demo-fe", "role": "frontend", "downstream": ["release-lifecycle-demo"]},
        {"name": "release-lifecycle-demo", "role": "middleware", "downstream": ["demo-api"]},
        {"name": "demo-api", "role": "persistence", "downstream": []},
    ]
    simulated = simulate_chain(stack_apps, incoming_header="pr-42")
    assert simulated["hops"][0]["role"] == "originator"
    assert simulated["hops"][1]["role"] == "forwarder"
    assert simulated["hops"][2]["role"] == "terminal"
    assert all(h["session"] == "pr-42" for h in simulated["hops"])
