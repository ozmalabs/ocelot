"""CEREBRAL ACHROMATOPSIA — colour-SIGN / chromatic-STRUCTURE dissociation: the
migrated gate (VISION_ACHROMATOPSIA_PREREG.md).

Deterministic. A LESION-VALIDATION gate for the design's luminance-structure /
colour-sign split (VISION_VENTRAL_GROUNDING.md failure-mode gate 5; Heywood & Cowey
1997). Ablating the colour-IDENTITY sign layer (achromatopsia=1 ⇒ ci_mint_category +
ci_assign suppressed, ci_opponent + the vision_colour salience seed untouched) via
ONE new flag on ColourIdentityParams (OFF by default = INTACT, §9) yields a CLEAN
dissociation:

  * DISSOCIATION — categorization is LOST (2 categories → 0, 36 signs → 0) while the
    chromatic-structure readouts (chromatic-border csal, shape-from-colour,
    colour-defined boundary + its +1-col displacement) are BYTE-FOR-BYTE PRESERVED,
    identical across arms.
  * CONTROL_VALIDITY (§1.1 — neither side dead) — the ablated arm's structure FIRES
    (csal>0, op_done=1 so the opponent signal is computed) and the intact arm
    categorizes correctly. The "0 categories" is a genuine suppression on live
    machinery, not a silent floor.
  * SPLIT_CLEAN — a luminance-defined edge yields lsal>0 IDENTICALLY in both arms
    (the colour lesion is chroma/identity-specific; luminance structure untouched).
  * FLOOR — an achromatic stimulus yields NO chromatic structure (csal=0) and NO
    colour sign (0 chromatic categories) in EITHER arm, while luminance is present
    (lsal>0): the achromatic condition kills colour regardless of the identity flag,
    so the dissociation is not a luminance artifact.
  * §9 — the seeds are inert with all flags OFF (default); the achromatopsia default
    (0) leaves the committed colour-identity gate byte-identical.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from scripts.achromatopsia_measure import (  # noqa: E402
    arm_dissociation, arm_split_clean, arm_floor, arm_offday)


def test_dissociation_categorization_lost_chromatic_structure_preserved():
    r = arm_dissociation()
    assert r["pass_dissociation"], r
    # categorization LOST under the lesion
    assert r["n_categories_intact"] == 2 and r["n_categories_ablated"] == 0
    assert r["n_signs_intact"] == 36 and r["n_signs_ablated"] == 0
    # chromatic STRUCTURE preserved, BYTE-identical across arms
    assert r["max_csal_ablated"] > 0.0
    assert r["csal_max_abs_diff_across_arms"] == 0.0
    assert r["n_csal_positive_intact"] == r["n_csal_positive_ablated"] > 0
    # equiluminant figure ⇒ shape-from-colour (lsal 0, boundary traced by chroma)
    assert r["max_lsal_intact"] == 0.0
    # colour-defined boundary DISPLACEMENT preserved (+1 col, identical across arms)
    assert r["boundary_shift_intact"] == 1.0 and r["boundary_shift_ablated"] == 1.0


def test_control_validity_neither_arm_trivially_null():
    r = arm_dissociation()
    assert r["pass_control_validity"], r
    # ablated structure ALIVE (not a dead instrument, §1.1): opponent signal computed
    assert r["op_done_min_ablated"] == 1.0
    assert r["ablated_structure_alive"]
    # intact identity ALIVE
    assert r["all_signs_correct_intact"] and r["n_categories_intact"] == 2


def test_split_clean_luminance_structure_intact_and_lesion_is_chroma_specific():
    r = arm_split_clean()
    assert r["pass"], r
    assert r["max_lsal_intact"] > 0.0
    assert r["lsal_max_abs_diff_across_arms"] == 0.0   # identical intact vs ablated
    assert r["max_csal"] == 0.0                        # no chroma in this stimulus


def test_floor_achromatic_yields_no_colour_in_either_arm_not_confounded():
    r = arm_floor()
    assert r["pass"], r
    assert r["max_csal_intact"] == 0.0 and r["max_csal_ablated"] == 0.0
    assert r["n_chromatic_categories_intact"] == 0
    assert r["n_chromatic_categories_ablated"] == 0
    assert r["max_lsal_intact"] > 0.0                  # luminance present (not blank)
    # the intact arm's only mint is a colourless grey origin category (honest report)
    assert r["achromatic_grey_categories_intact"] == 1


def test_offday_seeds_inert_by_default():
    r = arm_offday()
    assert r["pass"], r
    assert r["max_cc_done"] == 0.0 and r["n_categories"] == 0
    assert r["max_op_done"] == 0.0 and r["max_sign_rg"] == 0.0
