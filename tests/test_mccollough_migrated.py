"""McCOLLOUGH CONTINGENT AFTEREFFECT — the migrated gate (VISION_MCCOLLOUGH_PREREG.md).

THE decisive predictive-coding gate (VISION_VENTRAL_GROUNDING.md §FAILURE-MODE
GATES, "highest discriminative value"). Deterministic. Pins the headline claim that
the substrate's render-from-prior + opponent-residual reproduces the
orientation-CONTINGENT colour aftereffect a FEEDFORWARD classifier CANNOT fake, via
three seed rules (mcc_learn / mcc_percept_pred / mcc_percept_ff) composing
vision_colour's opponent coordinates with vision_lateral's predict-then-residual
shape — with NO new Rust:

  * CONTINGENCY — after red-vertical / green-horizontal adaptation, an achromatic
    vertical test is GREEN-biased (percept_rg<0) and a horizontal one PINK-biased
    (percept_rg>0); the aftereffect lives in the colour⊗orientation JOINT (swap the
    orientation label on the SAME patch → the aftereffect colour FLIPS).
  * THE CRUX (§1.1) — a FEEDFORWARD control (direct colour read, no
    render-from-prior) produces NO aftereffect (achromatic in → achromatic out),
    while remaining ALIVE (a coloured test reports the real colour). The predictive
    and feedforward arms differ ONLY in whether the render-from-prior is subtracted.
  * PERSISTENCE / error-driven — the prior is STORED (bit-identical across an
    intervening no-adaptation tick block; not fatigue) and error-driven (n grows
    with exposure).
  * FLOORS — no adaptation → no aftereffect; colour alone (no orientation pairing)
    → an aftereffect that is NOT orientation-contingent (C=0).
  * NOISE FLOOR — 0/100 iid colour-noise adaptations invent a coherent contingency.
  * §9 — the seed is inert with the flag OFF (default).
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from scripts.mccollough_measure import (  # noqa: E402
    arm_contingency, arm_swap_flip, arm_crux, arm_persist,
    arm_floor_no_adapt, arm_floor_colour_alone, arm_offday, arm_noise)


def test_contingency_achromatic_test_is_green_for_vertical_pink_for_horizontal():
    r = arm_contingency()
    assert r["pass"], r
    assert r["percept_rg_vert"] == -10.0      # adapted red-vertical → GREEN aftereffect
    assert r["percept_rg_horiz"] == 10.0      # adapted green-horizontal → PINK aftereffect
    assert r["contingency"] == -20.0          # orientation-contingent
    # the manipulation is a pure rg-axis contingency (equiluminant on by).
    assert r["percept_by_vert"] == 0.0 and r["percept_by_horiz"] == 0.0


def test_aftereffect_lives_in_the_joint_swap_orientation_flips_the_colour():
    r = arm_swap_flip()
    assert r["pass"], r
    # SAME achromatic patch, ONLY theta differs → opposite-sign percept.
    assert r["vert_label"] == -10.0 and r["horiz_label"] == 10.0
    assert r["flipped"]


def test_THE_CRUX_feedforward_control_produces_no_contingent_aftereffect():
    """A feedforward classifier CANNOT fake McCollough — the decisive test (§1.1)."""
    r = arm_crux()
    assert r["pass"], r
    # predictive arm PRODUCES the aftereffect...
    assert r["pred_vert"] == -10.0 and r["pred_horiz"] == 10.0
    # ...the feedforward control does NOT (achromatic in → achromatic out).
    assert r["ff_vert"] == 0.0 and r["ff_horiz"] == 0.0
    assert r["ff_null"]
    assert r["D_crux"] > 0.0                   # the arms genuinely differ
    # ...and the FF arm is ALIVE (a coloured test reports the real colour) — its
    # achromatic null is a real null, NOT a dead arm scoring a perfect floor (§1.1).
    assert r["ff_arm_alive"] and r["ff_alive_coloured"] == 10.0


def test_persistence_prior_is_stored_and_error_driven_not_fatigue():
    r = arm_persist()
    assert r["pass"], r
    assert r["stored_bit_identical"]           # survives intervening ticks (not fatigue)
    assert r["percept_after"] == -10.0
    assert r["n_after_1_frame"] == 1.0 and r["n_after_FRAMES"] == 8.0   # error-driven


def test_floor_no_adaptation_means_no_aftereffect():
    r = arm_floor_no_adapt()
    assert r["pass"], r
    assert r["percept_rg"] == 0.0
    assert r["prior"]["n"] == 0.0


def test_floor_colour_alone_gives_no_orientation_contingency():
    r = arm_floor_colour_alone()
    assert r["pass"], r
    # red adapted on BOTH orientations → aftereffect present but NOT contingent.
    assert r["percept_rg_vert"] == r["percept_rg_horiz"] == -10.0
    assert r["contingency"] == 0.0


def test_offday_flag_off_is_inert():
    r = arm_offday()
    assert r["pass"], r
    assert r["percept_rg"] == 0.0
    assert r["prior"]["n"] == 0.0


def test_noise_adaptation_invents_no_coherent_contingency():
    # smaller n in-gate (the full 100-seed confirmatory floor is in the runner).
    r = arm_noise(n=20, seed0=41000)
    assert r["pass"], r
    assert r["hits_ge_structured"] == 0
