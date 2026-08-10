#!/usr/bin/env python3
"""Emit seeds/vision_lighting_l4.json — ADVANCED LIGHTING RUNG L4:
SHADOW vs REFLECTANCE EDGES as pure graph data (NO new Rust).

See VISION_LIGHTING_L4_PREREG.md.

THE PREMISE (L2 MEASURED IT, and it is the gap this rung closes)
----------------------------------------------------------------
L2 found that a shadow EDGE is NOT refused by a LOCAL mechanism: a step
function is piecewise constant, so every locale except the two straddling the
step sees a single gain and is discounted correctly (10/12 correct, 0 false, at
every jump). A discontinuity is out-of-class for a GLOBAL mechanism and
perfectly IN-class for a LOCAL one.

BUT: L2 recovers identities on both sides of the edge WITHOUT EVER KNOWING AN
EDGE EXISTS, let alone that it was a shadow. ATTRIBUTION was untouched. That is
exactly what L4 does.

THE CUE, AND WHERE IT ALREADY LIVES IN THIS TREE
-------------------------------------------------
An ILLUMINANT edge scales every channel by ONE factor and therefore PRESERVES
chromatic ratios; a REFLECTANCE edge changes the ratios themselves.

Written out, this is L2's OWN `_slowvar_clause` with the quantifier moved from
SPACE to WAVELENGTH:

  L2 (build_vision_lighting_l2.py:357) -- do two LOCALES agree on one gain?
      | a_i * ra_j  -  ra_i * a_j |  <=  LS*ra_j + HS*ra_j + HS*ra_i

  L4 (here) -- do two CHANNELS agree on one gain across an adjacency?
      | c_QX * c_RY - c_RX * c_QY |  <=  HS*(c_QX + c_RY + c_RX + c_QY) + LS + HS

Same operator, same cross-multiplication (so no ratio is ever divided into a
float -- the frame/continuum invariant), same "two roundings" envelope. The pair
of indices is (locale, locale) there and (channel, channel) here.

L4 NEEDS STRICTLY WEAKER ASSUMPTIONS THAN L2 AND L3
----------------------------------------------------
NO reference frame, NO compares_to, NO SurfaceIdentity codebook, NO locale
pairing, NO spatial registration, and NEITHER L2's per-locale gain NOR L3's
pooled scene estimate. The discrimination is INTRA-FRAME and purely LOCAL. L4 is
not built on top of L2/L3 -- it sits beside them. (It therefore also cannot
inherit their identity machinery; see the BOUNDS.)

THE ENVELOPE FALLS OUT (sec 13) -- NO NEW CONSTANT
---------------------------------------------------
Under the illuminant hypothesis the two sides are the SAME material under gains
g_R, g_Q. Write u = g_R*r_X, v = g_R*r_Y, g = g_Q/g_R, so the TRUE cone values
are (u, v) and (g*u, g*v), and each observation carries its own rounding
|e| <= HS:

  D_XY = C_QX*C_RY - C_RX*C_QY
       = (gu+a)(v+b) - (u+c)(gv+d)
       = gu*b + v*a - u*d - gv*c + ab - cd

  |D_XY| <= HS*(gu + v + u + gv) + 2*HS*HS
         <= HS*(C_QX + C_RY + C_RX + C_QY) + 4*HS*HS + 2*HS*HS   [true->observed]
          = HS*(C_QX + C_RY + C_RX + C_QY) + LATTICE_STEP + HALF_STEP

Every term is a rounding the observation ALREADY carries. The seed's entire
numeric literal set is {0.0, 0.5, 1.0} -- a STRICT SUBSET of L2's and L3's
{0.0, 0.5, 1.0, 1.0e9} (L4 has no codebook, so it needs no empty-population
sentinel).

The EDGE-EXISTENCE test falls out the same way: a change within one lattice step
is indistinguishable from rounding, so it is not an edge.

THE RULES (every decision is a RULE -- CLAUDE.md sec 0)
-------------------------------------------------------
  l4_classify_illuminant   / _v   ratios PRESERVED across a real edge => a
                                  SHADOW / illuminant discontinuity.
  l4_classify_reflectance  / _v   ratios CHANGED across a real edge => a
                                  MATERIAL boundary.
  l4_flat                  / _v   below one lattice step => NOT an edge. A
                                  POSITIVE datum (sec 1.1 clause 4): "refused"
                                  and "never ran" must be distinguishable.
  l4_flood                        THE MERGE, and the tie to border-ownership:
                                  bo_label's min-flood with Eq(val,val) replaced
                                  by the ratio-preserving predicate. At the
                                  run_rules fixpoint, cells joined through
                                  ILLUMINANT edges and FLAT adjacencies share a
                                  label; cells across a REFLECTANCE edge do not.
                                  So a shadow boundary CANNOT become a component
                                  boundary, while a material boundary MUST.

Horizontal verdicts are written on the LEFT cell (l4_kind), vertical on the
UPPER cell (l4_kindv) -- unambiguous, because each cell has exactly ONE right
and ONE lower neighbour. The FLOOD is fully 4-connected.

BORDER-OWNERSHIP IS NOT EDITED AND NOT DEPENDED ON. The runner shows the
committed, unmodified `vision_border_ownership` seed two DIFFERENT val fields
(raw luminance vs l4_val) in two SEPARATE graphs -- separate because that seed's
aggregates are global NodesOfType("Cell") grabs. L4 changes what border-ownership
is SHOWN, never how it decides.

Flag-gated on LightingL4Params.lighting_l4, OFF by default (sec 9), read
ABSENCE-TOLERANTLY via MaxOver(..., default 0) and NEVER via PickUnique.

NO new Rust: reuses Times/Minus/Abs/Plus/Max/Lte/Gt/Lt/Eq/And/Not/Exists/
Filter/Argmin/MaxOver/Neighbours/NodesOfType/Div + run_rules.

BOUNDED: SINGLE-ILLUMINANT, NEUTRAL-SHADOW edge attribution. CHROMATIC shadows
are NOT handled (measured as a predicted failure); PROPORTIONAL materials are
IRREDUCIBLY ambiguous to any local ratio cue (measured); MULTI-ILLUMINANT scenes
are unsolved; L3's "anchor of the anchor" is untouched (L4 uses no anchor at
all); reflectance is GIVEN at the abstract cone-triple grain; adjacency is
GIVEN, not grown; the ratio-preserving relation is NOT transitive and l4_flood
takes its transitive closure. L4 CLASSIFIES EDGES; IT DOES NOT RECOVER
REFLECTANCE -- no L2/L3 arm consumes an L4 attribute.

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_lighting_l4.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms) -----------------------------------
# THE KNOWN TRAP (VISION_LIGHTING_RESULTS.md's central finding, and process rule
# 4): some Terms take an `items` LIST and some take `a`/`b`. Writing a LIST term
# in a/b form parses to an EMPTY operand list -- and AN EMPTY PRODUCT IS 1 --
# which turned T3's invariant into Eq(1,1): a UNIVERSAL CONTAINER with a
# FLAWLESS invariance score. Here the same defect would collapse every D_XY to
# |1 - 1| = 0 and call EVERY adjacency a shadow. Every constructor below states
# its form, and the gate is POSITIVE-CONTROLLED against exactly this defect.
def V(name):            return {"type": "Var", "name": name}
def Lit(v):             return {"type": "Lit", "value": v}
def A(node, key):       return {"type": "Attr", "node": node, "key": key}
def Gt(a, b):           return {"type": "Gt", "a": a, "b": b}          # a/b
def Lt(a, b):           return {"type": "Lt", "a": a, "b": b}          # a/b
def Lte(a, b):          return {"type": "Lte", "a": a, "b": b}         # a/b
def Eq(a, b):           return {"type": "Eq", "a": a, "b": b}          # a/b
def Minus(a, b):        return {"type": "Minus", "a": a, "b": b}       # a/b
def Div(a, b):          return {"type": "Div", "a": a, "b": b}         # a/b
def Abs(x):             return {"type": "Abs", "arg": x}               # arg
def Not(x):             return {"type": "Not", "arg": x}               # arg


def Times(items):
    """`items` LIST (jsonio.rs:1274). NEVER a/b -- that is the EMPTY-PRODUCT trap."""
    return {"type": "Times", "items": list(items)}


def Plus(items):
    """`items` LIST (jsonio.rs:1269). NEVER a/b -- an empty sum is 0."""
    return {"type": "Plus", "items": list(items)}


def Max(items):
    """`items` LIST (jsonio.rs:1403). NEVER a/b."""
    return {"type": "Max", "items": list(items)}


def And(items):         return {"type": "And", "items": list(items)}
def NodesOf(t):         return {"type": "NodesOfType", "node_type": t}


def Nbrs(node, et):
    return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}


def Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}


def Exists(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}


def MaxOver(src, var, value, default=None):
    t = {"type": "MaxOver", "source": src, "var_name": var, "value": value}
    if default is not None:
        t["default"] = default
    return t


def Argmin(src, var, value, default=None):
    t = {"type": "Argmin", "source": src, "var_name": var, "value": value}
    if default is not None:
        t["default"] = default
    return t


def IfThenElse(cond, then, other):
    """`cond`/`then`/`other` (jsonio.rs:1405)."""
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def term(x):            return {"__term__": x}


CH = ["L", "M", "S"]
# THE THREE CHANNEL-PAIRS. Not a choice: with three channels there are exactly
# three independent ratio constraints, and all three are tested.
PAIRS = [("L", "M"), ("L", "S"), ("M", "S")]

# THE LATTICE STEP -- L1's OWN falls-out step, INHERITED UNCHANGED through L2 and
# L3 and NOT re-derived, NOT re-tuned. Here it does two jobs, both of which fall
# out of the same fact (the observation is stepped): it is the threshold below
# which a change IS NOT AN EDGE, and it is one of the two second-order terms in
# the ratio envelope.
LATTICE_STEP = 1.0

# HALF a lattice step -- the maximum displacement a single round() introduces.
HALF_STEP = 0.5


def ENABLED():
    """The L4 flag, read ABSENCE-TOLERANTLY.

    MaxOver with an explicit default returns 0.0 when NO LightingL4Params node
    exists, so the seed is inert in a graph that never loaded it. Deliberately
    NOT PickUnique on a params node (process rule 3): PickUnique returns None on
    an absent node, which silently changes behaviour instead of reading as OFF.
    """
    return Gt(MaxOver(NodesOf("LightingL4Params"), "lp",
                      A(V("lp"), "lighting_l4"), default=Lit(0.0)),
              Lit(0.5))


# ---------------------------------------------------------------------------
# THE TWO PREDICATES. Everything else in this seed is scaffolding around them.
# ---------------------------------------------------------------------------
def _D(R, Q, X, Y):
    """|c_QX * c_RY - c_RX * c_QY| -- the CROSS-MULTIPLIED ratio deviation.

    Cross-multiplied, never divided: a ratio divided into a float would put a
    real number where the frame's own stepped coordinates live. The comparison
    that follows is a CROSS-FRAME statement (does one gain explain both sides?),
    which is exactly where a real-valued quantity is admissible.
    """
    return Abs(Minus(Times([A(Q, "c" + X), A(R, "c" + Y)]),
                     Times([A(R, "c" + X), A(Q, "c" + Y)])))


def _envelope(R, Q, X, Y):
    """HS*(c_QX + c_RY + c_RX + c_QY) + LS + HS -- the module docstring's bound.

    Four half-steps, one per observation entering the cross-product, plus the
    second-order term the true->observed substitution costs. NOTHING IS TUNED:
    every term is a rounding the observation already carries.
    """
    return Plus([Times([Lit(HALF_STEP), A(Q, "c" + X)]),
                 Times([Lit(HALF_STEP), A(R, "c" + Y)]),
                 Times([Lit(HALF_STEP), A(R, "c" + X)]),
                 Times([Lit(HALF_STEP), A(Q, "c" + Y)]),
                 Lit(LATTICE_STEP),
                 Lit(HALF_STEP)])


def _PRESERVED(R, Q):
    """ONE GAIN EXPLAINS BOTH SIDES on ALL THREE channel-pairs.

    This is the whole cue. It is TRUE for a neutral illuminant change (a shadow)
    and for no change at all; it is FALSE when the chromatic ratios themselves
    move (a material boundary). Its two declared failure modes are measured
    rather than hidden: a CHROMATIC shadow reads FALSE (the cue is simply wrong
    there), and two PROPORTIONAL materials read TRUE (irreducibly ambiguous to
    any local ratio cue).
    """
    return And([Lte(_D(R, Q, X, Y), _envelope(R, Q, X, Y)) for X, Y in PAIRS])


def _IS_EDGE(R, Q):
    """The observation changes by MORE THAN THE LATTICE RECORDS on some channel.

    Below one lattice step a change is indistinguishable from rounding, so it is
    NOT an edge -- which is why a shallow penumbra is correctly not one edge but
    a sequence of sub-edges with a sub-lattice tail.
    """
    return Gt(Max([Abs(Minus(A(Q, "c" + ch), A(R, "c" + ch))) for ch in CH]),
              Lit(LATTICE_STEP))


def _MARGIN(R, Q):
    """max over channel-pairs of D_XY / envelope_XY -- REPORT ONLY, gates nothing.

    Process rule 7: a bound whose occupancy is never reported can be a bound that
    never binds (rung L1b measured exactly that). This makes L4's bound auditable
    from its own results -- if illuminant edges sat at margin 0 and reflectance
    edges at 0.001, the classes would be separated by something other than the
    bound, and the number would say so.
    """
    return Max([Div(_D(R, Q, X, Y), _envelope(R, Q, X, Y)) for X, Y in PAIRS])


def _NPAIRS_INSIDE(R, Q):
    """How many of the three channel-pairs lie INSIDE the envelope. REPORT ONLY.

    The literal COUNT process rule 7 asks for, computed IN-GRAPH. 3 =>
    illuminant (all three constraints satisfied); 0..2 => reflectance, and WHICH
    number says how far from the cue the edge is. A build in which this is 3 for
    EVERY adjacency is the empty-product defect; a build in which it is 0 for
    every adjacency is refuse-everything. Both are positive-controlled.
    """
    return Plus([IfThenElse(Lte(_D(R, Q, X, Y), _envelope(R, Q, X, Y)),
                            Lit(1.0), Lit(0.0))
                 for X, Y in PAIRS])


# ---------------------------------------------------------------------------
# THE CLASSIFICATION RULES. `axis` is HORIZONTAL (left cell) or VERTICAL (upper).
# ---------------------------------------------------------------------------
def _axis_guards(axis):
    """R is the LEFT (horizontal) or UPPER (vertical) member of the adjacency.

    Each cell has exactly ONE right neighbour and ONE lower neighbour, so a
    per-cell verdict attribute is unambiguous. This is a canonical ORIENTATION of
    an undirected adjacency, not a decision about the scene.
    """
    if axis == "h":
        return [Eq(A(V("R"), "crow"), A(V("Q"), "crow")),
                Lt(A(V("R"), "ccol"), A(V("Q"), "ccol"))]
    return [Eq(A(V("R"), "ccol"), A(V("Q"), "ccol")),
            Lt(A(V("R"), "crow"), A(V("Q"), "crow"))]


def _kind_key(axis):
    return "l4_kind" if axis == "h" else "l4_kindv"


def _classify_rule(axis, name, label, extra_where, comment):
    k = _kind_key(axis)
    suffix = "" if axis == "h" else "v"
    return {
        "name": name,
        "comment": comment,
        "match": [["fld", "has_l4cell", "R"], ["R", "l4_neighbour", "Q"]],
        "where": And([ENABLED(),
                      Lt(A(V("R"), k + "_done"), Lit(0.5))]
                     + _axis_guards(axis)
                     + extra_where),
        "effects": [
            ["set_attr", "R", k, term(Lit(label))],
            ["set_attr", "R", k + "_done", term(Lit(1.0))],
            ["set_attr", "R", "l4_margin" + suffix,
             term(_MARGIN(V("R"), V("Q")))],
            ["set_attr", "R", "l4_npairs" + suffix,
             term(_NPAIRS_INSIDE(V("R"), V("Q")))],
        ],
    }


L4_ILLUM_H = _classify_rule(
    "h", "l4_classify_illuminant", "l4_illuminant",
    [_IS_EDGE(V("R"), V("Q")), _PRESERVED(V("R"), V("Q"))],
    ("THE HEADLINE DECISION. A real edge (the observation changes by more than "
     "one lattice step on some channel) across which ONE GAIN EXPLAINS ALL THREE "
     "CHANNEL-PAIRS is an ILLUMINANT discontinuity -- a cast shadow, not a "
     "material boundary. L2 measured that a LOCAL mechanism recovers identities "
     "on both sides of such an edge WITHOUT KNOWING IT IS THERE; this rule is "
     "the graph knowing. The envelope is NOT a threshold anyone chose: it is the "
     "sum of the four half-step roundings the four observations entering the "
     "cross-product carry, plus the second-order term the true->observed "
     "substitution costs. Cross-multiplied so no ratio is divided into a float. "
     "l4_margin RECORDS the bound's occupancy so its discriminativeness is "
     "reported rather than assumed (rung L1b's lesson). Flag-gated, OFF by "
     "default (sec 9)."))

L4_REFL_H = _classify_rule(
    "h", "l4_classify_reflectance", "l4_reflectance",
    [_IS_EDGE(V("R"), V("Q")), Not(_PRESERVED(V("R"), V("Q")))],
    ("THE DISCRIMINATION THAT MAKES THE HEADLINE NON-TRIVIAL. A real edge across "
     "which NO single gain explains all three channel-pairs is a MATERIAL "
     "boundary. Without this rule the seed could call everything a shadow and "
     "score a perfect headline -- which is the refuse-everything disease in its "
     "mirror form, and is exactly what the pre-registered Times empty-product "
     "positive control injects. It is the EXACT complement of "
     "l4_classify_illuminant's predicate, so the two rules PARTITION the real "
     "edges. Flag-gated, OFF by default (sec 9)."))

L4_FLAT_H = _classify_rule(
    "h", "l4_flat", "l4_flat",
    [Not(_IS_EDGE(V("R"), V("Q")))],
    ("NOT AN EDGE -- as a POSITIVE datum (sec 1.1 clause 4). A change within one "
     "lattice step is indistinguishable from rounding. Without this rule an "
     "unclassified adjacency would be indistinguishable from a rule that never "
     "fired, and a silent classifier scores a FLAWLESS noise floor while "
     "measuring nothing. With it, the floor arm can report how many adjacencies "
     "got ANY classification and so demonstrate the arm is ALIVE. Flag-gated, "
     "OFF by default (sec 9)."))

L4_ILLUM_V = _classify_rule(
    "v", "l4_classify_illuminant_v", "l4_illuminant",
    [_IS_EDGE(V("R"), V("Q")), _PRESERVED(V("R"), V("Q"))],
    "l4_classify_illuminant on the VERTICAL adjacency (verdict on the UPPER "
    "cell). Present so a 2-D shadow boundary is classified all the way round, "
    "not only on its left and right sides.")

L4_REFL_V = _classify_rule(
    "v", "l4_classify_reflectance_v", "l4_reflectance",
    [_IS_EDGE(V("R"), V("Q")), Not(_PRESERVED(V("R"), V("Q")))],
    "l4_classify_reflectance on the VERTICAL adjacency (verdict on the UPPER "
    "cell).")

L4_FLAT_V = _classify_rule(
    "v", "l4_flat_v", "l4_flat",
    [Not(_IS_EDGE(V("R"), V("Q")))],
    "l4_flat on the VERTICAL adjacency (verdict on the UPPER cell).")


# ---------------------------------------------------------------------------
# l4_flood -- THE MERGE. This is the rule that ties L4 to border-ownership.
# ---------------------------------------------------------------------------
L4_FLOOD = {
    "name": "l4_flood",
    "comment": (
        "THE MERGE, AND THE WHOLE POINT OF THE RUNG: a SHADOW boundary must not "
        "become an OBJECT boundary, while a MATERIAL boundary must. l4_val := the "
        "minimum l4_val among this cell's RATIO-PRESERVING 4-neighbours (init "
        "cid). Fires only when such a neighbour has a STRICTLY SMALLER l4_val, so "
        "l4_val decreases monotonically and the flood terminates; at the "
        "run_rules fixpoint every ratio-preserving connected component shares its "
        "root's cid. "
        "THIS IS bo_label's CONSTRUCTION (tools/build_vision_border_ownership.py "
        ":176) WITH Eq(val,val) REPLACED BY THE RATIO-PRESERVING PREDICATE -- the "
        "same min-flood-to-fixpoint idiom, proven O(N) per sweep under the "
        "run_rules drive. Cells joined through ILLUMINANT edges and FLAT "
        "adjacencies end up in ONE component; cells across a REFLECTANCE edge do "
        "not. Border-ownership, UNMODIFIED, then mints a ProtoObject for the "
        "material patch and NONE for the cast shadow -- because the shadow is no "
        "longer a component boundary for it to enclose. "
        "DECLARED (sec 8): the ratio-preserving relation is NOT transitive, and "
        "this flood takes its TRANSITIVE CLOSURE. A chain of individually "
        "admissible steps can merge two materials that are not ratio-preserving "
        "with each other. NOT tested here; NAMED. "
        "Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["fld", "has_l4cell", "R"]],
    "where": And([
        ENABLED(),
        Exists(Nbrs(V("R"), "l4_neighbour"), "m",
               And([Lt(A(V("m"), "l4_val"), A(V("R"), "l4_val")),
                    _PRESERVED(V("R"), V("m"))])),
    ]),
    "effects": [
        ["set_attr", "R", "l4_val",
         term(A(Argmin(Filter(Nbrs(V("R"), "l4_neighbour"), "m",
                              _PRESERVED(V("R"), V("m"))),
                       "m", A(V("m"), "l4_val")),
                "l4_val"))],
    ],
}


SEED = {
    "id": "vision_lighting_l4",
    "version": "1.0.0",
    "depends_on": [],
    "description": (
        "ADVANCED LIGHTING RUNG L4 -- SHADOW vs REFLECTANCE EDGES. L2 measured "
        "that a shadow EDGE is NOT refused by a LOCAL mechanism (10/12 correct, "
        "0 false, only the two straddling locales refused: a discontinuity is "
        "out-of-class for a GLOBAL mechanism and IN-class for a LOCAL one) -- but "
        "that identities are recovered on both sides WITHOUT THE SYSTEM EVER "
        "KNOWING AN EDGE EXISTS. L4 closes exactly that gap: it ATTRIBUTES the "
        "edge. An ILLUMINANT edge scales every channel by ONE factor and so "
        "PRESERVES chromatic ratios; a REFLECTANCE edge changes the ratios "
        "themselves. THE PREDICATE IS L2'S OWN _slowvar_clause WITH THE "
        "QUANTIFIER MOVED FROM SPACE TO WAVELENGTH -- the same cross-multiplied "
        "ratio-agreement test with the index pair (locale,locale) replaced by "
        "(channel,channel), so no ratio is ever divided into a float. "
        "l4_classify_illuminant / _reflectance PARTITION the real edges; l4_flat "
        "makes 'not an edge' a POSITIVE datum so a silent classifier cannot score "
        "a flawless floor; l4_flood is bo_label's min-flood with Eq(val,val) "
        "replaced by the ratio-preserving predicate, so cells joined through "
        "illuminant edges share a component and cells across a material boundary "
        "do not -- which is how a SHADOW BOUNDARY IS PREVENTED FROM BECOMING AN "
        "OBJECT BOUNDARY in the UNMODIFIED vision_border_ownership seed. "
        "L4's ASSUMPTIONS ARE STRICTLY WEAKER THAN L2's AND L3's: no reference "
        "frame, no compares_to, no SurfaceIdentity codebook, no locale pairing, "
        "no spatial registration, no per-locale gain and no pooled scene "
        "estimate. It sits BESIDE them, not on top. NO new Rust, NO new constant "
        "-- literal set {0.0, 0.5, 1.0}, a STRICT SUBSET of L2's and L3's; the "
        "envelope is the four half-step roundings the four observations entering "
        "the cross-product carry, and the edge threshold is L1's own falls-out "
        "ONE LATTICE STEP. BOUNDED: SINGLE-ILLUMINANT, NEUTRAL-SHADOW "
        "attribution. CHROMATIC shadows are NOT handled and PROPORTIONAL "
        "materials are IRREDUCIBLY ambiguous -- both are MEASURED as predicted "
        "failures, not hidden. MULTI-ILLUMINANT scenes unsolved; L3's 'anchor of "
        "the anchor' untouched (L4 uses no anchor); reflectance GIVEN at the "
        "cone-triple grain; adjacency GIVEN not grown; the ratio-preserving "
        "relation is NOT transitive and l4_flood takes its transitive closure. "
        "L4 CLASSIFIES EDGES; IT DOES NOT RECOVER REFLECTANCE -- no L2/L3 arm "
        "consumes an L4 attribute. Flag-gated on LightingL4Params.lighting_l4, "
        "OFF by default (sec 9 -- default 0 => byte-identical, seed inert), read "
        "ABSENCE-TOLERANTLY via MaxOver(default 0), never PickUnique. See "
        "VISION_LIGHTING_L4_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_lighting_l4_mt",
        "label": ("shadow vs reflectance: an illuminant edge preserves chromatic "
                  "ratios, so it is a discontinuity that is NOT an object boundary"),
    },
    "nodes": [
        {"local_id": 0, "type": "LightingL4Params", "attrs": {"lighting_l4": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [L4_ILLUM_H, L4_REFL_H, L4_FLAT_H,
              L4_ILLUM_V, L4_REFL_V, L4_FLAT_V,
              L4_FLOOD],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_lighting_l4.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out, "-", len(SEED["rules"]), "rules")


if __name__ == "__main__":
    main()
