"""Pipeline reliability helpers: timeouts, retries, transient failure classification.

M13 pillars 1 and 4 — distinguish infrastructure failures (retry) from
application/test failures and OOM (do not blindly retry).
"""

from __future__ import annotations

import re
from typing import Any

# Reasons / messages that indicate transient infrastructure problems.
_TRANSIENT_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"node\s*lost",
        r"pod\s*evict",
        r"evicted",
        r"DeadlineExceeded",
        r"i/?o\s*timeout",
        r"connection\s*reset",
        r"temporary\s*failure",
        r"TLS handshake timeout",
        r"registry.*(timeout|unavailable|429|rate.?limit)",
        r"TOO_MANY_REQUESTS",
        r"ServerTimeout",
        r"UnexpectedAdmissionError",
        r"FailedScheduling",
        r"ImagePullBackOff",  # often registry flake; callers may still size-tune
    ]
]

_NON_RETRYABLE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"OOMKilled",
        r"OutOfMemory",
        r"Error\s*\(Exit\s*Code:\s*[1-9]",  # app exit codes (not 137 alone)
        r"tests?\s*failed",
        r"assertion",
        r"Newman\s*run\s*failed",
        r"Playwright.*failed",
        r"compilation\s*failed",
        r"BUILD FAILURE",
    ]
]

DEFAULT_PIPELINE_TIMEOUT = "2h"
DEFAULT_MAX_RETRIES = 2


def classify_failure(
    reason: str = "",
    message: str = "",
    exit_code: int | None = None,
) -> dict[str, Any]:
    """
    Classify a TaskRun/PipelineRun failure.

    Returns:
      {
        "category": "transient" | "oom" | "application" | "unknown",
        "retryable": bool,
        "reason": str,
      }
    """
    blob = f"{reason} {message}".strip()
    if exit_code == 137 or re.search(r"OOMKilled", blob, re.IGNORECASE):
        return {
            "category": "oom",
            "retryable": False,
            "reason": "OOMKilled — increase resource limits, do not retry blindly",
        }
    for pat in _NON_RETRYABLE_PATTERNS:
        if pat.search(blob):
            return {
                "category": "application",
                "retryable": False,
                "reason": f"non-retryable match: {pat.pattern}",
            }
    for pat in _TRANSIENT_PATTERNS:
        if pat.search(blob):
            return {
                "category": "transient",
                "retryable": True,
                "reason": f"transient match: {pat.pattern}",
            }
    if exit_code in (130, 137, 143):  # SIGINT/OOM/SIGTERM — 137 handled above
        return {
            "category": "unknown",
            "retryable": exit_code != 137,
            "reason": f"exit_code={exit_code}",
        }
    return {
        "category": "unknown",
        "retryable": False,
        "reason": "unclassified failure",
    }


def should_retry(
    *,
    reason: str = "",
    message: str = "",
    exit_code: int | None = None,
    attempt: int = 0,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> bool:
    """True when this failure should be retried given attempt/max_retries."""
    if attempt >= max_retries:
        return False
    return bool(classify_failure(reason, message, exit_code)["retryable"])


def apply_reliability(
    run: dict[str, Any],
    *,
    timeout: str | None = DEFAULT_PIPELINE_TIMEOUT,
    max_retries: int | None = DEFAULT_MAX_RETRIES,
) -> dict[str, Any]:
    """
    Mutate a PipelineRun dict to include timeout and max-retries param.

    - ``spec.timeouts.pipeline`` when timeout is a non-empty string
    - appends ``max-retries`` param when max_retries is not None
    """
    spec = run.setdefault("spec", {})
    if timeout:
        timeouts = spec.setdefault("timeouts", {})
        timeouts["pipeline"] = timeout
    if max_retries is not None:
        params = spec.setdefault("params", [])
        # Replace existing max-retries if present
        params[:] = [p for p in params if p.get("name") != "max-retries"]
        params.append({"name": "max-retries", "value": str(max_retries)})
    return run


def retry_annotation(attempt: int, original_reason: str) -> dict[str, str]:
    """Structured annotations for TaskRun retry post-mortems."""
    return {
        "tekton-dag.io/retry-attempt": str(attempt),
        "tekton-dag.io/retry-original-reason": (original_reason or "")[:200],
    }
