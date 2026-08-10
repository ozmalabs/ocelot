#!/usr/bin/env python3
"""Emit seeds/vision_lighting_l1.json — ADVANCED LIGHTING RUNG L1:
REAL-VALUED ILLUMINANT GAINS, as pure graph data (NO new Rust).

See VISION_LIGHTING_L1_PREREG.md.

T3 (`vision_lighting`) crossed lighting-invariance for the EXACT-RENDERING
(integer-ratio) diagonal illuminant class and REFUSED real-valued gains (0/12 at
1.5/2.5/3.3/7.5 vs 12/12 at 2.0/3.0/4.0), deliberately adding NO tolerance (sec 5)
and NAMING the resolution-derived identifiability bound rather than building it.

L1 BUILDS IT, by the mechanism continuous pose (T1) established for real-angle
rotation, transposed from rotation to gain:

  * the gain is a CONTINUOUS parameter living in the CROSS-FRAME MAP (never an
    in-frame coordinate) -- so `Div(a_ch, pa_ch)` producing a REAL number is
    CORRECT here, exactly as a real theta is correct inside `Rotate`;
  * the candidate is RENDERED at that continuous gain onto the stepped integer
    lattice (`Times([p_ch, ghat_ch])`);
  * recognition is decided by a CONTINUOUS VERDICT (the L-infinity residual) over a
    proposal from the DISCRETE codebook that T3's integer `li_mint` minted --
    "bins propose, continuous decides";
  * the admission bound is pinned ONLY to observational RESOLUTION.

THE BOUND FALLS OUT (sec 13) -- IT IS NOT TUNED. Per channel, with the reference
frame at unit gain (T3's own protocol), p = r, pa = M := max_i r_i, and the test
frame rendered c = round(r*g) = r*g + e_c, a = round(M*g) = M*g + e_a with
|e_c| <= 1/2 and |e_a| <= 1/2 (round is monotone so the max commutes with render):

    residual = | c - p * (a/pa) |
             = | (r*g + e_c) - r*(M*g + e_a)/M |
             = | e_c - e_a * (r/M) |
             <= 1/2 + 1/2 * (r/M)
             <= 1/2 + 1/2            because r <= M = the anchor, BY DEFINITION
             =  1

ONE LATTICE STEP: the sum of exactly TWO half-step rounding displacements -- the
observation's own, and the anchor estimate's ATTENUATED by r/a <= 1, which holds
because the anchor IS the frame's maximum. The exact analogue of continuous pose's
sqrt(2)/2 (there: ONE rounding, 2-D Euclidean half-diagonal; here: TWO roundings,
per-channel L-infinity). The three channels are aggregated by Max (L-infinity)
because each channel rounds INDEPENDENTLY, so the per-channel bound is also the
vector bound.

THE IN-CLASS ENVELOPE also falls out. T3's exact order-statistic identity is
a*ref_s == s*ref_a. Under rounding, with n surfaces, S := sum r_i, E := sum e_i so
|E| <= n/2:

    | a*ref_s - s*ref_a | = | (M*g+e_a)*S - (S*g+E)*M | = | e_a*S - E*M |
                          <= 1/2*S + (n/2)*M = 1/2 * ( ref_s + n*ref_a )

n = Count(frame's surfaces), READ FROM THE DATA. Honestly LOOSE (the sum
accumulates n roundings), so L1 adds a SECOND, TIGHTER necessary clause on the MIN
order statistic, which accumulates only TWO roundings exactly like the recognition
bound:

    | a*ref_m - m*ref_a | <= 1/2 * ( ref_m + ref_a )

BOTH clauses must hold on ALL THREE channels. Declared IN ADVANCE in the
pre-registration on the principled ground that fewer accumulated roundings give a
tighter falls-out envelope -- a design choice, NOT sec 5 metric surgery.

  l1_frame_stats  the frame's OWN per-channel anchor (MaxOver), sum (Sum), min
                  (MinOver) and surface count (Count), hub-scoped through
                  Neighbours(frame,"has_surface") -- the frame's own population,
                  never a global NodesOfType grab (sec 12.1). Written into an
                  L1-ONLY attr namespace (l1_a*/l1_s*/l1_m*/l1_n) so NO T3
                  attribute is ever written by L1 and both arms are readable from
                  ONE graph.
  l1_inclass      the CONTINUOUS-ENVELOPE sibling of T3's exact li_inclass: both
                  the sum clause and the (tighter) min clause, all three channels.
                  Holds => mint an IlluminantL1 carrying the REAL per-channel gain
                  Div(l1_a, ref.l1_a) -- a real number is CORRECT here because it
                  is a CROSS-FRAME quantity (the frame/continuum invariant) -- and
                  set l1_inclass=1. Fails => nothing minted, the frame is REFUSED.
  l1_recognize    THE CONTINUOUS VERDICT. Guard Lte(MinOver over the reference
                  frame's OWN has_identity population of the L-infinity residual,
                  1.0); effect names the winner with Argmin over the SAME source
                  and the SAME value -- continuous pose's cp_recognize shape
                  exactly. The codebook PROPOSES (SurfaceIdentity nodes minted by
                  T3's integer li_mint); the CONTINUOUS rendered residual DECIDES.
  l1_refuse       marks l1_status="l1_refused" when the frame is in-class but NO
                  candidate is within the bound -- so a refusal is a POSITIVE
                  datum and the arm can be shown ALIVE rather than merely silent
                  (sec 1.1 clause 4).

T3 IS NOT MODIFIED. seeds/vision_lighting.json and tools/build_vision_lighting.py
stay byte-identical; L1 REUSES T3's SurfaceIdentity codebook (minted in the
REFERENCE frame at unit gain, so entirely unaffected by the test frame's real
gain) and therefore DEPENDS on vision_lighting being loaded with lighting=1.

Flag-gated on LightingL1Params.lighting_l1, OFF by default (sec 9). The flag is
read ABSENCE-TOLERANTLY via MaxOver(..., default 0) and NEVER via PickUnique,
which returns None on an absent params node and silently changes behaviour
elsewhere.

NO new Rust: reuses Div/Times/Minus/Abs/Max/Plus/Lte/Gte/MinOver/MaxOver/Argmin/
Sum/Count/Neighbours/NodesOfType/Not/Exists/And/Eq + run_rules.

BOUNDED: the GLOBAL diagonal illuminant class, now at REAL values. Spatially-
varying illuminant / Retinex, global illuminant inference, shadow-vs-reflectance
edges and multi-illuminant scenes are NOT solved -- only REFUSED. Reflectance is
GIVEN at the abstract cone-triple grain. That is the NAMED FRONTIER.

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_lighting_l1.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms) -----------------------------------
# THE KNOWN TRAP (VISION_LIGHTING_RESULTS.md's central finding): some Terms take an
# `items` LIST and some take `a`/`b`. Writing a LIST term in a/b form parses to an
# EMPTY operand list -- and an EMPTY PRODUCT IS 1 -- which turned T3's invariant
# into Eq(1,1): a UNIVERSAL CONTAINER with a FLAWLESS invariance score. Every
# constructor below states its form, and the gate is POSITIVE-CONTROLLED against
# exactly this defect (sec 12.3).
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


def Count(src):         return {"type": "Count", "source": src}


def MaxOver(src, var, value, default=None):
    t = {"type": "MaxOver", "source": src, "var_name": var, "value": value}
    if default is not None:
        t["default"] = default
    return t


def MinOver(src, var, value, default=None):
    t = {"type": "MinOver", "source": src, "var_name": var, "value": value}
    if default is not None:
        t["default"] = default
    return t


def Sum(src, var, value):
    return {"type": "Sum", "source": src, "var_name": var, "value": value}


def Argmin(src, var, value, default=None):
    t = {"type": "Argmin", "source": src, "var_name": var, "value": value}
    if default is not None:
        t["default"] = default
    return t


def term(x):            return {"__term__": x}


CH = ["L", "M", "S"]        # the three cone channels
D_CONE = 3

# THE RECOGNITION BOUND. NOT A TUNED CONSTANT: it is ONE LATTICE STEP, derived in
# the module docstring as 1/2 (the observation's own rounding) + 1/2 * (r/a) with
# r/a <= 1 BY THE DEFINITION OF THE ANCHOR AS THE FRAME'S MAXIMUM. It is the exact
# analogue of continuous pose's sqrt(2)/2 half-diagonal. Changing it would be
# changing what "one step of the integer lattice" means.
LATTICE_STEP = 1.0

# HALF a lattice step -- the maximum displacement a single round() can introduce.
# Every envelope below is a sum of these, each scaled by its own cross-multiplier.
HALF_STEP = 0.5

# The MinOver default when the reference frame holds NO identities: a value that
# cannot pass the bound, so an empty codebook REFUSES rather than silently
# admitting (an absent population must never read as a match -- sec 1.1).
NO_CANDIDATE = 1.0e9


def ENABLED():
    """The L1 flag, read ABSENCE-TOLERANTLY.

    MaxOver with an explicit default returns 0.0 when NO LightingL1Params node
    exists, so the seed is inert in a graph that never loaded it. Deliberately NOT
    PickUnique: PickUnique returns None on an absent params node, which silently
    changes behaviour elsewhere instead of reading as OFF.
    """
    return Gt(MaxOver(NodesOf("LightingL1Params"), "lp",
                      A(V("lp"), "lighting_l1"), default=Lit(0.0)),
              Lit(0.5))


def surfaces_of(frame):
    """The frame's OWN surfaces -- hub-scoped, never a global NodesOfType grab."""
    return Nbrs(frame, "has_surface")


