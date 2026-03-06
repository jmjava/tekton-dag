#!/usr/bin/env python3
"""Minimal HTTP server that returns a fixed body so we can identify local vs cluster response."""
import http.server
import socketserver

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"LOCAL-PR-RESPONSE")
    def log_message(self, *args): pass

socketserver.TCPServer(("", 8080), Handler).serve_forever()
