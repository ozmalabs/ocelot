"""STYLE AS A DISCOVERED DIMENSION (FRONTIER T5) — a style as a per-SOURCE COHERENT
offset on a DISCOVERED continuous axis: the migrated gate (VISION_STYLE_PREREG.md).

Deterministic (the two sampled arms are seeded from the pre-registered block). Pins
the claim that STYLE — the coherent within-category variation shared across instances
from ONE source and DIFFERING across sources — composes from T2's continuous
proportion axes plus the Omniglot writer-dimension rung's per-source coherence mint,
via ONE seed (vision_style: sty_project / sty_mint_a0 / sty_mint_a1 /
sty_recognize_a0 / sty_recognize_a1 / sty_memorize) with NO new Rust:

  * STYLE DISCOVERED (headline) — each source mints EXACTLY ONE style, on the CORRECT
    axis, with NOTHING telling the mechanism which axis carries the style: there is
    one mint rule per axis and both run on every source. A source coherent on axis 0
    mints on axis 0 and NOT on its free axis.
  * GENERALIZATION — a NEW instance whose raw coordinate is provably absent from
    training is recognized as its source's style AND as the correct kind (3/3).
  * DISCRIMINATION — distinct sources mint DISTINCT styles and cross_false is exactly
    0, decided SOURCE-BLIND (no recognition rule reads the `produced` edge).
  * THE COHERENCE CRUX (§1.1, RISKED) — an INCOHERENT source, given the same instance
    count / kinds / spread in the SAME scene, mints at CHANCE level, not always: a
    mechanism that minted a style for any source would be a universal container.
    Paired positive controls: the styled sources still mint 3/3 and the incoherent
    source's items are ALIVE (a silent arm is a failed gate, never a good floor).
  * MEMORIZATION (ENTAILED) — exact-raw-coordinate matching refuses every held-out
    while the offset recognizes all: the offset generalizes what the coordinate
    memorizes.
  * MDL — m_min = 3 falls out of d_style = 2 (a style is an (axis, delta) PAIR;
    membership is FREE because the source is observed).
  * FLOOR — iid noise mints ZERO styles (and zero categories).
  * BOUND / anchor coverage — the pre-registered PREDICTED REFUSAL: cross-kind
    coherence is a property of the data, not of the rule. Pinned as a BOUND.
  * DOWNSTREAM / §9 — the flag is load-bearing; the seed is inert at its default,
    including on a scene where T2's categories are live.

BOUNDED: the axes are GIVEN (not learned from pixels); a style is a CONSTANT offset on
ONE axis; two sources sharing a delta ARE one style; the anchor is the category box
origin; chance-level false agreement exists over a finite value pool. The learned
axis-codebook at natural-image scale, and whatever the deformation rung leaves open,
remain the named frontiers.
"""
import json
import os

from domains.engine_provenance import engine_preamble
engine_preamble()

from scripts.style_measure import (  # noqa: E402
    arm_style_discovered, arm_generalization, arm_discrimination,
    arm_memorization, arm_mdl, arm_downstream, arm_offday,
    arm_bound_anchor_coverage, arm_coherence_crux, arm_floor_noise,
    _p_max_mult_ge3, _binom_crit, SOURCES)

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- THE HEADLINE: the axis is DISCOVERED ------------------------------------
def test_style_is_discovered_one_per_source_on_the_correct_axis():
    r = arm_style_discovered()
    assert r["pass"], r
    assert r["n_styles"] == 3
    assert r["observed"] == r["expected"]
    for sid, v in r["per_source"].items():
        # exactly ONE style per source ...
        assert v["n_styles"] == 1, (sid, v)
        # ... on the axis the source is actually coherent on ...
        assert v["axis_correct"] is True, (sid, v)
        # ... and NONE on its free axis. Nothing told the mechanism which is which:
        # both mint rules run on every source.
        assert v["n_on_free_axis"] == 0, (sid, v)


def test_both_axes_are_represented_across_sources():
    """The discovery is not a constant: S1/S2 cohere on axis 0, S3 on axis 1, and
    the mechanism finds each on its own axis."""
    r = arm_style_discovered()
    axes = {v["discovered"][0]["axis"] for v in r["per_source"].values()}
    assert axes == {0, 1}, r["per_source"]


