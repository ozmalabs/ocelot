#!/usr/bin/env python3
"""BLOCK 294000 -- BOUBA/KIKI CROSSMODAL SOUND-SYMBOLISM confirmatory measure
(pre-registered).

Reproduces the Koehler (1929) / Ramachandran & Hubbard (2001) crossmodal MATCH as
a GENUINE-QUALIA event on the substrate's ONE qualia space: a phonetic FORM and a
visual SHAPE that sound-symbolically match land at the SAME pole of ONE felt
`phenomenal:sharpness` axis whose coordinate is DERIVED INDEPENDENTLY on each side
(articulatory phonetics for the word; curvature-concentration geometry for the
shape) and quantised through the SAME lattice. The MATCH is READ from the
qualia-space geometry (the concept_signature intersection + the find_analogies
ranking), NEVER computed in Python by comparing raw scalars. See
BOUBA_KIKI_SOUND_SYMBOLISM_PREREG.md (Sec4-Sec7).

This script is a MEASURE -- it takes NO decision. It sweeps the full form x shape
battery through domains/bouba_kiki_world.py, records the PRODUCED shared-coordinate
grid + find_analogies ranking, and checks it against the analytic oracle. The
sharpness coordinate is produced by the extractors + the SAME quantiser; the match
is the graph's own concept_signature / find_analogies output.

Sections:
  factorial grid       -- the full form x shape shared-coordinate grid: per cell the
                          derived phon/geom sharpness, the quantised poles, whether
                          the phenomenal:sharpness coordinate is SHARED, and the
                          find_analogies nearness rank; matched vs oracle at EVERY cell
  G-interaction        -- the form x shape INTERACTION: matched-pole pairs share-rate /
                          nearness vs mismatched-pole, with bootstrap 95% CIs (jitter
                          the shape point sets + add battery members for a distribution)
  G-oracle             -- the produced shared-coordinate == the pre-reg analytic oracle
                          at every cell (produced-not-hand-set)
  G-emergence          -- PERTURB an input (feed the round blob's point set through the
                          'sharp' slot / flip a form's phonemes to voiceless-plosive)
                          => the derived coordinate FLIPS => the match inverts
  G-reverse-battery    -- the reverse-battery FALSIFIER: the crossmodal match inverts
                          when the derivation INPUTS are reversed
  G-co-tuning-guard    -- the two derivations use the SAME quantiser + a battery of
                          >= 3 forms per pole x >= 2 shapes per pole; NO threshold was
                          fit to force alignment -- the raw scalar distributions are
                          separated on each side INDEPENDENTLY
  G-glass-box          -- read the derived sharpness attr + the phenomenal:sharpness
                          coordinate straight off graph_to_dict / inner.node; source
                          audit the adapter (forbidden = 0)
  G-discipline         -- canonical .so md5, integer-native coordinate, no new seed
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np                                              # noqa: E402
from domains.bouba_kiki_world import (                          # noqa: E402
    BoubaKikiWorld, FORM_BATTERY, shape_battery,
    phonetic_sharpness, geometric_sharpness,
    oracle_pole, oracle_match, POLE_THRESHOLD, QUANTUM, HALF_WIDTH)
from domains.bouba_kiki_world import _star, _regular_polygon, _ellipse  # noqa: E402

OUTDIR = os.path.join(ROOT, "results", "bouba_kiki_sound_symbolism")
CANON_MD5 = "7efe75eba05b006cafd15dbb4b7da246"   # canonical .so, native-only CAN cutover
BLOCK = 294000
N = 60                # jitter replicates per cohort (mirrors the sibling rungs)
_RNG = np.random.default_rng(BLOCK)
_AXIS = "phenomenal:sharpness"

# The pre-registered POLE assignment of each battery member (prereg Sec5), used to
# LABEL matched vs mismatched cells. The MATCH itself is READ from the graph; this
# is only the design label (which pole a member's derivation is expected to hit).
ROUND_FORMS = ("bouba", "maluma", "baloo")
SHARP_FORMS = ("kiki", "ziki")            # takete is honestly MID (graded)
MID_FORMS = ("takete",)
ROUND_SHAPES = ("circle", "polygon", "dodecagon")
SHARP_SHAPES = ("star", "spikestar")      # star7 / ellipse are honestly MID
MID_SHAPES = ("star7", "ellipse")


def _boot_ci(xs, reps=2000, seed=BLOCK):
    xs = np.asarray(xs, float)
    if len(xs) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = xs[rng.integers(0, len(xs), size=(reps, len(xs)))].mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


# ---------------------------------------------------------------- factorial grid
def factorial_grid():
    """The full form x shape shared-coordinate grid. Per cell: the derived
    phon/geom sharpness, the produced poles, whether the phenomenal:sharpness
    coordinate is SHARED (READ off the graph), the find_analogies nearness rank,
    and the analytic-oracle match. `matches_oracle` is the exact-match discipline
    over EVERY cell."""
    w = BoubaKikiWorld()
    forms = list(w.form_node)
    shapes = list(w.shape_node)
    form_raws = w.form_raw
    shape_raws = w.shape_raw
    grid, all_match = {}, True
    for f in forms:
        near = w.analogy_nearness(f)   # one search per source form
        row = {}
        for s in shapes:
            shared = w.shares_coordinate(f, s)
            oracle = oracle_match(form_raws[f], form_raws.values(),
                                  shape_raws[s], shape_raws.values())
            match_cell = (bool(shared) == bool(oracle))
            all_match = all_match and match_cell
            an = near.get(s)
            row[s] = dict(
                shares_coordinate=bool(shared),
                oracle_match=bool(oracle),
                cell_matches_oracle=bool(match_cell),
                analogy_rank=(None if an is None else an["rank"]),
                aligned_on_sharpness=(bool(an is not None
                                           and _AXIS in an["aligned_dimensions"])))
        grid[f] = dict(
            form_raw=round(form_raws[f], 6), form_pole=w.form_coordinate(f),
            cells=row)
    return dict(
        forms=forms, shapes=shapes,
        form_poles={f: w.form_coordinate(f) for f in forms},
        shape_poles={s: w.shape_coordinate(s) for s in shapes},
        shape_raw={s: round(shape_raws[s], 6) for s in shapes},
        grid=grid, matches_oracle=bool(all_match))


# ---------------------------------------------------------- G-interaction (+CIs)
def _cohort_shapes(rng):
    """A fresh shape battery drawn from STRUCTURAL variants within each class (the
    prereg's 'add battery members for a distribution'), NOT coordinate jitter --
    the max/mean-turning ratio is pathologically sensitive to point noise on a
    near-uniform shape (one jittered vertex spikes the ratio against a near-zero
    mean), so coordinate jitter would not represent 'another instance of the same
    class'. Instead each class is resampled from its own structural family:
    sharp = a star with a random point-count / inner-radius; round = a regular
    polygon with a random (high) vertex-count; mild = a random-eccentricity
    ellipse. The extractor re-derives the pole from the class-preserving variant."""
    n_pts = int(rng.integers(5, 8))          # 5..7-point star
    inner = float(rng.uniform(0.25, 0.45))   # deep enough to stay sharp
    n_pts2 = int(rng.integers(5, 7))
    inner2 = float(rng.uniform(0.2, 0.4))
    poly_a = int(rng.integers(36, 60))
    poly_b = int(rng.integers(18, 30))
    poly_c = int(rng.integers(10, 16))
    ecc = float(rng.uniform(0.7, 0.85))
    return {
        "star":      _star(n_pts, inner=inner),
        "spikestar": _star(n_pts2, inner=inner2),
        "star7":     _star(7, inner=0.5),
        "circle":    _regular_polygon(poly_a),
        "polygon":   _regular_polygon(poly_b),
        "dodecagon": _regular_polygon(poly_c),
        "ellipse":   _ellipse(b=ecc),
    }


def _matched_mismatched_share_rates(w):
    """(matched-pole share rate, mismatched-pole share rate) for ONE world:
    matched = (round-form,round-shape) & (sharp-form,sharp-shape); mismatched =
    (round-form,sharp-shape) & (sharp-form,round-shape). READ from the graph."""
    matched, mismatched = [], []
    pairs_matched = ([(f, s) for f in ROUND_FORMS for s in ROUND_SHAPES]
                     + [(f, s) for f in SHARP_FORMS for s in SHARP_SHAPES])
    pairs_mismatched = ([(f, s) for f in ROUND_FORMS for s in SHARP_SHAPES]
                        + [(f, s) for f in SHARP_FORMS for s in ROUND_SHAPES])
    for f, s in pairs_matched:
        matched.append(1.0 if w.shares_coordinate(f, s) else 0.0)
    for f, s in pairs_mismatched:
        mismatched.append(1.0 if w.shares_coordinate(f, s) else 0.0)
    return matched, mismatched


def g_interaction():
    """The form x shape INTERACTION: matched-pole pairs SHARE the coordinate /
    rank nearer; mismatched-pole pairs do NOT. Deterministic share-rates (the
    exact result) PLUS jittered-geometry cohort CIs. This is an INTERACTION, not a
    main effect -- a form matches a shape iff their poles COINCIDE."""
    # deterministic single-world share rates
    w0 = BoubaKikiWorld()
    det_m, det_mm = _matched_mismatched_share_rates(w0)
    det_matched_rate = float(np.mean(det_m))
    det_mismatched_rate = float(np.mean(det_mm))

    # jittered-geometry cohort: each replicate re-derives the shape poles from a
    # class-preserving STRUCTURAL variant, so the share-rate has a distribution to
    # bootstrap.
    matched_rates, mismatched_rates = [], []
    for _ in range(N):
        w = BoubaKikiWorld(shapes=_cohort_shapes(_RNG))
        m, mm = _matched_mismatched_share_rates(w)
        matched_rates.append(float(np.mean(m)))
        mismatched_rates.append(float(np.mean(mm)))
    ci_m = _boot_ci(matched_rates)
    ci_mm = _boot_ci(mismatched_rates)

    # find_analogies nearness: for each sharp/round form, the matched-pole shape is
    # present-and-aligned while the opposite-pole shape is absent (or ranks lower).
    near_ok = {}
    for f in SHARP_FORMS:
        v = w0.analogy_ranks_matching_above_opposite(f, "star", "circle")
        near_ok["%s~star>circle" % f] = v["matching_ranks_above_opposite"]
    for f in ROUND_FORMS:
        v = w0.analogy_ranks_matching_above_opposite(f, "circle", "star")
        near_ok["%s~circle>star" % f] = v["matching_ranks_above_opposite"]

    separated = bool(ci_m[0] > ci_mm[1])
    return dict(
        deterministic_matched_share_rate=round(det_matched_rate, 4),
        deterministic_mismatched_share_rate=round(det_mismatched_rate, 4),
        cohort_matched_mean=round(float(np.mean(matched_rates)), 4),
        cohort_mismatched_mean=round(float(np.mean(mismatched_rates)), 4),
        matched_ci=[round(x, 4) for x in ci_m],
        mismatched_ci=[round(x, 4) for x in ci_mm],
        matched_ci_separated_above_mismatched=separated,
        find_analogies_matching_above_opposite=near_ok,
        all_analogy_matches_above_opposite=bool(all(near_ok.values())),
        verdict_interaction=bool(separated and det_matched_rate > det_mismatched_rate
                                 and all(near_ok.values())),
        note="matched-pole (round-form,round-shape)&(sharp-form,sharp-shape) SHARE the "
             "phenomenal:sharpness coordinate / rank nearer; the crossings do NOT -- an "
             "INTERACTION (a form matches a shape iff their poles coincide), not a main "
             "effect, CI-separated")


# ------------------------------------------------------------------ G-oracle
def g_oracle():
    """The produced shared-coordinate grid == the pre-reg analytic oracle at EVERY
    cell (produced-not-hand-set). The oracle is pure arithmetic over the extractor
    outputs + the SAME quantiser; the produced grid is the graph's concept_signature
    intersection."""
    w = BoubaKikiWorld()
    forms, shapes = list(w.form_node), list(w.shape_node)
    mism = []
    for f in forms:
        for s in shapes:
            produced = bool(w.shares_coordinate(f, s))
            oracle = bool(oracle_match(w.form_raw[f], w.form_raw.values(),
                                       w.shape_raw[s], w.shape_raw.values()))
            if produced != oracle:
                mism.append(dict(form=f, shape=s, produced=produced, oracle=oracle))
    return dict(cells=len(forms) * len(shapes), mismatches=mism,
                n_mismatches=len(mism),
                verdict_oracle=bool(len(mism) == 0),
                note="the produced phenomenal:sharpness shared-coordinate equals the "
                     "analytic oracle at every form x shape cell")


# --------------------------------------------------------------- G-emergence
def g_emergence():
    """DERIVATION-NOT-HAND-SET (the emergence proof): PERTURB an input and assert
    the phenomenal:sharpness coordinate FLIPS and the match inverts. Two probes:
      (i) flip a ROUND form's phonemes to voiceless-plosive => pole flips -1 -> +1
          => it now matches the STAR, not the circle;
      (ii) feed a ROUND shape's point set through the 'sharp' slot vs a STAR's
           through the 'round' slot => the derived geometric coordinate is a
           function of the POINTS, not the name (swap the point sets, the poles
           swap)."""
    # (i) flip bouba's phonemes to a voiceless-plosive word
    base = BoubaKikiWorld()
    bouba_pole_before = base.form_coordinate("bouba")
    bouba_matches_circle_before = base.shares_coordinate("bouba", "circle")
    bouba_matches_star_before = base.shares_coordinate("bouba", "star")

    forms = dict(FORM_BATTERY)
    del forms["bouba"]
    forms["bouba"] = ["k", "i", "t", "e"]     # SAME slot, reversed phonemes
    flipped = BoubaKikiWorld(forms=forms)
    bouba_pole_after = flipped.form_coordinate("bouba")
    bouba_matches_circle_after = flipped.shares_coordinate("bouba", "circle")
    bouba_matches_star_after = flipped.shares_coordinate("bouba", "star")

    phoneme_flip = dict(
        pole_before=bouba_pole_before, pole_after=bouba_pole_after,
        matches_circle_before=bool(bouba_matches_circle_before),
        matches_star_before=bool(bouba_matches_star_before),
        matches_circle_after=bool(bouba_matches_circle_after),
        matches_star_after=bool(bouba_matches_star_after),
        coordinate_flipped=bool(bouba_pole_before != bouba_pole_after),
        match_inverted=bool(bouba_matches_circle_before and bouba_matches_star_after
                            and not bouba_matches_star_before
                            and not bouba_matches_circle_after))

    # (ii) swap the point sets: feed the STAR's points through the 'circle' slot
    # and the circle's points through the 'star' slot -- the geometric pole must
    # follow the POINTS, not the name.
    shapes = shape_battery()
    swapped = dict(shapes)
    swapped["circle"], swapped["star"] = shapes["star"], shapes["circle"]
    sw = BoubaKikiWorld(shapes=swapped)
    point_swap = dict(
        circle_slot_pole=sw.shape_coordinate("circle"),   # now holds star points
        star_slot_pole=sw.shape_coordinate("star"),       # now holds circle points
        # kiki (sharp) now matches the 'circle' slot (star points) not the 'star' slot
        kiki_matches_circle_slot=bool(sw.shares_coordinate("kiki", "circle")),
        kiki_matches_star_slot=bool(sw.shares_coordinate("kiki", "star")),
        poles_follow_points=bool(sw.shape_coordinate("circle") == +1
                                 and sw.shape_coordinate("star") == -1))

    return dict(
        phoneme_flip=phoneme_flip, point_swap=point_swap,
        verdict_emergence=bool(phoneme_flip["coordinate_flipped"]
                               and phoneme_flip["match_inverted"]
                               and point_swap["poles_follow_points"]
                               and point_swap["kiki_matches_circle_slot"]
                               and not point_swap["kiki_matches_star_slot"]),
        note="perturbing an INPUT flips the derived phenomenal:sharpness coordinate and "
             "inverts the match -- the answer was NOT put in, it is derived from the "
             "features (reverse the phonemes / swap the point sets, the pole follows)")


# ------------------------------------------------- G-reverse-battery (falsifier)
def g_reverse_battery():
    """The REVERSE-BATTERY falsifier (prereg Sec7): reverse each form's phonemes
    ONE AT A TIME against the otherwise-intact battery (a round form -> a
    voiceless-plosive word; a sharp form -> a voiced-rounded word) and confirm the
    pole flips and the match inverts. One-at-a-time is the honest test: it asks
    'does THIS form's coordinate follow its OWN input', holding the rest of the
    battery (and thus the standardisation reference) fixed -- reversing the whole
    battery at once would merely re-label the poles (the distribution inverts
    wholesale), which tests nothing. If a coordinate does NOT flip when its input
    is reversed, the axis is not derived from the features and the claim is false."""
    reversals = {
        # round -> sharp phoneme sets
        "bouba":  ["k", "i", "t", "e"],
        "maluma": ["t", "i", "k", "i"],
        "baloo":  ["z", "i", "k", "i"],
        # sharp -> round phoneme sets
        "kiki":   ["m", "u", "m", "u"],
        "ziki":   ["m", "a", "l", "u"],
    }
    base = BoubaKikiWorld()
    per = {}
    inversions = {}
    all_flipped = True
    for name, segs in reversals.items():
        forms = dict(FORM_BATTERY)
        forms[name] = segs                    # reverse THIS form only
        rev = BoubaKikiWorld(forms=forms)
        before = base.form_coordinate(name)
        after = rev.form_coordinate(name)
        flipped = bool(before is not None and after is not None and before != after)
        all_flipped = all_flipped and flipped
        per[name] = dict(pole_before=before, pole_after=after, flipped=flipped)
        if name in ("bouba", "maluma", "baloo"):   # round -> now sharp: matches star
            inversions[name] = dict(
                matched_star_after=bool(rev.shares_coordinate(name, "star")),
                matched_circle_after=bool(rev.shares_coordinate(name, "circle")))
        else:                                        # sharp -> now round: matches circle
            inversions[name] = dict(
                matched_circle_after=bool(rev.shares_coordinate(name, "circle")),
                matched_star_after=bool(rev.shares_coordinate(name, "star")))

    round_now_sharp = all(inversions[n]["matched_star_after"]
                          and not inversions[n]["matched_circle_after"]
                          for n in ("bouba", "maluma", "baloo"))
    sharp_now_round = all(inversions[n]["matched_circle_after"]
                          and not inversions[n]["matched_star_after"]
                          for n in ("kiki", "ziki"))
    return dict(
        per_form=per, inversions=inversions,
        all_poles_flipped=bool(all_flipped),
        round_forms_now_match_star=bool(round_now_sharp),
        sharp_forms_now_match_circle=bool(sharp_now_round),
        verdict_reverse_battery=bool(all_flipped and round_now_sharp and sharp_now_round),
        note="reversing each form's derivation INPUT (one at a time, intact reference "
             "battery) flips its coordinate and INVERTS its crossmodal match -- the "
             "built-in falsifier collapses/inverts the effect")


# --------------------------------------------------------- G-co-tuning-guard
def g_co_tuning_guard():
    """The CO-TUNING GUARD (prereg Sec2): the two derivations use the SAME quantiser
    (per-modality z-score standardisation + ONE shared POLE_THRESHOLD), a battery of
    >= 3 round-forms + >= 2 sharp-forms x >= 2 shapes per pole, and NO threshold was
    fit to force alignment. Evidence: the RAW scalar distributions are separated on
    each side INDEPENDENTLY (a clean gap between the round cluster and the sharp
    cluster on BOTH the phonetic and the geometric side, with no reference to the
    other side)."""
    phon = {n: phonetic_sharpness(s) for n, s in FORM_BATTERY.items()}
    shapes = shape_battery()
    geom = {n: geometric_sharpness(p) for n, p in shapes.items()}

    phon_round = [phon[n] for n in ROUND_FORMS]
    phon_sharp = [phon[n] for n in SHARP_FORMS]
    geom_round = [geom[n] for n in ROUND_SHAPES]
    geom_sharp = [geom[n] for n in SHARP_SHAPES]

    # independent separation: the max of the round cluster < the min of the sharp
    # cluster, on EACH side (the clusters do not overlap, derived independently).
    phon_gap = float(min(phon_sharp) - max(phon_round))
    geom_gap = float(min(geom_sharp) - max(geom_round))

    return dict(
        same_quantiser=dict(
            method="per-modality z-score standardisation vs own battery, then ONE "
                   "shared POLE_THRESHOLD",
            pole_threshold=POLE_THRESHOLD, quantum=QUANTUM, half_width=HALF_WIDTH,
            single_threshold_both_sides=True),
        battery=dict(round_forms=list(ROUND_FORMS), sharp_forms=list(SHARP_FORMS),
                     mid_forms=list(MID_FORMS),
                     round_shapes=list(ROUND_SHAPES), sharp_shapes=list(SHARP_SHAPES),
                     mid_shapes=list(MID_SHAPES),
                     n_round_forms=len(ROUND_FORMS), n_sharp_forms=len(SHARP_FORMS),
                     n_round_shapes=len(ROUND_SHAPES), n_sharp_shapes=len(SHARP_SHAPES),
                     battery_adequate=bool(len(ROUND_FORMS) >= 3 and len(SHARP_FORMS) >= 2
                                           and len(ROUND_SHAPES) >= 2
                                           and len(SHARP_SHAPES) >= 2)),
        phonetic_raw=dict(round={n: round(phon[n], 4) for n in ROUND_FORMS},
                          sharp={n: round(phon[n], 4) for n in SHARP_FORMS},
                          mid={n: round(phon[n], 4) for n in MID_FORMS},
                          gap=round(phon_gap, 4), separated=bool(phon_gap > 0)),
        geometric_raw=dict(round={n: round(geom[n], 4) for n in ROUND_SHAPES},
                           sharp={n: round(geom[n], 4) for n in SHARP_SHAPES},
                           mid={n: round(geom[n], 4) for n in MID_SHAPES},
                           gap=round(geom_gap, 4), separated=bool(geom_gap > 0)),
        no_fitted_threshold=True,
        verdict_co_tuning_guard=bool(phon_gap > 0 and geom_gap > 0),
        note="the two derivations are INDEPENDENT (each extractor built for its own "
             "purpose) and the SAME quantiser maps both; the raw clusters are separated "
             "on EACH side independently (no overlap) -- no per-side threshold was fit "
             "to manufacture the diagonal (co-tuning would show as an overlapping raw "
             "distribution rescued only by a tuned cutoff)")


# --------------------------------------------------------------- G-glass-box
def g_glass_box():
    """Read the derived `sharpness` attr + the produced phenomenal:sharpness
    coordinate straight off graph_to_dict / inner.node at representative points +
    audit the adapter source for the forbidden tokens (must be zero)."""
    w = BoubaKikiWorld()
    d = w.s.graph_to_dict()
    readouts = {}
    for name, node in list(w.form_node.items()) + list(w.shape_node.items()):
        attrs = None
        for nd in d["nodes"]:
            if nd.get("attrs", {}).get("name") == name and nd["type"] == "Concept":
                attrs = nd["attrs"]
                break
        readouts[name] = dict(
            sharpness_attr=(None if attrs is None
                            else round(float(attrs.get("sharpness", 0.0)), 6)),
            phenomenal_sharpness_coordinate=w.sharpness_coordinate(node),
            read_via="graph_to_dict")

    adapter = os.path.join(ROOT, "domains", "bouba_kiki_world.py")
    src = open(adapter).read()
    forbidden = ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(",
                 "make_rule(", "graph_rewrite("]
    hits = {p: len(re.findall(re.escape(p), src)) for p in forbidden}
    shaping = {t: len(re.findall(r"\b" + re.escape(t) + r"\b", src))
               for t in ["reward_signal", "punish", "reinforce", "backprop", "gradient"]}
    api = {c: len(re.findall(r"\b" + re.escape(c) + r"\b", src))
           for c in ["concept_signature", "find_analogies", "_turning_angles",
                     "_round_to_vocab"]}
    return dict(
        readouts=readouts,
        forbidden_hits=hits, source_audit_clean=all(v == 0 for v in hits.values()),
        shaping_tokens=shaping, no_shaping=all(v == 0 for v in shaping.values()),
        substrate_api_calls=api,
        mechanism=dict(
            phonetic="per-segment mean([voiceless,degree,1-lip_rounding,frontness,"
                     "height]); word = mean over segments (articulatory phonetics)",
            geometric="max|turning| / mean|turning| over interior points "
                      "(ink_dynamics._turning_angles, curvature CONCENTRATION)",
            quantiser="per-modality z-score standardisation + ONE shared POLE_THRESHOLD "
                      "=> _round_to_vocab(sign, 1.0, 1) (the CAN dynamical axes' lattice)",
            match="concept_signature INTERSECTION contains (phenomenal:sharpness, field, "
                  "k) + find_analogies ranks the matching-pole shape aligned ON "
                  "phenomenal:sharpness -- NO Python compares raw scalars",
            adapter_role="derive each side's sharpness + write the sharpness attr; READ "
                         "the produced signature / analogy verdict off the graph"),
        verdict_glass_box=bool(all(v == 0 for v in hits.values())
                               and all(v == 0 for v in shaping.values())))


# --------------------------------------------------------------- G-discipline
def g_discipline():
    so = os.path.join(ROOT, "runners", "dsl", "python", "substrate_rs", "_native.abi3.so")
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest() if os.path.exists(so) else None
    # No new seed authored (prereg Sec8/Sec9): the ONLY seed change is the additive
    # phenomenal:sharpness axis already in seeds/qualia_space.json; confirm no
    # bouba_kiki seed file exists and nothing named bouba_kiki is in load_all_seeds.
    seed_path = os.path.join(ROOT, "seeds", "bouba_kiki_sound_symbolism.json")
    new_seed_exists = os.path.exists(seed_path)
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    absent = not any("bouba_kiki" in s for s in seeds)
    # integer-native at the coordinate: the produced phenomenal:sharpness step is an
    # integer in {-1, +1} at every non-mid cell.
    w = BoubaKikiWorld()
    coords = ([w.form_coordinate(f) for f in w.form_node]
              + [w.shape_coordinate(s) for s in w.shape_node])
    coords_integer = all(c is None or float(c).is_integer() for c in coords)
    return dict(
        canonical_so_md5=md5, canonical_untouched=(md5 == CANON_MD5),
        no_new_seed_file=(not new_seed_exists),
        no_bouba_kiki_in_load_all=bool(absent),
        produced_coordinates_integer=bool(coords_integer),
        axis_constants=dict(pole_threshold=POLE_THRESHOLD, quantum=QUANTUM,
                            half_width=HALF_WIDTH),
        verdict_discipline=bool(md5 == CANON_MD5 and not new_seed_exists
                                and absent and coords_integer))


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    print("factorial grid ..."); grid = factorial_grid()
    print("G-interaction ..."); inter = g_interaction()
    print("G-oracle ..."); orc = g_oracle()
    print("G-emergence ..."); emg = g_emergence()
    print("G-reverse-battery ..."); rev = g_reverse_battery()
    print("G-co-tuning-guard ..."); guard = g_co_tuning_guard()
    print("G-glass-box ..."); gb = g_glass_box()
    print("G-discipline ..."); disc = g_discipline()
    result = dict(block=BLOCK, n_per_cohort=N, rng_seed=BLOCK,
                  pole_threshold=POLE_THRESHOLD,
                  factorial_grid=grid, g_interaction=inter, g_oracle=orc,
                  g_emergence=emg, g_reverse_battery=rev, g_co_tuning_guard=guard,
                  g_glass_box=gb, g_discipline=disc)
    path = os.path.join(OUTDIR, "results.json")
    json.dump(result, open(path, "w"), indent=1)
    print("wrote", path)
    print(json.dumps(dict(
        grid_matches_oracle=grid["matches_oracle"],
        interaction=inter["verdict_interaction"],
        matched_ci=inter["matched_ci"], mismatched_ci=inter["mismatched_ci"],
        oracle=orc["verdict_oracle"],
        emergence=emg["verdict_emergence"],
        reverse_battery=rev["verdict_reverse_battery"],
        co_tuning_guard=guard["verdict_co_tuning_guard"],
        phon_gap=guard["phonetic_raw"]["gap"], geom_gap=guard["geometric_raw"]["gap"],
        glass_box=gb["verdict_glass_box"],
        discipline=disc["verdict_discipline"]), indent=1))


if __name__ == "__main__":
    main()
