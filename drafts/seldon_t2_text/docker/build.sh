#!/usr/bin/env bash
# =============================================================================
# build.sh — assemble the Docker build context and build the Track 2 image.
#
# Steps:
#   1. (Re)build the substrate_rs abi3 wheel with maturin (release), unless a
#      fresh wheel already exists — this is the ONLY heavy step and it runs
#      OUTSIDE the image (see Dockerfile "SUBSTRATE_RS BUILD").
#   2. Assemble a self-contained app/ dir (forecast_cli + adapter + phase3
#      typers + PoC forecasters) so container imports do not depend on the
#      repo's ../seldon_t2_poc relative layout.
#   3. Copy the wheel into wheels/.
#   4. docker build.
#
# Usage:
#   bash docker/build.sh                 # build image qfb2-t2-ocelot:latest
#   IMAGE=myname:tag bash docker/build.sh
#   SKIP_WHEEL=1 bash docker/build.sh    # reuse existing wheel, skip maturin
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"          # .../docker
TEXT_DIR="$(cd "$HERE/.." && pwd)"                            # .../seldon_t2_text
REPO_ROOT="$(cd "$TEXT_DIR/../.." && pwd)"                    # ocelot repo root
POC_DIR="$TEXT_DIR/../seldon_t2_poc"
DSL_DIR="$REPO_ROOT/runners/dsl"
IMAGE="${IMAGE:-qfb2-t2-ocelot:latest}"

echo "== Track 2 image build =="
echo "  context : $HERE"
echo "  image   : $IMAGE"

# ---- 1. substrate_rs wheel (heavy step, outside the image) -----------------
WHEEL_GLOB="$DSL_DIR/target/wheels/substrate_rs-*-abi3-*.whl"
if [ "${SKIP_WHEEL:-0}" != "1" ]; then
  echo "== building substrate_rs abi3 wheel (maturin, release) =="
  ( cd "$DSL_DIR" && maturin build --release )
fi
WHEEL="$(ls -t $WHEEL_GLOB 2>/dev/null | head -1 || true)"
if [ -z "$WHEEL" ]; then
  echo "ERROR: no substrate_rs abi3 wheel found under $DSL_DIR/target/wheels/." >&2
  echo "       Run without SKIP_WHEEL=1 to build it, or: cd runners/dsl && maturin build --release" >&2
  exit 1
fi
echo "  wheel   : $WHEEL"

# ---- 2. assemble self-contained app/ --------------------------------------
APP="$HERE/app"
rm -rf "$APP"; mkdir -p "$APP/phase3_derisk"
cp "$TEXT_DIR/forecast_cli.py" "$APP/"
cp "$TEXT_DIR/t2_adapter.py"   "$APP/"
cp "$POC_DIR/forecasters.py"   "$APP/"        # PoC mechanism (numpy-only)
cp "$TEXT_DIR/phase3_derisk/rules_typer.py"          "$APP/phase3_derisk/"
cp "$TEXT_DIR/phase3_derisk/model_endpoint_typer.py" "$APP/phase3_derisk/"
# also flatten the phase3 typers onto the top level so `import rules_typer`
# works regardless of the sys.path insertion order.
cp "$TEXT_DIR/phase3_derisk/rules_typer.py"          "$APP/"
cp "$TEXT_DIR/phase3_derisk/model_endpoint_typer.py" "$APP/"

# ---- 3. wheel into context -------------------------------------------------
mkdir -p "$HERE/wheels"
rm -f "$HERE/wheels/"*.whl
cp "$WHEEL" "$HERE/wheels/"

# ---- 4. docker build -------------------------------------------------------
echo "== docker build =="
docker build -t "$IMAGE" "$HERE"
echo "== done: $IMAGE =="
