#!/usr/bin/env bash
# SERVE OCELOT SUBSTRATE STUDIO
#
# Launches a local static HTTP server for the OCELOT WebAssembly Substrate Studio
# and Experiments Laboratory.
#
# Usage:
#   scripts/serve_wasm_studio.sh [PORT]
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-8000}"

echo "=========================================================="
echo "  OCELOT SUBSTRATE STUDIO & EXPERIMENTS LABORATORY"
echo "=========================================================="
echo "  Root:      $ROOT"
echo "  Port:      $PORT"
echo "  URL:       http://localhost:$PORT/runners/wasm/web/index.html"
echo "=========================================================="
echo "Press Ctrl+C to stop the server."

cd "$ROOT"
python3 -m http.server "$PORT"
