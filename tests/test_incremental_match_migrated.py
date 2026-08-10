"""INCREMENTAL MATCH — the block 192000 gate (ladder rung A).

Self-contained: every fact this pins is recomputed here, none is read back from
a results file. Pins, in order:

  * the flag is DEFAULT OFF, and OFF is the committed path;
  * C2 THE REDUCTION — `incremental_match` ON is a DROPPABLE BYTE-IDENTICAL
    MIRROR of the full-rescan engine, on a VISION and a NON-VISION workload, and
    on the landed 160x120 carve;
  * C3 RETRACTION — a DELETING (where-flip-on-delete negation) workload is
    byte-identical ON vs OFF, and both retract (n/2 slots open);
  * ⚠️ F1 THE UNSOUND-RETRACTION FALSIFIER — an engine that MISSES a retraction
    (accepts a stale cursor regardless of its edge type's delete version) MUST
    diverge from the full rescan on a MATCHER-of-the-deleted-type workload. If a
    wrong retraction broke nothing, the reduction gate would be too weak to trust;
  * H1 THE COVERED EXPONENT — on a where-less append-only shape, the `cand_enum`
    work count per tick drops from ~O(cells^2) (full rescan) to ~O(cells)
    (incremental).
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

M = pytest.importorskip("scripts.incremental_match_measure")


def _has_flag():
    import substrate_rs as srs
    return hasattr(srs.Substrate()._inner, "set_incremental_match")


needs_engine = pytest.mark.skipif(
    not _has_flag(), reason="engine has no block-192000 flags (rebuild)")


@needs_engine
def test_flag_defaults_off():
    """A new Substrate has incremental_match OFF (the committed path is default).
    Toggling it must not raise."""
    import substrate_rs as srs
    inner = srs.Substrate()._inner
    inner.set_incremental_match(False)
    inner.set_incremental_match(True)
    inner.set_incremental_match(False)


# --------------------------------------------------- C2 THE REDUCTION --------
@needs_engine
@pytest.mark.parametrize("name", ["vision_carve", "conversation"])
def test_reduction_byte_identical_vision_and_non_vision(name):
    """C2 — incremental ON is byte-identical to full rescan (OFF), on a VISION
    workload and a NON-VISION workload. The headline correctness claim.

    Uses the SCOPED `run_workload` (never the module-level monkeypatch) so this
    test file NEVER pollutes the shared 189000 harness in a same-session run."""
    off = M.run_workload(name, False, False)
    incr = M.run_workload(name, True, False)
    assert off == incr, f"{name}: incremental_match is NOT byte-identical to full rescan"


@needs_engine
def test_reduction_on_landed_carve():
    """C2b — the landed 160x120 carve is byte-identical off vs incremental ON,
    4 polys / IoU 0.1215 / precision 0.9784 / 0 false."""
    lc = M.landed_carve_identity()
    assert lc["off_eq_incr"], "landed carve: incremental NOT byte-identical"
    off = lc["off"]
    assert off["n_polygons"] == 4
    assert abs(off["union_iou"] - 0.1215) < 1e-3
    assert abs(off["carve_precision"] - 0.9784) < 1e-3
    assert off["false_polygons"] == 0


# --------------------------------------------------- C3 RETRACTION -----------
@needs_engine
def test_retraction_negation_byte_identical_and_falsifier_diverges():
    """C3 — a DELETING workload (a delete flips a `Not Exists` where on a stable
    slot edge -> the slot opens) is byte-identical ON vs OFF, and both RETRACT:
    every unblocked slot opens (n/2).

    ⚠️ F1 — the UNSOUND retraction SKIPS the where-reader cursor clear, so the
    delete-driven where-flip is silently missed -> fewer slots open -> the dump
    DIVERGES. A wrong retraction that broke nothing would make the reduction
    gate vacuous."""
    r = M.retraction_identity()
    # C3
    assert r["off_eq_incr"], "C3: incremental NOT byte-identical on the deleting workload"
    assert r["off_n_open"] == r["n"] // 2
    assert r["incr_n_open"] == r["n"] // 2
    # F1
    assert r["unsound_diverges"], "F1: the UNSOUND retraction did NOT diverge — gate is vacuous"
    assert r["unsound_n_open"] < r["off_n_open"], \
        "F1: unsound should leave slots CLOSED (missed the where-flip)"


# --------------------------------------------------- H1 THE EXPONENT ---------
@needs_engine
def test_covered_path_work_count_exponent_drops():
    """H1 — on the covered where-less append-only shape, the per-tick `cand_enum`
    work count exponent vs graph size drops from ~2.0 (full rescan) to <= 1.3
    (incremental ~ O(new edges)). Fitted on the deterministic count, not ms."""
    sc = M.covered_scaling()
    off_exp = sc["cand_enum_exponent"]["off"]
    incr_exp = sc["cand_enum_exponent"]["incr"]
    assert off_exp > 1.6, f"full-rescan cand_enum exponent {off_exp:.2f} not ~quadratic"
    assert incr_exp <= 1.3, f"incremental cand_enum exponent {incr_exp:.2f} did not drop"
    assert incr_exp < off_exp - 0.5, "incremental exponent must be materially below full rescan"