# --- GENERALIZATION -----------------------------------------------------------
def test_new_instance_in_a_known_style_is_recognized_as_that_style_and_kind():
    r = arm_generalization()
    assert r["pass"], r
    assert r["gen_correct"] == 3 and r["K"] == 3
    for sid, h in r["held_out"].items():
        assert h["coord_unseen"] is True          # raw coordinate never trained
        assert h["sty_recognized"] == 1           # recognized as a style ...
        assert h["sty_src"] == int(sid)           # ... its OWN source's ...
        assert h["sty_axis"] == SOURCES[int(sid)]["axis"]   # ... on the right axis
        assert h["cat_recognized"] == 1           # and still recognized as its KIND


# --- DISCRIMINATION -----------------------------------------------------------
def test_distinct_sources_mint_distinct_styles_no_cross_source_pollution():
    r = arm_discrimination()
    assert r["pass"], r
    assert r["cross_false"] == 0                   # exact-0
    assert r["styles_distinct"] is True
    assert r["n_recognized_items"] > 0             # the arm is ALIVE (§1.1)


# --- THE COHERENCE CRUX (RISKED) ---------------------------------------------
def test_incoherent_source_mints_no_style_beyond_chance():
    """A source with RANDOM offsets must NOT mint a style. Small sample here
    (20 seeds from the pre-registered block); the 100-seed confirmatory arm is in
    the runner and pinned below."""
    r = arm_coherence_crux(n_seeds=20, base_seed=47100)
    assert r["pass"], r
    # NOT a universal container — the disqualifying outcome
    assert r["universal_container"] is False
    assert r["false_mint_scenes"] < r["binom_crit_95"], r
    # PAIRED POSITIVE CONTROLS in the same scenes (§1.1):
    assert r["styled_mint_ok"] == 20, r            # coherent sources still mint 3/3
    assert r["incoherent_items_alive_scenes"] == 20, r   # and its items are ALIVE
    assert r["incoherent_items_alive_total"] == r["incoherent_items_expected"]


def test_chance_rate_is_computed_exactly_not_assumed():
    """The crux's decision rule is pinned to an EXACT analytic chance rate, not a
    tuned tolerance (§5/§13)."""
    p = _p_max_mult_ge3(6, 40)
    assert 0.011 < p < 0.013, p                    # ~1.2% per axis
    p_chance = 1.0 - (1.0 - p) ** 2
    assert 0.023 < p_chance < 0.024, p_chance      # ~2.35% over two axes
    # a degenerate pool must make agreement CERTAIN — the formula is not vacuous
    assert _p_max_mult_ge3(6, 1) == 1.0
    assert _binom_crit(100, p_chance) > 0


# --- MEMORIZATION (ENTAILED) --------------------------------------------------
def test_offset_generalizes_what_the_raw_coordinate_memorizes():
    r = arm_memorization()
    assert r["pass"], r
    assert r["sum_mem_recognized"] == 0            # exact-coordinate control refuses
    assert r["sum_sty_recognized"] == 3            # the offset recognizes all
    assert r["entailed"] is True                   # declared in advance (§13.1)


# --- MDL ----------------------------------------------------------------------
def test_mdl_styles_compress_and_m_min_falls_out_of_d_style():
    r = arm_mdl()
    assert r["pass"], r
    assert r["n_styles"] == 3
    assert r["mdl_styled"] < r["mdl_raw"]
    assert r["mdl_raw"] == 18 and r["mdl_styled"] == 6      # ratio 3.0
    assert r["m_min"] == 3 and r["d_style"] == 2
    assert r["m_min"] == r["d_style"] + 1          # m > d_style ⟺ m >= 3


# --- FLOOR --------------------------------------------------------------------
def test_noise_mints_no_style():
    # small sample here (10 seeds); the 100-seed confirmatory floor is in the runner.
    r = arm_floor_noise(n_seeds=10, base_seed=47000)
    assert r["pass"], r
    assert r["false_style_fields"] == 0
    assert r["false_category_fields"] == 0


