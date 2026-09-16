"""Guards that remaining default-branch CI stays closable to green."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_dependabot_groups_reject_breaking_majors():
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text())
    for entry in config["updates"]:
        groups = entry.get("groups") or {}
        assert groups, f"{entry['package-ecosystem']} must group updates"
        for name, group in groups.items():
            types = set(group.get("update-types") or [])
            assert "major" not in types, f"{name} must not auto-open majors"
            assert types <= {"minor", "patch"}
            if entry["package-ecosystem"] == "gomod":
                assert types == {"patch"}


def test_dependency_review_skips_when_graph_unavailable():
    workflow = (ROOT / ".github/workflows/dependency-review.yml").read_text()

    assert "actions/dependency-review-action@" in workflow
    assert "continue-on-error: true" in workflow
    assert "dependency-graph/compare/" in workflow
    assert "skipping review" in workflow
