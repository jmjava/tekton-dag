#!/usr/bin/env python3
"""Ruff ratchets.

  cayc      Fail when a finding that is not in the frozen baseline sits on a
            changed line.
  baseline  Fail when any current finding is not covered by the frozen baseline.

The baseline file is never rewritten. --write-baseline is refused.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "ruff" / "ruff.toml"
BASELINE = ROOT / "config" / "ruff" / "baseline.txt"
BASE_REF = os.environ.get("RATCHET_BASE", "origin/main")
SCOPE_PREFIXES = (
    "libs/tekton-dag-common/tekton_dag_common/",
    "libs/baggage-python/tekton_dag_baggage/",
    "orchestrator/",
    "management-gui/backend/",
)


def in_scope(path: str) -> bool:
    if "/tests/" in path or path.startswith("tests/"):
        return False
    if not any((ROOT / prefix.rstrip("/")).is_dir() for prefix in SCOPE_PREFIXES):
        return path.endswith(".py")
    return path.startswith(SCOPE_PREFIXES)


def lint_paths() -> list[str]:
    existing = [prefix.rstrip("/") for prefix in SCOPE_PREFIXES if (ROOT / prefix.rstrip("/")).is_dir()]
    return existing or ["."]


def refuse_rewrite(argv: list[str]) -> None:
    blocked = {"--write-baseline", "--create-baseline", "-cb"}
    if blocked.intersection(argv):
        sys.stderr.write("refusing to rewrite the ruff baseline\n")
        raise SystemExit(1)


def run_ruff(paths: list[str] | None = None) -> list[dict]:
    cmd = [
        "ruff",
        "check",
        "--config",
        str(CONFIG),
        "--output-format",
        "json",
        "--exit-zero",
    ]
    cmd.extend(paths or lint_paths())
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit(result.returncode or 1)
    text = result.stdout.strip() or "[]"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(1) from None
    return payload if isinstance(payload, list) else []


def rel_path(filename: str) -> str:
    path = Path(filename)
    if path.is_absolute():
        try:
            path = path.relative_to(ROOT)
        except ValueError:
            return filename.replace("\\", "/")
    return path.as_posix()


def findings_from_ruff(payload: list[dict]) -> list[tuple[str, str, int]]:
    rows: list[tuple[str, str, int]] = []
    for item in payload:
        code = str(item.get("code") or "")
        filename = rel_path(str(item.get("filename") or ""))
        location = item.get("location") or {}
        line = int(location.get("row") or 0)
        if code and filename and line:
            rows.append((filename, code, line))
    return rows


def load_baseline(path: Path) -> Counter[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter()
    if not path.is_file():
        sys.stderr.write(f"missing ruff baseline: {path}\n")
        raise SystemExit(1)
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        filename, code = line.split("\t", 1)
        counts[(filename, code)] += 1
    return counts


def git_text(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode or 1)
    return result.stdout


def require_base() -> None:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", BASE_REF],
        cwd=ROOT,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.write(f"{BASE_REF} is required\n")
        raise SystemExit(1)


def changed_python() -> list[str]:
    names: set[str] = set()
    chunks = [
        git_text("diff", "--name-only", "--diff-filter=ACMR", f"{BASE_REF}...HEAD"),
        git_text("diff", "--name-only", "--diff-filter=ACMR"),
        git_text("diff", "--name-only", "--diff-filter=ACMR", "--cached"),
        git_text("ls-files", "--others", "--exclude-standard"),
    ]
    for chunk in chunks:
        for line in chunk.splitlines():
            path = line.strip()
            if path.endswith(".py") and in_scope(path):
                names.add(path)
    return sorted(path for path in names if (ROOT / path).is_file())


def changed_lines() -> dict[str, set[int]]:
    acc: dict[str, set[int]] = {}

    def parse(diff: str) -> None:
        path = None
        for line in diff.splitlines():
            if line.startswith("+++ b/"):
                path = line[6:]
                if path == "/dev/null":
                    path = None
                continue
            if path is None or not line.startswith("@@"):
                continue
            plus = line.split(" ")[2][1:]
            if "," in plus:
                start_s, count_s = plus.split(",", 1)
                start, count = int(start_s), int(count_s)
            else:
                start, count = int(plus), 1
            if count <= 0:
                continue
            acc.setdefault(path, set()).update(range(start, start + count))

    parse(git_text("diff", "-U0", "--diff-filter=ACMR", f"{BASE_REF}...HEAD"))
    parse(git_text("diff", "-U0", "--diff-filter=ACMR"))
    parse(git_text("diff", "-U0", "--diff-filter=ACMR", "--cached"))
    for rel in git_text("ls-files", "--others", "--exclude-standard").splitlines():
        rel = rel.strip()
        if not rel.endswith(".py") or not in_scope(rel):
            continue
        full = ROOT / rel
        if not full.is_file():
            continue
        count = sum(1 for _ in full.open(encoding="utf-8", errors="replace"))
        if count:
            acc.setdefault(rel, set()).update(range(1, count + 1))
    return acc


def extras(
    rows: list[tuple[str, str, int]],
    baseline: Counter[tuple[str, str]],
    prefer_unchanged: dict[str, set[int]] | None,
) -> list[tuple[str, str, int]]:
    remaining = baseline.copy()

    def unchanged(row: tuple[str, str, int]) -> bool:
        if prefer_unchanged is None:
            return False
        path, _code, line = row
        return line not in prefer_unchanged.get(path, set())

    ordered = sorted(rows, key=lambda row: (not unchanged(row), row))
    overflow: list[tuple[str, str, int]] = []
    for row in ordered:
        key = (row[0], row[1])
        if remaining[key] > 0:
            remaining[key] -= 1
        else:
            overflow.append(row)
    return overflow


def print_current() -> None:
    for path, code, _line in sorted(findings_from_ruff(run_ruff())):
        sys.stdout.write(f"{path}\t{code}\n")


def mode_baseline() -> int:
    baseline = load_baseline(BASELINE)
    overflow = extras(findings_from_ruff(run_ruff()), baseline, None)
    if overflow:
        sys.stderr.write("ruff baseline: new findings are not in the frozen baseline\n")
        for path, code, line in overflow:
            sys.stderr.write(f"  {path}:{line}: {code}\n")
        return 1
    print("ruff baseline: no new findings")
    return 0


def mode_cayc() -> int:
    require_base()
    files = changed_python()
    if not files:
        print(f"ruff clean-as-you-code: no Python changes versus {BASE_REF}")
        return 0
    lines = changed_lines()
    baseline = load_baseline(BASELINE)
    overflow = extras(findings_from_ruff(run_ruff(files)), baseline, lines)
    gated = [row for row in overflow if row[2] in lines.get(row[0], set())]
    if gated:
        sys.stderr.write("clean-as-you-code failed on changed lines:\n")
        for path, code, line in gated:
            sys.stderr.write(f"  {path}:{line}: {code}\n")
        return 1
    print("ruff clean-as-you-code: no new findings on changed lines")
    return 0


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def self_test() -> None:
    if shutil.which("ruff") is None:
        sys.stderr.write("ruff is required for the self-test\n")
        raise SystemExit(1)
    global ROOT, CONFIG, BASELINE, BASE_REF
    original = (ROOT, CONFIG, BASELINE, BASE_REF)
    tmp = Path(tempfile.mkdtemp(prefix="ruff-ratchet-"))
    try:
        ROOT, BASE_REF = tmp, "origin/main"
        CONFIG = tmp / "config" / "ruff" / "ruff.toml"
        BASELINE = tmp / "config" / "ruff" / "baseline.txt"
        CONFIG.parent.mkdir(parents=True)
        CONFIG.write_text(
            'line-length = 100\ntarget-version = "py312"\n\n[lint]\nselect = ["F"]\n',
            encoding="utf-8",
        )
        git(tmp, "init", "-q")
        git(tmp, "config", "user.email", "ratchet@example.com")
        git(tmp, "config", "user.name", "ratchet")
        (tmp / "pkg").mkdir()
        (tmp / "pkg" / "mod.py").write_text("import os\n\nvalue = 1\n", encoding="utf-8")
        git(tmp, "add", "pkg")
        git(tmp, "commit", "-q", "-m", "init")
        git(tmp, "update-ref", "refs/remotes/origin/main", "HEAD")
        rows = findings_from_ruff(run_ruff())
        BASELINE.write_text(
            "".join(f"{path}\t{code}\n" for path, code, _line in sorted(rows)),
            encoding="utf-8",
        )
        if mode_baseline() != 0:
            raise SystemExit("ruff self-test: frozen findings must pass baseline")
        if mode_cayc() != 0:
            raise SystemExit("ruff self-test: clean tree must pass cayc")
        (tmp / "pkg" / "mod.py").write_text(
            "import os\nimport sys\n\nvalue = 1\n",
            encoding="utf-8",
        )
        git(tmp, "add", "pkg/mod.py")
        git(tmp, "commit", "-q", "-m", "new unused import")
        if mode_baseline() == 0 or mode_cayc() == 0:
            raise SystemExit("ruff self-test: a new finding on a changed line must fail")
        print("ruff self-test: baseline and clean-as-you-code OK")
    finally:
        ROOT, CONFIG, BASELINE, BASE_REF = original
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    argv = sys.argv[1:]
    refuse_rewrite(argv)
    if "--self-test" in argv:
        self_test()
        return
    if "--print-current" in argv:
        print_current()
        return
    mode = argv[0] if argv else ""
    if mode == "baseline":
        raise SystemExit(mode_baseline())
    if mode == "cayc":
        raise SystemExit(mode_cayc())
    sys.stderr.write("usage: ruff-ratchet.py cayc|baseline|--print-current|--self-test\n")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
