"""GitHub webhook HMAC signature verification (M13 / security hardening)."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

logger = logging.getLogger("orchestrator.webhook_auth")


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


def resolve_webhook_secret(
    *,
    configured_secret: str = "",
    secret_name: str = "",
    namespace: str = "tekton-pipelines",
    fetch_secret=None,
) -> str:
    """
    Resolve the webhook HMAC secret.

    Preference order:
      1. ``configured_secret`` (env WEBHOOK_SECRET) — for local/tests
      2. Kubernetes Secret ``secret_name`` key ``secret`` (or ``value``)
    """
    if configured_secret:
        return configured_secret
    if not secret_name or fetch_secret is None:
        return ""
    data = fetch_secret(secret_name, namespace=namespace) or {}
    for key in ("secret", "value", "webhook-secret"):
        if key in data and data[key]:
            return data[key]
    return ""
