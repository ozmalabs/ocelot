"""BoubaKikiWorld -- a MECHANICAL bouba/kiki CROSSMODAL SOUND-SYMBOLISM adapter
(block 294000, BOUBA_KIKI_SOUND_SYMBOLISM_PREREG.md).

Reproduces the Koehler (1929) / Ramachandran & Hubbard (2001) crossmodal MATCH:
a heard FORM and a seen SHAPE that "go together" land at the SAME pole of ONE
felt `phenomenal:sharpness` axis. The coordinate is DERIVED INDEPENDENTLY on each
side by two pre-existing, independently-motivated feature extractors -- articulatory
phonetics for a word (voiceless / constriction / spread / front / high => sharp),
curvature-concentration geometry for a shape (a star PEAKS, a circle is UNIFORM =>
round) -- and quantised through the SAME lattice both sides project through. The
MATCH is then READ from the qualia-space geometry (the concept_signature
intersection / the find_analogies ranking on the graph), NEVER computed in Python
by comparing raw scalars.

ARCHITECTURE RULE COMPLIANCE (see CLAUDE.md): this file is a WORLD ADAPTER. It
does exactly two things -- INGEST (derive each side's sharpness scalar from its OWN
feature extractor, quantise both with the SAME quantiser, write the derived scalar
onto each concept's `sharpness` attr -- the SOURCE the `phenomenal:sharpness` axis
reads) and EMIT (read the produced `concept_signature` coordinate and the
`find_analogies` ranking back off the graph).

  * the GEOMETRIC extractor imports `domains.ink_dynamics._turning_angles`
    (READ-ONLY, NOT reimplemented) and computes sharpness = max|turning| /
    mean|turning| over interior points -- built for the two-thirds power law, NOT
    for sounds.
  * the PHONETIC extractor is standard articulatory phonetics: per-segment
    sharp = mean([voiceless, constriction_degree, 1-lip_rounding, frontness,
    height]); a word's sharpness is the mean over its segments -- chosen for the
    SOUNDS, NOT for shapes.
  * the SAME quantiser (`_round_to_vocab`, imported from analogy_search) maps BOTH
    derived scalars onto the axis pole after each is centred on the SAME battery
    midpoint. There is NO per-side threshold to co-tune.
  * the MATCH is the qualia-space geometry: `match(form, shape)` reads
    `concept_signature(form)` & `concept_signature(shape)` and returns whether they
    SHARE the `(phenomenal:sharpness, "field", k)` coordinate, PLUS a
    `find_analogies` nearness (does the matching-pole shape rank above the
    opposite-pole shape when the form concept is the query).

No `graph_rewrite.run` / `_match` / `_apply` / `make_rule`; no if/else over graph
state that SELECTS the match by comparing raw scalars (the ONLY conditionals are
over WORLD state -- which battery member, loop bounds -- and the quantiser's own
sign, which is the shared feature-extractor arithmetic, not a match decision). No
reward/punishment shaping: each derived scalar is a FIXED function of the stimulus
features, never a learned reward.

No new seed is authored or loaded: the adapter reuses the already-landed
`phenomenal:sharpness` axis (seeds/qualia_space.json) by import, so `load_all_seeds`
/ the base tree is byte-identical when this adapter is absent
(BOUBA_KIKI_SOUND_SYMBOLISM_PREREG.md Sec8, Sec9).
"""
from __future__ import annotations

import json
import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np                                             # noqa: E402
from substrate_rs import _native                              # noqa: E402
import domains.analogy_search as asr                          # noqa: E402
import domains.relation_grounding as rg                       # noqa: E402
from domains.analogy_search import (                          # noqa: E402
    concept_signature, find_analogies, _round_to_vocab)
# The GEOMETRY extractor -- imported READ-ONLY, NOT reimplemented (prereg Sec2).
from domains.ink_dynamics import _turning_angles              # noqa: E402

