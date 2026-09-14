"""Tests for shared API authentication primitives."""

from tekton_dag_common.api_auth import bearer_token_matches


def test_bearer_token_matches_valid_token():
    assert bearer_token_matches("Bearer expected-token", "expected-token")
    assert bearer_token_matches("bearer expected-token", "expected-token")


def test_bearer_token_rejects_missing_malformed_and_invalid_values():
    assert not bearer_token_matches(None, "expected-token")
    assert not bearer_token_matches("Basic expected-token", "expected-token")
    assert not bearer_token_matches("Bearer", "expected-token")
    assert not bearer_token_matches("Bearer wrong-token", "expected-token")
    assert not bearer_token_matches("Bearer expected-token", "")
