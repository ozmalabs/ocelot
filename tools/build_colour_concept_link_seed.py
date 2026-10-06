"""Emit seeds/colour_concept_link.json (Mary's Room stage 4 fix: the CONCEPT link).

Links a post-exposure perceived ColourProperty (colour_property) to Mary's
PRE-EXPOSURE research concepts: the four frozen hue4 classes of the broad study
(red/purple, yellow, green, blue). Every decision is a graph rule; this script
only writes JSON and compiles DATA. Run:

    PYTHONPATH=. python tools/build_colour_concept_link_seed.py

DATA COMPILATION (at generation time; not an agent decision). Mary's research
only:
  * the four frozen unique-hue anchor stimuli of results/marys_room_broad_armA.json
    'anchors' (defined in scripts/marys_room_broad_theory.py build_anchors):
    blue/green/yellow = CIE 2006 2-deg LMS interpolated linearly between the
    10 nm training wavelengths bracketing the Kuehni (2004) loci 478 / 514.8 /
    576.3 nm; red/purple = the 400 nm + 700 nm line-energy mixture whose
    E-referenced complementary dominant wavelength is 495.2 nm. The generator
    RECOMPUTES each anchor's LMS from domains.spectral_forward.load_lms and the
    recorded definition and asserts it equals the frozen JSON value;
  * equal-energy white X_E = spectral_forward.lms_from_spd(illuminant('E'));
  * WHITE-NORMALISED anchor X' = X / X_E (X in L, M, S);
  * prototype = unit direction of (L' - M', S' - 0.5 (L' + M')).
  Written as ColourConcept{name, proto_rg, proto_by, anchor_L/M/S, white_L/M/S,
  proto_angle_deg} nodes under ColourConceptParams -has_colour_concept->.

RULES (ColourConceptParams.enabled):
  cc_link        per ColourProperty CP with every pa_ch >= 1: descriptor
                 r_ch = p_ch / pa_ch (anchor-relative = white-normalised, the
                 anchor being the scene's per-channel max, i.e. its white);
                 d = (r_L - r_M, r_S - 0.5 (r_L + r_M)); angle to concept K =
                 Atan2(|d x u_K|, d . u_K) in [0, pi]; CP -categorised_as-> the
                 Argmin concept, with concept_angle_deg and concept_margin_deg
                 (second-smallest angle minus smallest) on CP.
  cc_achromatic  d exactly (0, 0) (e.g. the anchor surface itself): REFUSED,
                 concept_status 'achromatic', no link.
  cc_tied        margin exactly 0: REFUSED, concept_status 'tied', no link.
  cc_no_anchor   some pa_ch < 1 (the descriptor is undefined): REFUSED.
The link quality on real post-exposure properties measures the Mary gap: the
research prototypes are CIE-observer directions, the properties are this eye's
Gaussian-sensor catch ratios. No threshold, no tuned constant (sec 13): the
only literals are 0, 1/2 (the opponent definition) and 180/pi (unit change).

Flag ColourConceptParams.enabled, OFF by default (sec 9). Manifest
latency_class hard_realtime. Depends on colour_property.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import spectral_forward as sf  # noqa: E402  (numpy only; no engine)

OUT = os.path.join(ROOT, "seeds", "colour_concept_link.json")
ARMA = os.path.join(ROOT, "results", "marys_room_broad_armA.json")
HUE4 = ("red/purple", "yellow", "green", "blue")   # frozen hue4 classes


# --------------------------------------------------------------- data compile
def _lmsbar(wl_nm):
    return sf.load_lms("2deg", 1)[sf._index(wl_nm, 1)]


def _line_energy_lms(recipe):
    """LMS of a recipe of the broad theory's kinds 'line_energy' / 'mixture'."""
    if recipe["kind"] == "line_energy":
        return float(recipe["energy"]) * _lmsbar(recipe["wavelength_nm"])
    if recipe["kind"] == "mixture":
        return sum(float(c["weight"]) * _line_energy_lms(c["recipe"])
                   for c in recipe["components"])
    raise ValueError(recipe["kind"])


def anchor_lms(name, a):
    """Recompute a frozen anchor's LMS from its recorded definition."""
    if "recipe" in a:
        return _line_energy_lms(a["recipe"]), np.array(a["lms"], dtype=float)
    lo, hi = a["train_bracket_nm"]
    x0, x1 = _lmsbar(lo), _lmsbar(hi)
    lms = x0 + (a["locus_nm"] - lo) / float(hi - lo) * (x1 - x0)
    return lms, np.array(a["lms_per_unit_energy"], dtype=float)


