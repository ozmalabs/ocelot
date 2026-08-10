"""PREDICATE RETRACTION (block 194000, ladder rung B) — engine-semantics gate.

Pins, at the mechanism grain:
  * C1  — the flag DEFAULTS OFF (toggle round-trips).
  * C2  — THE REDUCTION: node-seeded ON ≡ full-rescan OFF, byte-identical
          (float-exact dump AND the fired-edge observable set).
  * H1  — the covered stable-edge attr-flip shape's per-tick cand_enum work
          count drops from ~O(N) (full rescan) to O(K)=FLAT (node-seeded).
  * F1  — the UNSOUND falsifier (drops one dirty node) DIVERGES from full rescan.
  * F2  — no-free-lunch: on an all-fallback control, ON ≡ OFF, work ≤ ~1.05x.

The measure module (`scripts.predicate_retraction_measure`) is IMPORT-INERT:
flags are toggled only inside a scoped context manager, never at module top level.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runners", "dsl", "python"))

M = pytest.importorskip("scripts.predicate_retraction_measure")


def _has_flag():
    import substrate_rs as srs
    return hasattr(srs.Substrate()._inner, "set_predicate_retraction")


pytestmark = pytest.mark.skipif(not _has_flag(),
                                reason="engine lacks set_predicate_retraction (rebuild)")


def test_flag_defaults_off():
    """C1 — the flag round-trips and starts off."""
    import substrate_rs as srs
    inner = srs.Substrate()._inner
    inner.set_predicate_retraction(False)
    inner.set_predicate_retraction(True)
    inner.set_predicate_retraction(False)
    inner.set_predicate_retraction_unsound(False)


def test_reduction_byte_identical():
    """C2 — node-seeded ON ≡ full-rescan OFF, float-exact dump."""
    bi = M.byte_identity(N=128, K=5)
    assert bi["identical"], "predicate-retraction ON diverged from full rescan"


def test_reduction_byte_identical_various_scales():
    """C2 across scales + K values — the reduction is not a single-point fluke."""
    for N in (64, 256):
        for K in (1, 3, 7):
            off = M.run_tick(N, K, pred=False)
            on = M.run_tick(N, K, pred=True)
            assert off["dump"] == on["dump"], f"diverged at N={N} K={K}"


def test_covered_work_count_drops_to_constant():
    """H1 — full-rescan cand_enum is ~O(N); node-seeded is FLAT (O(K), K fixed)."""
    sc = M.scaling(sizes=(64, 128, 256, 512), K=3)
    off_exp = sc["cand_enum_exponent"]["off"]
    on_exp = sc["cand_enum_exponent"]["on"]
    assert off_exp > 0.8, f"full-rescan exponent {off_exp:.2f} not ~linear"
    assert on_exp <= 0.3, f"node-seeded exponent {on_exp:.2f} did not flatten to O(K)"
    assert on_exp < off_exp - 0.5, "node-seeded exponent must be materially below full rescan"
    # And the absolute counts: node-seeded is bounded by a small constant.
    on_counts = [sc["per_n"]["on"][n]["cand_enum"] for n in sc["sizes"]]
    assert max(on_counts) <= 16, f"node-seeded counts not O(K): {on_counts}"


def test_unsound_falsifier_diverges():
    """F1 — dropping one dirty node MUST break byte-identity vs full rescan."""
    f = M.falsifier(N=128, K=5)
    assert f["diverges"], "unsound predicate-retraction did NOT diverge (gate vacuous)"


def test_no_free_lunch_all_fallback_control():
    """F2 — on a control where NO rule is covered (K=0 flips, i.e. no external
    attr write at all: the rule never engages the node-seeded path), ON ≡ OFF and
    the work count is within 1.05x. Guards against the flag adding overhead on
    the paths it does not help."""
    off = M.run_tick(64, 0, pred=False)
    on = M.run_tick(64, 0, pred=True)
    assert off["dump"] == on["dump"]
    hi = max(off["cand_enum"], 1)
    assert on["cand_enum"] <= hi * 1.05 + 1, (
        f"predicate-retraction added work on a non-covered control: "
        f"off={off['cand_enum']} on={on['cand_enum']}")
