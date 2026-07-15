"""Tests for GitHub webhook HMAC verification."""

import webhook_auth


def test_compute_and_verify_signature():
    body = b'{"action":"opened"}'
    secret = "topsecret"
    sig = webhook_auth.compute_signature(secret, body)
    assert sig.startswith("sha256=")
    assert webhook_auth.verify_signature(secret, body, sig) is True


def test_verify_rejects_bad_signature():
    body = b'{"action":"opened"}'
    assert webhook_auth.verify_signature("secret", body, "sha256=deadbeef") is False


def test_verify_rejects_missing_header_when_secret_set():
    assert webhook_auth.verify_signature("secret", b"{}", None) is False
    assert webhook_auth.verify_signature("secret", b"{}", "") is False


def test_verify_allows_when_secret_empty():
    assert webhook_auth.verify_signature("", b"{}", None) is True


def test_resolve_webhook_secret_prefers_configured():
    def fetch(_name, namespace=""):
        raise AssertionError("should not fetch")

    assert (
        webhook_auth.resolve_webhook_secret(
            configured_secret="from-env",
            secret_name="github-webhook-secret",
            fetch_secret=fetch,
        )
        == "from-env"
    )


def test_resolve_webhook_secret_from_k8s():
    def fetch(name, namespace=""):
        assert name == "github-webhook-secret"
        return {"secret": "from-k8s"}

    assert (
        webhook_auth.resolve_webhook_secret(
            configured_secret="",
            secret_name="github-webhook-secret",
            namespace="ns",
            fetch_secret=fetch,
        )
        == "from-k8s"
    )