# ---------------------------------------------------------------------------
# l1_frame_stats -- the frame's own per-channel anchor / sum / min, and its count.
# ---------------------------------------------------------------------------
LI_L1_FRAME_STATS = {
    "name": "l1_frame_stats",
    "comment": (
        "The frame's OWN per-channel order statistics for L1: the ANCHOR "
        "l1_a_ch = MaxOver(frame's surfaces, c_ch), the SUM l1_s_ch, the MIN "
        "l1_m_ch, and the surface COUNT l1_n. Scoped by "
        "Neighbours(frame,'has_surface') -- the frame's own population, NOT a "
        "global NodesOfType grab (sec 12.1). Written into an L1-ONLY attribute "
        "namespace so NO T3 attribute is ever written by L1: T3's exact arm and "
        "L1's continuous arm are then readable from ONE graph in ONE run, which "
        "is what makes the CONTINUOUS-DECIDES contrast a measurement rather than "
        "two separate experiments. The anchor is the frame's MEASURED "
        "dynamic-range ceiling (no constant introduced); the MIN is carried "
        "because the min-based in-class clause accumulates only TWO roundings "
        "where the sum-based clause accumulates n, giving a tighter falls-out "
        "envelope; the COUNT is read from the DATA and is what makes the sum "
        "envelope's n a measured quantity rather than a magic number. Matched "
        "through a surface edge so the rule only ever sees a frame that HAS a "
        "population. The l1_stats_done guard makes it fire once per frame so "
        "run_rules converges. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "anysurf"]],
    "where": And([
        ENABLED(),
        Lt(A(V("frame"), "l1_stats_done"), Lit(0.5)),
    ]),
    "effects": (
        [["set_attr", "frame", "l1_a" + ch,
          term(MaxOver(surfaces_of(V("frame")), "w", A(V("w"), "c" + ch)))]
         for ch in CH]
        + [["set_attr", "frame", "l1_s" + ch,
            term(Sum(surfaces_of(V("frame")), "w", A(V("w"), "c" + ch)))]
           for ch in CH]
        + [["set_attr", "frame", "l1_m" + ch,
            term(MinOver(surfaces_of(V("frame")), "w", A(V("w"), "c" + ch)))]
           for ch in CH]
        + [["set_attr", "frame", "l1_n",
            term(Count(surfaces_of(V("frame"))))],
           ["set_attr", "frame", "l1_stats_done", term(Lit(1.0))]]
    ),
}


def _sum_clause(test, ref, ch):
    """|a*ref_s - s*ref_a| <= 1/2 * (ref_s + n*ref_a) -- the SUM in-class clause.

    Under a diagonal (von Kries) illuminant every order statistic scales by the
    same per-channel gain, so anchor:sum is invariant -- T3's exact test. Under a
    REAL gain the render rounds, so the equality is displaced by exactly the
    roundings it contains: ONE in the anchor (scaled by ref_s) and n in the sum
    (scaled by ref_a), each at most HALF a lattice step. n is COUNTED from the
    data. Honestly LOOSE -- see _min_clause for the tighter companion.
    """
    lhs = Abs(Minus(Times([A(test, "l1_a" + ch), A(ref, "l1_s" + ch)]),
                    Times([A(test, "l1_s" + ch), A(ref, "l1_a" + ch)])))
    envelope = Times([Lit(HALF_STEP),
                      Plus([A(ref, "l1_s" + ch),
                            Times([A(test, "l1_n"), A(ref, "l1_a" + ch)])])])
    return Lte(lhs, envelope)


def _min_clause(test, ref, ch):
    """|a*ref_m - m*ref_a| <= 1/2 * (ref_m + ref_a) -- the MIN in-class clause.

    The same order-statistic consistency read on the MINIMUM instead of the sum.
    It accumulates only TWO roundings (one in the anchor, one in the min), so its
    falls-out envelope is far tighter than the sum clause's. Both clauses are
    necessary conditions and BOTH are required, on all three channels. Declared in
    the pre-registration BEFORE the run (not sec 5 metric surgery).
    """
    lhs = Abs(Minus(Times([A(test, "l1_a" + ch), A(ref, "l1_m" + ch)]),
                    Times([A(test, "l1_m" + ch), A(ref, "l1_a" + ch)])))
    envelope = Times([Lit(HALF_STEP),
                      Plus([A(ref, "l1_m" + ch), A(ref, "l1_a" + ch)])])
    return Lte(lhs, envelope)


# ---------------------------------------------------------------------------
# l1_inclass -- the CONTINUOUS-ENVELOPE in-class discovery + the REAL gain.
# ---------------------------------------------------------------------------
LI_L1_INCLASS = {
    "name": "l1_inclass",
    "comment": (
        "DISCOVERS whether the lighting change between this frame and its "
        "reference is in the GLOBAL DIAGONAL class, now at REAL-VALUED gains. T3's "
        "li_inclass demands EXACT integer cross-multiplication, which a rounded "
        "real gain breaks -- that is precisely why T3 measured 0/12 at gains "
        "1.5/2.5/3.3/7.5. This rule replaces the exact equality with the "
        "ROUNDING ENVELOPE THE LATTICE ITSELF IMPLIES: the displacement of the "
        "order-statistic identity is a sum of half-lattice-step roundings, each "
        "scaled by its own cross-multiplier, and nothing more. TWO clauses must "
        "hold on ALL THREE channels -- the SUM clause (T3's own statistic, "
        "envelope 1/2*(ref_s + n*ref_a), loose because the sum accumulates n "
        "roundings) and the tighter MIN clause (envelope 1/2*(ref_m + ref_a), "
        "only two roundings). NO TOLERANCE IS TUNED: every 1/2 is the maximum "
        "displacement of a single round(), and n is COUNTED from the data. "
        "Holds => mint an IlluminantL1 carrying the REAL per-channel gain "
        "Div(l1_a, ref.l1_a). A REAL number is CORRECT here and is not a "
        "violation of the frame/continuum invariant: the gain is a CROSS-FRAME "
        "MAP, never an in-frame coordinate -- the surfaces' cones stay integers. "
        "This is exactly how continuous pose holds a real theta inside Rotate. "
        "Fails => nothing minted, l1_inclass stays 0, l1_recognize cannot fire: a "
        "spatially-varying (multi-illuminant) change is REFUSED, not force-"
        "normalised. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Lt(A(V("frame"), "l1_inclass"), Lit(0.5)),
        Gt(A(V("frame"), "l1_stats_done"), Lit(0.5)),
        Gt(A(V("ref"), "l1_stats_done"), Lit(0.5)),
    ] + [_sum_clause(V("frame"), V("ref"), ch) for ch in CH]
      + [_min_clause(V("frame"), V("ref"), ch) for ch in CH]),
    "effects": [
        ["add_node", "ill", "IlluminantL1", {
            # The discovered gain as a REAL number -- correct, it is CROSS-FRAME.
            "gL": term(Div(A(V("frame"), "l1_aL"), A(V("ref"), "l1_aL"))),
            "gM": term(Div(A(V("frame"), "l1_aM"), A(V("ref"), "l1_aM"))),
            "gS": term(Div(A(V("frame"), "l1_aS"), A(V("ref"), "l1_aS"))),
            "minted": term(Lit(1.0)),
        }],
        ["add_edge", "frame", "has_illuminant_l1", "ill"],
        ["set_attr", "frame", "l1_inclass", term(Lit(1.0))],
    ],
}


