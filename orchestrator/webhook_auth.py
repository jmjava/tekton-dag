"""GitHub webhook HMAC signature verification (M13 / security hardening)."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

logger = logging.getLogger("orchestrator.webhook_auth")

# Resolution outcomes for webhook secret lookup.
STATUS_OK = "ok"
STATUS_UNSET = "unset"  # no env secret and no secret name configured
STATUS_MISSING = "missing"  # named Secret not found / empty keys
STATUS_UNAVAILABLE = "unavailable"  # fetch failed (e.g. no kubeconfig)


def compute_signature(secret: str, body: bytes) -> str:
    """Return GitHub-style ``sha256=<hex>`` signature for body."""
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, body: bytes, header_value: Optional[str]) -> bool:
    """
    Validate ``X-Hub-Signature-256`` against the request body.

    Returns False when secret is non-empty and the header is missing/invalid.
    """
    if not secret:
        return True
    if not header_value:
        logger.warning("Webhook rejected: missing X-Hub-Signature-256")
        return False
    expected = compute_signature(secret, body)
    if not hmac.compare_digest(expected, header_value.strip()):
        logger.warning("Webhook rejected: invalid signature")
        return False
    return True


def _extract_secret_value(data: dict) -> str:
    for key in ("secret", "value", "webhook-secret"):
        if key in data and data[key]:
            return data[key]
    return ""


def resolve_webhook_secret(
    *,
    configured_secret: str = "",
    secret_name: str = "",
    namespace: str = "tekton-pipelines",
    fetch_secret=None,
) -> str:
    """
    Resolve the webhook HMAC secret (legacy helper).

    Preference order:
      1. ``configured_secret`` (env WEBHOOK_SECRET)
      2. Kubernetes Secret ``secret_name`` key ``secret`` (or ``value``)
    """
    secret, _status = resolve_webhook_secret_status(
        configured_secret=configured_secret,
        secret_name=secret_name,
        namespace=namespace,
        fetch_secret=fetch_secret,
    )
    return secret


def resolve_webhook_secret_status(
    *,
    configured_secret: str = "",
    secret_name: str = "",
    namespace: str = "tekton-pipelines",
    fetch_secret=None,
) -> tuple[str, str]:
    """
    Resolve webhook secret and a status code.

    Returns:
      (secret, status) where status is one of STATUS_* constants.
    """
    if configured_secret:
        return configured_secret, STATUS_OK
    if not secret_name:
        return "", STATUS_UNSET
    if fetch_secret is None:
        return "", STATUS_UNAVAILABLE
    try:
        data = fetch_secret(secret_name, namespace=namespace)
    except Exception as exc:
        logger.debug("Webhook secret fetch failed: %s", exc)
        return "", STATUS_UNAVAILABLE
    if not data:
        return "", STATUS_MISSING
    value = _extract_secret_value(data)
    if not value:
        return "", STATUS_MISSING
    return value, STATUS_OK
