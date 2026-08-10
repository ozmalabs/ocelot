#!/usr/bin/env python3
"""GATE for the realism-degradation ladder (block 150000-150999).

Asserts the per-axis BREAK-POINT STRUCTURE on the IDEAL SUB-CELL ORACLE, which
is CROSS-PROCESS DETERMINISTIC by construction: it uses GIVEN integer anchors
(round of the true sub-cell top) — NO carve — a fixed texture seed, and fixed
degradation seeds, so no cross-process HashMap (carve-id) artifact enters. The
real-clip numbers in the results doc use the carve and are therefore reported as
INFORMATIONAL, never gated here.

Every verdict is read from the GRAPH-MINTED order-N coefficient (via
`physics_test` -> `accel_coeff` -> the seed rule's `latent:time` mint); NO test
asserts exact second-difference constancy (148000's flaky-gate lesson).

ABLE TO FAIL, both directions:
  * POSITIVE control — the clean oracle MUST pass the single-sign replication
    test; a dead instrument (always None / always-fail) reddens this.
  * NEGATIVE control — past each measured break point the method MUST fail; a
    method that magically became robust (or a test that always "passes") reddens
    these. Occlusion and noise fail by breaking the two-window SIGN replication
    (the exact 149000 failure); a short trajectory fails by not minting order-2.

Cross-process stability: run this file in several fresh `python3 -m pytest`
processes and confirm the same pass count (the ladder headline is anchor-given,
so it is invariant).
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.realism_ladder_measure import (   # noqa: E402
    physics_test, given_anchors, clean_frames, blur_vertical, occlude_bar,
    add_noise, jitter_anchors, BASE_N, SEED_NOISE, TARGET_FINE,
)


def _clean_run(n):
    fr, top = clean_frames(n)
    return fr, given_anchors(top, n)


def test_clean_oracle_passes_single_sign():
    """POSITIVE control: the undegraded sub-cell oracle recovers ONE constant
    acceleration of the CORRECT sign, and TWO overlapping windows agree in sign
    (the 149000 replication test). Reads the graph-minted coeff, not d2."""
    fr, run = _clean_run(BASE_N)
    pt = physics_test(fr, run)
    assert pt["coeff_full"] is not None            # order-2 minted by the seed rule
    assert pt["coeff_full"] > 0                     # correct (downward) sign; not exact-valued
    assert (TARGET_FINE > 0)
    assert pt["P1_order_sign"] is True
    assert pt["P2_replication_sign"] is True
    assert pt["PASS"] is True


def test_occlusion_breaks_replication():
    """NEGATIVE control: a static bright occluder (the 'ruler') the ball passes
    behind breaks the two-window sign replication -> PASS is False. Occlusion is
    the ladder's most sensitive axis (break at the smallest nonzero level)."""
    fr0, top0 = clean_frames(BASE_N)
    run0 = given_anchors(top0, BASE_N)
    fr = occlude_bar(fr0, top0, 12)
    pt = physics_test(fr, run0)
    assert pt["PASS"] is False
    assert pt["P2_replication_sign"] is False      # the windows no longer agree


def test_heavy_noise_breaks_replication():
    """NEGATIVE control: heavy sensor noise flips a window's recovered sign
    (149000's exact +/- disagreement) -> PASS is False."""
    fr0, top0 = clean_frames(BASE_N)
    run0 = given_anchors(top0, BASE_N)
    fr = add_noise(fr0, 120, SEED_NOISE)
    pt = physics_test(fr, run0)
    assert pt["PASS"] is False


def test_short_trajectory_breaks():
    """NEGATIVE control: a 5-frame trajectory is too short for the two-window
    replication to mint order-2 in both windows -> PASS is False (break at N=5;
    N>=6 passes)."""
    fr, run = _clean_run(5)
    pt = physics_test(fr, run)
    assert pt["PASS"] is False


def test_trajectory_six_still_passes():
    """The break is AT 5, not above it: a 6-frame trajectory still recovers a
    single-sign acceleration. Pins the break location (able to fail if the break
    moved to 6)."""
    fr, run = _clean_run(6)
    pt = physics_test(fr, run)
    assert pt["PASS"] is True
    assert pt["coeff_full"] is not None and pt["coeff_full"] > 0


def test_robust_axes_do_not_break_in_range():
    """Motion blur (6 rows) and carve-anchor jitter (+/-3 cells, inside the
    residual search window) do NOT break the method -> both still PASS. This is
    the ladder's discrimination: only occlusion / heavy-noise / short-trajectory
    break; blur and small anchor jitter are absorbed."""
    fr0, top0 = clean_frames(BASE_N)
    run0 = given_anchors(top0, BASE_N)
    pt_blur = physics_test(blur_vertical(fr0, 6), run0)
    assert pt_blur["PASS"] is True
    pt_jit = physics_test(fr0, jitter_anchors(run0, 3, 150200))
    assert pt_jit["PASS"] is True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