def _render_residual(surf, frame, cand, ch):
    """| c_ch - p_ch * (a_ch / pa_ch) | -- the per-channel CONTINUOUS residual.

    THE RENDER. Div(a_ch, pa_ch) is the continuous gain, a REAL number in the
    cross-frame map; Times([p_ch, ghat]) RENDERS the held prototype at it; Minus
    against the observation and Abs gives the residual on the stepped lattice.
    Structurally identical to continuous pose's MapList(Rotate(p, theta)) followed
    by PointSetDist against the observation -- render the candidate at the
    continuous cross-frame parameter, then compare with a continuous verdict.
    """
    ghat = Div(A(frame, "l1_a" + ch), A(cand, "pa" + ch))
    rendered = Times([A(cand, "p" + ch), ghat])
    return Abs(Minus(A(surf, "c" + ch), rendered))


def _verdict(surf, frame, cand):
    """The L-infinity residual over the three channels -- THE CONTINUOUS VERDICT.

    Max (not a sum, not a Euclidean norm) because each channel is rounded
    INDEPENDENTLY, so the per-channel bound of ONE LATTICE STEP is also the vector
    bound. Aggregating any other way would either need a different derivation or
    smuggle in a constant.
    """
    return Max([_render_residual(surf, frame, cand, ch) for ch in CH])


