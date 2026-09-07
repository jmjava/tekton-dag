"""Isolation evaluation protocol: stack width, cost model, probe interpretation, CSV.

This is the research harness *measurement contract*. Cluster runs fill the same
columns; offline/self-test only checks the contract and estimated (not measured) costs.

Paper numbers must come from ``scripts/run-isolation-eval.sh --cluster``.
"""

from __future__ import annotations

import csv
import io
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CSV_FIELDS = [
    "timestamp_utc",
    "run_id",
    "mode",  # estimated | measured | self-test
    "strategy",  # clone | intercept
    "stack_file",
    "stack_width",
    "changed_app",
    "repeat",
    "keep_baseline",
    "wall_clock_s",
    "pod_count",
    "matched_body",
    "unmatched_body",
    "matched_ok",
    "unmatched_ok",
    "isolation_ok",
    "notes",
]

DEFAULT_STACKS = (
    "stacks/single-app.yaml",
    "stacks/stack-one.yaml",
    "stacks/stack-two-vendor.yaml",
)


@dataclass(frozen=True)
class ProbeOutcome:
    matched_body: str
    unmatched_body: str
    expected_pr: str
    expected_baseline: str
    strategy: str

    @property
    def matched_ok(self) -> bool:
        return self.expected_pr in self.matched_body

    @property
    def unmatched_ok(self) -> bool:
        if self.strategy == "clone":
            # PR namespace has no baseline replica: unmatched still hits PR.
            return self.expected_pr in self.unmatched_body
        if self.strategy == "intercept":
            return self.expected_baseline in self.unmatched_body and self.expected_pr not in self.unmatched_body
        raise ValueError(f"unknown strategy {self.strategy}")

    @property
    def isolation_ok(self) -> bool:
        return self.matched_ok and self.unmatched_ok


def stack_width(stack_path: str | Path) -> int:
    """Count app nodes in a stack YAML (requires PyYAML)."""
    import yaml

    data = yaml.safe_load(Path(stack_path).read_text())
    apps = data.get("apps") or []
    if not isinstance(apps, list):
        raise ValueError(f"{stack_path}: apps is not a list")
    return len(apps)


def stack_app_names(stack_path: str | Path) -> list[str]:
    import yaml

    data = yaml.safe_load(Path(stack_path).read_text())
    return [a["name"] for a in (data.get("apps") or [])]


def default_changed_app(stack_path: str | Path) -> str:
    names = stack_app_names(stack_path)
    if not names:
        raise ValueError(f"{stack_path}: no apps")
    return names[0]


def estimate_pod_count(strategy: str, width: int, keep_baseline: bool = True) -> int:
    """Pods implied by the strategy (dummy HTTP servers, not Kaniko).

    clone: optional shared baseline (width) + a full PR namespace (width).
    intercept: baseline (width) + one PR replica + one header router.
    """
    if width < 1:
        raise ValueError("width must be >= 1")
    if strategy == "clone":
        return (width if keep_baseline else 0) + width
    if strategy == "intercept":
        return width + 2
    raise ValueError(f"unknown strategy {strategy}")


def experiment_cells(
    stack_files: Iterable[str | Path],
    strategies: Iterable[str] = ("clone", "intercept"),
    repeats: int = 1,
    keep_baseline: bool = True,
) -> list[dict]:
    cells = []
    for stack in stack_files:
        path = Path(stack)
        width = stack_width(path)
        changed = default_changed_app(path)
        for strategy in strategies:
            for repeat in range(1, repeats + 1):
                cells.append(
                    {
                        "strategy": strategy,
                        "stack_file": str(path).replace("\\", "/"),
                        "stack_width": width,
                        "changed_app": changed,
                        "repeat": repeat,
                        "keep_baseline": keep_baseline,
                        "estimated_pod_count": estimate_pod_count(strategy, width, keep_baseline),
                    }
                )
    return cells


def write_csv(rows: Iterable[dict], dest: str | Path | io.StringIO) -> None:
    rows = list(rows)
    if isinstance(dest, io.StringIO):
        fh = dest
        close = False
    else:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        fh = dest.open("w", newline="")
        close = True
    try:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})
    finally:
        if close:
            fh.close()


def outcome_to_row(base: dict, outcome: ProbeOutcome, **extra) -> dict:
    row = {k: base.get(k, "") for k in CSV_FIELDS}
    row.update(
        {
            "matched_body": outcome.matched_body,
            "unmatched_body": outcome.unmatched_body,
            "matched_ok": str(outcome.matched_ok).lower(),
            "unmatched_ok": str(outcome.unmatched_ok).lower(),
            "isolation_ok": str(outcome.isolation_ok).lower(),
        }
    )
    row.update(extra)
    return row


def as_public_dict(obj) -> dict:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return dict(obj)