# --------------------------------------------------------------------------- #
#  FIXED axis constants (pre-registered, BOUBA_KIKI_SOUND_SYMBOLISM_PREREG.md Sec3)
#  -- the axis the derived `sharpness` attr projects onto is
#  `phenomenal:sharpness`, source `field:sharpness`, quantum=1.0, half_width=1
#  => a clean bipolar {-1, 0, +1} sign axis. These MUST equal the seeded axis.
# --------------------------------------------------------------------------- #
QUANTUM = 1.0
HALF_WIDTH = 1
# The SHARED POLE THRESHOLD on the per-modality STANDARDISED (z-scored) derived
# scalar (prereg Sec2 point 2, Sec3). One fixed constant applied to BOTH sides:
# each side standardises its OWN raw scalar against its OWN battery's mean/std
# (a standard z-score, NOT a fitted per-side cutoff), then the SAME threshold
# maps the z-score to a pole: z >= +T => +1 (sharp), z <= -T => -1 (round),
# else 0 (MID -- omitted, honest: a scalar near its battery centre matches
# neither pole, e.g. takete). Standardisation is per-modality because the two
# extractors live on DIFFERENT native scales (phonetic ~[0.3,0.8]; geometric
# ratio >= 1.0) -- z-scoring each to its own battery is the honest way to put
# both on ONE comparable axis WITHOUT a fitted alignment threshold; the guard
# (Sec2, the raw distributions are separated on each side independently) is what
# proves this is standardisation, not co-tuning.
POLE_THRESHOLD = 0.75

_SHARPNESS_ATTR = "sharpness"          # the field:sharpness axis SOURCE attr
_AXIS = "phenomenal:sharpness"

# --------------------------------------------------------------------------- #
#  PHONETICS -- per-phoneme 5-dim articulatory feature dicts + source label
#  (prereg Sec2; the standard-phonetics feature set from articulatory_gamma).
#  Each phoneme: (frontness, height, place, degree, lip_rounding) in [0,1] plus
#  source {voiced=0, fric=1, burst=2}. Chosen for the SOUNDS, not the shapes.
# --------------------------------------------------------------------------- #
#: source -> voiceless-ness contribution (prereg Sec2): burst(voiceless plosive)=1,
#: frication=0.5, voiced=0.
_SOURCE_VOICELESS = {0: 0.0, 1: 0.5, 2: 1.0}   # voiced / fric / burst

PHONEME_FEATURES = {
    # voiced / rounded / sonorant / back-open  => ROUND
    "b": dict(frontness=0.4, height=0.2, place=1.0, degree=1.0, lip_rounding=1.0, source=2),
    "m": dict(frontness=0.3, height=0.2, place=1.0, degree=0.9, lip_rounding=0.9, source=0),
    "l": dict(frontness=0.5, height=0.4, place=0.6, degree=0.5, lip_rounding=0.2, source=0),
    "u": dict(frontness=0.1, height=0.9, place=0.0, degree=0.1, lip_rounding=1.0, source=0),
    "o": dict(frontness=0.2, height=0.5, place=0.0, degree=0.1, lip_rounding=0.9, source=0),
    "a": dict(frontness=0.3, height=0.0, place=0.0, degree=0.0, lip_rounding=0.0, source=0),
    # voiceless plosive / front-high / spread   => SHARP
    "k": dict(frontness=0.6, height=0.8, place=0.4, degree=1.0, lip_rounding=0.0, source=2),
    "t": dict(frontness=0.9, height=0.7, place=0.7, degree=1.0, lip_rounding=0.0, source=2),
    "z": dict(frontness=0.9, height=0.7, place=0.8, degree=1.0, lip_rounding=0.0, source=1),
    "i": dict(frontness=1.0, height=1.0, place=1.0, degree=0.1, lip_rounding=0.0, source=0),
    "e": dict(frontness=0.8, height=0.6, place=0.9, degree=0.1, lip_rounding=0.0, source=0),
}

#: The pre-registered BATTERY of nonwords (prereg Sec5). Each maps to its ordered
#: phoneme segments (the word is spelled phonemically). ROUND-forms and SHARP-forms
#: -- >= 3 per pole (the anti-luck guard, prereg Sec2 point 3).
FORM_BATTERY = {
    # ROUND cluster (voiced / rounded / sonorant / back-open)
    "bouba":  ["b", "u", "b", "a"],
    "maluma": ["m", "a", "l", "u", "m", "a"],
    "baloo":  ["b", "a", "l", "u"],
    # SHARP cluster (voiceless-plosive / front-high / spread)
    "kiki":   ["k", "i", "k", "i"],
    "takete": ["t", "a", "k", "e", "t", "e"],
    "ziki":   ["z", "i", "k", "i"],
}

