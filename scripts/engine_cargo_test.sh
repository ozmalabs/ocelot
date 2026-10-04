#!/usr/bin/env bash
# RUN THE ENGINE'S RUST TESTS (runners/dsl).
#
# The engine is a pyo3 extension: its default feature `extension-module`
# deliberately does NOT link libpython (the loading interpreter provides the
# symbols). A `cargo test` binary is an executable, so with that feature it
# cannot link (undefined PyErr_* / PyObject_* ...). This script builds the
# tests WITHOUT the default feature, so pyo3 links the interpreter's
# libpython, and points the runtime loader at that interpreter's LIBDIR.
#
#   scripts/engine_cargo_test.sh                 # cargo test --lib
#   scripts/engine_cargo_test.sh --lib -- --test-threads=1
#   scripts/engine_cargo_test.sh --test p3_graph
#
# Extra arguments are passed to `cargo test` (default: --lib). The scale-audit
# tests share process-global counters; use --test-threads=1 for a
# deterministic run (META_SHAPE_FIRST_CLASS_RESULTS §7.1).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3}"
LIBDIR="$("$PY" -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))')"
export PYO3_PYTHON="$(command -v "$PY")"
export LD_LIBRARY_PATH="${LIBDIR}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cd "$ROOT/runners/dsl"
if [ "$#" -eq 0 ]; then set -- --lib; fi
exec cargo test --no-default-features "$@"
