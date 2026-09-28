#!/usr/bin/env python3
"""Echo the original override on GET /propagation and nest the BFF hop."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


APP_NAME = _env("APP_NAME", "demo-fe")
HEADER_NAME = _env("BAGGAGE_HEADER_NAME", "x-dev-session")
BAGGAGE_KEY = _env("BAGGAGE_KEY", "dev-session")
BFF_UPSTREAM = _env("BFF_UPSTREAM").rstrip("/")


def downstream_hop(session: str) -> list:
    if not BFF_UPSTREAM or not session:
        return []
    url = BFF_UPSTREAM + "/propagation"
    headers = {
        HEADER_NAME: session,
        "baggage": f"{BAGGAGE_KEY}={session}",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = resp.read().decode("utf-8", "replace")
        return [json.loads(payload)]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        return [{"error": str(exc)}]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        session = self.headers.get(HEADER_NAME, "") or ""
        body = json.dumps(
            {"app": APP_NAME, "session": session, "hops": downstream_hop(session)}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def main() -> None:
    ThreadingHTTPServer(("127.0.0.1", 8081), Handler).serve_forever()


if __name__ == "__main__":
    main()
