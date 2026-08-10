#!/usr/bin/env python3
"""Emit seeds/vision_lighting_l2.json — ADVANCED LIGHTING RUNG L2:
SPATIALLY-VARYING ILLUMINANT (RETINEX) as pure graph data (NO new Rust).

See VISION_LIGHTING_L2_PREREG.md.

T3 (`vision_lighting`) crossed lighting-invariance for the EXACT-INTEGER-RATIO
GLOBAL diagonal illuminant; L1 (`vision_lighting_l1`) widened it to REAL-VALUED
GLOBAL gains by a continuous verdict. BOTH REFUSE a spatially-varying scene as
out-of-class (0/20 admitted, measured twice).

L2 MAKES THE SPATIALLY-VARYING CASE ADMISSIBLE, by Land's Retinex first step:
reflectance is recovered from SPATIAL RATIOS of neighbouring cone activity,
which discounts a slowly-varying illuminant LOCALLY -- with NO global estimate
and NO path integration (that is L3, and it is NOT this rung).

THE ALGEBRA
-----------
A surface i at position x_i with reflectance r_i under a field g:
c_i = round(r_i * g(x_i)). Let N(i) be i TOGETHER WITH ITS IMMEDIATE spatial
neighbours -- RADIUS 1, the SMALLEST neighbourhood that has a neighbour (the
double-opponent local-contrast grain), NOT a tuned width.

The LOCAL ANCHOR is the locale's own per-channel maximum,
a_loc(i) = max_{j in N(i)} c_j. The reference frame is at unit gain, so its
local anchor is pa_loc(i) = max_{j in N(i)} r_j =: A_loc(i). If g is constant
ACROSS ONE LOCALE:

    ghat(i) = a_loc(i) / pa_loc(i) = g(x_i)      <- the LOCAL illuminant estimate

and the held prototype rendered at it, p * ghat(i), reproduces the observation.
THE ILLUMINANT FIELD CANCELS LOCALLY. This is exactly T3's anchor-relative
invariant with the anchor LOCALIZED -- which is the whole content of the rung.

THE BOUND IS INHERITED, NOT RE-DERIVED AND NOT RE-TUNED (sec 13)
----------------------------------------------------------------
The recognition bound is L1's OWN ONE LATTICE STEP = 1.0: 1/2 (the
observation's own rounding) + 1/2*(r/a) with r/a <= 1 BECAUSE THE ANCHOR IS A
MAXIMUM OVER A SET CONTAINING THE SURFACE ITSELF (the locale contains its own
centre -- the adapter links the centre into its own locale, so the property
L1's derivation rests on is preserved verbatim at locale grain).

The admission envelope is L1's TIGHTER MIN CLAUSE, localized:
    | a*ref_m - m*ref_a |  <=  1/2 * ( ref_m + ref_a )
Two roundings, each at most half a lattice step, each scaled by its own
cross-multiplier. NO NEW CONSTANT IS INTRODUCED ANYWHERE IN THIS SEED.

WHAT "SLOWLY VARYING" MEANS -- AND IT FALLS OUT TOO
---------------------------------------------------
g is NOT constant across a locale; it varies, and the local estimate is
contaminated by ~ c*|dg/g| per adjacency. So the mechanism admits exactly those
fields whose PER-ADJACENCY variation is below what the lattice records:

    c_max * (rho - 1)  <~  1 lattice step   =>   rho - 1  <~  1 / c_max

"Slowly varying" is therefore NOT a tuned threshold -- it is the lattice step
divided by the frame's OWN MEASURED DYNAMIC RANGE (sec 13's "a fraction of a
dynamic range the system measures for itself"). The TOTAL field variation
across the scene is rho^(N-1) and GROWS WITH SCENE EXTENT while every adjacency
stays sub-step. That is the precise, bounded sense in which local ratios buy a
spatially-varying illuminant.

THE RULES (every decision is a RULE -- CLAUDE.md sec 0)
-------------------------------------------------------
  l2_frame_stats      the FRAME's global anchor, in an L2-only namespace. Used
                      ONLY by the ablation control arm.
  l2_locale_stats     the LOCALE's own per-channel anchor / min / count,
                      hub-scoped by Neighbours(loc,"in_locale") -- the locale's
                      own population, never a global NodesOfType grab (sec 12.1).
  l2_pair             THE GRAPH'S OWN pairing of a test locale with its
                      reference counterpart: an Eq(pos,pos) JOIN across the
                      frame's compares_to edge. The adapter supplies `pos`
                      (world layout, the same class of mechanical ingest as the
                      cone triple); the PAIRING DECISION is the rule's.
  l2_slowvar          the NON-CIRCULAR field-slowness DISCOVERY: the locale's
                      illuminant estimate must agree with EVERY adjacent
                      locale's to within one lattice step of rendered
                      displacement plus the two anchors' half-step roundings.
                      REPORTED, NOT A GATE -- its envelope is worst-case over
                      the locale while l2_recognize's is exact for the actual
                      surface, so it is STRICTLY MORE CONSERVATIVE than the test
                      it would precede (see PREREG AMENDMENT 1).
  l2_recognize        THE INVARIANT. Lte(MinOver(codebook, Linf residual), 1.0)
                      guards; Argmin names the winner; l2_ncand RECORDS THE
                      NUMBER OF CANDIDATES INSIDE THE BOUND so the bound's
                      discriminativeness is reported, not assumed (the L1b
                      lesson: reporting only the winner's residual hid a bound
                      that never bound).
  l2_refuse           refusal as a POSITIVE datum (sec 1.1 clause 4).
  l2_recognize_globalanchor
                      THE ABLATION CONTROL, ALWAYS COMPUTED ON THE SAME GRAPH:
                      identical except ghat comes from the FRAME's global anchor
                      instead of the locale's. This is the ratio / local-contrast
                      step ABLATED (sec 13.2), read from ONE graph in ONE run so
                      the contrast is a measurement and not two experiments.

T3 AND L1 ARE NOT MODIFIED. seeds/vision_lighting.json and
seeds/vision_lighting_l1.json stay byte-identical; L2 REUSES T3's SurfaceIdentity
codebook (minted in the reference frame at unit gain) and therefore DEPENDS on
vision_lighting being loaded with lighting=1.

Flag-gated on LightingL2Params.lighting_l2, OFF by default (sec 9), read
ABSENCE-TOLERANTLY via MaxOver(..., default 0) and NEVER via PickUnique.

NO new Rust: reuses Div/Times/Minus/Abs/Max/Plus/Lte/Gte/MinOver/MaxOver/Argmin/
Count/Filter/Neighbours/NodesOfType/Not/And/Eq/Gt/Lt + run_rules.

BOUNDED: a SLOWLY-VARYING SINGLE illuminant field via LOCAL ratios. Global
illuminant inference (L3), shadow-vs-reflectance edge ATTRIBUTION (L4) and
MULTI-ILLUMINANT scenes are NOT solved. Reflectance is GIVEN at the abstract
cone-triple grain. Spatial registration between reference and test at LOCALE
grain is GIVEN (strictly stronger than T3/L1's frame-level assumption, declared
loudly in the pre-registration); adjacency is GIVEN, not grown. IDENTITY
correspondence is NOT given -- that is what recognition decides.

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_lighting_l2.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms) -----------------------------------
# THE KNOWN TRAP (VISION_LIGHTING_RESULTS.md's central finding, and process rule
# 4): some Terms take an `items` LIST and some take `a`/`b`. Writing a LIST term
# in a/b form parses to an EMPTY operand list -- and AN EMPTY PRODUCT IS 1 --
# which turned T3's invariant into Eq(1,1): a UNIVERSAL CONTAINER with a
# FLAWLESS invariance score. Every constructor below states its form, and the
# gate is POSITIVE-CONTROLLED against exactly this defect (sec 12.3).
def V(name):            return {"type": "Var", "name": name}
def Lit(v):             return {"type": "Lit", "value": v}
def A(node, key):       return {"type": "Attr", "node": node, "key": key}
def Gt(a, b):           return {"type": "Gt", "a": a, "b": b}          # a/b
def Lt(a, b):           return {"type": "Lt", "a": a, "b": b}          # a/b
def Lte(a, b):          return {"type": "Lte", "a": a, "b": b}         # a/b
def Gte(a, b):          return {"type": "Gte", "a": a, "b": b}         # a/b
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


def Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}


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


def Argmin(src, var, value, default=None):
    t = {"type": "Argmin", "source": src, "var_name": var, "value": value}
    if default is not None:
        t["default"] = default
    return t


def term(x):            return {"__term__": x}


CH = ["L", "M", "S"]

# THE RECOGNITION BOUND -- L1's OWN falls-out ONE LATTICE STEP, INHERITED
# UNCHANGED and NOT re-derived: 1/2 (the observation's own rounding) + 1/2*(r/a)
# with r/a <= 1 BECAUSE THE ANCHOR IS A MAXIMUM OVER A SET CONTAINING THE
# SURFACE ITSELF. The locale contains its own centre, so the property the
# derivation rests on holds verbatim at locale grain.
LATTICE_STEP = 1.0

# HALF a lattice step -- the maximum displacement a single round() introduces.
# The admission envelope is a sum of exactly two of these, each scaled by its own
# cross-multiplier (L1's tighter MIN clause, localized).
HALF_STEP = 0.5

# The MinOver default when the codebook is EMPTY: a value that cannot pass the
# bound, so an absent population REFUSES rather than silently admitting (an
# absence must never read as a match -- sec 1.1).
NO_CANDIDATE = 1.0e9


def ENABLED():
    """The L2 flag, read ABSENCE-TOLERANTLY.

    MaxOver with an explicit default returns 0.0 when NO LightingL2Params node
    exists, so the seed is inert in a graph that never loaded it. Deliberately
    NOT PickUnique on a params node (process rule 3): PickUnique returns None on
    an absent node, which silently changes behaviour instead of reading as OFF.
    """
    return Gt(MaxOver(NodesOf("LightingL2Params"), "lp",
                      A(V("lp"), "lighting_l2"), default=Lit(0.0)),
              Lit(0.5))


# ---------------------------------------------------------------------------
# l2_frame_stats -- the FRAME's global anchor (the ABLATION arm's input ONLY).
# ---------------------------------------------------------------------------
L2_FRAME_STATS = {
    "name": "l2_frame_stats",
    "comment": (
        "The frame's OWN GLOBAL per-channel anchor, written into an L2-only "
        "attribute namespace (l2f_a*). It exists SOLELY to feed the ablation "
        "control arm (l2_recognize_globalanchor), so that the LOCAL-vs-GLOBAL "
        "contrast -- the measurement that decides whether the spatial-ratio step "
        "is LOAD-BEARING or decorative (sec 13.2) -- is read from ONE graph in "
        "ONE run rather than from two experiments. Computed here rather than "
        "read from L1's l1_a* so that L2 does not depend on L1's flag being on, "
        "and so that L2 never writes or reads a T3/L1 attribute. Hub-scoped by "
        "Neighbours(frame,'has_surface') -- never a global NodesOfType grab "
        "(sec 12.1). The l2f_done guard makes it fire once per frame so "
        "run_rules converges. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "anysurf"]],
    "where": And([
        ENABLED(),
        Lt(A(V("frame"), "l2f_done"), Lit(0.5)),
    ]),
    "effects": (
        [["set_attr", "frame", "l2f_a" + ch,
          term(MaxOver(Nbrs(V("frame"), "has_surface"), "w", A(V("w"), "c" + ch)))]
         for ch in CH]
        + [["set_attr", "frame", "l2f_done", term(Lit(1.0))]]
    ),
}


# ---------------------------------------------------------------------------
# l2_locale_stats -- THE LOCAL RATIO'S DENOMINATOR: the locale's own statistics.
# ---------------------------------------------------------------------------
L2_LOCALE_STATS = {
    "name": "l2_locale_stats",
    "comment": (
        "THE LOCAL ANCHOR. Per-channel MaxOver / MinOver and the Count over the "
        "LOCALE's own membership -- Neighbours(loc,'in_locale'), the locale's own "
        "population, never a global grab (sec 12.1). This is the entire "
        "difference between L2 and T3/L1: T3 and L1 read ONE anchor for the WHOLE "
        "FRAME, so a spatially-varying field makes that single anchor wrong "
        "everywhere except where it was measured; L2 reads an anchor PER LOCALE, "
        "so a slowly-varying field is discounted where it is observed. The locale "
        "CONTAINS ITS OWN CENTRE (the adapter links the centre surface into its "
        "own locale), which is what preserves L1's r/a <= 1 -- the property its "
        "ONE-LATTICE-STEP bound is derived from -- verbatim at locale grain. The "
        "MIN is carried because the admission clause built on it accumulates only "
        "TWO roundings; the COUNT is read from the DATA. Matched through an "
        "in_locale edge so the rule only ever sees a locale that HAS a "
        "population (an empty MaxOver would read as a lookup, sec 1.1). The "
        "l2_loc_done guard makes it fire once per locale so run_rules converges. "
        "Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["loc", "in_locale", "anysurf"]],
    "where": And([
        ENABLED(),
        Lt(A(V("loc"), "l2_loc_done"), Lit(0.5)),
    ]),
    "effects": (
        [["set_attr", "loc", "l2_a" + ch,
          term(MaxOver(Nbrs(V("loc"), "in_locale"), "w", A(V("w"), "c" + ch)))]
         for ch in CH]
        + [["set_attr", "loc", "l2_m" + ch,
            term(MinOver(Nbrs(V("loc"), "in_locale"), "w", A(V("w"), "c" + ch)))]
           for ch in CH]
        + [["set_attr", "loc", "l2_n",
            term(Count(Nbrs(V("loc"), "in_locale")))],
           ["set_attr", "loc", "l2_loc_done", term(Lit(1.0))]]
    ),
}


# ---------------------------------------------------------------------------
# l2_pair -- THE GRAPH pairs a test locale with its reference counterpart.
# ---------------------------------------------------------------------------
L2_PAIR = {
    "name": "l2_pair",
    "comment": (
        "THE PAIRING IS THE GRAPH'S DECISION, NOT THE ADAPTER'S. A three-pattern "
        "JOIN -- the test frame's compares_to reference, the test frame's "
        "locales, the reference frame's locales -- closed by Eq on the `pos` the "
        "adapter supplied as WORLD LAYOUT (the same class of mechanical ingest as "
        "the cone triple itself). The adapter draws NO cross-frame locale edge; "
        "this rule mints the locale_pairs edge from position data. "
        "WHAT THIS ASSUMES, DECLARED: the two frames are SPATIALLY REGISTERED at "
        "LOCALE grain -- strictly stronger than T3/L1's frame-level compares_to, "
        "and stated as a BOUND in VISION_LIGHTING_L2_PREREG.md sec 1. WHAT IT "
        "DOES NOT ASSUME: which surface is which MATERIAL. Identity "
        "correspondence is exactly what l2_recognize has to decide, and nothing "
        "here supplies it. The l2_paired guard makes the mint idempotent so "
        "run_rules converges (a repeated add_edge would not). Flag-gated, OFF by "
        "default (sec 9)."
    ),
    "match": [["frame", "compares_to", "ref"],
              ["frame", "has_locale", "loc"],
              ["ref", "has_locale", "rloc"]],
    "where": And([
        ENABLED(),
        Lt(A(V("loc"), "l2_paired"), Lit(0.5)),
        Gt(A(V("loc"), "l2_loc_done"), Lit(0.5)),
        Gt(A(V("rloc"), "l2_loc_done"), Lit(0.5)),
        Eq(A(V("loc"), "pos"), A(V("rloc"), "pos")),
    ]),
    "effects": (
        [["add_edge", "loc", "locale_pairs", "rloc"]]
        # COPY the reference locale's own statistics onto the test locale. This is
        # not a convenience: it makes every later clause read from ONE node, so the
        # slow-variation test can quantify over a locale's NEIGHBOURS without a
        # nested cross-frame traversal inside a predicate. The values are the
        # reference locale's, verbatim.
        + [["set_attr", "loc", "l2_ra" + ch, term(A(V("rloc"), "l2_a" + ch))]
           for ch in CH]
        + [["set_attr", "loc", "l2_rm" + ch, term(A(V("rloc"), "l2_m" + ch))]
           for ch in CH]
        + [["set_attr", "loc", "l2_paired", term(Lit(1.0))]]
    ),
}


def Exists(src_, var, pred):
    return {"type": "Exists", "source": src_, "var_name": var, "predicate": pred}


def _slowvar_clause(loc, other, ch):
    """THE SLOW-VARIATION TEST, between a locale and an ADJACENT locale.

        | a_i * ra_j  -  ra_i * a_j |  <=  LS*ra_j + HS*ra_j + HS*ra_i

    DERIVATION (sec 13 -- every term falls out; nothing is tuned).
    ghat_i = a_i / ra_i is the locale's illuminant estimate. Using locale i's
    estimate where the true local gain is locale j's displaces a rendered
    prototype p by p*|ghat_i - ghat_j|, and p <= ra_i (the reference local
    anchor bounds every prototype in the locale). Requiring that displacement to
    stay within ONE LATTICE STEP gives ra_i*|ghat_i - ghat_j| <= 1. Each anchor
    also carries its own half-step observation rounding (a = g*ra + e,
    |e| <= 1/2), contributing ra_i*(1/2/ra_i + 1/2/ra_j). Multiplying through by
    ra_j clears both denominators and leaves exactly the three terms above: ONE
    lattice step of admissible FIELD drift, plus the TWO half-step roundings the
    two anchors carry. Cross-multiplied so no ratio is ever divided into a float
    (the frame/continuum invariant).

    THIS IS THE RUNG'S OWN PREMISE MADE CHECKABLE. "Slowly varying" is not a
    threshold someone chose -- it is the lattice step measured against the
    frame's own dynamic range, exactly as the module docstring derives.
    """
    lhs = Abs(Minus(Times([A(loc, "l2_a" + ch), A(other, "l2_ra" + ch)]),
                    Times([A(loc, "l2_ra" + ch), A(other, "l2_a" + ch)])))
    envelope = Plus([Times([Lit(LATTICE_STEP), A(other, "l2_ra" + ch)]),
                     Times([Lit(HALF_STEP), A(other, "l2_ra" + ch)]),
                     Times([Lit(HALF_STEP), A(loc, "l2_ra" + ch)])])
    return Lte(lhs, envelope)


# ---------------------------------------------------------------------------
# l2_slowvar -- the NON-CIRCULAR field-slowness DISCOVERY. REPORTED, NOT A GATE.
# ---------------------------------------------------------------------------
L2_SLOWVAR = {
    "name": "l2_slowvar",
    "comment": (
        "DISCOVERS, WITHOUT ANY SURFACE CORRESPONDENCE, whether the illuminant "
        "field is SLOWLY VARYING at this locale: the locale's own illuminant "
        "estimate must agree with EVERY spatially adjacent locale's to within one "
        "lattice step of rendered displacement, plus the two half-step roundings "
        "the two anchors carry. Quantification is Not(Exists a neighbour that "
        "violates it on any channel), so it is a genuine 'for all neighbours'. "
        "IT IS REPORTED, NOT USED AS A GATE, AND THAT IS A MEASURED DECISION "
        "TAKEN BEFORE THE CONFIRMATORY RUN, NOT A CONVENIENCE (see "
        "VISION_LIGHTING_L2_PREREG.md, AMENDMENT 1). Its envelope is WORST-CASE "
        "over the locale -- it bounds the displacement of the LARGEST prototype "
        "the locale could contain (p <= ra) -- whereas l2_recognize measures the "
        "displacement of the ACTUAL surface against the ACTUAL candidate. So the "
        "clause is STRICTLY MORE CONSERVATIVE than the exact test it would "
        "precede, and a necessary-condition pre-filter that is TIGHTER than the "
        "exact test it precedes does not filter -- it discards rows the exact "
        "test correctly accepts (measured: it admits 4/12 locales where the "
        "verdict is 12/12 correct at rho=1.010). Using it as a gate would buy "
        "nothing and cost recall, so it ships as the DISCOVERY it is: a "
        "non-circular, per-locale statement about the FIELD, readable alongside "
        "the recognition it does not gate. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_locale", "loc"]],
    "where": And([
        ENABLED(),
        Lt(A(V("loc"), "l2_slowvar"), Lit(0.5)),
        Gt(A(V("loc"), "l2_paired"), Lit(0.5)),
        Not(Exists(Nbrs(V("loc"), "locale_adj"), "q",
                   And([Gt(A(V("q"), "l2_paired"), Lit(0.5)),
                        Not(And([_slowvar_clause(V("loc"), V("q"), ch)
                                 for ch in CH]))]))),
    ]),
    "effects": [
        ["set_attr", "loc", "l2_slowvar", term(Lit(1.0))],
    ],
}


def _residual(surf, anch, ranch, cand, ch, akey, rkey):
    """| c_ch - p_ch * (a_ch / pa_ch) | -- the per-channel CONTINUOUS residual.

    THE RENDER. Div(a_ch, pa_ch) is the LOCAL illuminant estimate, a REAL number
    living in the CROSS-FRAME map (never an in-frame coordinate -- the surfaces'
    cones stay integers, per the frame/continuum invariant); Times([p_ch, ghat])
    RENDERS the held prototype at it; Minus + Abs give the residual on the
    stepped lattice. Structurally IDENTICAL to l1_recognize's _render_residual --
    the ONLY difference is WHERE the anchor comes from, which is precisely the
    variable this rung manipulates and precisely what the ablation arm ablates.
    """
    ghat = Div(A(anch, akey + ch), A(ranch, rkey + ch))
    return Abs(Minus(A(surf, "c" + ch), Times([A(cand, "p" + ch), ghat])))


def _verdict(surf, anch, ranch, cand, akey, rkey):
    """The L-infinity residual over the three channels -- THE CONTINUOUS VERDICT.

    Max (not a sum, not a Euclidean norm) because each channel rounds
    INDEPENDENTLY, so the per-channel ONE-LATTICE-STEP bound is also the vector
    bound. Inherited from l1_recognize unchanged.
    """
    return Max([_residual(surf, anch, ranch, cand, ch, akey, rkey) for ch in CH])


def _codebook(ref):
    """The reference frame's OWN identity population -- hub-scoped (sec 12.1).

    These are the SurfaceIdentity nodes T3's INTEGER li_mint minted, REUSED
    UNMODIFIED. They are the DISCRETE PROPOSAL; the continuous verdict over the
    LOCAL illuminant estimate decides among them. "Bins propose, continuous
    decides", with the illuminant now local.
    """
    return Nbrs(ref, "has_identity")


def _best(ref, surf, anch, ranch, akey, rkey):
    return MinOver(_codebook(V(ref)), "cand",
                   _verdict(V(surf), V(anch), V(ranch), V("cand"), akey, rkey),
                   default=Lit(NO_CANDIDATE))


# ---------------------------------------------------------------------------
# l2_recognize -- THE INVARIANT, over the LOCAL illuminant estimate.
# ---------------------------------------------------------------------------
L2_RECOGNIZE = {
    "name": "l2_recognize",
    "comment": (
        "THE SPATIALLY-VARYING LIGHTING INVARIANT. A surface is recognized iff "
        "(a) its locale has been PAIRED with its reference counterpart and (b) "
        "the best candidate in the "
        "reference frame's held codebook, RENDERED at the LOCAL illuminant "
        "estimate ghat_loc = a_loc/pa_loc, lies within ONE LATTICE STEP of the "
        "observation on every channel. The illuminant FIELD cancels locally; what "
        "it leaves fixed is the invariant. "
        "l2_ncand RECORDS THE NUMBER OF CANDIDATES INSIDE THE BOUND. That is not "
        "decoration: rung L1b measured that a landed rung's bound never bound -- "
        "two or more candidates sat inside it in 63/63 of its headline regime -- "
        "and it was INVISIBLE because only the winner's residual had been "
        "reported. Counting the admissible set makes this rung's bound auditable "
        "from its own results, and makes the silent-Argmin hazard reportable "
        "rather than latent. "
        "THE BOUND IS NOT TUNED AND NOT NEW: it is L1's ONE LATTICE STEP, "
        "inherited unchanged, and it holds at locale grain because the locale "
        "contains its own centre. MinOver carries an explicit NO_CANDIDATE "
        "default so an EMPTY codebook REFUSES rather than silently admitting "
        "(sec 1.1). Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["R", "sits_in", "loc"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("loc"), "l2_paired"), Lit(0.5)),
        Lte(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"), Lit(LATTICE_STEP)),
    ]),
    "effects": [
        ["set_attr", "R", "l2_recognized", term(Lit(1.0))],
        ["set_attr", "R", "l2_id", term(A(
            Argmin(_codebook(V("ref")), "cand",
                   _verdict(V("R"), V("loc"), V("loc"), V("cand"), "l2_a", "l2_ra"),
                   default=Lit(0.0)),
            "sid_key"))],
        ["set_attr", "R", "l2_resid",
         term(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"))],
        ["set_attr", "R", "l2_ncand", term(Count(Filter(
            _codebook(V("ref")), "cand",
            Lte(_verdict(V("R"), V("loc"), V("loc"), V("cand"), "l2_a", "l2_ra"),
                Lit(LATTICE_STEP)))))],
        ["set_attr", "R", "l2_status", term(Lit("l2_recognized"))],
    ],
}


# ---------------------------------------------------------------------------
# l2_refuse -- the REFUSAL as a POSITIVE datum (sec 1.1 clause 4).
# ---------------------------------------------------------------------------
L2_REFUSE = {
    "name": "l2_refuse",
    "comment": (
        "Marks l2_status='l2_refused' for a surface whose locale was admitted but "
        "whose best rendered candidate exceeds the lattice-step bound. This "
        "exists so a REFUSAL IS A POSITIVE DATUM: sec 1.1's dead-arm lesson is "
        "that an absence is indistinguishable from an inert mechanism unless the "
        "mechanism can be shown to fire at all. With this rule the floors (noise, "
        "novel material, fast-varying fields) report l2_refused rather than "
        "merely leaving l2_recognized at its 0 init, so 'refused' and 'never ran' "
        "are distinguishable in the readback. It is the exact complement of "
        "l2_recognize's bound clause, so the two rules partition the surfaces "
        "whose locale was admitted. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["R", "sits_in", "loc"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("loc"), "l2_paired"), Lit(0.5)),
        Lt(A(V("R"), "l2_recognized"), Lit(0.5)),
        Not(Lte(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"), Lit(LATTICE_STEP))),
    ]),
    "effects": [
        ["set_attr", "R", "l2_status", term(Lit("l2_refused"))],
        ["set_attr", "R", "l2_resid",
         term(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"))],
    ],
}


# ---------------------------------------------------------------------------
# l2_recognize_globalanchor -- THE ABLATION CONTROL (sec 13.2), ALWAYS COMPUTED.
# ---------------------------------------------------------------------------
L2_RECOGNIZE_GLOBAL = {
    "name": "l2_recognize_globalanchor",
    "comment": (
        "THE ABLATION ARM: the spatial-ratio step REMOVED, and NOTHING ELSE "
        "CHANGED. Identical to l2_recognize term-for-term except that ghat is "
        "formed from the FRAME's GLOBAL anchor (l2f_a*) instead of the LOCALE's "
        "(l2_a*) -- the same codebook, the same render, the same L-infinity "
        "verdict, the same inherited ONE-LATTICE-STEP bound, the same Argmin. "
        "It writes its own l2g_* namespace and is ALWAYS computed when the flag "
        "is on, so the LOCAL-vs-GLOBAL contrast is read from ONE graph in ONE "
        "run: that is what makes 'the ratios are load-bearing' a MEASUREMENT "
        "(sec 13.2's max|on - off|) rather than two experiments compared by hand. "
        "It is gated by exactly the same thing l2_recognize is -- its own "
        "verdict against the same inherited bound -- so the ablation is the "
        "honest no-mechanism condition (sec 6), differing in the ANCHOR and in "
        "nothing else. "
        "AND IT MUST BE SHOWN ALIVE (sec 1.1 clause 4): under a UNIFORM gain the "
        "global anchor IS the right anchor, so this arm scores full marks there. "
        "An ablation arm that is merely dead scores a perfect collapse and means "
        "nothing. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("frame"), "l2f_done"), Lit(0.5)),
        Gt(A(V("ref"), "l2f_done"), Lit(0.5)),
        Lte(_best("ref", "R", "frame", "ref", "l2f_a", "l2f_a"), Lit(LATTICE_STEP)),
    ]),
    "effects": [
        ["set_attr", "R", "l2g_recognized", term(Lit(1.0))],
        ["set_attr", "R", "l2g_id", term(A(
            Argmin(_codebook(V("ref")), "cand",
                   _verdict(V("R"), V("frame"), V("ref"), V("cand"), "l2f_a", "l2f_a"),
                   default=Lit(0.0)),
            "sid_key"))],
        ["set_attr", "R", "l2g_resid",
         term(_best("ref", "R", "frame", "ref", "l2f_a", "l2f_a"))],
    ],
}


SEED = {
    "id": "vision_lighting_l2",
    "version": "1.0.0",
    "depends_on": ["vision_lighting"],
    "description": (
        "ADVANCED LIGHTING RUNG L2 -- SPATIALLY-VARYING ILLUMINANT (RETINEX). T3 "
        "crossed lighting-invariance for the exact-integer-ratio GLOBAL diagonal "
        "illuminant and L1 widened it to REAL-VALUED GLOBAL gains; BOTH REFUSE a "
        "spatially-varying scene as out-of-class (0/20, measured twice). L2 makes "
        "that case ADMISSIBLE by Land's Retinex first step: reflectance is "
        "recovered from SPATIAL RATIOS of neighbouring cone activity. The anchor "
        "is LOCALIZED -- l2_locale_stats reads a per-channel max/min/count over "
        "the LOCALE's own membership (Neighbours(loc,'in_locale'), hub-scoped, "
        "never a global grab), l2_pair mints the test<->reference locale pairing "
        "AS A RULE (an Eq(pos,pos) join across compares_to; the adapter draws no "
        "cross-frame edge), l2_slowvar DISCOVERS non-circularly whether the field "
        "is slowly varying at each locale (REPORTED, NOT a gate -- its worst-case "
        "envelope is strictly more conservative than the exact verdict, measured), "
        "and l2_recognize renders the held "
        "prototype at the LOCAL illuminant estimate a_loc/pa_loc and admits "
        "within ONE LATTICE STEP -- so the illuminant field cancels LOCALLY, with "
        "NO global estimate and NO path integration. l2_refuse makes a refusal a "
        "POSITIVE datum; l2_recognize_globalanchor is the ABLATION CONTROL (the "
        "spatial-ratio step removed, global anchor restored, everything else "
        "identical, always computed on the SAME graph so the contrast is one "
        "measurement); l2_ncand records the candidate count INSIDE the bound so "
        "the bound's discriminativeness is reported rather than assumed (rung "
        "L1b's lesson). NO NEW RUST and NO NEW CONSTANT: the bound is L1's OWN "
        "falls-out ONE LATTICE STEP, inherited unchanged and valid at locale "
        "grain because the locale contains its own centre; the admission "
        "envelope is L1's tighter MIN clause, localized. 'Slowly varying' itself "
        "falls out -- the admissible per-adjacency variation is the lattice step "
        "over the frame's own measured dynamic range, so the TOTAL admissible "
        "field variation grows with scene extent. BOUNDED: a SLOWLY-VARYING "
        "SINGLE illuminant field via LOCAL ratios. Global illuminant inference "
        "(L3), shadow-vs-reflectance edge ATTRIBUTION (L4) and MULTI-ILLUMINANT "
        "scenes are NOT solved; reflectance is GIVEN at the abstract cone-triple "
        "grain; adjacency is GIVEN not grown; spatial registration at LOCALE "
        "grain is GIVEN (strictly stronger than T3/L1's frame-level assumption) "
        "while IDENTITY correspondence is NOT. Flag-gated on "
        "LightingL2Params.lighting_l2, OFF by default (sec 9 -- default 0 => "
        "byte-identical, seed inert), read ABSENCE-TOLERANTLY via "
        "MaxOver(default 0), never PickUnique. See VISION_LIGHTING_L2_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_lighting_l2_mt",
        "label": ("spatially-varying illuminant: reflectance from LOCAL spatial "
                  "ratios, the field discounted per locale rather than per frame"),
    },
    "nodes": [
        {"local_id": 0, "type": "LightingL2Params", "attrs": {"lighting_l2": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [L2_FRAME_STATS, L2_LOCALE_STATS, L2_PAIR, L2_SLOWVAR,
              L2_RECOGNIZE, L2_REFUSE, L2_RECOGNIZE_GLOBAL],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_lighting_l2.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out, "-", len(SEED["rules"]), "rules")


if __name__ == "__main__":
    main()