def _codebook(ref):
    """The reference frame's OWN identity population -- hub-scoped (sec 12.1).

    These are the SurfaceIdentity nodes T3's INTEGER li_mint minted. They are the
    DISCRETE PROPOSAL; the continuous verdict decides among them.
    """
    return Nbrs(ref, "has_identity")


# ---------------------------------------------------------------------------
# l1_recognize -- THE CONTINUOUS VERDICT. "Bins propose, continuous decides."
# ---------------------------------------------------------------------------
LI_L1_RECOGNIZE = {
    "name": "l1_recognize",
    "comment": (
        "THE REAL-GAIN LIGHTING INVARIANT. A surface in a TEST frame is recognized "
        "iff (a) the frame's lighting change was DISCOVERED in-class under the "
        "rounding envelope, and (b) the BEST candidate in the reference frame's "
        "own held codebook, RENDERED at the continuous cross-frame gain, lies "
        "within ONE LATTICE STEP of the observation on every channel. "
        "BINS PROPOSE, CONTINUOUS DECIDES: the proposal set is the DISCRETE "
        "codebook T3's integer li_mint produced; the decision is the CONTINUOUS "
        "rendered residual. The guard is Lte(MinOver(...), LATTICE_STEP) and the "
        "effect names the winner with Argmin over the SAME source and the SAME "
        "value -- continuous pose's cp_recognize shape exactly, which is the "
        "precedent that an Argmin (unlike a Pick(Filter(...))) does apply its "
        "value expression in effect position. MinOver carries an explicit "
        "NO_CANDIDATE default so an EMPTY codebook REFUSES rather than silently "
        "admitting (an absent population must never read as a match, sec 1.1). "
        "THE BOUND IS NOT TUNED: 1.0 is ONE STEP OF THE INTEGER LATTICE, derived "
        "as 1/2 (the observation's own rounding) + 1/2*(r/a) with r/a <= 1 BY THE "
        "DEFINITION OF THE ANCHOR AS THE FRAME'S MAXIMUM -- the analogue of "
        "continuous pose's sqrt(2)/2 half-diagonal. It is therefore pinned to "
        "OBSERVATIONAL RESOLUTION and to nothing else, and it MUST fail when the "
        "resolution is inadequate: at a dimming gain distinct materials render "
        "onto the same lattice points and no verdict can separate what the steps "
        "did not record. That failure is the measurement, not a defect. "
        "Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("frame"), "l1_inclass"), Lit(0.5)),
        Gt(A(V("frame"), "l1_stats_done"), Lit(0.5)),
        Lte(MinOver(_codebook(V("ref")), "cand",
                    _verdict(V("R"), V("frame"), V("cand")),
                    default=Lit(NO_CANDIDATE)),
            Lit(LATTICE_STEP)),
    ]),
    "effects": [
        ["set_attr", "R", "l1_recognized", term(Lit(1.0))],
        ["set_attr", "R", "l1_id", term(A(
            Argmin(_codebook(V("ref")), "cand",
                   _verdict(V("R"), V("frame"), V("cand")),
                   default=Lit(0.0)),
            "sid_key"))],
        ["set_attr", "R", "l1_resid", term(MinOver(
            _codebook(V("ref")), "cand",
            _verdict(V("R"), V("frame"), V("cand")),
            default=Lit(NO_CANDIDATE)))],
        ["set_attr", "R", "l1_status", term(Lit("l1_recognized"))],
    ],
}


