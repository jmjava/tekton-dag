#!/usr/bin/env bash
# Build and push tekton-dag build images to a registry.
#
# Usage:
#   ./build-and-push.sh [REGISTRY] [TAG]           # default images only
#   ./build-and-push.sh --matrix [REGISTRY]         # build all language version variants
#   ./build-and-push.sh --matrix --tool maven       # only maven variants
#
# Environment:
#   REGISTRY   — override registry (default: localhost:5000)
#   FORCE      — set to "true" to rebuild even if image exists

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="${REGISTRY:-localhost:5000}"
TAG="latest"
IMAGE_BASE="tekton-dag-build"
MATRIX=false
TOOL_FILTER=""
FORCE="${FORCE:-false}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --matrix)  MATRIX=true; shift ;;
    --tool)    TOOL_FILTER="$2"; shift 2 ;;
    --force)   FORCE=true; shift ;;
    -*)        echo "Unknown flag: $1" >&2; exit 1 ;;
    *)
      if [[ -z "${_pos1:-}" ]]; then _pos1="$1"; else TAG="$1"; fi
      shift ;;
  esac
done
[[ -n "${_pos1:-}" ]] && REGISTRY="$_pos1"

build_image() {
  local tool="$1" tag="$2" build_arg="${3:-}"
  local image="${REGISTRY}/${IMAGE_BASE}-${tool}:${tag}"
  local dockerfile="Dockerfile.$tool"

  if [[ "$FORCE" != "true" ]] && docker pull "$image" 2>/dev/null; then
    echo "  Exists: $image (skip; use --force to rebuild)"
    return
  fi

  local args=()
  [[ -n "$build_arg" ]] && args+=(--build-arg "$build_arg")

  echo "  Building $image ..."
  docker build "${args[@]}" -t "$image" -f "$SCRIPT_DIR/$dockerfile" "$SCRIPT_DIR"
  docker push "$image"
  echo "  -> $image"
}

TOOLS=(node maven gradle python php mirrord)

echo "=== tekton-dag build images ==="
echo "  Registry: $REGISTRY"
echo ""

# ── Default images (latest tag) ──────────────────────────────────────
echo "--- Default images (tag: $TAG) ---"
for tool in "${TOOLS[@]}"; do
  [[ -n "$TOOL_FILTER" && "$tool" != "$TOOL_FILTER" ]] && continue
  build_image "$tool" "$TAG"
done

# ── Version matrix (only with --matrix) ──────────────────────────────
if [[ "$MATRIX" == "true" ]]; then
  echo ""
  echo "--- Version matrix ---"

  declare -A VARIANT_MAP
  VARIANT_MAP[maven]="JAVA_VERSION=11:java11 JAVA_VERSION=17:java17 JAVA_VERSION=21:java21"
  VARIANT_MAP[gradle]="JAVA_VERSION=11:java11 JAVA_VERSION=17:java17 JAVA_VERSION=21:java21"
  VARIANT_MAP[node]="NODE_VERSION=18:node18 NODE_VERSION=20:node20 NODE_VERSION=22:node22"
  VARIANT_MAP[python]="PYTHON_VERSION=3.10:python310 PYTHON_VERSION=3.11:python311 PYTHON_VERSION=3.12:python312"
  VARIANT_MAP[php]="PHP_VERSION=8.1:php81 PHP_VERSION=8.2:php82 PHP_VERSION=8.3:php83"

  for tool in "${!VARIANT_MAP[@]}"; do
    [[ -n "$TOOL_FILTER" && "$tool" != "$TOOL_FILTER" ]] && continue
    echo ""
    echo "  $tool variants:"
    for entry in ${VARIANT_MAP[$tool]}; do
      build_arg="${entry%%:*}"
      variant_tag="${entry##*:}"
      build_image "$tool" "$variant_tag" "$build_arg"
    done
  done
fi

echo ""
echo "=== Done ==="
echo ""
echo "Default compile-image refs:"
for tool in "${TOOLS[@]}"; do
  echo "  compile-image-${tool}: ${REGISTRY}/${IMAGE_BASE}-${tool}:${TAG}"
done

if [[ "$MATRIX" == "true" ]]; then
  echo ""
  echo "Variant refs (set in values.yaml compileImageVariants):"
  for tool in maven gradle node python php; do
    [[ -n "${VARIANT_MAP[$tool]:-}" ]] || continue
    for entry in ${VARIANT_MAP[$tool]}; do
      variant_tag="${entry##*:}"
      echo "  ${tool}-${variant_tag}: ${REGISTRY}/${IMAGE_BASE}-${tool}:${variant_tag}"
    done
  done
fi
