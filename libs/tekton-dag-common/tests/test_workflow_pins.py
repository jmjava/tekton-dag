"""SHA-pin helper coverage and Dependabot Action cadence."""

from pathlib import Path

import yaml

try:
    from .workflow_pins import SHA_PINNED_ACTION, assert_actions_sha_pinned
except ImportError:
    from workflow_pins import SHA_PINNED_ACTION, assert_actions_sha_pinned

ROOT = Path(__file__).resolve().parents[3]


def test_assert_actions_sha_pinned_accepts_any_digest():
    workflow = (
        "uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "uses: actions/setup-go@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
    )
    assert SHA_PINNED_ACTION.search(workflow)
    assert_actions_sha_pinned(workflow, "actions/checkout", "actions/setup-go")


def test_assert_actions_sha_pinned_rejects_mutable_tags():
    try:
        assert_actions_sha_pinned("uses: actions/checkout@v4\n", "actions/checkout")
    except AssertionError as exc:
        assert "actions/checkout" in str(exc)
    else:
        raise AssertionError("mutable tag should fail SHA-pin check")


def test_github_actions_dependabot_is_minor_patch_only():
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())
    actions = next(
        entry for entry in config["updates"] if entry["package-ecosystem"] == "github-actions"
    )
    groups = actions["groups"]
    update_types = {
        name: set(group.get("update-types") or [])
        for name, group in groups.items()
    }
    assert update_types
    assert all(types == {"minor", "patch"} for types in update_types.values())