# --------------------------------------------------------------------------- #
#  SHAPES -- point sets. Round blob = high-gon polygon (uniform turning), spiky
#  star = 5-point star (turning CONCENTRATED at the points), plus a mild /
#  intermediate shape (dodecagon -- also uniform, geometrically round but a
#  distinct battery member). Built for the geometry extractor, not the sounds.
# --------------------------------------------------------------------------- #
def _regular_polygon(n, *, radius=1.0):
    """A regular n-gon point set (closed loop; last point repeats the first so the
    interior turning at every vertex is defined)."""
    pts = [(radius * math.cos(2 * math.pi * i / n),
            radius * math.sin(2 * math.pi * i / n)) for i in range(n)]
    pts.append(pts[0])
    return np.array(pts, dtype=float)


def _star(points=5, *, outer=1.0, inner=0.4):
    """An `points`-point star: alternating outer/inner vertices. The turning
    CONCENTRATES at the outer points (sharp) vs the shallow inner ones."""
    pts = []
    for i in range(2 * points):
        r = outer if i % 2 == 0 else inner
        theta = math.pi * i / points
        pts.append((r * math.cos(theta), r * math.sin(theta)))
    pts.append(pts[0])
    return np.array(pts, dtype=float)


def _ellipse(n=64, *, a=1.0, b=0.8):
    """A sampled ellipse -- curvature is NON-uniform (concentrated at the two
    ends) but far less peaked than a star: a genuinely INTERMEDIATE / mild shape
    (the geometric twin of takete)."""
    pts = [(a * math.cos(2 * math.pi * i / n), b * math.sin(2 * math.pi * i / n))
           for i in range(n)]
    pts.append(pts[0])
    return np.array(pts, dtype=float)


def shape_battery():
    """The pre-registered SHAPE battery (prereg Sec5), BALANCED >= 2 per pole so
    the per-modality standardisation is non-degenerate (the co-tuning guard): the
    spiky STARs (concentrated turning => + pole), the round CIRCLE (48-gon) /
    POLYGON (24-gon) / DODECAGON (all UNIFORM turning, ratio exactly 1.0 => -
    pole), and a mild/INTERMEDIATE ELLIPSE (mildly non-uniform => lands MID, the
    geometric twin of takete). Fresh point sets each call (so a caller may jitter
    them)."""
    return {
        # SHARP cluster (curvature CONCENTRATED at the points)
        "star":      _star(5, inner=0.4),
        "spikestar": _star(5, inner=0.25),
        "star7":     _star(7, inner=0.5),
        # ROUND cluster (UNIFORM turning, ratio 1.0)
        "circle":    _regular_polygon(48),
        "polygon":   _regular_polygon(24),
        "dodecagon": _regular_polygon(12),
        # MILD / intermediate (mildly non-uniform curvature)
        "ellipse":   _ellipse(),
    }


# --------------------------------------------------------------------------- #
#  TWO INDEPENDENT FEATURE EXTRACTORS (each fixed by its OWN internal logic).
# --------------------------------------------------------------------------- #
def phonetic_sharpness(segments):
    """The PHONETIC sharpness of a word (prereg Sec2): per-segment
    sharp = mean([voiceless, constriction_degree, 1 - lip_rounding, frontness,
    height]); the word's sharpness is the mean over its segments. Standard
    articulatory phonetics -- NO reference to shapes or to the axis."""
    if not segments:
        return 0.0
    seg_vals = []
    for ph in segments:
        f = PHONEME_FEATURES[ph]
        voiceless = _SOURCE_VOICELESS[int(f["source"])]
        seg = np.mean([voiceless, f["degree"], 1.0 - f["lip_rounding"],
                       f["frontness"], f["height"]])
        seg_vals.append(float(seg))
    return float(np.mean(seg_vals))


def geometric_sharpness(points):
    """The GEOMETRIC sharpness of a shape (prereg Sec2): curvature CONCENTRATION,
    max|turning| / mean|turning| over the INTERIOR points, from
    ink_dynamics._turning_angles (imported READ-ONLY). A regular polygon has
    UNIFORM turning => ratio ~1.0; a star PEAKS => > 1.0. NO reference to sounds
    or to the axis."""
    pts = np.asarray(points, dtype=float)
    ang = np.abs(_turning_angles(pts))
    interior = ang[1:-1] if ang.size >= 3 else ang
    interior = interior[interior > 1e-9]
    if interior.size == 0:
        return 0.0
    mean_turn = float(interior.mean())
    if mean_turn <= 1e-12:
        return 0.0
    return float(interior.max() / mean_turn)