def compile_concepts():
    with open(ARMA) as f:
        anchors = json.load(f)["anchors"]
    assert set(anchors) == set(HUE4), sorted(anchors)
    white = sf.lms_from_spd(sf.illuminant("E", 1))
    out = []
    for name in HUE4:
        lms, frozen = anchor_lms(name, anchors[name])
        assert np.allclose(lms, frozen, rtol=1e-12, atol=0.0), (name, lms, frozen)
        Ln, Mn, Sn = (frozen / white).tolist()
        rg, by = Ln - Mn, Sn - 0.5 * (Ln + Mn)
        norm = math.hypot(rg, by)
        out.append({
            "name": name,
            "proto_rg": rg / norm, "proto_by": by / norm,
            "proto_angle_deg": math.degrees(math.atan2(by, rg)),
            "anchor_L": float(frozen[0]), "anchor_M": float(frozen[1]),
            "anchor_S": float(frozen[2]),
            "white_L": float(white[0]), "white_M": float(white[1]),
            "white_S": float(white[2]),
            "source": "results/marys_room_broad_armA.json anchors['%s']" % name,
        })
    return out


CONCEPTS = compile_concepts()


# --------------------------------------------------------------- AST helpers
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Ne(a, b): return Not(Eq(a, b))
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Abs(x): return {"type": "Abs", "arg": x}
def Atan2(y, x): return {"type": "Atan2", "y": y, "x": x}
def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
def Nbrs(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def MaxOver(src, var, val, default=None):
    t = {"type": "MaxOver", "source": src, "var_name": var, "value": val}
    if default is not None:
        t["default"] = default
    return t
def MinOver(src, var, val, default=None):
    t = {"type": "MinOver", "source": src, "var_name": var, "value": val}
    if default is not None:
        t["default"] = default
    return t
def Argmin(src, var, val):
    return {"type": "Argmin", "source": src, "var_name": var, "value": val}
def T(term): return {"__term__": term}


def seta(var, key, value):
    return ["set_attr", var, key, value]


PARAMS = "ColourConceptParams"
CONCEPT = "ColourConcept"
CH = ("L", "M", "S")
HALF = L(0.5)
DEG = L(180.0 / math.pi)
ENABLED = Gt(MaxOver(NodesOfType(PARAMS), "ccp_", A("ccp_", "enabled"), L(0.0)), HALF)
LIB = Nbrs("cpp", "has_colour_concept")


def r(ch):
    return Div(A("CP", "p" + ch), A("CP", "pa" + ch))


D_RG = Minus(r("L"), r("M"))
D_BY = Minus(r("S"), Times(HALF, Plus(r("L"), r("M"))))


def angle(k):
    """Angle in [0, pi] between d and concept k's unit prototype."""
    cross = Minus(Times(D_RG, A(k, "proto_by")), Times(D_BY, A(k, "proto_rg")))
    dot = Plus(Times(D_RG, A(k, "proto_rg")), Times(D_BY, A(k, "proto_by")))
    return Atan2(Abs(cross), dot)


BEST = Argmin(LIB, "kb_", angle("kb_"))
BEST_ANGLE = MinOver(LIB, "km_", angle("km_"))
SECOND_ANGLE = MinOver(Filter(LIB, "ko_", Not(Eq(V("ko_"), BEST))), "ko2_", angle("ko2_"))
MARGIN = Minus(SECOND_ANGLE, BEST_ANGLE)
ANCHOR_OK = And(*[Gte(A("CP", "pa" + ch), L(1.0)) for ch in CH])
ACHROMATIC = And(Eq(D_RG, L(0.0)), Eq(D_BY, L(0.0)))
UNDECIDED = Eq(A("CP", "concept_status"), L(None))
MATCH = [["P", "has_colour_property", "CP"]]

RULES = [
    {
        "name": "cc_link",
        "comment": "Pre-exposure research applied to a post-exposure property: "
                   "CP -categorised_as-> the ColourConcept with the smallest angle "
                   "between CP's white-normalised opponent descriptor d = (r_L - "
                   "r_M, r_S - (r_L + r_M)/2), r = p/pa, and the concept's unit "
                   "prototype. Records the angle and the margin to the runner-up.",
        "match": MATCH + [["cpp", "has_colour_concept", "K"]],
        "where": And(ENABLED, UNDECIDED, ANCHOR_OK, Not(ACHROMATIC),
                     Eq(V("K"), BEST), Gt(MARGIN, L(0.0))),
        "effects": [
            ["add_edge", "CP", "categorised_as", "K"],
            seta("CP", "concept", T(A("K", "name"))),
            seta("CP", "concept_status", "categorised"),
            seta("CP", "concept_rg", T(D_RG)),
            seta("CP", "concept_by", T(D_BY)),
            seta("CP", "concept_angle_deg", T(Times(angle("K"), DEG))),
            seta("CP", "concept_margin_deg", T(Times(MARGIN, DEG))),
        ],
    },
    {
        "name": "cc_achromatic",
        "comment": "REFUSAL: a descriptor exactly at (0, 0) (r_L = r_M = r_S, e.g. "
                   "the anchor surface) has no hue direction; no link.",
        "match": MATCH,
        "where": And(ENABLED, UNDECIDED, ANCHOR_OK, ACHROMATIC),
        "effects": [seta("CP", "concept_status", "achromatic"),
                    seta("CP", "concept_rg", T(D_RG)),
                    seta("CP", "concept_by", T(D_BY))],
    },
    {
        "name": "cc_tied",
        "comment": "REFUSAL: two concepts exactly equidistant (margin 0); no link, "
                   "no tie-break guess.",
        "match": MATCH,
        "where": And(ENABLED, UNDECIDED, ANCHOR_OK, Not(ACHROMATIC),
                     Not(Gt(MARGIN, L(0.0)))),
        "effects": [seta("CP", "concept_status", "tied"),
                    seta("CP", "concept_rg", T(D_RG)),
                    seta("CP", "concept_by", T(D_BY))],
    },
    {
        "name": "cc_no_anchor",
        "comment": "REFUSAL: some anchor channel pa < 1 -- the anchor-relative "
                   "descriptor is undefined.",
        "match": MATCH,
        "where": And(ENABLED, UNDECIDED, Not(ANCHOR_OK)),
        "effects": [seta("CP", "concept_status", "no_anchor")],
    },
]

DESCRIPTION = (
    "Mary's Room stage 4 fix (concept link): ColourProperty -categorised_as-> "
    "one of Mary's four pre-exposure research concepts (frozen hue4 classes "
    "red/purple, yellow, green, blue). ColourConcept prototypes are DATA "
    "compiled at generation time from Mary's research only: the frozen "
    "unique-hue anchor stimuli of results/marys_room_broad_armA.json (recomputed "
    "from CIE 2006 2-deg LMS, spectral_forward.load_lms, and asserted equal), "
    "white-normalised X' = X/X_E by the CIE LMS of equal-energy white, "
    "prototype = unit (L'-M', S'-(L'+M')/2). Rule cc_link: descriptor r_ch = "
    "p_ch/pa_ch (anchor-relative = white-normalised; the anchor is the scene "
    "max/white), d = (r_L-r_M, r_S-(r_L+r_M)/2); angle to each prototype = "
    "Atan2(|d x u|, d.u); link the Argmin, with concept_angle_deg and "
    "concept_margin_deg on the property. Refusals (concept_status): "
    "'achromatic' (d exactly (0,0)), 'tied' (margin 0), 'no_anchor' (some "
    "pa < 1). No tuned constant. The link quality measures the Mary gap "
    "(CIE-observer research vs this eye's Gaussian catches). Flag "
    "ColourConceptParams.enabled, OFF by default (sec 9). See "
    "tools/build_colour_concept_link_seed.py."
)

NODES = [{"local_id": 0, "type": PARAMS, "attrs": {"enabled": 0.0}}]
EDGES = [{"src": {"role": "agent_root"}, "type": "has_colour_concept_params",
          "tgt": {"local": 0}, "attrs": {}}]
for i, c in enumerate(CONCEPTS, start=1):
    NODES.append({"local_id": i, "type": CONCEPT, "attrs": dict(c)})
    EDGES.append({"src": {"local": 0}, "type": "has_colour_concept",
                  "tgt": {"local": i}, "attrs": {}})

MANIFEST = {
    "id": "colour_concept_link",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["colour_property"],
    "latency_class": "hard_realtime",
    "description": DESCRIPTION,
    "microtheory": {
        "name": "colour_concept_link",
        "description": "perceived colour property -> Mary's research hue concept",
    },
    "nodes": NODES,
    "edges": EDGES,
    "productions": [],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
        f.write("\n")
    print(f"wrote {OUT} with {len(RULES)} rules and {len(CONCEPTS)} concepts")
    for c in CONCEPTS:
        print(f"  {c['name']:10s} proto=({c['proto_rg']:+.4f}, {c['proto_by']:+.4f}) "
              f"angle={c['proto_angle_deg']:+.2f} deg")
