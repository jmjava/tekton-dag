#!/usr/bin/env python3
"""Minimal HTTP server that returns a configurable body for M5/M6 (identify local vs cluster)."""
import os
import http.server
import socketserver

# M6: use MIRRORD_M6_RESPONSE for unique body (e.g. LOCAL-PR-1); default for M5
RESPONSE_BODY = os.environ.get("MIRRORD_M6_RESPONSE", "LOCAL-PR-RESPONSE").encode("utf-8")
PORT = int(os.environ.get("PORT", "8080"))

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(RESPONSE_BODY)
    def log_message(self, *args): pass

socketserver.TCPServer(("", PORT), Handler).serve_forever()
