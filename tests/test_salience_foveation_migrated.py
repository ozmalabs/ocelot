"""GATE — salience-driven foveation (block 159000-159999).

Foveation = supergraph-optimal compute allocation: a COARSE global flow finds
WHERE the surprise is (the residual/tangential salience field, 158000's
depth-independent mover residual made spatial), a FINE local flow resolves it
THERE, the rest stays cheap. H1 (synthetic, ideal oracle) proves the mechanism:
the residual-salience argmax LOCATES the mover (the raw-|flow| argmax does not);
the coarse sensor under-resolves depth at the region; the foveated FINE flow
recovers it (near-exact + 4x the cells) at a small fraction of full-res cost. The
three controls verify no-salient->no-fovea, residual-not-raw, two-regions->both.
H2 (E1M1, real WAD) is GROUND-TRUTH-scored vs the VizDoom DEPTH + labels buffers:
foveated fine depth beats the coarse-in-window null; the imp is sub-pixel at
coarse (0 monster tracks) but super-pixel in a fine window (the named DEGRADE:
motion-only salience cannot bootstrap a mover with no coarse motion signal);
foveated ms/frame < full-res-everywhere.

Reads MEASURED values only (Spearman / IoU / distance / cell counts / ms), never
an exact d2. Skips H2 explicitly if VizDoom / DOOM.WAD are absent.

ARCHITECTURE (CLAUDE.md): the gate calls the probe's mechanical numpy glue
(salience field, top-K window selection, block-SAD on a crop) + 158000's
mechanical sensors; no agent decision, no graph-state conditional.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.salience_foveation_probe import (  # noqa: E402
    run_h1, run_h2, capture_e1m1, timing_arm,
)


_H1 = None
_H2 = None
_FRAMES = "unset"


def _h1():
    global _H1
    if _H1 is None:
        _H1 = run_h1()
    return _H1


def _frames():
    global _FRAMES
    if _FRAMES == "unset":
        _FRAMES = capture_e1m1()
    return _FRAMES


def _h2():
    global _H2
    if _H2 is None:
        fr = _frames()
        _H2 = "skip" if not fr else run_h2(fr)
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
def test_fovea_locates_the_mover_on_the_residual_not_the_raw_flow():
    """(ii) + the residual-not-raw control. The residual (tangential) salience
    argmax lands ON the mover; the RAW |flow| argmax lands OFF it (on the
    highest-magnitude near/parallax background — the 157000 reason salience must
    be on the RESIDUAL). Able to fail: a raw-magnitude salience would pick the
    background."""
    fl = _h1()["fovea_locates"]
    assert fl["n_fovea"] >= 1, fl
    assert fl["residual_peak_on_mover"] is True, fl
    assert fl["raw_flow_peak_on_mover"] is False, fl


def test_coarse_under_resolves_fine_recovers_depth_at_the_region():
    """(i) + (iii) HEADLINE. At the salient region the COARSE (quantized, low-res)
    depth-from-motion under-resolves; the FOVEATED FINE flow RECOVERS it —
    near-exact on the ideal oracle and over ~4x the cells. Able to fail: a broken
    fine recompute would not beat coarse."""
    cr = _h1()["coarse_null_vs_fine_recover"]
    assert cr["fine_depth_spearman"] is not None, cr
    assert cr["fine_depth_spearman"] >= 0.90, cr
    assert cr["coarse_depth_spearman"] is not None, cr
    # fine strictly recovers over coarse
    assert cr["fine_depth_spearman"] > cr["coarse_depth_spearman"], cr
    # and resolves many more cells (the resolution the fovea buys)
    assert cr["fine_consistent_cells"] > 2 * cr["coarse_consistent_cells"], cr
    # the mover stays isolated at fine resolution
    assert cr["fine_mover_iou"] >= 0.5, cr


def test_foveated_is_a_fraction_of_full_res_cost():
    """(iv) COST. Foveated (coarse-everywhere + one fine window) is a small
    fraction of full-res-everywhere. Able to fail: a window as big as the frame
    would not be cheap."""
    co = _h1()["cost"]
    assert co["foveated_fraction_of_fullres"] <= 0.5, co
    assert co["fine_window_cells"] < co["fullres_everywhere_cells"], co


def test_control_no_salient_region_no_fovea_fires():
    """No independent mover (pure radial egomotion) => the residual salience is
    below the one-pixel floor everywhere => NO fovea fires (falls back to coarse).
    Able to fail: a salience that fired on egomotion would fire here."""
    c = _h1()["control_no_salient"]
    assert c["n_fovea"] == 0, c
    assert c["falls_back_to_coarse"] is True, c


def test_control_two_regions_foveates_both():
    """Two matched movers => top-2 foveae land on BOTH regions, not one merged
    window. Able to fail: a single-peak selector would miss one."""
    c = _h1()["control_two_regions"]
    assert c["n_fovea"] == 2, c
    assert c["both_regions_covered"] is True, c


# ======================================================================
#  H2 — E1M1, ground-truth-scored. Skips if WAD/VizDoom absent.
# ======================================================================
def test_h2_foveated_fine_depth_beats_the_coarse_in_window_null():
    """HEADLINE H2. The foveated FINE-in-window depth-from-motion (vs the VizDoom
    DEPTH buffer) beats the coarse-in-the-same-window arm (the null it
    re-resolves). Reads measured Spearman medians, never an exact d2."""
    h2 = _h2()
    if h2 == "skip":
        pytest.skip("vizdoom or DOOM.WAD absent")
    d = h2["depth"]
    fine = d["fovea_fine_in_window"]
    coarse = d["fovea_coarse_in_window"]
    assert fine["n"] > 0 and coarse["n"] > 0, d
    assert fine["median"] is not None and coarse["median"] is not None, d
    assert fine["median"] > coarse["median"], d


def test_h2_imp_subpixel_at_coarse_superpixel_in_fine_window():
    """The imp is sub-pixel at coarse (0 monster tracks, the 156/157/158 wall) but
    a FINE window placed on the imp resolves super-pixel flow the coarse misses —
    proving foveation resolves the imp WHEN pointed there. Reads measured
    flow-cell counts."""
    h2 = _h2()
    if h2 == "skip":
        pytest.skip("vizdoom or DOOM.WAD absent")
    ir = h2["imp_recovery"]
    assert ir["n_imp_frames"] > 0, ir
    # foveation resolves more imp flow at fine than coarse (super-pixel recovery)
    assert ir["fine_imp_flow_cells_total"] > ir["coarse_imp_flow_cells_total"], ir


def test_h2_foveated_cheaper_than_full_res():
    """Foveated (coarse global flow + fine windows) is cheaper per frame than
    full-res-down=1-everywhere. Measured ms/frame; the real-time lever."""
    fr = _frames()
    if not fr:
        pytest.skip("vizdoom or DOOM.WAD absent")
    t = timing_arm(fr)
    assert t["foveated_ms_per_frame"] < t["full_res_ms_per_frame"], t
