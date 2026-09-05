"""BLOCK 294000 -- BOUBA/KIKI CROSSMODAL SOUND-SYMBOLISM gate. The crossmodal
MATCH is the graph's own qualia-space geometry: a phonetic FORM and a visual
SHAPE that sound-symbolically match SHARE the `(phenomenal:sharpness, "field", k)`
coordinate in their `concept_signature` (the frozenset INTERSECTION) and rank
nearer in `find_analogies` (aligned ON phenomenal:sharpness) -- NOT a Python scalar
compare. The coordinate is DERIVED INDEPENDENTLY on each side by two pre-existing,
independently-motivated extractors (articulatory phonetics; curvature-concentration
geometry via ink_dynamics._turning_angles) and quantised through the SAME lattice.

This file gates the Koehler (1929) / Ramachandran & Hubbard (2001) crossmodal
correspondence: (a) the produced shared-coordinate grid EQUALS the pre-reg oracle
EXACTLY; (b) the form x shape INTERACTION -- matched-pole pairs SHARE / rank nearer,
CI-separated ABOVE the crossings which do NOT (an interaction, not a main effect);
(c) DERIVATION-NOT-HAND-SET (the emergence proof) -- perturb an input, the
coordinate FLIPS and the match inverts; (d) the reverse-battery falsifier
collapses/inverts the match; (e) native-only / integer discipline (canonical .so
md5, schema valid, no new auto-loaded seed, source audit); (f) default==today (a
concept without the derived sharpness attr has an unchanged signature)."""
import hashlib
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate_rs import _native                                # noqa: E402
import domains.qualia_schema as qs                              # noqa: E402
from domains.analogy_search import concept_signature            # noqa: E402
from domains.bouba_kiki_world import (                          # noqa: E402
    BoubaKikiWorld, FORM_BATTERY, shape_battery,
    phonetic_sharpness, geometric_sharpness,
    oracle_match, POLE_THRESHOLD, QUANTUM, HALF_WIDTH,
    _star, _regular_polygon, _ellipse)

CANON_MD5 = "a32ed336662eaa9eb6df27b7112541ac"   # canonical .so after native-only CAN cutover
BLOCK = 294000
N = 60
_AXIS = "phenomenal:sharpness"

ROUND_FORMS = ("bouba", "maluma", "baloo")
SHARP_FORMS = ("kiki", "ziki")
ROUND_SHAPES = ("circle", "polygon", "dodecagon")
SHARP_SHAPES = ("star", "spikestar")


def _boot_ci(xs, reps=2000, seed=BLOCK):
    xs = np.asarray(xs, float)
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def _cohort_shapes(rng):
    """Class-preserving STRUCTURAL variants (mirrors the measure): a star with a
    random point-count/inner-radius (sharp), a regular polygon with a random
    high vertex-count (round), a random-eccentricity ellipse (mild). NOT
    coordinate jitter -- the max/mean ratio is pathologically sensitive to point
    noise on a near-uniform shape."""
    return {
        "star":      _star(int(rng.integers(5, 8)), inner=float(rng.uniform(0.25, 0.45))),
        "spikestar": _star(int(rng.integers(5, 7)), inner=float(rng.uniform(0.2, 0.4))),
        "star7":     _star(7, inner=0.5),
        "circle":    _regular_polygon(int(rng.integers(36, 60))),
        "polygon":   _regular_polygon(int(rng.integers(18, 30))),
        "dodecagon": _regular_polygon(int(rng.integers(10, 16))),
        "ellipse":   _ellipse(b=float(rng.uniform(0.7, 0.85))),
    }


# ------------------------------------------------------------------- (a) grid==oracle
def test_produced_shared_coordinate_grid_equals_oracle_exactly():
    """PRODUCED-not-hand-set: the graph's produced phenomenal:sharpness
    shared-coordinate (READ from the concept_signature INTERSECTION) equals the
    analytic oracle (pure arithmetic over the extractor outputs + the SAME
    quantiser) at EVERY form x shape cell -- the geometry PRODUCES the grid, it is
    not written by the test."""
    w = BoubaKikiWorld()
    for f in w.form_node:
        for s in w.shape_node:
            produced = bool(w.shares_coordinate(f, s))
            oracle = bool(oracle_match(w.form_raw[f], w.form_raw.values(),
                                       w.shape_raw[s], w.shape_raw.values()))
            assert produced == oracle, (f, s, produced, oracle)


