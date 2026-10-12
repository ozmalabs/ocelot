#!/usr/bin/env bash
# BUILD THIS TREE'S ENGINE — the ONLY sanctioned way to install a
# `substrate_rs` engine (PROTOCOL §10/§11).
#
# Run this in any tree that CHANGES `runners/dsl/src/*.rs` or `Cargo.toml`.
# `tests/test_engine_provenance_migrated.py` will refuse to let you measure
# without it: a tree whose Rust source diverges from the engine it loads is
# attributing numbers to source that did not produce them.
#
# WHY A SCRIPT AND NOT A `cp` IN THE DOCS -- this is a real footgun, proven:
#
#   `runners/dsl/python/substrate_rs/_native.abi3.so` is often a SYMLINK to
#   the canonical tree's build (`engine_provenance.ensure_tree_engine()`
#   creates it, so that a worktree sharing identical Rust source is
#   self-consistent for every script that inserts `runners/dsl/python`).
#
#   A plain `cp target/release/libsubstrate_rs.so python/substrate_rs/_native.abi3.so`
#   FOLLOWS THAT SYMLINK and writes THROUGH it -- silently overwriting the
#   CANONICAL tree's engine underneath every other agent's concurrent run.
#   That is precisely the shared-mutable-state failure §11 exists to stop,
#   and it is worse than the bug it would be fixing.
#
#   Verified: `cp new.so link.so` replaced the LINK TARGET's contents.
#   `cp --remove-destination` replaces the link itself. This script always
#   uses the safe form.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# A Python-runtime-only measurement may need the cdylib but none of the Rust
# probe executables. Keep the same safe install and provenance steps while
# allowing that narrower build target; default behavior remains the full tree.
BUILD_ARGS=()
if [ "${1:-}" = "--lib-only" ]; then
  BUILD_ARGS+=(--lib)
  shift
fi
if [ "$#" -gt 0 ]; then
  echo "usage: scripts/engine_build.sh [--lib-only]" >&2
  exit 2
fi

# WHICH PYTHON — resolved HERE, before the build, and fatal if absent.
#
# The build-record step at the bottom used to invoke a bare `python`, which is
# not guaranteed to exist: on a box carrying only `python3` it exits 127, and
# under `set -e` that aborts the script AFTER the .so has already been
# installed. The result is a binary NEWER than its own provenance record, so
# `build_is_stale` then refuses to measure -- 102 test files erroring out with
# what reads like a test problem when it is a build problem. Measured, in this
# tree, after ~8 rebuilds that all reported "== installed:" and looked fine.
#
# Failing up front instead means the worst case is a build that did not start,
# rather than an engine installed without the record that makes it usable.
# `PYTHON=... scripts/engine_build.sh` overrides the search.
PY=""
for cand in "${PYTHON:-}" python3 python; do
  [ -n "$cand" ] || continue
  if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -n "${PYTHON:-}" ] && [ "$PY" != "${PYTHON:-}" ]; then
  echo "!! PYTHON=${PYTHON} is not executable; using '$PY' instead" >&2
fi
if [ -z "$PY" ]; then
  echo "!! no python interpreter found (tried \$PYTHON, python3, python)" >&2
  echo "!! refusing to build: the engine would install WITHOUT its build record," >&2
  echo "!! and provenance would then refuse to measure anywhere." >&2
  exit 1
fi
echo "== build-record interpreter: $PY ($($PY -V 2>&1))"

cd "$ROOT/runners/dsl" || exit 1

echo "== building this tree's engine: $(pwd)"
cargo build --release "${BUILD_ARGS[@]}"

# --remove-destination: unlink first, THEN copy. Never write through a
# symlink into another tree.
cp --remove-destination target/release/libsubstrate_rs.so \
   python/substrate_rs/_native.abi3.so

echo "== installed: $(realpath python/substrate_rs/_native.abi3.so)"
cd "$ROOT"

# THE BUILD RECORD — the content of the Rust source this artifact was just
# built from, written beside it. `engine_provenance.build_is_stale` answers
# "did the source move since the build?" from THIS, by content. It used to
# answer from mtimes, which a `git checkout` rewrites in arbitrary order —
# 85 false "STALE" accusations in a freshly created worktree, refusing to
# measure in 88 test files on an engine that was exactly the committed one.
"$PY" -c "import sys; sys.path.insert(0, '.'); \
from domains.engine_provenance import record_build; \
print('== build record:', record_build())"

"$PY" domains/engine_provenance.py
echo "== verify:  $PY -m pytest tests/test_engine_provenance_migrated.py -q"