# --------------------------------------------------------------------------- #
#  THE SHARED QUANTISER -- the SAME threshold both sides project through (prereg
#  Sec2 point 2, Sec4). Each derived scalar is STANDARDISED against its OWN
#  battery (mean/std z-score, off-graph) then the SAME POLE_THRESHOLD maps the
#  z-score to a pole. Per-modality standardisation (not one global midpoint)
#  because the extractors live on different native scales; the co-tuning guard
#  is that the RAW distributions are separated on each side independently.
# --------------------------------------------------------------------------- #
def standardise(raw, battery_raws):
    """z-score a derived scalar against its OWN battery's mean/std (prereg Sec2:
    'z-scored to the battery midpoint off-graph'). A degenerate (zero-std)
    battery returns the centred value directly (avoids /0)."""
    arr = np.asarray(list(battery_raws), dtype=float)
    mu = float(arr.mean())
    sd = float(arr.std())
    if sd <= 1e-12:
        return float(raw) - mu
    return (float(raw) - mu) / sd


def quantise_z(z, *, threshold=POLE_THRESHOLD):
    """The axis POLE a STANDARDISED scalar maps to: +1 (sharp), -1 (round), or
    None (mid -- omitted, matches neither pole). The SAME threshold band applied
    to BOTH modalities' z-scores; then rounded through the CAN dynamical axes'
    own `_round_to_vocab` lattice (quantum=1.0, half_width=1 => the seeded
    `phenomenal:sharpness` axis's own quantum/half_width)."""
    if z >= threshold:
        signed = 1.0
    elif z <= -threshold:
        signed = -1.0
    else:
        signed = 0.0
    return _round_to_vocab(signed, QUANTUM, HALF_WIDTH)


def quantise(raw, battery_raws, *, threshold=POLE_THRESHOLD):
    """Standardise `raw` against `battery_raws` then map to the axis pole with the
    SHARED threshold. The single entry both extractors funnel through."""
    return quantise_z(standardise(raw, battery_raws), threshold=threshold)


# native identity-rule bookkeeping ledger (mirrors tests/test_qualia_cross_family
# _LEDGER) -- present so a CAN Concept is well-formed, but the felt `sharpness`
# attr is the DERIVED coordinate SOURCE, written by the extractor, not this ledger.
_LEDGER = {
    "identity_evidence_confirm": 0, "identity_evidence_disconfirm": 0,
    "identity_evidence_tick": -1, "identity_decay_tick": -1,
    "identity_field_tick": -1,
}

_SEEDS = ("shape_vocabulary", "qualia_space", "analogy_search")


