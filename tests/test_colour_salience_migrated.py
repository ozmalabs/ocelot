"""COLOUR SALIENCE — pop-out for the EQUILUMINANT target: the migrated gate
(VISION_COLOUR_PREREG.md).

Deterministic. Pins the headline claim that colour is the pop-out channel where
luminance salience is ZERO, via TWO seed rules (cc_contrast / cc_salience) that
generalise the eye's surround-relative difference (vision_lateral's centre-surround)
to the cone-opponent axes and feed the UNCHANGED vision_stream budget — with NO new
Rust:

  * EQUILUMINANT POP-OUT — a target with zero luminance contrast but high
    cone-opponent contrast is streamed in under COLOUR and MISSED under
    luminance-only ("ripe fruit against foliage").
  * INTERACTIVE COMBINATION — a both-channel target is found, but the combine is
    lsal + csal + lsal*csal, NOT a trivial sum.
  * LUMINANCE-ONLY STILL WORKS — a purely luminance-salient target is found without
    any colour signal (colour is additive capability; the corrected chroma-neutral
    stimulus co-varies S with L+M, since S-(L+M) is not luminance-invariant).
  * UNIFORM-COLOUR FLOOR — a uniform field mints ZERO colour salience.
  * NOISE FLOOR — iid colour noise invents no coherent pop.
  * §9 — the seed is inert with both flags OFF (default).

The 100-seed confirmatory noise floor lives in scripts/colour_measure.py (slow); a
small floor is exercised here.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

import random  # noqa: E402

from scripts.colour_measure import (  # noqa: E402
    arm_equiluminant, arm_interactive, arm_luminance_only_works,
    arm_uniform_floor, arm_offday, _boot, _run)
from domains import colour_world as cw  # noqa: E402
from scripts.stream_measure import tunnel  # noqa: E402


def test_equiluminant_target_pops_under_colour_and_is_missed_under_luminance():
    r = arm_equiluminant()
    assert r["pass"], r
    assert r["target_lsal"] == 0.0            # zero luminance contrast (equiluminant)
    assert r["target_csal"] > 0.0             # high cone-opponent contrast
    assert r["colour_target_order"] == 0      # streamed in under COLOUR
    assert r["lum_only_target_order"] == -1   # MISSED under luminance-only
    assert r["lum_only_spent"] == 0


def test_colour_and_luminance_combine_interactively_not_as_a_sum():
    r = arm_interactive()
    assert r["pass"], r
    assert r["target_order"] == 0
    assert r["residual"] > r["trivial_sum"]   # strictly non-additive
    # the interaction term is exactly lsal*csal (the (1+lsal)(1+csal)-1 combine).
    assert abs(r["interaction_term"] - r["lsal"] * r["csal"]) < 1e-9


def test_luminance_only_target_still_found_without_colour_signal():
    r = arm_luminance_only_works()
    assert r["pass"], r
    assert r["target_csal"] == 0.0            # genuinely chroma-neutral
    assert r["with_colour_target_order"] == 0
    assert r["lum_only_target_order"] == 0    # colour does not break the lum path


def test_uniform_colour_field_mints_zero_colour_salience():
    r = arm_uniform_floor()
    assert r["pass"], r
    assert r["max_csal"] == 0.0
    assert r["n_positive_csal"] == 0
    assert r["spent"] == 0


def test_flags_off_is_inert():
    r = arm_offday()
    assert r["pass"], r
    assert r["spent"] == 0
    assert r["max_residual"] == 0.0
    assert r["max_cc_done"] == 0.0            # cc_contrast never fired
    assert r["all_unresolved"]


def test_noise_floor_invents_no_pop():
    # A small colour-noise floor (the full n=100 is in scripts/colour_measure.py).
    B = 4
    for k in range(8):
        rng = random.Random(34000 + k)
        cells = [dict(rrow=r, rcol=c,
                      cL=rng.randint(0, 20), cM=rng.randint(0, 20),
                      cS=rng.randint(0, 20))
                 for r in range(10) for c in range(10)]
        s, _ = _boot()
        h = cw.add_field(s, budget=B, cells=cells, nrows=10, ncols=10)
        _run(s, h, salience=1.0, colour=1.0)
        order = cw.read_order(s, h)
        spent = cw.read_spent(s, h)
        regions = [{"residual": v} for v in cw.read_attr(s, h, "residual")]
        assert not tunnel(regions, order, spent, B)
