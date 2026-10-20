#!/usr/bin/env bash
# BUILD THIS TREE'S WASM ENGINE — WebAssembly target for OCELOT (G, Gamma, C) Substrate
#
# Builds `runners/wasm` (`substrate-wasm`) targeting `wasm32-unknown-unknown`
# with wasm-bindgen for browser Web Worker and main-thread execution.
#
# Usage:
#   scripts/engine_build_wasm.sh [--target web|bundler|nodejs] [--dev|--release]
#
set -euo pipefail

# Ensure rustup cargo/rustc takes precedence over homebrew system rust
export PATH="$HOME/.cargo/bin:$PATH"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="web"
PROFILE="--release"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
    --dev)
      PROFILE="--dev"
      shift
      ;;
    --release)
      PROFILE="--release"
      shift
      ;;
    -h|--help)
      echo "Usage: scripts/engine_build_wasm.sh [--target web|bundler|nodejs] [--dev|--release]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

# Resolve wasm-pack runner
WASM_PACK_CMD=""
if command -v wasm-pack >/dev/null 2>&1; then
  WASM_PACK_CMD="wasm-pack"
elif command -v npx >/dev/null 2>&1; then
  WASM_PACK_CMD="npx --yes wasm-pack"
else
  echo "!! Error: Neither wasm-pack nor npx found." >&2
  echo "!! Install wasm-pack via 'cargo install wasm-pack' or ensure npm/npx is installed." >&2
  exit 1
fi

echo "== using wasm-pack: $WASM_PACK_CMD"
echo "== target: $TARGET"
echo "== profile: $PROFILE"

cd "$ROOT/runners/wasm"

echo "== building wasm engine: $(pwd)"
$WASM_PACK_CMD build --target "$TARGET" --out-dir pkg $PROFILE

PKG_DIR="$ROOT/runners/wasm/pkg"
WASM_FILE="$PKG_DIR/substrate_wasm_bg.wasm"

if [ ! -f "$WASM_FILE" ]; then
  echo "!! Error: expected output $WASM_FILE not found!" >&2
  exit 1
fi

WASM_BYTES=$(wc -c < "$WASM_FILE")
WASM_KB=$(( WASM_BYTES / 1024 ))
WASM_MB=$(awk "BEGIN {printf \"%.2f\", $WASM_BYTES / (1024 * 1024)}")

GZIP_BYTES=$(gzip -c "$WASM_FILE" | wc -c)
GZIP_KB=$(( GZIP_BYTES / 1024 ))

echo "=========================================================="
echo "== WASM Engine Built Successfully!"
echo "== Location:    $WASM_FILE"
echo "== Binary size: $WASM_KB KB ($WASM_MB MB)"
echo "== Gzip size:   $GZIP_KB KB"
echo "== JS bindings: $PKG_DIR/substrate_wasm.js"
echo "== TypeScript:  $PKG_DIR/substrate_wasm.d.ts"
echo "=========================================================="