class BoubaKikiWorld:
    """ONE crossmodal qualia space holding the FORM battery + the SHAPE battery as
    CAN Concepts, each carrying its INDEPENDENTLY-DERIVED `sharpness` attr (the
    `phenomenal:sharpness` axis SOURCE). `match(form, shape)` reads the produced
    concept_signature intersection + the find_analogies nearness -- the crossmodal
    correspondence is the qualia-space geometry, never a Python scalar compare.

    Forms live in a `bk_forms` Mt, shapes in a `bk_shapes` Mt, so a find_analogies
    query with a form runs across the shapes field (cross-modal by construction --
    the concepts share NO lexical role, no edge, no category; the ONLY axis they
    can align on is the shared felt `phenomenal:sharpness`)."""

    def __init__(self, *, threshold=POLE_THRESHOLD, forms=None, shapes=None):
        self.threshold = float(threshold)
        asr._QUALIA_SCHEMA_CACHE.clear()
        self.s = _native.Substrate()
        self.agent = self.s.add_node("Agent", {})
        for name in _SEEDS:
            self.s.load_seed_manifest(
                json.load(open(os.path.join(_ROOT, "seeds", "%s.json" % name))),
                self.agent)
        self._open_productions()

        self.forms_mt = self.s.add_node("Microtheory", {
            "name": "bk_forms", "category": "phonetic_form"})
        self.shapes_mt = self.s.add_node("Microtheory", {
            "name": "bk_shapes", "category": "visual_shape"})

        # derived scalars + concept ids, per battery member.
        self.form_raw = {}
        self.form_pole = {}
        self.form_node = {}
        self.shape_raw = {}
        self.shape_pole = {}
        self.shape_node = {}

        forms = FORM_BATTERY if forms is None else forms
        shapes = shape_battery() if shapes is None else shapes
        # DERIVE each side's raw scalar FIRST (each extractor, independent), so the
        # per-modality standardisation sees its whole OWN battery -- the raw
        # distributions are what the co-tuning guard reports as separated.
        self.form_segments = dict(forms)
        self.shape_points = {n: np.asarray(p, dtype=float) for n, p in shapes.items()}
        for name, segs in self.form_segments.items():
            self.form_raw[name] = phonetic_sharpness(segs)
        for name, pts in self.shape_points.items():
            self.shape_raw[name] = geometric_sharpness(pts)
        # QUANTISE + mint each concept (each standardised against its OWN battery).
        for name in self.form_segments:
            self._mint_form(name)
        for name in self.shape_points:
            self._mint_shape(name)

    # ---- production admissibility (mirrors test_qualia_cross_family._boot) --
    def _open_productions(self):
        node_types = ("Agent", "Concept", "Microtheory", "QualiaDimension",
                      "DimensionEdgeRole")
        edge_types = tuple(set(rg.RELATION_EDGE_TYPES) | {
            "has_concept", "genls", "is_a", "built_from", "depends_on", "grounds"})
        for a in node_types:
            for b in node_types:
                for et in edge_types:
                    try:
                        self.s.add_production({
                            "src": {"type": a, "var": "x"}, "edge_type": et,
                            "tgt": {"type": b, "var": "y"}, "where": None,
                            "weight": {"type": "Lit", "value": 1.0},
                            "provenance": "bouba_kiki:open"})
                    except Exception:
                        pass

    # ---- ingest -----------------------------------------------------------
    def _mint_concept(self, mt, name, category, sharpness_scalar):
        """Mint a CAN Concept carrying the DERIVED `sharpness` attr (the axis
        SOURCE). state/external_field/identity_field start at ZERO -- the ONLY
        felt coordinate this concept carries is the extractor-derived sharpness."""
        attrs = {"name": name, "category": category,
                 "state": 0.0, "external_field": 0.0, "identity_field": 0.0,
                 _SHARPNESS_ATTR: float(sharpness_scalar)}
        attrs.update(_LEDGER)
        c = self.s.add_node("Concept", attrs)
        self.s.add_edge_unchecked(mt, "has_concept", c)
        return c

    def _mint_form(self, name):
        pole = self.quantise(self.form_raw[name], self.form_raw.values())
        node = self._mint_concept(self.forms_mt, name, "phonetic_form",
                                  0.0 if pole is None else float(pole))
        self.form_pole[name] = pole
        self.form_node[name] = node
        return pole

    def _mint_shape(self, name):
        pole = self.quantise(self.shape_raw[name], self.shape_raw.values())
        node = self._mint_concept(self.shapes_mt, name, "visual_shape",
                                  0.0 if pole is None else float(pole))
        self.shape_pole[name] = pole
        self.shape_node[name] = node
        return pole

    def quantise(self, raw, battery_raws):
        """The SHARED quantiser bound to this world's threshold (prereg Sec2):
        standardise `raw` against its OWN battery, then map to the pole with the
        SAME threshold both modalities use."""
        return quantise(raw, battery_raws, threshold=self.threshold)

    # ---- emit (read the qualia-space geometry) ----------------------------
    def sharpness_coordinate(self, node):
        """READ the produced `(phenomenal:sharpness, "field", k)` coordinate off
        `concept_signature` (glass-box). Returns k in {-1, +1} or None (absent =>
        mid). NO Python re-derives it -- it is the graph's own signature."""
        for (dim, pred, val) in concept_signature(self.s, node):
            if dim == _AXIS and pred == "field":
                return int(val)
        return None

    def form_coordinate(self, name):
        return self.sharpness_coordinate(self.form_node[name])

    def shape_coordinate(self, name):
        return self.sharpness_coordinate(self.shape_node[name])

    def shares_coordinate(self, form_name, shape_name):
        """Do the FORM and the SHAPE SHARE the phenomenal:sharpness coordinate?
        READ from the concept_signature INTERSECTION -- the crossmodal felt
        correspondence is a shared coordinate in the qualia space, NOT a scalar
        compared in Python. Returns True iff the intersection of the two
        signatures contains a `phenomenal:sharpness` field coordinate."""
        sig_f = concept_signature(self.s, self.form_node[form_name])
        sig_s = concept_signature(self.s, self.shape_node[shape_name])
        shared = sig_f & sig_s
        return any(dim == _AXIS and pred == "field" for (dim, pred, _v) in shared)

    def analogy_nearness(self, form_name, order_n=None, min_score=1):
        """Run `find_analogies` with the FORM concept's field (bk_forms) as the
        SOURCE against the SHAPES field (bk_shapes): return {shape_name: rank_dict}
        for every emitted analogy whose source is `form_name`. The MATCH-pole shape
        should appear (aligned on phenomenal:sharpness); the opposite-pole shape
        should NOT. Read from the graph fixpoint, never scored in Python."""
        results = find_analogies(self.s, "bk_forms", ["bk_shapes"],
                                 order_n=order_n, min_score=min_score)
        out = {}
        for i, r in enumerate(results):
            if r["source_concept"] != form_name:
                continue
            out[r["target_concept"]] = dict(
                rank=i,
                aligned_dimensions=r["aligned_dimensions"],
                struct_shared=r["struct_shared"],
                order_n=r["order_n"])
        return out

    def analogy_ranks_matching_above_opposite(self, form_name, match_shape,
                                              opposite_shape):
        """Does the MATCHING-pole shape rank ABOVE (or is present while absent) the
        OPPOSITE-pole shape in find_analogies with `form_name` as query? Returns a
        dict with both entries + the verdict (present-and-aligned-on-sharpness for
        the match, absent-or-lower for the opposite). Read from the graph."""
        near = self.analogy_nearness(form_name)
        m = near.get(match_shape)
        o = near.get(opposite_shape)
        m_ok = bool(m is not None and _AXIS in m["aligned_dimensions"])
        # matching ranks above opposite when the opposite is ABSENT, or present
        # but at a strictly worse (higher index) rank.
        if o is None:
            ranks_above = m_ok
        else:
            ranks_above = bool(m_ok and m["rank"] < o["rank"])
        return dict(match=m, opposite=o, match_aligned_on_sharpness=m_ok,
                    matching_ranks_above_opposite=ranks_above)

    def match(self, form_name, shape_name):
        """The crossmodal correspondence verdict for a (FORM, SHAPE) cell, READ
        entirely from the qualia-space geometry:
          * `shares_coordinate` -- the concept_signature INTERSECTION contains the
            phenomenal:sharpness coordinate;
          * `analogy` -- the find_analogies emission for this pair (aligned on
            phenomenal:sharpness) if any.
        Returns {shares_coordinate, form_pole, shape_pole, analogy}. NO Python
        compares the raw scalars to decide the match."""
        near = self.analogy_nearness(form_name)
        return dict(
            form=form_name, shape=shape_name,
            form_pole=self.form_coordinate(form_name),
            shape_pole=self.shape_coordinate(shape_name),
            shares_coordinate=self.shares_coordinate(form_name, shape_name),
            analogy=near.get(shape_name))

    # ---- glass-box read ---------------------------------------------------
    def read(self):
        """One snapshot of every derived scalar + produced pole + coordinate, for
        the glass-box dump."""
        return dict(
            threshold=self.threshold,
            forms={n: dict(raw=round(self.form_raw[n], 6),
                           pole=self.form_pole[n],
                           coordinate=self.form_coordinate(n))
                   for n in self.form_node},
            shapes={n: dict(raw=round(self.shape_raw[n], 6),
                            pole=self.shape_pole[n],
                            coordinate=self.shape_coordinate(n))
                    for n in self.shape_node})


