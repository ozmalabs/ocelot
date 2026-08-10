"""CATEGORY-LEVEL RECOGNITION (FRONTIER T2) — a category as an MDL-minted
AXIS-CODEBOOK region: the migrated gate (VISION_CATEGORY_PREREG.md).

Deterministic. Pins the claim that category-level recognition — generalization to a
KIND: a NEW instance never seen before recognized as a member of a known category —
composes from the colour-identity MDL mint generalized from a POINT to a REGION (a
MinOver/MaxOver box over object axes), via ONE seed (vision_category:
cat_mint / cat_recognize / cat_memorize) with NO new Rust:

  * GENERALIZATION (headline) — a HELD-OUT instance of each trained kind, its
    continuous coordinates PROVABLY absent from training and interior to the learned
    box, is recognized as that kind by projection-containment (3/3).
  * DISCRIMINATION exact-0 — no held-out instance is recognized as a different kind.
  * THE CRUX — on the SAME held-out instances, exact-match MEMORIZATION refuses all
    (0) while the region GENERALIZES all (K): (sum_mem, sum_cat) == (0, 3). This is
    the proof it generalizes rather than memorizes.
  * MDL — 3 categories from 12 training instances (k << N), the shared discrete
    signature compresses (24 -> 18); m_min = 3 falls out of d_disc = 2.
  * FLOORS — a NOVEL discrete signature is refused; an EXTRAPOLATION instance
    (matching signature, out-of-box proportions) is refused (the box is
    load-bearing); iid noise mints ZERO categories (a small sample here; the
    100-seed confirmatory floor, seeds 44000-44099, lives in the runner).
  * DOWNSTREAM — the flag is load-bearing (categories + recognitions ON, absent OFF).
  * §9 — the seed is inert with the flag OFF (default): byte-identity holds.

BOUNDED: the axes are GIVEN (not learned from pixels); the region is an axis-aligned
BOX; generalization is INTERPOLATION within the box (extrapolation refused). The full
learned axis-codebook at natural-image scale is the named frontier.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

from scripts.category_measure import (  # noqa: E402
    arm_generalization, arm_discrimination, arm_crux, arm_mdl,
    arm_floor_novel, arm_floor_extrapolation, arm_downstream, arm_offday,
    arm_floor_noise)


def test_generalization_held_out_unseen_instances_are_recognized():
    r = arm_generalization()
    assert r["pass"], r
    assert r["gen_correct"] == 3 and r["K"] == 3
    for name, h in r["held_out"].items():
        assert h["cat_recognized"] == 1          # recognized as the category
        assert h["coord_unseen"] is True          # coords never in training
        assert h["correct"] is True               # correct kind's signature


def test_discrimination_no_cross_kind_recognition():
    r = arm_discrimination()
    assert r["pass"], r
    assert r["cross_false"] == 0                   # exact-0


def test_crux_region_generalizes_where_memorization_refuses():
    r = arm_crux()
    assert r["pass"], r
    # exact-match memorization refuses all held-out; the region recognizes all
    assert r["sum_mem_recognized"] == 0
    assert r["sum_cat_recognized"] == 3


def test_mdl_categories_compress_and_m_min_falls_out():
    r = arm_mdl()
    assert r["pass"], r
    assert r["n_categories"] == 3 and r["n_train"] == 12
    assert r["mdl_categorized"] < r["mdl_raw"]
    assert r["mdl_categorized"] == 18 and r["mdl_raw"] == 24
    assert r["m_min"] == 3 and r["d_disc"] == 2   # m_min falls out of d_disc


def test_floor_novel_signature_is_refused():
    r = arm_floor_novel()
    assert r["pass"], r
    assert r["recognition"]["cat_recognized"] == 0


def test_floor_extrapolation_is_refused_box_is_load_bearing():
    r = arm_floor_extrapolation()
    assert r["pass"], r
    assert r["recognition"]["cat_recognized"] == 0


def test_noise_mints_no_category():
    # small sample here (10 seeds); the 100-seed confirmatory floor is in the runner.
    r = arm_floor_noise(n_seeds=10, base_seed=44000)
    assert r["pass"], r
    assert r["false_mint_fields"] == 0


def test_flag_is_load_bearing_downstream():
    r = arm_downstream()
    assert r["pass"], r
    assert r["on_categories"] == 3 and r["off_categories"] == 0
    assert r["d_categories"] > 0 and r["d_recognized_max"] > 0


def test_offday_seed_is_inert_by_default():
    r = arm_offday()
    assert r["pass"], r
    assert r["n_categories"] == 0
    assert r["max_cat_recognized"] == 0.0 and r["max_mem_recognized"] == 0.0