# ---------------------------------------------------------------------------
# l1_refuse -- the REFUSAL as a POSITIVE datum (sec 1.1 clause 4).
# ---------------------------------------------------------------------------
LI_L1_REFUSE = {
    "name": "l1_refuse",
    "comment": (
        "Marks l1_status='l1_refused' for a surface in an IN-CLASS frame whose "
        "best rendered candidate exceeds the lattice-step bound. This exists so a "
        "REFUSAL IS A POSITIVE DATUM: sec 1.1's dead-arm lesson is that an absence "
        "is indistinguishable from an inert mechanism unless the mechanism can be "
        "shown to fire at all. With this rule the floors (noise, novel material, "
        "low-resolution gains) report l1_refused rather than merely leaving "
        "l1_recognized at its 0 init, so 'refused' and 'never ran' are "
        "distinguishable in the readback. It is the exact complement of "
        "l1_recognize's guard, so the two rules partition the in-class surfaces. "
        "Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("frame"), "l1_inclass"), Lit(0.5)),
        Gt(A(V("frame"), "l1_stats_done"), Lit(0.5)),
        Lt(A(V("R"), "l1_recognized"), Lit(0.5)),
        Not(Lte(MinOver(_codebook(V("ref")), "cand",
                        _verdict(V("R"), V("frame"), V("cand")),
                        default=Lit(NO_CANDIDATE)),
                Lit(LATTICE_STEP))),
    ]),
    "effects": [
        ["set_attr", "R", "l1_status", term(Lit("l1_refused"))],
        ["set_attr", "R", "l1_resid", term(MinOver(
            _codebook(V("ref")), "cand",
            _verdict(V("R"), V("frame"), V("cand")),
            default=Lit(NO_CANDIDATE)))],
    ],
}


