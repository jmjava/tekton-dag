from pathlib import Path

import pytest

from protocol import (
    ProbeOutcome,
    estimate_pod_count,
    experiment_cells,
    stack_app_names,
    stack_width,
    write_csv,
)

ROOT = Path(__file__).resolve().parents[2]


def test_stack_widths():
    assert stack_width(ROOT / "stacks/single-app.yaml") == 1
    assert stack_width(ROOT / "stacks/stack-one.yaml") == 3
    assert stack_width(ROOT / "stacks/stack-two-vendor.yaml") == 5


def test_default_apps():
    assert stack_app_names(ROOT / "stacks/stack-one.yaml")[0] == "demo-fe"


def test_pod_model_clone_vs_intercept():
    # clone keeps baseline + PR copy; intercept is baseline + PR replica + router
    assert estimate_pod_count("clone", 3, keep_baseline=True) == 6
    assert estimate_pod_count("clone", 3, keep_baseline=False) == 3
    assert estimate_pod_count("intercept", 3) == 5
    assert estimate_pod_count("intercept", 1) == 3
    with pytest.raises(ValueError):
        estimate_pod_count("clone", 0)


def test_intercept_probes():
    ok = ProbeOutcome(
        matched_body="pr/demo-fe/app-0",
        unmatched_body="baseline/app-0",
        expected_pr="pr/demo-fe",
        expected_baseline="baseline/",
        strategy="intercept",
    )
    assert ok.isolation_ok
    steal = ProbeOutcome(
        matched_body="pr/demo-fe/app-0",
        unmatched_body="pr/demo-fe/app-0",
        expected_pr="pr/demo-fe",
        expected_baseline="baseline/",
        strategy="intercept",
    )
    assert steal.matched_ok and not steal.unmatched_ok


def test_clone_probes():
    ok = ProbeOutcome(
        matched_body="pr/demo-fe/app-0",
        unmatched_body="pr/demo-fe/app-0",
        expected_pr="pr/demo-fe",
        expected_baseline="baseline/",
        strategy="clone",
    )
    assert ok.isolation_ok


def test_experiment_matrix_and_csv(tmp_path):
    cells = experiment_cells(
        [ROOT / "stacks/single-app.yaml", ROOT / "stacks/stack-one.yaml"],
        repeats=2,
    )
    # 2 stacks × 2 strategies × 2 repeats
    assert len(cells) == 8
    widths = {c["stack_width"] for c in cells}
    assert widths == {1, 3}
    dest = tmp_path / "out.csv"
    write_csv(
        [
            {
                "timestamp_utc": "t",
                "run_id": "r",
                "mode": "self-test",
                "strategy": c["strategy"],
                "stack_file": c["stack_file"],
                "stack_width": c["stack_width"],
                "changed_app": c["changed_app"],
                "repeat": c["repeat"],
                "keep_baseline": c["keep_baseline"],
                "pod_count": c["estimated_pod_count"],
                "isolation_ok": "",
                "notes": "plan",
            }
            for c in cells
        ],
        dest,
    )
    text = dest.read_text()
    assert text.startswith("timestamp_utc,")
    assert "clone" in text and "intercept" in text
