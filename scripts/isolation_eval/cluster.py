"""Kind/cluster driver for clone-vs-intercept dummy HTTP stacks.

Uses echo servers (not app images) so the experiment measures isolation
strategy and pod count, not Kaniko. Requires kubectl.
"""

from __future__ import annotations

import socket
import subprocess
import time
import urllib.request

HEADER_NAME = "x-dev-session"
HEADER_VALUE = "pr-eval"

ECHO_IMAGE = "hashicorp/http-echo:1.0.0"
ROUTER_IMAGE = "python:3.12-alpine"

ROUTER_PY = r'''
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen

HEADER = os.environ.get("HEADER_NAME", "x-dev-session")
MATCH = os.environ.get("HEADER_VALUE", "pr-eval")
BASE = os.environ["BASELINE_URL"].rstrip("/")
PR = os.environ["PR_URL"].rstrip("/")

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        dest = PR if self.headers.get(HEADER) == MATCH else BASE
        try:
            req = Request(dest + "/", method="GET")
            with urlopen(req, timeout=5) as resp:
                body = resp.read()
                self.send_response(200)
                self.send_header("content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
        except Exception as exc:
            msg = ("router-error:" + str(exc)).encode()
            self.send_response(502)
            self.end_headers()
            self.wfile.write(msg)

    def log_message(self, fmt, *args):
        return

HTTPServer(("0.0.0.0", 8080), H).serve_forever()
'''


def echo_deploy(name: str, text: str, ns: str) -> str:
    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {ns}
  labels:
    app: {name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
        eval.tektondag.io/role: echo
    spec:
      containers:
        - name: echo
          image: {ECHO_IMAGE}
          args: ["-text={text}", "-listen=:8080"]
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {ns}
spec:
  selector:
    app: {name}
  ports:
    - port: 80
      targetPort: 8080
"""


def _indent_router() -> str:
    return "\n".join("    " + line if line else "" for line in ROUTER_PY.strip().splitlines())


def router_manifest(ns: str, baseline_svc: str, pr_svc: str) -> str:
    return f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: header-router
  namespace: {ns}
data:
  router.py: |
{_indent_router()}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: entry
  namespace: {ns}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: entry
  template:
    metadata:
      labels:
        app: entry
        eval.tektondag.io/role: router
    spec:
      containers:
        - name: router
          image: {ROUTER_IMAGE}
          command: ["python", "/app/router.py"]
          env:
            - name: HEADER_NAME
              value: "{HEADER_NAME}"
            - name: HEADER_VALUE
              value: "{HEADER_VALUE}"
            - name: BASELINE_URL
              value: "http://{baseline_svc}"
            - name: PR_URL
              value: "http://{pr_svc}"
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: script
              mountPath: /app
      volumes:
        - name: script
          configMap:
            name: header-router
---
apiVersion: v1
kind: Service
metadata:
  name: entry
  namespace: {ns}
spec:
  selector:
    app: entry
  ports:
    - port: 80
      targetPort: 8080
"""


def clone_manifests(ns: str, width: int, changed_app: str) -> str:
    parts = [echo_deploy(f"app-{i}", f"pr/{changed_app}/app-{i}", ns) for i in range(width)]
    parts.append(
        f"""apiVersion: v1
kind: Service
metadata:
  name: entry
  namespace: {ns}
spec:
  selector:
    app: app-0
  ports:
    - port: 80
      targetPort: 8080
"""
    )
    return "\n---\n".join(parts)


def intercept_manifests(ns: str, width: int, changed_app: str) -> str:
    parts = [echo_deploy(f"app-{i}", f"baseline/app-{i}", ns) for i in range(width)]
    parts.append(echo_deploy("app-0-pr", f"pr/{changed_app}/app-0", ns))
    parts.append(router_manifest(ns, "app-0", "app-0-pr"))
    return "\n---\n".join(parts)


def apply_yaml(yaml_text: str) -> None:
    subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=yaml_text,
        text=True,
        check=True,
        capture_output=True,
    )


def kubectl(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["kubectl", *args], check=True, capture_output=True, text=True)


def ensure_ns(ns: str) -> None:
    subprocess.run(["kubectl", "create", "namespace", ns], check=False, capture_output=True)


def delete_ns(ns: str) -> None:
    subprocess.run(["kubectl", "delete", "namespace", ns, "--wait=true", "--timeout=120s"], check=False)


def wait_ready(ns: str, timeout_s: int = 180) -> None:
    """Wait until labeled pods exist and become Ready.

    `kubectl wait` on a label selector exits immediately with
    "no matching resources found" if the ReplicaSet has not created
    pods yet. Poll get first so the first cell after a cold Kind
    create is not a false isolation failure.
    """
    deadline = time.time() + timeout_s
    while True:
        remaining = max(1, int(deadline - time.time()))
        listed = subprocess.run(
            [
                "kubectl",
                "get",
                "pods",
                "-n",
                ns,
                "-l",
                "eval.tektondag.io/role",
                "--no-headers",
            ],
            capture_output=True,
            text=True,
        )
        if listed.returncode == 0 and listed.stdout.strip():
            kubectl(
                [
                    "wait",
                    "--for=condition=Ready",
                    "pod",
                    "-l",
                    "eval.tektondag.io/role",
                    "-n",
                    ns,
                    f"--timeout={remaining}s",
                ]
            )
            return
        if time.time() >= deadline:
            err = (listed.stderr or listed.stdout or "no pods").strip()
            raise RuntimeError(
                f"no eval.tektondag.io/role pods in {ns} within {timeout_s}s: {err}"
            )
        time.sleep(0.4)


def pod_count(ns: str) -> int:
    # Label filter omits kubectl-run probe pods from the cost metric.
    cp = kubectl(["get", "pods", "-n", ns, "-l", "eval.tektondag.io/role", "--no-headers"])
    return len([ln for ln in cp.stdout.splitlines() if ln.strip()])


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def curl_entry(ns: str, header: bool) -> str:
    """Hit svc/entry via kubectl port-forward.

    Nested Kind (Cloud Agent Docker-in-Docker) often cannot program ClusterIP
    iptables (missing xt_statistic). Port-forward goes through the API server
    to the pod and still exercises the intercept router on that pod.
    """
    port = _free_port()
    pf = subprocess.Popen(
        ["kubectl", "-n", ns, "port-forward", "svc/entry", f"{port}:80"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    url = f"http://127.0.0.1:{port}/"
    last_err = "port-forward never accepted a connection"
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                req = urllib.request.Request(url)
                if header:
                    req.add_header(HEADER_NAME, HEADER_VALUE)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    return resp.read().decode("utf-8", "replace").strip()
            except Exception as exc:
                last_err = str(exc)
                if pf.poll() is not None:
                    out = pf.stdout.read() if pf.stdout else ""
                    return f"probe-error:port-forward:{out or last_err}"
                time.sleep(0.2)
        return f"probe-error:{last_err}"
    finally:
        pf.terminate()
        try:
            pf.wait(timeout=5)
        except Exception:
            pf.kill()
