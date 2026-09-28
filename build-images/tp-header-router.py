#!/usr/bin/env python3
"""Route a Telepresence TCP intercept by session header.

Matching requests go to the PR pod. Everything else goes to the live
app (typically via kubectl port-forward so we do not hairpin the agent).
"""
from __future__ import annotations

import os
import socket
import sys
import threading

LISTEN = ("127.0.0.1", int(os.environ.get("ROUTER_PORT", "18080")))
PR = (os.environ["PR_HOST"], int(os.environ["PR_PORT"]))
LIVE = (os.environ.get("LIVE_HOST", "127.0.0.1"), int(os.environ.get("LIVE_PORT", "18081")))
HEADER_NAME = os.environ["HEADER_NAME"].lower().encode()
HEADER_VALUE = os.environ["HEADER_VALUE"].encode()


def header_match(buf: bytes) -> bool:
    head = buf.split(b"\r\n\r\n", 1)[0]
    for line in head.split(b"\r\n")[1:]:
        if b":" not in line:
            continue
        key, value = line.split(b":", 1)
        if key.strip().lower() == HEADER_NAME and value.strip() == HEADER_VALUE:
            return True
    return False


def pipe(src: socket.socket, dst: socket.socket) -> None:
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def handle(client: socket.socket) -> None:
    buf = b""
    try:
        while b"\r\n\r\n" not in buf and len(buf) < 65536:
            chunk = client.recv(4096)
            if not chunk:
                client.close()
                return
            buf += chunk
        dest = PR if header_match(buf) else LIVE
        upstream = socket.create_connection(dest, timeout=5)
        upstream.sendall(buf)
        reply = threading.Thread(target=pipe, args=(upstream, client), daemon=True)
        reply.start()
        pipe(client, upstream)
        reply.join(timeout=120)
    except OSError as exc:
        print(f"header-router error: {exc}", file=sys.stderr, flush=True)
    finally:
        try:
            client.close()
        except OSError:
            pass


def main() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(LISTEN)
    srv.listen(128)
    print(
        f"header-router listening on {LISTEN[0]}:{LISTEN[1]} "
        f"match {HEADER_NAME.decode()}={HEADER_VALUE.decode()} -> {PR[0]}:{PR[1]} "
        f"else {LIVE[0]}:{LIVE[1]}",
        flush=True,
    )
    while True:
        client, _ = srv.accept()
        threading.Thread(target=handle, args=(client,), daemon=True).start()


if __name__ == "__main__":
    main()
