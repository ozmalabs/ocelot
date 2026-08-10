"""GATE — residual-salience (block 157000-157999).

The efference -> residual -> salience attention pipeline. H1 (synthetic, ideal
oracle) proves the mechanism: the dominant-MODE egomotion gain recovers the true
egomotion where 155000's median-over-all-cells reads (0,0), and RESIDUAL
salience ranks the independent mover ABOVE the egomotion-swung background where
RAW salience fails. The controls verify the OFF paths are byte-identical. H2
(E1M1, real WAD) records the honest split: the dominant-mode gain CAPTURES the
egomotion (mode nonzero where the median is zero) -- a clear sub-mechanism win --
but the end-to-end ranking does NOT improve on the real forward-walk carve (the
named DEGRADE: depth-dependent translational flow + a sub-pixel imp).

Reads MEASURED values only (AUC / mode / rank), never an exact d2. Skips H2
explicitly if VizDoom / DOOM.WAD are absent.

ARCHITECTURE (CLAUDE.md): the gate calls the probe's mechanical functions (a
flow-histogram peak, arithmetic cancellation, the EXISTING Rust
`Substrate.shape_salience`); no agent decision, no graph-state conditional.
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.residual_salience_probe import (  # noqa: E402
    run_h1, run_h2, dominant_mode_gain, median_all_gain, make_coverage_field,
    capture_e1m1,
)


# ---- shared, cached H1 (fast, deterministic) --------------------------------
_H1 = None


def _h1():
    global _H1
    if _H1 is None:
        _H1 = run_h1()
    return _H1


def test_engine_source_is_matched_not_stale():
    """§10 — the number records WHICH binary; assert source_match in {own, shared},
    NEVER a pinned build hash and NEVER a context-specific value. From a worktree
    the shared canonical reads 'shared'; ON MAIN the same engine reads 'own' (the
    tree owns its build) — both are matched, only 'stale'/mismatch is a failure."""
    from domains.engine_provenance import provenance_stamp
    prov = provenance_stamp(strict=False)
    assert prov.get("source_match") in ("own", "shared"), prov


# ======================================================================
#  H1 — the mechanism, against an ideal oracle (able to fail)
# ======================================================================
def test_dominant_mode_gain_recovers_egomotion_where_median_fails():
    """The dominant MODE recovers the true egomotion at <50% flow coverage,
    exactly where 155000's median-over-all-cells reads (0,0). Able to fail:
    a wrong mode would not equal E_true."""
    rec = _h1()["gain_recovery"]
    r42 = rec["coverage_0.42"]
    assert r42["gain_mode"] == r42["true_egomotion"], r42          # MODE recovers
    assert tuple(r42["gain_median_all"]) == (0.0, 0.0), r42        # MEDIAN fails
    # and a genuinely <50% field also recovers
    r30 = rec["coverage_0.3"]
    assert r30["gain_mode"] == r30["true_egomotion"], r30
    assert tuple(r30["gain_median_all"]) == (0.0, 0.0), r30


def test_dominant_mode_is_the_histogram_peak_not_a_threshold():
    """§13 — the mode falls OUT of the flow histogram. Direct able-to-fail check:
    the mode of a field whose plurality flow is a KNOWN vector is that vector,
    even when it is a minority of ALL cells."""
    rng = np.random.default_rng(157000 + 3)
    vy, vx = make_coverage_field(60, 80, (0, 5), 0.35, rng)
    assert dominant_mode_gain(vy, vx) == (0.0, 5.0)
    # median over all cells (majority static) reads zero — the 156000 failure
    assert median_all_gain(vy, vx) == (0.0, 0.0)


def test_residual_salience_ranks_mover_above_background_where_raw_fails():
    """HEADLINE H1. On a synthetic walk (uniform egomotion + independent mover +
    view-fixed apparatus + fragmented background), RAW salience does NOT rank the
    mover above the background (egomotion-swung background dominates), but
    RESIDUAL salience does — mover top-1, fg-vs-bg AUC = 1.0, apparatus stays
    demoted. Able to fail: a broken cancellation would not lift the AUC."""
    p = _h1()["primary"]
    assert p["auc_residual_fg_vs_bg"] > p["auc_raw_fg_vs_bg"], p     # the fix
    assert p["auc_residual_fg_vs_bg"] >= 0.95, p                     # ~1.0
    assert p["mover_rank_residual"] == 1, p                          # mover top-1
    assert p["auc_residual_fg_vs_apparatus"] >= 0.95, p             # apparatus demoted
    # RAW genuinely fails (background is as/more salient than the mover)
    assert p["auc_raw_fg_vs_bg"] <= 0.6, p


# ======================================================================
#  H1 controls — the OFF paths (must correspond to the experiment, §6)
# ======================================================================
def test_control_no_egomotion_is_byte_identical_ranking():
    """E=0 -> mode ~0 -> residual == raw -> ranking byte-identical."""
    c = _h1()["control_no_egomotion"]
    assert c["gain_mode_all_zero"] is True
    assert c["ranking_identical"] is True
    assert c["raw_eq_residual_values"] is True


def test_control_static_plus_egomotion_is_flat_everywhere():
    """Static scene swung by egomotion -> all residuals ~0 -> low salience
    everywhere (no track ranks high)."""
    c = _h1()["control_static_plus_egomotion"]
    assert c["all_low"] is True, c
    assert c["residual_salience_max"] < 1.0, c


def test_control_mover_no_egomotion_unchanged():
    """Independent mover with NO egomotion -> salient with AND without
    cancellation (residual == raw there)."""
    c = _h1()["control_mover_no_egomotion"]
    assert c["mover_top_raw"] is True
    assert c["mover_top_residual"] is True
    assert c["raw_eq_residual"] is True


# ======================================================================
#  H2 — E1M1, ground-truth-scored. The honest split. Skips if WAD absent.
# ======================================================================
def test_h2_e1m1_egomotion_captured_and_subpixel_degrade():
    """On the real E1M1 walk: the dominant-mode gain CAPTURES the egomotion
    (mode nonzero in far more frames than 155000's median-over-all, which is
    ~always zero at 42% coverage) — the sub-mechanism WIN. The live imp is
    sub-pixel at down=2 (0 trackable monster tracks) — the named DEGRADE,
    a SEPARATE wall. Reads measured values, never an exact d2."""
    frames = capture_e1m1()
    if not frames:
        pytest.skip("vizdoom or DOOM.WAD absent")
    h2 = run_h2(frames)
    ec = h2["egomotion_capture"]
    # THE H2 WIN: the mode captures egomotion where the median reads (0,0).
    assert ec["mode_nonzero_frames"] > 5 * max(1, ec["median_all_nonzero_frames"]), ec
    assert ec["mode_nonzero_frames"] >= 0.5 * ec["total_motion_frames"], ec
    # THE NAMED DEGRADE: the live imp is sub-pixel -> 0 trackable monster tracks.
    assert h2["n_monster_tracks"] == 0, h2["n_monster_tracks"]
    # the residual pipeline RAN (produced its own AUC), whether or not it helped
    assert h2["auc_residual_fg_vs_bg"] is not None, h2
    # honest record: the end-to-end fg-vs-bg improvement did NOT clear the
    # centroid-only raw baseline on this forward-walk carve (the DEGRADE we own)
    assert h2["auc_residual_fg_vs_bg"] <= h2["auc_rawmotion_fg_vs_bg"] + 0.05, h2
