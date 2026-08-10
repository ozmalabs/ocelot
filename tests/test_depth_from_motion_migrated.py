"""GATE — depth-from-motion / depth-aware egomotion (block 158000-158999).

Forward walk = global radial expansion from the FOE (154000's op, global). H1
(synthetic, ideal oracle) proves the mechanism: the FOE is recovered by
least-squares; the single-global-vector cancellation (157000) FAILS to isolate
the mover on depth-varying (parallax) flow while the radial-direction-consistency
(tangential) residual ISOLATES it; recovered depth r/|flow| = Z/speed correlates
exactly with the known depth; the view-fixed apparatus (zero flow) stays demoted.
The three controls verify rotation->no-FOE, static->depth-everywhere-no-mover,
mover-no-ego->plain-residual-flags. H2 (E1M1, real WAD) is GROUND-TRUTH-scored
against the VizDoom DEPTH buffer: FOE near image centre; depth-from-motion
recovers real scene depth when the flow carries signal (down=1) though the
157000-reused coarse L=4/down=2 flow is a diagnosed null (flow-quality wall); the
imp is sub-pixel (0 monster tracks, the named 156000/157000 DEGRADE).

Reads MEASURED values only (Spearman / AUC / IoU / FOE), never an exact d2. Skips
H2 explicitly if VizDoom / DOOM.WAD are absent.

ARCHITECTURE (CLAUDE.md): the gate calls the probe's mechanical numpy sensors
(FOE least-squares, radial decomposition, depth-from-magnitude) + the EXISTING
Rust Substrate.shape_salience; no agent decision, no graph-state conditional.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.depth_from_motion_probe import (  # noqa: E402
    run_h1, run_h2, estimate_foe, radial_decompose, flag_movers,
    synth_forward_scene, capture_e1m1,
)


# ---- shared, cached H1 (fast, deterministic) --------------------------------
_H1 = None
_H2 = None


def _h1():
    global _H1
    if _H1 is None:
        _H1 = run_h1()
    return _H1


def _h2():
    global _H2
    if _H2 is None:
        frames = capture_e1m1()
        if not frames:
            _H2 = "skip"
        else:
            _H2 = run_h2(frames)
    return _H2


def test_engine_source_is_matched_not_stale():
    """§10 — the number records WHICH binary; assert source_match in {own, shared},
    NEVER a pinned build hash and NEVER a context-specific value. From a worktree
    the shared canonical reads 'shared'; ON MAIN the same engine reads 'own' — both
    are matched, only 'stale'/'DIVERGED'/'unknown' is a failure."""
    from domains.engine_provenance import provenance_stamp
    prov = provenance_stamp(strict=False)
    assert prov.get("source_match") in ("own", "shared"), prov


# ======================================================================
#  H1 — the mechanism, against an ideal oracle (able to fail)
# ======================================================================
def test_foe_estimated_from_flow_lines():
    """The FOE FALLS OUT of the flow field (least-squares intersection of the
    flow lines) — recovered to sub-cell error on a KNOWN off-centre FOE. Able to
    fail: a wrong FOE would not match the planted one."""
    foe = _h1()["foe"]
    assert foe["estimated"] is not None, foe
    assert foe["error_cells"] is not None and foe["error_cells"] < 1.0, foe
    assert foe["expansion_dominant"] is True, foe          # forward => expansion


def test_single_vector_fails_radial_isolates_the_mover():
    """(i)+(ii) HEADLINE. On DEPTH-VARYING (parallax) forward-walk flow, the
    single-global-vector cancellation (157000: dominant MODE and 155000: median)
    does NOT isolate the independently-moving object (buried in the near/far
    background residual), but the radial-direction-consistency (tangential)
    residual DOES — AUC 1.0, IoU 1.0. Able to fail: a broken decomposition would
    not separate the mover."""
    mi = _h1()["mover_isolation"]
    # (i) single-vector fails (both baselines at or below chance-ish)
    assert mi["auc_singlevec_mode_mover_vs_bg"] <= 0.65, mi
    assert mi["auc_singlevec_median_mover_vs_bg"] <= 0.65, mi
    assert mi["iou_singlevec_flag_vs_mover"] <= 0.2, mi
    # (ii) radial isolates the mover, strictly better than single-vector
    assert mi["auc_radial_mover_vs_bg"] >= 0.90, mi
    assert mi["iou_radial_flag_vs_mover"] >= 0.5, mi
    assert mi["auc_radial_mover_vs_bg"] > mi["auc_singlevec_median_mover_vs_bg"], mi
    assert mi["iou_radial_flag_vs_mover"] > mi["iou_singlevec_flag_vs_mover"], mi


def test_recovered_depth_correlates_with_known_depth():
    """(iii) recovered depth = r/|flow| = Z/speed correlates with the known depth
    field over radial-consistent static cells (near-exact on the ideal oracle).
    Able to fail: a wrong depth read would not track Z."""
    dr = _h1()["depth_recovery"]
    assert dr["spearman_recovered_vs_true"] is not None, dr
    assert dr["spearman_recovered_vs_true"] >= 0.90, dr
    assert dr["n_consistent_cells"] > 100, dr


def test_apparatus_zero_flow_stays_demoted():
    """(iv) the view-fixed apparatus (zero flow) is NEVER flagged as a mover by the
    radial residual — no flow => no defined direction => excluded. Able to fail: a
    decomposition that flagged flat cells would flag it."""
    ap = _h1()["apparatus"]
    assert ap["radial_flagged_as_mover"] == 0, ap


# ---- H1 controls (must correspond to the experiment, §6) --------------------
def test_control_rotation_no_spurious_foe():
    """Pure rotation (uniform-ish flow, curl-dominated) is NOT an expansion, so no
    FOE is spuriously fit — falls back to 155000's uniform cancellation."""
    c = _h1()["control_rotation"]
    assert c["expansion_dominant"] is False, c
    assert c["foe_would_be_spurious"] is False, c


