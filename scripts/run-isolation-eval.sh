#!/usr/bin/env bash
# Clone-vs-intercept isolation evaluation harness.
#
# Offline (default, no cluster): write an experiment *plan* CSV and run protocol
# self-tests. Estimated pod counts are a model, not measurements.
#
# Cluster: deploy dummy echo servers per cell (hashicorp/http-echo + a header
# router). Measures wall-clock, pod_count, isolation probes. Does not run Tekton.
#
# Usage:
#   ./scripts/run-isolation-eval.sh                 # offline plan + pytest protocol
#   ./scripts/run-isolation-eval.sh --offline
#   ./scripts/run-isolation-eval.sh --cluster --repeats 3 --out /tmp/eval.csv
#   ./scripts/run-isolation-eval.sh --help
set -euo pipefail
[ -z "${BASH_VERSION:-}" ] && exec bash "$0" "$@"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"
cd "$REPO_ROOT"

MODE=offline
REPEATS=1
OUT=""
KEEP_BASELINE=true
HELP=false
SKIP_PYTEST=false
STACKS="stacks/single-app.yaml,stacks/stack-one.yaml,stacks/stack-two-vendor.yaml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline) MODE=offline; shift ;;
    --cluster) MODE=cluster; shift ;;
    --repeats) REPEATS="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --stacks) STACKS="$2"; shift 2 ;;
    --no-keep-baseline) KEEP_BASELINE=false; shift ;;
    --skip-pytest) SKIP_PYTEST=true; shift ;;
    --help|-h) HELP=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ "$HELP" == "true" ]]; then
  sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

export PYTHONPATH="$REPO_ROOT/scripts${PYTHONPATH:+:$PYTHONPATH}"
if [[ -x "$REPO_ROOT/.venv/bin/python3" ]]; then
  export PATH="$REPO_ROOT/.venv/bin:$PATH"
fi

need python3

if [[ "$MODE" == "offline" ]]; then
  echo ">>> isolation-eval OFFLINE (plan CSV); not a cluster measurement"
  if [[ "$SKIP_PYTEST" != "true" ]]; then
    (cd "$REPO_ROOT/scripts/isolation_eval" && python3 -m pytest test_protocol.py test_cluster_manifests.py test_cluster.py -v --tb=short)
  fi
  TS="$(date -u +%Y%m%dT%H%M%SZ)"
  OUT="${OUT:-/tmp/isolation-eval-plan.csv}"
  python3 - "$OUT" "$STACKS" "$REPEATS" "$KEEP_BASELINE" "$TS" <<'PY'
import os, sys
from datetime import datetime, timezone
from isolation_eval.protocol import experiment_cells, write_csv

out, stacks, repeats, keep, ts = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4] == "true", sys.argv[5]
files = [s.strip() for s in stacks.split(",") if s.strip()]
cells = experiment_cells(files, repeats=repeats, keep_baseline=keep)
rows = []
for c in cells:
    rows.append({
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": ts,
        "mode": "estimated",
        "strategy": c["strategy"],
        "stack_file": c["stack_file"],
        "stack_width": c["stack_width"],
        "changed_app": c["changed_app"],
        "repeat": c["repeat"],
        "keep_baseline": str(c["keep_baseline"]).lower(),
        "wall_clock_s": "",
        "pod_count": c["estimated_pod_count"],
        "matched_body": "",
        "unmatched_body": "",
        "matched_ok": "",
        "unmatched_ok": "",
        "isolation_ok": "",
        "notes": "offline estimate; run --cluster for measurements",
    })
write_csv(rows, out)
print(f"wrote {out} ({len(rows)} rows)")
PY
  exit 0
fi

need kubectl
kubectl cluster-info &>/dev/null || die "no kubectl cluster (create Kind first)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${OUT:-$REPO_ROOT/docs/research/seip/data/isolation-eval-measured-$TS.csv}"
echo ">>> isolation-eval CLUSTER → $OUT"
python3 - "$OUT" "$STACKS" "$REPEATS" "$KEEP_BASELINE" "$TS" <<'PY'
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from isolation_eval.cluster import (
    apply_yaml,
    clone_manifests,
    curl_entry,
    delete_ns,
    ensure_ns,
    intercept_manifests,
    pod_count,
    wait_ready,
)
from isolation_eval.protocol import ProbeOutcome, experiment_cells, write_csv

out, stacks, repeats, keep, ts = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4] == "true", sys.argv[5]
files = [s.strip() for s in stacks.split(",") if s.strip()]
cells = experiment_cells(files, repeats=repeats, keep_baseline=keep)
rows = []
for c in cells:
    stem = Path(c["stack_file"]).stem[:12]
    ns = f"eval-{c['strategy'][:3]}-{stem}-r{c['repeat']}"[:40]
    delete_ns(ns)
    ensure_ns(ns)
    t0 = time.time()
    notes = ""
    try:
        if c["strategy"] == "clone":
            apply_yaml(clone_manifests(ns, c["stack_width"], c["changed_app"]))
            if c["keep_baseline"]:
                # extra baseline namespace copy of the same width
                bns = ns + "-base"
                delete_ns(bns)
                ensure_ns(bns)
                apply_yaml(clone_manifests(bns, c["stack_width"], "baseline"))
                wait_ready(bns)
        else:
            apply_yaml(intercept_manifests(ns, c["stack_width"], c["changed_app"]))
        wait_ready(ns)
        unmatched = curl_entry(ns, header=False)
        matched = curl_entry(ns, header=True)
        elapsed = round(time.time() - t0, 3)
        pods = pod_count(ns)
        if c["strategy"] == "clone" and c["keep_baseline"]:
            pods += pod_count(ns + "-base")
        outcome = ProbeOutcome(
            matched_body=matched,
            unmatched_body=unmatched,
            expected_pr=f"pr/{c['changed_app']}",
            expected_baseline="baseline/",
            strategy=c["strategy"],
        )
        rows.append({
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "run_id": ts,
            "mode": "measured",
            "strategy": c["strategy"],
            "stack_file": c["stack_file"],
            "stack_width": c["stack_width"],
            "changed_app": c["changed_app"],
            "repeat": c["repeat"],
            "keep_baseline": str(c["keep_baseline"]).lower(),
            "wall_clock_s": elapsed,
            "pod_count": pods,
            "matched_body": matched,
            "unmatched_body": unmatched,
            "matched_ok": str(outcome.matched_ok).lower(),
            "unmatched_ok": str(outcome.unmatched_ok).lower(),
            "isolation_ok": str(outcome.isolation_ok).lower(),
            "notes": notes,
        })
    except Exception as exc:
        elapsed = round(time.time() - t0, 3)
        rows.append({
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "run_id": ts,
            "mode": "measured",
            "strategy": c["strategy"],
            "stack_file": c["stack_file"],
            "stack_width": c["stack_width"],
            "changed_app": c["changed_app"],
            "repeat": c["repeat"],
            "keep_baseline": str(c["keep_baseline"]).lower(),
            "wall_clock_s": elapsed,
            "pod_count": "",
            "matched_ok": "false",
            "unmatched_ok": "false",
            "isolation_ok": "false",
            "notes": f"error:{exc}",
        })
    finally:
        delete_ns(ns)
        if c["strategy"] == "clone" and c["keep_baseline"]:
            delete_ns(ns + "-base")

write_csv(rows, out)
print(f"wrote {out} ({len(rows)} rows)")
fails = [r for r in rows if str(r.get("isolation_ok")).lower() != "true"]
if fails:
    sys.exit(f"isolation-eval: {len(fails)}/{len(rows)} cells failed isolation_ok")
PY