SEED = {
    "id": "vision_lighting_l1",
    "version": "1.0.0",
    "depends_on": ["vision_lighting"],
    "description": (
        "ADVANCED LIGHTING RUNG L1 -- REAL-VALUED ILLUMINANT GAINS. T3 crossed "
        "lighting-invariance for the EXACT-RENDERING (integer-ratio) diagonal "
        "illuminant class and REFUSED real gains, NAMING the resolution-derived "
        "identifiability bound rather than building it. L1 BUILDS it by continuous "
        "pose's mechanism transposed from rotation to gain: the illuminant gain is "
        "a CONTINUOUS parameter in the CROSS-FRAME MAP (never an in-frame "
        "coordinate -- the surfaces' cones stay integers), the held prototype is "
        "RENDERED at that continuous gain onto the stepped integer lattice, and "
        "recognition is decided by a CONTINUOUS VERDICT (the L-infinity residual) "
        "over a proposal from the DISCRETE codebook T3's integer li_mint minted: "
        "BINS PROPOSE, CONTINUOUS DECIDES. l1_frame_stats reads the frame's OWN "
        "anchor/sum/min/count hub-scoped via Neighbours, into an L1-only attr "
        "namespace so T3's arm is readable from the SAME graph; l1_inclass "
        "replaces T3's exact order-statistic equality with the ROUNDING ENVELOPE "
        "THE LATTICE IMPLIES (a sum clause and a tighter min clause, both "
        "necessary, both derived) and mints an IlluminantL1 holding the REAL gain; "
        "l1_recognize admits iff the best rendered candidate is within ONE LATTICE "
        "STEP; l1_refuse makes a refusal a POSITIVE datum. NO NEW RUST: reuses "
        "Div/Times/Minus/Abs/Max/Plus/Lte/MinOver/MaxOver/Argmin/Sum/Count/"
        "Neighbours + run_rules. NO MAGIC NUMBER: the bound is ONE LATTICE STEP, "
        "falling out as 1/2 (the observation's rounding) + 1/2*(r/a) with r/a <= 1 "
        "BY THE DEFINITION OF THE ANCHOR AS THE MAXIMUM -- the analogue of "
        "continuous pose's sqrt(2)/2; every envelope term is a half-step rounding "
        "scaled by its own cross-multiplier; n is COUNTED from the data. The bound "
        "is pinned to OBSERVATIONAL RESOLUTION and to nothing else, so it MUST "
        "fail at a dimming gain where distinct materials render onto the same "
        "lattice points -- that failure is the measurement. BOUNDED: the GLOBAL "
        "diagonal class only. Spatially-varying illuminant / Retinex, global "
        "illuminant inference, shadow-vs-reflectance edges and multi-illuminant "
        "scenes are NOT solved, only REFUSED; reflectance is GIVEN at the abstract "
        "cone-triple grain. Flag-gated on LightingL1Params.lighting_l1, OFF by "
        "default (sec 9 -- default 0 => byte-identical, seed inert), read "
        "ABSENCE-TOLERANTLY via MaxOver(default 0), never PickUnique. See "
        "VISION_LIGHTING_L1_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_lighting_l1_mt",
        "label": ("real-valued illuminant gains: the gain as a continuous "
                  "cross-frame parameter, rendered to the stepped lattice and "
                  "decided by a continuous verdict pinned to resolution"),
    },
    "nodes": [
        {"local_id": 0, "type": "LightingL1Params", "attrs": {"lighting_l1": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [LI_L1_FRAME_STATS, LI_L1_INCLASS, LI_L1_RECOGNIZE, LI_L1_REFUSE],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_lighting_l1.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out, "-", len(SEED["rules"]), "rules")


if __name__ == "__main__":
    main()