def test_headline_grid_matches_pre_reg():
    """The pre-registered headline (prereg Sec5): round forms match round shapes,
    sharp forms match sharp shapes, NO crossings, takete (mid) matches neither."""
    w = BoubaKikiWorld()
    # round forms x round shapes: SHARE
    for f in ROUND_FORMS:
        for s in ROUND_SHAPES:
            assert w.shares_coordinate(f, s), (f, s)
        for s in SHARP_SHAPES:
            assert not w.shares_coordinate(f, s), (f, s)
    # sharp forms x sharp shapes: SHARE
    for f in SHARP_FORMS:
        for s in SHARP_SHAPES:
            assert w.shares_coordinate(f, s), (f, s)
        for s in ROUND_SHAPES:
            assert not w.shares_coordinate(f, s), (f, s)
    # takete is honestly MID: matches NEITHER pole
    assert w.form_coordinate("takete") is None
    for s in ROUND_SHAPES + SHARP_SHAPES:
        assert not w.shares_coordinate("takete", s), s


# ------------------------------------------------------------ (b) interaction shape
def test_interaction_matched_pole_shares_ci_separated_above_crossings():
    """The form x shape INTERACTION: matched-pole (round-form,round-shape) &
    (sharp-form,sharp-shape) pairs SHARE the phenomenal:sharpness coordinate /
    rank nearer in find_analogies, CI-separated ABOVE the crossings
    (round-form,sharp-shape) & (sharp-form,round-shape) which do NOT. This is an
    INTERACTION (a form matches a shape iff their poles coincide), not a main
    effect -- neither modality matches everything at its pole across the board."""
    rng = np.random.default_rng(BLOCK)
    matched_pairs = ([(f, s) for f in ROUND_FORMS for s in ROUND_SHAPES]
                     + [(f, s) for f in SHARP_FORMS for s in SHARP_SHAPES])
    mismatched_pairs = ([(f, s) for f in ROUND_FORMS for s in SHARP_SHAPES]
                        + [(f, s) for f in SHARP_FORMS for s in ROUND_SHAPES])

    matched_rates, mismatched_rates = [], []
    for _ in range(N):
        w = BoubaKikiWorld(shapes=_cohort_shapes(rng))
        matched_rates.append(float(np.mean(
            [1.0 if w.shares_coordinate(f, s) else 0.0 for f, s in matched_pairs])))
        mismatched_rates.append(float(np.mean(
            [1.0 if w.shares_coordinate(f, s) else 0.0 for f, s in mismatched_pairs])))
    ci_m, ci_mm = _boot_ci(matched_rates), _boot_ci(mismatched_rates)
    assert ci_m[0] > ci_mm[1], (ci_m, ci_mm)          # matched separated ABOVE
    assert np.mean(matched_rates) > np.mean(mismatched_rates)

    # find_analogies nearness: the matching-pole shape is present-and-aligned on
    # phenomenal:sharpness while the opposite-pole shape is absent (or ranks lower).
    w0 = BoubaKikiWorld()
    for f in SHARP_FORMS:
        v = w0.analogy_ranks_matching_above_opposite(f, "star", "circle")
        assert v["matching_ranks_above_opposite"], (f, v)
    for f in ROUND_FORMS:
        v = w0.analogy_ranks_matching_above_opposite(f, "circle", "star")
        assert v["matching_ranks_above_opposite"], (f, v)


