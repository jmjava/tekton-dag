"""Start three Flask hops locally and fail-closed on a rewritten override."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from tekton_dag_common.propagation_validate import evaluate_propagation, format_report

ROOT = Path(__file__).resolve().parents[2]
APP = Path(__file__).resolve().parent / "app.py"
CHAIN = ["demo-fe", "release-lifecycle-demo", "demo-api"]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_http(url: str, timeout: float = 8.0) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=0.4)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            last = exc
            time.sleep(0.1)
    raise RuntimeError(f"server at {url} did not start: {last}")


def _python() -> str:
    venv = ROOT / ".venv" / "bin" / "python3"
    return str(venv) if venv.is_file() else sys.executable


def run() -> int:
    ports = {name: _free_port() for name in CHAIN}
    env_base = os.environ.copy()
    env_base["PYTHONPATH"] = os.pathsep.join(
        [
            str(ROOT / "libs" / "baggage-python"),
            str(ROOT / "libs" / "tekton-dag-common"),
            env_base.get("PYTHONPATH", ""),
        ]
    )
    children: list[subprocess.Popen] = []
    try:
        specs = [
            ("demo-api", "terminal", ""),
            ("release-lifecycle-demo", "forwarder", f"http://127.0.0.1:{ports['demo-api']}"),
            ("demo-fe", "originator", f"http://127.0.0.1:{ports['release-lifecycle-demo']}"),
        ]
        for name, role, downstream in specs:
            env = env_base.copy()
            env.update(
                {
                    "BAGGAGE_ENABLED": "true",
                    "BAGGAGE_ROLE": role,
                    "BAGGAGE_HEADER_NAME": "x-dev-session",
                    "BAGGAGE_KEY": "dev-session",
                    "APP_NAME": name,
                    "PORT": str(ports[name]),
                    "DOWNSTREAM_URL": downstream,
                }
            )
            children.append(
                subprocess.Popen(
                    [_python(), str(APP)],
                    cwd=str(ROOT),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            )
        _wait_http(f"http://127.0.0.1:{ports['demo-api']}/propagation")
        _wait_http(f"http://127.0.0.1:{ports['release-lifecycle-demo']}/propagation")
        _wait_http(f"http://127.0.0.1:{ports['demo-fe']}/propagation")

        req = urllib.request.Request(
            f"http://127.0.0.1:{ports['demo-fe']}/propagation",
            headers={
                "x-dev-session": "pr-42",
                "baggage": "dev-session=pr-42",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
        parsed = json.loads(body)
        print(json.dumps(parsed, indent=2))
        report = evaluate_propagation(
            parsed,
            chain=CHAIN,
            header_value="pr-42",
            build_apps="demo-api",
            roles={
                "demo-fe": "originator",
                "release-lifecycle-demo": "forwarder",
                "demo-api": "terminal",
            },
        )
        print(format_report(report))
        return 0 if report.ok else 1
    finally:
        for proc in children:
            proc.terminate()
        for proc in children:
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(run())
