from pathlib import Path

from tekton_dag_common.propagation_validate import evaluate_propagation

ROOT = Path(__file__).resolve().parents[3]


def test_local_hop_chain_script_copies_original_override():
    import runpy

    ns = runpy.run_path(str(ROOT / "scripts" / "local_hop_chain" / "run.py"))
    code = ns["run"]()
    assert code == 0


def test_rewritten_local_report_still_fails_closed():
    report = evaluate_propagation(
        {
            "app": "demo-fe",
            "session": "pr-42",
            "hops": [
                {
                    "app": "release-lifecycle-demo",
                    "session": "minted",
                    "hops": [{"app": "demo-api", "session": "minted"}],
                }
            ],
        },
        chain="demo-fe release-lifecycle-demo demo-api",
        header_value="pr-42",
        build_apps="demo-api",
    )
    assert not report.ok