def test_control_static_forward_depth_everywhere_no_mover():
    """Static scene + forward translation (NO mover): every cell is
    radial-consistent => NOTHING flagged as a mover; depth recovered everywhere."""
    c = _h1()["control_static_forward"]
    assert c["n_flagged_as_mover"] == 0, c
    assert c["depth_spearman"] is not None and c["depth_spearman"] >= 0.90, c


def test_control_mover_no_egomotion_plain_residual_flags():
    """Independent mover + NO egomotion: no expansion => the radial check is a
    no-op => the PLAIN residual (raw flow) flags the mover."""
    c = _h1()["control_mover_no_ego"]
    assert c["expansion_dominant"] is False, c
    assert c["radial_is_noop"] is True, c
    assert c["plain_residual_flags_mover_iou"] >= 0.5, c


# ======================================================================
#  H2 — E1M1, ground-truth-scored against the VizDoom DEPTH buffer.
#  Skips if WAD/VizDoom absent.
# ======================================================================
def test_h2_foe_near_image_centre():
    """On the real E1M1 forward walk the estimated FOE (heading) sits near the
    image centre — a sanity check that the FOE least-squares tracks the heading."""
    h2 = _h2()
    if h2 == "skip":
        pytest.skip("vizdoom or DOOM.WAD absent")
    foe = h2["foe"]
    assert foe["n"] > 50, foe
    cx, cy = foe["image_centre"]
    assert abs(foe["median_x"] - cx) < 0.5 * cx, foe        # within half-frame
    assert abs(foe["median_y"] - cy) < 0.5 * cy, foe


def test_h2_depth_from_motion_recovers_real_depth_and_flowquality_wall():
    """HEADLINE H2. Depth-from-motion vs the VizDoom DEPTH buffer:
      * the 157000-reused coarse flow (L=4, down=2) is a NULL — the diagnosed
        flow-quality DEGRADE (noise-dominated block matches on 4 luma levels);
      * the mechanism RECOVERS real Doom scene depth when the flow carries signal
        (down=1 raw luma): sign-correct positive Spearman on a majority of forward
        frames.
    Reads measured Spearman values, never an exact d2."""
    h2 = _h2()
    if h2 == "skip":
        pytest.skip("vizdoom or DOOM.WAD absent")
    arms = h2["depth_from_motion"]
    coarse = arms["reused_L4_down2"]["forward_frames"]
    fine = arms["raw_luma_down1"]["forward_frames"]
    # the pre-registered coarse pipeline is a null (honest degrade)
    assert coarse["median"] < 0.30, coarse
    # the mechanism recovers depth on adequate flow: sign-correct, majority-positive
    assert fine["n"] > 30, fine
    assert fine["median"] >= 0.25, fine
    assert fine["frac_pos"] >= 0.70, fine
    # and the finer flow strictly beats the coarse reused pipeline
    assert fine["median"] > coarse["median"], (coarse, fine)


def test_h2_mover_isolation_subpixel_degrade():
    """The live imp is sub-pixel at down=2 => 0 trackable monster tracks (the named
    156000/157000 wall). The residual pipelines RAN (produced their AUCs); the
    depth recovery — not the mover ranking — is the measurable win here."""
    h2 = _h2()
    if h2 == "skip":
        pytest.skip("vizdoom or DOOM.WAD absent")
    tk = h2["mover_isolation_track"]
    assert tk["n_monster_tracks"] == 0, tk               # the sub-pixel DEGRADE
    assert tk["auc_radial_fg_vs_bg"] is not None, tk
    assert tk["auc_singlevec_fg_vs_bg"] is not None, tk
    pc = h2["mover_isolation_per_cell_forward"]
    assert pc["n_fg_cells"] > 0 and pc["n_bg_cells"] > 0, pc
