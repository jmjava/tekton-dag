"""Tests for reliability helpers."""

from tekton_dag_common.reliability import (
    DEFAULT_MAX_RETRIES,
    apply_reliability,
    classify_failure,
    retry_annotation,
    should_retry,
)


def test_classify_transient_node_lost():
    result = classify_failure(reason="Failed", message="node lost")
    assert result["category"] == "transient"
    assert result["retryable"] is True


def test_classify_transient_registry_rate_limit():
    result = classify_failure(message="registry 429 rate limit exceeded")
    assert result["retryable"] is True


def test_classify_oom_not_retryable():
    result = classify_failure(reason="OOMKilled", exit_code=137)
    assert result["category"] == "oom"
    assert result["retryable"] is False


def test_classify_test_failure_not_retryable():
    result = classify_failure(message="Newman run failed: 3 assertions")
    assert result["category"] == "application"
    assert result["retryable"] is False


def test_should_retry_respects_max():
    assert should_retry(message="pod evicted", attempt=0, max_retries=2) is True
    assert should_retry(message="pod evicted", attempt=2, max_retries=2) is False


def test_apply_reliability_sets_timeout_and_param():
    run = {"spec": {"params": [{"name": "git-url", "value": "u"}]}}
    apply_reliability(run, timeout="90m", max_retries=3)
    assert run["spec"]["timeouts"]["pipeline"] == "90m"
    params = {p["name"]: p["value"] for p in run["spec"]["params"]}
    assert params["max-retries"] == "3"
    assert params["git-url"] == "u"


def test_apply_reliability_replaces_existing_max_retries():
    run = {
        "spec": {
            "params": [{"name": "max-retries", "value": "1"}],
            "timeouts": {"pipeline": "1h"},
        }
    }
    apply_reliability(run, timeout="2h", max_retries=DEFAULT_MAX_RETRIES)
    assert run["spec"]["timeouts"]["pipeline"] == "2h"
    values = [p["value"] for p in run["spec"]["params"] if p["name"] == "max-retries"]
    assert values == ["2"]


def test_retry_annotation():
    ann = retry_annotation(1, "DeadlineExceeded")
    assert ann["tekton-dag.io/retry-attempt"] == "1"
    assert "DeadlineExceeded" in ann["tekton-dag.io/retry-original-reason"]