# --------------------------------------------------------------------------- #
#  THE ANALYTIC ORACLE (pure arithmetic over the extractor outputs, prereg Sec4)
#  -- used ONLY to CHECK the graph's produced shared-coordinate grid, never to
#  drive it.
# --------------------------------------------------------------------------- #
def oracle_pole(raw, battery_raws, *, threshold=POLE_THRESHOLD):
    """The pre-registered pole a derived scalar maps to (prereg Sec4): the SAME
    standardise-then-threshold the world uses, expressed as pure arithmetic."""
    return quantise(raw, battery_raws, threshold=threshold)


def oracle_match(form_raw, form_battery, shape_raw, shape_battery_raws,
                 *, threshold=POLE_THRESHOLD):
    """The pre-registered crossmodal correspondence (prereg Sec4): a FORM and a
    SHAPE SHARE the phenomenal:sharpness coordinate IFF both quantise to the SAME
    nonzero pole. Pure arithmetic ORACLE."""
    kf = oracle_pole(form_raw, form_battery, threshold=threshold)
    ks = oracle_pole(shape_raw, shape_battery_raws, threshold=threshold)
    return (kf is not None) and (kf == ks)


__all__ = [
    "BoubaKikiWorld", "PHONEME_FEATURES", "FORM_BATTERY", "shape_battery",
    "phonetic_sharpness", "geometric_sharpness", "quantise", "quantise_z",
    "standardise", "oracle_pole", "oracle_match",
    "QUANTUM", "HALF_WIDTH", "POLE_THRESHOLD",
]
