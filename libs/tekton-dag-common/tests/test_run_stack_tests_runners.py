"""Fixture coverage for run-stack-tests Newman, Playwright, and Artillery branches."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RUNNERS = ROOT / "scripts" / "run-stack-tests-runners.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR)


def _stub_bin(
    tmp_path: Path,
    *,
    newman: int = 0,
    playwright: int = 0,
    artillery: int = 0,
) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir(parents=True)
    _write_executable(
        bindir / "newman",
        f"#!/bin/sh\necho newman-stub \"$@\"\nexit {newman}\n",
    )
    _write_executable(
        bindir / "artillery",
        f"#!/bin/sh\necho artillery-stub \"$@\"\nexit {artillery}\n",
    )
    _write_executable(
        bindir / "npx",
        "#!/bin/sh\n"
        'if [ "$1" = "playwright" ]; then\n'
        f'  echo playwright-stub "$@"\n  exit {playwright}\n'
        "fi\n"
        "exit 0\n",
    )
    _write_executable(bindir / "npm", "#!/bin/sh\nexit 0\n")
    _write_executable(
        bindir / "curl",
        "#!/bin/sh\n"
        'echo \'{"frontend":"ok","api":"ok","sess-1":"present"}\'\n',
    )
    return bindir


def _stack(*apps: dict) -> str:
    return json.dumps(
        {
            "propagation": {"baggage-key": "dev-session"},
            "defaults": {"namespace": "staging", "service-port": "80"},
            "apps": list(apps),
        }
    )


def _app(name: str, **tests: str) -> dict:
    payload: dict = {"name": name, "namespace": "staging", "service-port": "80"}
    if tests:
        payload["tests"] = tests
    return payload


def _prepare_runner_files(source: Path, kind: str) -> None:
    if kind == "newman":
        collection = source / "tests" / "postman" / "api.json"
        collection.parent.mkdir(parents=True, exist_ok=True)
        collection.write_text('{"info":{"name":"api"},"item":[]}\n')
        return
    if kind == "playwright":
        suite = source / "tests" / "playwright"
        suite.mkdir(parents=True, exist_ok=True)
        (source / "tests" / "package.json").write_text('{"name":"api-tests"}\n')
        (suite / "example.spec.js").write_text("test('ok', () => {});\n")
        return
    if kind == "artillery":
        script = source / "tests" / "artillery" / "load.yml"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("config:\n  target: http://localhost\n")
        return
    raise AssertionError(kind)


def _run(
    root: Path,
    stack_json: str,
    *,
    newman: int = 0,
    playwright: int = 0,
    artillery: int = 0,
    extra_env: dict[str, str] | None = None,
    prepare: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    source = root / "source"
    source.mkdir(parents=True)
    if prepare:
        _prepare_runner_files(source, prepare)
    summary = root / "summary.json"
    bindir = _stub_bin(
        root, newman=newman, playwright=playwright, artillery=artillery
    )
    env = os.environ.copy()
    env.update(
        {
            "STACK_JSON": stack_json,
            "APP_LIST": "frontend api",
            "ENTRY_APP": "frontend",
            "CHAIN": "frontend api",
            "BUILD_APPS": "api",
            "INTERCEPT": "x-dev-session:sess-1",
            "DEFAULT_NS": "staging",
            "TESTS_TO_RUN": "",
            "UNMAPPED_AREA": "",
            "APPS_TO_TEST": "",
            "TEST_SOURCE": str(source),
            "TEST_SUMMARY_PATH": str(summary),
            "PATH": f"{bindir}{os.pathsep}{env['PATH']}",
        }
    )
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        ["sh", str(RUNNERS)],
        cwd=source,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed, summary


def test_malformed_stack_json_fails(tmp_path: Path) -> None:
    completed, _summary = _run(tmp_path, "{not-json")
    assert completed.returncode == 1
    assert "stack-json is not valid JSON" in completed.stderr


def test_unmapped_area_exits_without_runners(tmp_path: Path) -> None:
    completed, summary = _run(
        tmp_path,
        _stack(_app("frontend"), _app("api")),
        extra_env={"UNMAPPED_AREA": "billing"},
    )
    assert completed.returncode == 0
    payload = json.loads(summary.read_text())
    assert payload["unmapped-area"] == "billing"
    assert "newman-stub" not in completed.stdout
    assert "playwright-stub" not in completed.stdout
    assert "artillery-stub" not in completed.stdout


@pytest.mark.parametrize(
    ("kind", "tests", "pass_token", "fail_token"),
    [
        (
            "newman",
            {"postman": "tests/postman/api.json"},
            "[postman] PASS",
            "[postman] FAIL",
        ),
        (
            "playwright",
            {"playwright": "tests/playwright"},
            "[playwright] PASS",
            "[playwright] FAIL",
        ),
        (
            "artillery",
            {"artillery": "tests/artillery/load.yml"},
            "[artillery] PASS",
            "[artillery] FAIL",
        ),
    ],
)
def test_runner_success_and_failure_paths(
    tmp_path: Path,
    kind: str,
    tests: dict[str, str],
    pass_token: str,
    fail_token: str,
) -> None:
    stack = _stack(_app("frontend"), _app("api", **tests))

    passed, passed_summary = _run(
        tmp_path / "success",
        stack,
        prepare=kind,
    )
    assert passed.returncode == 0, passed.stdout + passed.stderr
    assert pass_token in passed.stdout
    assert json.loads(passed_summary.read_text())["api"] == "pass"

    failed, failed_summary = _run(
        tmp_path / "failure",
        stack,
        prepare=kind,
        newman=1 if kind == "newman" else 0,
        playwright=1 if kind == "playwright" else 0,
        artillery=1 if kind == "artillery" else 0,
    )
    assert failed.returncode == 1, failed.stdout + failed.stderr
    assert fail_token in failed.stdout
    assert json.loads(failed_summary.read_text())["api"] == "fail"
