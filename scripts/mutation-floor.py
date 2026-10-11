#!/usr/bin/env python3
"""Fail when a mutmut cache scores under the frozen floor.

Reads the sqlite cache written by mutmut 2.5. Does not run mutation itself.
Killed mutants are ok_killed. Survived, timeout, and suspicious mutants count
against the score. Untested mutants fail the run. Skipped mutants are ignored.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import tempfile
from pathlib import Path

KILLED = "ok_killed"
AGAINST = ("bad_survived", "bad_timeout", "ok_suspicious")
UNTESTED = "untested"


def read_floor(path: Path) -> int:
    text = path.read_text(encoding="utf-8").strip()
    if not text.isdigit():
        sys.stderr.write(f"mutation floor must be an integer: {path}\n")
        raise SystemExit(1)
    return int(text)


def counts(cache: Path) -> dict[str, int]:
    if not cache.is_file():
        sys.stderr.write(f"missing mutation cache: {cache}\n")
        raise SystemExit(1)
    conn = sqlite3.connect(cache)
    try:
        tables = [
            name
            for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            if name.lower() == "mutant"
        ]
        if len(tables) != 1 or tables[0] not in {"mutant", "Mutant"}:
            sys.stderr.write("mutation cache has no mutant table\n")
            raise SystemExit(1)
        table = tables[0]
        found: dict[str, int] = {}
        for status, count in conn.execute(
            f'SELECT status, COUNT(*) FROM "{table}" GROUP BY status'
        ):
            found[str(status)] = int(count)
        return found
    finally:
        conn.close()


def score(found: dict[str, int]) -> tuple[int, int, int]:
    if found.get(UNTESTED, 0):
        sys.stderr.write(f"mutation cache still has {found[UNTESTED]} untested mutants\n")
        raise SystemExit(1)
    killed = found.get(KILLED, 0)
    against = sum(found.get(status, 0) for status in AGAINST)
    total = killed + against
    if total == 0:
        sys.stderr.write("mutation cache has no tested mutants\n")
        raise SystemExit(1)
    return killed, total, (killed * 100) // total


def check(cache: Path, floor: int) -> int:
    killed, total, percent = score(counts(cache))
    print(f"mutation floor: killed {killed} of {total} ({percent}%), floor {floor}")
    if percent < floor:
        sys.stderr.write(f"mutation score {percent} is below the frozen floor {floor}\n")
        return 1
    return 0


def self_test() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="mutation-floor-"))
    cache = tmp / "cache.sqlite"
    floor = tmp / "floor.txt"
    floor.write_text("50\n", encoding="utf-8")
    conn = sqlite3.connect(cache)
    conn.execute("CREATE TABLE mutant (id INTEGER PRIMARY KEY, status TEXT)")
    conn.executemany(
        "INSERT INTO mutant(status) VALUES (?)",
        [("ok_killed",)] * 8 + [("bad_survived",)] * 2,
    )
    conn.commit()
    conn.close()
    if check(cache, read_floor(floor)) != 0:
        raise SystemExit("mutation-floor self-test: 80 percent must pass a floor of 50")
    conn = sqlite3.connect(cache)
    conn.execute("DELETE FROM mutant")
    conn.executemany(
        "INSERT INTO mutant(status) VALUES (?)",
        [("ok_killed",)] * 2 + [("bad_survived",)] * 8,
    )
    conn.commit()
    conn.close()
    if check(cache, read_floor(floor)) == 0:
        raise SystemExit("mutation-floor self-test: 20 percent must fail a floor of 50")
    print("mutation-floor self-test: score above the floor passes and below it fails")


def main() -> None:
    if "--self-test" in sys.argv[1:]:
        self_test()
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--floor-file", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(check(args.cache, read_floor(args.floor_file)))


if __name__ == "__main__":
    main()
