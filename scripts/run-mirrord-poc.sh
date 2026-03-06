#!/usr/bin/env bash
# Milestone 5: Run mirrord PoC — local process with header-based steal, then validate with curl.
# Prereqs: Kind cluster with stack deployed in staging, mirrord CLI installed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MIRRORD_CONFIG="${REPO_ROOT}/docs/mirrord-poc/mirrord.json"
LOCAL_PORT=8080
PF_PORT=18080
NAMESPACE="${NAMESPACE:-staging}"

if [[ ! -f "$MIRRORD_CONFIG" ]]; then
  echo "Missing $MIRRORD_CONFIG" >&2
  exit 1
fi

if ! command -v mirrord &>/dev/null; then
  echo "mirrord not in PATH. Run: $SCRIPT_DIR/install-mirrord.sh" >&2
  exit 1
fi

kubectl get deployment release-lifecycle-demo -n "$NAMESPACE" &>/dev/null || {
  echo "Deployment release-lifecycle-demo not found in namespace $NAMESPACE. Bootstrap the stack first." >&2
  exit 1
}

echo "=== Mirrord PoC: release-lifecycle-demo with header_filter x-dev-session: pr-test ==="
echo "  Config: $MIRRORD_CONFIG"
echo "  Local server port: $LOCAL_PORT (must match pod container port)"
echo "  Port-forward: localhost:$PF_PORT -> svc/release-lifecycle-demo:80"
echo ""

# Minimal HTTP server that returns a distinguishable body (so we can tell local vs cluster)
serve_local() {
  echo "LOCAL-PR-RESPONSE"
  while true; do sleep 3600; done
}
export -f serve_local

# Start port-forward in background so we can curl the service from this host
kubectl port-forward "svc/release-lifecycle-demo" "$PF_PORT:80" -n "$NAMESPACE" &
PF_PID=$!
cleanup() { kill $PF_PID 2>/dev/null || true; }
trap cleanup EXIT

# Wait for port-forward to be ready
for i in {1..30}; do
  curl -sS -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PF_PORT/" 2>/dev/null | grep -q 200 && break
  sleep 0.5
done

echo "1. Request WITHOUT x-dev-session (expect ORIGINAL pod response):"
RESP_NO_HEADER="$(curl -sS -w '\n%{http_code}' "http://127.0.0.1:$PF_PORT/" 2>/dev/null)" || true
echo "$RESP_NO_HEADER"
echo ""

echo "2. Request WITH x-dev-session: pr-test (expect LOCAL process — run mirrord in another terminal first):"
echo "   In another terminal run:"
echo "   mirrord exec -f $MIRRORD_CONFIG -- bash -c 'echo -e \"HTTP/1.1 200 OK\r\nContent-Length: 20\r\n\r\nLOCAL-PR-RESPONSE\"; exec cat' | nc -l -p $LOCAL_PORT"
echo "   Or: cd $REPO_ROOT && mirrord exec -f $MIRRORD_CONFIG -- python3 -c \"
import http.server
import socketserver
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.send_header('Content-Type','text/plain'); self.end_headers(); self.wfile.write(b'LOCAL-PR-RESPONSE')
    def log_message(self,*a): pass
socketserver.TCPServer(('',$LOCAL_PORT), H).serve_forever()
\""
echo ""
echo "   Then run this script again, or manually:"
echo "   curl -H 'x-dev-session: pr-test' http://127.0.0.1:$PF_PORT/"
echo ""
echo "Port-forward is running (PID $PF_PID). Press Ctrl+C to stop."

wait $PF_PID
