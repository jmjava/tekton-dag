"""Helpers for GitHub Actions SHA-pin assertions."""

from __future__ import annotations

import re

SHA_PINNED_ACTION = re.compile(r"uses:\s+(?P<action>[\w.-]+/[\w.-]+)@(?P<sha>[0-9a-f]{40})\b")


def assert_actions_sha_pinned(workflow: str, *actions: str) -> None:
    found = {match.group("action") for match in SHA_PINNED_ACTION.finditer(workflow)}
    missing = [action for action in actions if action not in found]
    assert not missing, f"SHA-pinned actions missing: {missing}"