def test_match_aligned_dimension_is_phenomenal_sharpness():
    """The ONLY discriminative shared coordinate driving a crossmodal match is
    phenomenal:sharpness -- a phonetic_form and a visual_shape share no edge, no
    role, no category, so a match is IMPOSSIBLE except through the shared felt
    axis. The emitted analogy's aligned_dimensions contains phenomenal:sharpness."""
    w = BoubaKikiWorld()
    near = w.analogy_nearness("kiki")
    assert "star" in near, near
    assert _AXIS in near["star"]["aligned_dimensions"], near["star"]


# --------------------------------------------------------- (c) emergence proof
def test_derivation_not_hand_set_phoneme_flip_inverts_match():
    """DERIVATION-NOT-HAND-SET: flip a ROUND form's phonemes to voiceless-plosive
    and its phenomenal:sharpness coordinate FLIPS (-1 -> +1) and its match INVERTS
    (it now matches the STAR, not the circle) -- the answer was NOT put in, it is
    derived from the features."""
    base = BoubaKikiWorld()
    assert base.form_coordinate("bouba") == -1
    assert base.shares_coordinate("bouba", "circle")
    assert not base.shares_coordinate("bouba", "star")

    forms = dict(FORM_BATTERY)
    forms["bouba"] = ["k", "i", "t", "e"]     # SAME slot, sharp phonemes
    flipped = BoubaKikiWorld(forms=forms)
    assert flipped.form_coordinate("bouba") == +1              # coordinate FLIPPED
    assert flipped.shares_coordinate("bouba", "star")          # match INVERTED
    assert not flipped.shares_coordinate("bouba", "circle")


def test_derivation_not_hand_set_point_swap_follows_points():
    """The geometric coordinate follows the POINTS, not the name: swap the star's
    and circle's point sets and the poles swap with them (the 'circle' slot holding
    star points reads +1; the 'star' slot holding circle points reads -1), so kiki
    now matches the star-points-in-circle-slot."""
    shapes = shape_battery()
    swapped = dict(shapes)
    swapped["circle"], swapped["star"] = shapes["star"], shapes["circle"]
    w = BoubaKikiWorld(shapes=swapped)
    assert w.shape_coordinate("circle") == +1     # holds star points
    assert w.shape_coordinate("star") == -1       # holds circle points
    assert w.shares_coordinate("kiki", "circle")
    assert not w.shares_coordinate("kiki", "star")


# --------------------------------------------------------- (d) reverse-battery
def test_reverse_battery_falsifier_inverts_every_match():
    """The reverse-battery FALSIFIER: reverse each form's phonemes ONE AT A TIME
    against the otherwise-intact battery (round -> voiceless-plosive; sharp ->
    voiced-rounded) and the pole flips and the crossmodal match inverts. If a
    coordinate did NOT flip when its input is reversed, the axis would not be
    derived from the features."""
    reversals = {
        "bouba":  (["k", "i", "t", "e"], "star", "circle"),   # round -> sharp
        "maluma": (["t", "i", "k", "i"], "star", "circle"),
        "baloo":  (["z", "i", "k", "i"], "star", "circle"),
        "kiki":   (["m", "u", "m", "u"], "circle", "star"),   # sharp -> round
        "ziki":   (["m", "a", "l", "u"], "circle", "star"),
    }
    base = BoubaKikiWorld()
    for name, (segs, new_match, new_opposite) in reversals.items():
        forms = dict(FORM_BATTERY)
        forms[name] = segs
        rev = BoubaKikiWorld(forms=forms)
        before, after = base.form_coordinate(name), rev.form_coordinate(name)
        assert before is not None and after is not None and before != after, \
            (name, before, after)                              # pole FLIPPED
        assert rev.shares_coordinate(name, new_match), (name, new_match)
        assert not rev.shares_coordinate(name, new_opposite), (name, new_opposite)


# --------------------------------------------- (e) native-only / integer discipline
def test_canonical_so_untouched():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    if os.path.exists(so):
        md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
        assert md5 == CANON_MD5


def test_qualia_schema_valid_with_the_new_axis():
    """The phenomenal:sharpness axis + the minted form/shape concepts conform to
    the qualia schema (validate_qualia_space passes)."""
    w = BoubaKikiWorld()
    concepts = list(w.form_node.values()) + list(w.shape_node.values())
    rep = qs.validate_qualia_space(w.s, concepts)
    assert bool(rep), getattr(rep, "errors", rep)


