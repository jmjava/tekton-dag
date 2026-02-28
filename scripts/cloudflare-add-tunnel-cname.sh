#!/usr/bin/env bash
# Add a CNAME record in Cloudflare DNS for a Cloudflare Tunnel hostname.
# Uses Cloudflare API v4. Requires CLOUDFLARE_API_TOKEN in env (or .env).
#
# Usage:
#   ./scripts/cloudflare-add-tunnel-cname.sh
#   ./scripts/cloudflare-add-tunnel-cname.sh --zone menkelabs.com --name tekton-el --target 6e3bb35c-d779-44fa-a6d2-b913459b52a3.cfargotunnel.com
#
# Options:
#   --zone     DNS zone name (default: menkelabs.com); used to look up zone ID
#   --zone-id  Zone ID (skip lookup); get from Dashboard → zone → Overview → Zone ID
#   --name     Record name / subdomain (default: tekton-el) → result: tekton-el.menkelabs.com
#   --target   CNAME target (default: 6e3bb35c-d779-44fa-a6d2-b913459b52a3.cfargotunnel.com)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: $1 is required" >&2; exit 1; }; }
need jq
need curl
TEKTON_DAG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ZONE_NAME="menkelabs.com"
ZONE_ID_ARG=""
RECORD_NAME="tekton-el"
CNAME_TARGET="6e3bb35c-d779-44fa-a6d2-b913459b52a3.cfargotunnel.com"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --zone)     ZONE_NAME="$2"; shift 2 ;;
    --zone-id)  ZONE_ID_ARG="$2"; shift 2 ;;
    --name)     RECORD_NAME="$2"; shift 2 ;;
    --target)   CNAME_TARGET="$2"; shift 2 ;;
    *)          echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Load .env if present (for CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID)
if [[ -f "$TEKTON_DAG_ROOT/.env" ]]; then
  set -a
  source "$TEKTON_DAG_ROOT/.env"
  set +a
fi

[[ -n "${CLOUDFLARE_API_TOKEN:-}" ]] || { echo "ERROR: CLOUDFLARE_API_TOKEN not set. Add it to .env or export it." >&2; exit 1; }

# Use zone ID from env if not passed via --zone-id (zone ID = per-domain, not account ID)
[[ -n "$ZONE_ID_ARG" ]] || ZONE_ID_ARG="${CLOUDFLARE_ZONE_ID:-${CLOUD_FLARE_ZONE_ID:-${CF_ZONE_ID:-}}}"

API_BASE="https://api.cloudflare.com/client/v4"

# Resolve zone ID
if [[ -n "$ZONE_ID_ARG" ]]; then
  ZONE_ID="$ZONE_ID_ARG"
  echo "Zone ID: $ZONE_ID (from --zone-id)"
else
  ZONE_RESP=$(curl -sS -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json" \
    "$API_BASE/zones?name=$ZONE_NAME")
  ZONE_ID=$(echo "$ZONE_RESP" | jq -r '.result[0].id // empty')
  if [[ -z "$ZONE_ID" || "$ZONE_ID" == "null" ]]; then
    echo "ERROR: Zone '$ZONE_NAME' not found or token has no access to zones." >&2
    echo "  - Ensure the API token has Zone.DNS Edit and Zone.Zone Read (or Account scope)." >&2
    echo "  - Or pass the zone ID from Dashboard → your zone → Overview → Zone ID: --zone-id YOUR_ZONE_ID" >&2
    exit 1
  fi
  echo "Zone: $ZONE_NAME (id: $ZONE_ID)"
fi

# Check if record already exists
LIST_RESP=$(curl -sS -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json" \
  "$API_BASE/zones/$ZONE_ID/dns_records?type=CNAME&name=${RECORD_NAME}.${ZONE_NAME}")
EXISTING_ID=$(echo "$LIST_RESP" | jq -r '.result[0].id // empty')
EXISTING_CONTENT=$(echo "$LIST_RESP" | jq -r '.result[0].content // empty')

if [[ -n "$EXISTING_ID" && "$EXISTING_ID" != "null" ]]; then
  if [[ "$EXISTING_CONTENT" == "$CNAME_TARGET" ]]; then
    echo "CNAME ${RECORD_NAME}.${ZONE_NAME} already points to $CNAME_TARGET. Nothing to do."
    exit 0
  fi
  echo "Updating existing CNAME record (id: $EXISTING_ID) to target $CNAME_TARGET ..."
  UPDATE_RESP=$(curl -sS -X PATCH -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json" \
    "$API_BASE/zones/$ZONE_ID/dns_records/$EXISTING_ID" \
    -d "{\"type\":\"CNAME\",\"name\":\"$RECORD_NAME\",\"content\":\"$CNAME_TARGET\",\"ttl\":1,\"proxied\":false}")
  SUCCESS=$(echo "$UPDATE_RESP" | jq -r '.success')
  if [[ "$SUCCESS" != "true" ]]; then
    echo "ERROR: Update failed: $UPDATE_RESP" >&2
    exit 1
  fi
  echo "Updated CNAME ${RECORD_NAME}.${ZONE_NAME} → $CNAME_TARGET"
  exit 0
fi

# Create new record
echo "Creating CNAME ${RECORD_NAME}.${ZONE_NAME} → $CNAME_TARGET ..."
CREATE_RESP=$(curl -sS -X POST -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json" \
  "$API_BASE/zones/$ZONE_ID/dns_records" \
  -d "{\"type\":\"CNAME\",\"name\":\"$RECORD_NAME\",\"content\":\"$CNAME_TARGET\",\"ttl\":1,\"proxied\":false}")

SUCCESS=$(echo "$CREATE_RESP" | jq -r '.success')
if [[ "$SUCCESS" != "true" ]]; then
  echo "ERROR: Create failed: $CREATE_RESP" >&2
  exit 1
fi
echo "Created CNAME ${RECORD_NAME}.${ZONE_NAME} → $CNAME_TARGET"