# --- BOUND (predicted refusal) ------------------------------------------------
def test_bound_anchor_coverage_refuses_as_predicted():
    """PINNED AS A BOUND, not as a success: cross-kind coherence needs every kind's
    anchor to be set consistently. Removing S1 from kind C's training shifts that
    kind's origin, and S1's held-out there is correctly REFUSED rather than
    force-assigned."""
    r = arm_bound_anchor_coverage()
    assert r["pass"], r
    assert r["refused"] is True
    # the out-of-box case is refused at T2's containment floor ...
    assert r["held_out_a_outside_box"]["cat_recognized"] == 0
    assert r["held_out_a_outside_box"]["dv_set"] == 0
    # ... and the IN-box case is projected but its offset has shifted, so it is not
    # S1's style — the refusal is about the OFFSET, not merely about containment.
    assert r["held_out_b_inside_box"]["cat_recognized"] == 1
    assert r["held_out_b_inside_box"]["dv_set"] == 1
    assert r["held_out_b_inside_box"]["dv0"] != 0
    assert r["held_out_b_inside_box"]["sty_recognized"] == 0


# --- §1 clause 5 / §9 ---------------------------------------------------------
def test_flag_is_load_bearing_downstream():
    r = arm_downstream()
    assert r["pass"], r
    assert r["on_styles"] == 3 and r["off_styles"] == 0
    assert r["d_styles"] > 0
    assert r["d_recognized_max"] > 0 and r["d_projected_max"] > 0


def test_offday_seed_is_inert_by_default():
    r = arm_offday()
    assert r["pass"], r
    assert r["n_styles"] == 0
    assert r["max_sty_recognized"] == 0.0 and r["max_dv_set"] == 0.0
    assert r["max_mem_recognized"] == 0.0
    # and inert even where T2's categories are LIVE — the style seed does not ride
    # on the category flag.
    assert r["categories_live_styles_off"] == 3
    assert r["n_styles_with_categories_on"] == 0
    assert r["max_dv_set_with_categories_on"] == 0.0


# --- provenance / no-new-Rust / pinned results --------------------------------
def test_seed_uses_no_times_term():
    """T3's caught defect: `Times` takes an `items` LIST, so an a/b form parses to an
    EMPTY PRODUCT (= 1) and can silently make an invariant Eq(1,1) — true for
    everything. This seed avoids the list-form Term family outright."""
    with open(os.path.join(_HERE, "seeds", "vision_style.json")) as f:
        raw = f.read()
    assert '"Times"' not in raw
    assert '"Div"' not in raw


def test_seed_flag_guard_is_absence_tolerant_not_pickunique():
    """A PickUnique guard returns None on an absent params node and silently changes
    behaviour elsewhere (the agnosia rung's lesson)."""
    with open(os.path.join(_HERE, "seeds", "vision_style.json")) as f:
        seed = json.load(f)
    raw = json.dumps(seed)
    assert '"PickUnique"' not in raw
    assert '"StyleParams"' in raw
    # every rule is flag-gated
    assert len(seed["rules"]) == 6
    for rule in seed["rules"]:
        assert "StyleParams" in json.dumps(rule["where"]), rule["name"]
    # OFF by default (§9)
    assert seed["nodes"][0]["type"] == "StyleParams"
    assert seed["nodes"][0]["attrs"]["style"] == 0.0


def test_recognition_rules_are_source_blind():
    """What makes DISCRIMINATION a RISKED test: no recognition rule may read the
    `produced` edge or a source attribute."""
    with open(os.path.join(_HERE, "seeds", "vision_style.json")) as f:
        seed = json.load(f)
    for rule in seed["rules"]:
        if not rule["name"].startswith("sty_recognize"):
            continue
        body = json.dumps({"match": rule["match"], "where": rule["where"],
                           "effects": rule["effects"]})
        assert "produced" not in body, rule["name"]
        assert '"sid"' not in body, rule["name"]
        assert rule["match"] == [["scene", "has_obj", "R"]], rule["name"]


def test_pinned_results_reproduce():
    """The committed confirmatory numbers (§10 — a number without an engine is not a
    result)."""
    with open(os.path.join(_HERE, "results", "style_measure.json")) as f:
        d = json.load(f)
    assert d["ALL_PASS"] is True
    assert d["seed_block"] == [47000, 47999]
    assert "engine" in d["provenance"]
    assert d["H_style_discovered"]["n_styles"] == 3
    assert d["G_generalization"]["gen_correct"] == 3
    assert d["B_discrimination"]["cross_false"] == 0
    assert d["X1_coherence_crux"]["n_seeds"] == 100
    assert d["X1_coherence_crux"]["universal_container"] is False
    assert d["X1_coherence_crux"]["styled_mint_ok"] == 100
    assert d["E_floor_noise_entailed"]["false_style_fields"] == 0