def test_no_new_seed_authored_and_absent_from_load_all():
    """The adapter authors NO new seed (prereg Sec8/Sec9): there is no
    bouba_kiki_sound_symbolism.json, and nothing named bouba_kiki is in
    load_all_seeds -- the base tree is byte-identical when the adapter is absent
    (the ONLY seed change is the additive phenomenal:sharpness axis, already
    landed by the prior stage)."""
    assert not os.path.exists(
        os.path.join(ROOT, "seeds", "bouba_kiki_sound_symbolism.json"))
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert not any("bouba_kiki" in s for s in seeds), \
        [s for s in seeds if "bouba_kiki" in s]


def test_produced_coordinate_is_integer_native():
    """Integer discipline: every PRODUCED phenomenal:sharpness coordinate is an
    integer step in {-1, +1} (or absent at mid) -- the mapping introduces no
    non-integer coordinate."""
    w = BoubaKikiWorld()
    for f in w.form_node:
        c = w.form_coordinate(f)
        assert c is None or (float(c).is_integer() and c in (-1, 1)), (f, c)
    for s in w.shape_node:
        c = w.shape_coordinate(s)
        assert c is None or (float(c).is_integer() and c in (-1, 1)), (s, c)


def test_source_audit_no_forbidden_tokens():
    """The adapter is a WORLD ADAPTER: no graph rule engine, no if/else selecting
    the match from raw scalars, no reward/punishment shaping. Source-audit the
    adapter for the forbidden tokens (all must be zero)."""
    src = open(os.path.join(ROOT, "domains", "bouba_kiki_world.py")).read()
    for pat in ("graph_rewrite.run(", "gr.run(", "._match(", "._apply(", "make_rule("):
        assert src.count(pat) == 0, pat
    for tok in ("reward_signal", "reinforce", "backprop", "gradient"):
        assert not re.search(r"\b" + re.escape(tok) + r"\b", src), tok


# ------------------------------------------------------------ (f) default == today
def test_default_concept_without_sharpness_attr_has_unchanged_signature():
    """default == today: a Concept WITHOUT the derived `sharpness` attr emits NO
    phenomenal:sharpness coordinate and its signature is unchanged (the axis only
    lights up on a concept carrying the extractor-derived attr, which only the
    experiment's form/shape concepts have). So the adapter absent changes nothing."""
    w = BoubaKikiWorld()
    s = w.s
    mt = s.add_node("Microtheory", {"name": "bk_plain", "category": "misc"})
    # a plain concept with NO sharpness attr
    plain = s.add_node("Concept", {"name": "plain", "category": "misc",
                                   "state": 0.0, "external_field": 0.0,
                                   "identity_field": 0.0})
    s.add_edge_unchecked(mt, "has_concept", plain)
    sig = concept_signature(s, plain)
    # no phenomenal:sharpness coordinate present
    assert not any(dim == _AXIS for (dim, _p, _v) in sig), sig
    # a concept carrying sharpness=0.0 (mid) also emits NO coordinate
    plain0 = s.add_node("Concept", {"name": "plain0", "category": "misc",
                                    "state": 0.0, "external_field": 0.0,
                                    "identity_field": 0.0, "sharpness": 0.0})
    s.add_edge_unchecked(mt, "has_concept", plain0)
    sig0 = concept_signature(s, plain0)
    assert not any(dim == _AXIS for (dim, _p, _v) in sig0), sig0
    # only +1/-1 sharpness attrs light up the axis
    plainp = s.add_node("Concept", {"name": "plainp", "category": "misc",
                                    "state": 0.0, "external_field": 0.0,
                                    "identity_field": 0.0, "sharpness": 1.0})
    s.add_edge_unchecked(mt, "has_concept", plainp)
    sigp = concept_signature(s, plainp)
    assert (_AXIS, "field", 1) in sigp, sigp
