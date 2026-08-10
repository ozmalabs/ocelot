"""tests/conftest.py — session-wide safety net.

Twice-bitten (runs 47/48): `domains/teach.py`'s `teach()` persists to
`seeds/<category>.json` (the REAL boot seed dir) by default. Several migrated
test files exercise teach()-backed helpers (e.g. `domains/stroke_codebook.py`'s
`grow_stroke_quantum`) without the per-file tmp-redirect fixture, so the bench
mutates `seeds/stroke_shapes.json` — a file owned across sessions. That has
clobbered a parallel session's working file twice.

This arms `domains.teach`'s env-gated guard (`OZMA_SEED_PERSIST_DISABLED`) for
the ENTIRE test session, so no test — present or future, isolated or not —
can write to the real seeds/ dir. Individual tests that WANT to exercise
persistence still can: they pass an explicit `seeds_dir=tmp_path`, which never
resolves to the real SEEDS dir and so is never blocked by the guard (see
`domains/teach.py::_persist_blocked`).
"""
from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _disable_real_seed_persistence():
    """Session-scoped, autouse: block every default/real-dir teach() write for
    the whole pytest run, regardless of which test forgets isolation."""
    prev = os.environ.get("OZMA_SEED_PERSIST_DISABLED")
    os.environ["OZMA_SEED_PERSIST_DISABLED"] = "1"
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop("OZMA_SEED_PERSIST_DISABLED", None)
        else:
            os.environ["OZMA_SEED_PERSIST_DISABLED"] = prev
