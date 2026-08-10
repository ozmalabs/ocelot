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
cd "$ROOT/runners/dsl" || exit 1

echo "== building this tree's engine: $(pwd)"
cargo build --release

# --remove-destination: unlink first, THEN copy. Never write through a
# symlink into another tree.
cp --remove-destination target/release/libsubstrate_rs.so \
   python/substrate_rs/_native.abi3.so

echo "== installed: $(realpath python/substrate_rs/_native.abi3.so)"
cd "$ROOT"
python domains/engine_provenance.py
echo "== verify:  python -m pytest tests/test_engine_provenance_migrated.py -q"
