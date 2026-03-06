#!/usr/bin/env bash
# Install MetalBear mirrord CLI for Milestone 5 PoC.
# See: https://github.com/metalbear-co/mirrord
# Release assets: mirrord_linux_x86_64, mirrord_linux_aarch64, mirrord_mac_universal (no .tar.gz)
set -euo pipefail

MIRRORD_VERSION="${MIRRORD_VERSION:-latest}"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"

if [[ "$MIRRORD_VERSION" == "latest" ]]; then
  MIRRORD_TAG="$(curl -sS "https://api.github.com/repos/metalbear-co/mirrord/releases/latest" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')"
else
  MIRRORD_TAG="$MIRRORD_VERSION"
fi
[[ -z "$MIRRORD_TAG" ]] && { echo "Could not resolve mirrord version." >&2; exit 1; }

case "$(uname -s)" in
  Linux)
    ARCH="$(uname -m)"
    case "$ARCH" in
      x86_64) ASSET="mirrord_linux_x86_64" ;;
      aarch64|arm64) ASSET="mirrord_linux_aarch64" ;;
      *) echo "Unsupported arch: $ARCH" >&2; exit 1 ;;
    esac
    ;;
  Darwin)
    if command -v brew &>/dev/null; then
      echo "Installing mirrord via Homebrew..."
      brew install metalbear-co/mirrord/mirrord
      echo "Done. Run: mirrord --version"
      exit 0
    fi
    ASSET="mirrord_mac_universal"
    ;;
  *)
    echo "Unsupported OS. Install manually: cargo install mirrord or see https://github.com/metalbear-co/mirrord" >&2
    exit 1
    ;;
esac

URL="https://github.com/metalbear-co/mirrord/releases/download/${MIRRORD_TAG}/${ASSET}"
echo "Downloading mirrord ${MIRRORD_TAG} from $URL ..."
curl -fsSL "$URL" -o mirrord
chmod +x mirrord

if [[ -w "$INSTALL_DIR" ]]; then
  mv mirrord "$INSTALL_DIR/mirrord"
  echo "Installed to $INSTALL_DIR/mirrord"
else
  echo "Run: sudo mv $(pwd)/mirrord $INSTALL_DIR/mirrord"
  echo "Then: mirrord --version"
fi

"${INSTALL_DIR}/mirrord" --version 2>/dev/null || ./mirrord --version 2>/dev/null || true
