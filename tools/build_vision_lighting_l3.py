#!/usr/bin/env python3
"""Emit seeds/vision_lighting_l3.json — ADVANCED LIGHTING RUNG L3:
GLOBAL ILLUMINANT INFERENCE (pool local -> scene estimate, and CORROBORATE THE
ANCHOR) as pure graph data (NO new Rust).

See VISION_LIGHTING_L3_PREREG.md.

THE PROBLEM L2 HANDED THIS RUNG
--------------------------------
L2 (`vision_lighting_l2`) crossed the spatially-varying illuminant by LOCALIZING
T3/L1's anchor: ghat_loc = a_loc / ra_loc, the locale's own maximum over the
reference locale's own maximum. It scored 60/60 with exact-0 discrimination.

Its noise floor FAILED its own pre-registered rule: 13/1300 (1.0%) false
admissions, and the diagnosis is ARCHITECTURAL, not statistical:

    If a surface IS its locale's maximum then c = a_loc, so the prototype that
    is the REFERENCE locale's maximum renders to p*(a_loc/ra_loc) = a_loc = c
    EXACTLY. A local maximum is therefore ALWAYS recognized as whatever material
    is the reference locale's maximum, whether or not it IS that material.

12 of the 13 leaks are exactly that, matched at residual EXACTLY 0.0. This is
the WHITE-PATCH (ANCHOR) ASSUMPTION, localized: the local anchor's IDENTITY is
ASSUMED, never checked. L2 named the fix and refused to bolt it on (sec 5):
CORROBORATE THE ANCHOR, which is a statement about the WHOLE SCENE.

THE MECHANISM — POOL, THEN CORROBORATE
---------------------------------------
This is V4/PIT's step over V1/V2's: local double-opponent contrast is only the
FIRST step; the local estimates must be POOLED into a GLOBAL illuminant estimate
over a large receptive field. V4 damage leaves colour DISCRIMINATION intact but
ABOLISHES CONSTANCY -- the two are separable stages, and this rung builds the
second one and LESIONS it to show the dissociation.

  1. ghat_loc is already available per locale from L2's own stored statistics
     (l2_a*, l2_ra*). `l3_ghat` writes it as an explicit per-locale float. It is
     a CROSS-FRAME map, so a real value is CORRECT here (the frame/continuum
     invariant: in-frame is integer, between-frames may be real).

  2. `l3_pool` forms ONE SCENE-LEVEL illuminant estimate by POOLING every
     locale's estimate: the CHEBYSHEV CENTER of the pooled estimates --

         L* = Argmin_i  Max_j  Max_ch | ghat_i,ch - ghat_j,ch |
         Ghat_ch = ghat_{L*,ch}

     i.e. THE LOCAL ESTIMATE THAT IS MOST CORROBORATED BY EVERY OTHER LOCALE:
     the one minimising its worst disagreement with the scene. That is a
     ROBUST pool (a mean is dragged by an outlier; this is not), it is a
     GLOBAL statement (every locale participates in every candidate's score),
     it uses the SAME L-infinity the verdict uses, and it introduces NO NEW
     CONSTANT. It is the held `Argmin` -- "bins propose, continuous decides" --
     applied one level up, to locales instead of to prototypes.

  3. `l3_corroborate` CORROBORATES a locale's anchor: the locale's own estimate
     must agree with the SCENE's estimate to within the scene's admissible
     field drift. A locale whose ghat disagrees with the pooled scene estimate
     has an anchor that the rest of the scene does not support, so its anchor
     IDENTITY is NOT corroborated and its surfaces are refused.

  4. `l3_recognize` is L2's verdict AND corroboration. By construction it is
     l2_recognize's where-clause plus ONE conjunct, so L3 can only ever
     SUBTRACT claims from L2, never add any. THAT MAKES L2's OWN l2_* ARM, READ
     OFF THE SAME GRAPH IN THE SAME TICK, THE EXACT POOLING ABLATION (sec 13.2):
     it is this rule with the corroboration conjunct removed and nothing else
     changed. No duplicate rule is shipped for it.

THE ENVELOPE FALLS OUT — NO NEW CONSTANT (sec 13)
--------------------------------------------------
L2's `l2_slowvar` derives the PAIRWISE, ADJACENT-locale budget: using locale i's
estimate where locale j's is true displaces a rendered prototype by
p*|ghat_i - ghat_j| with p <= ra_i, and requiring that to stay within ONE
LATTICE STEP, plus the TWO anchors' half-step observation roundings, gives

    ra_i * | ghat_i - ghat_j |  <=  LS + HS + HS·(ra_i/ra_j)      (adjacent)

The pooled center is NOT adjacent to locale i -- it is at most N-1 adjacencies
away, where N is the number of locales the frame ACTUALLY HAS. Accumulating the
same per-adjacency budget along that path, and using N >= N-1 as the safe
over-estimate:

    ra_i,ch * | ghat_i,ch - Ghat_ch |  <=  N*LS + HS + HS       for every ch

N IS READ FROM THE DATA (`Count` over the frame's own locales), exactly as L1's
in-class envelope counted `n` from the data. LS and HS are L1's OWN inherited
lattice step and half step. NOTHING IS TUNED AND NOTHING IS NEW: the seed's
entire numeric literal set is {0.0, 0.5, 1.0, 1.0e9} -- identical to L2's.

This is why the envelope GROWS WITH SCENE EXTENT, which is the same property L2
derived for the field itself: a bigger scene admits more total drift while every
adjacency stays sub-step. A corroboration bound that did NOT scale with N would
refuse L2's own headline (measured in the prereg's build-phase note).

WHY THIS IS NOT `l2_slowvar` AGAIN
-----------------------------------
`l2_slowvar` is PAIRWISE and ADJACENT, and L2 measured it to be STRICTLY MORE
CONSERVATIVE than the exact verdict it would precede, which is why it ships as a
DISCOVERY and gates nothing. `l3_corroborate` is a GLOBAL statement against a
POOLED estimate the scene had to agree on first -- it is LOOSER locally (the
N-scaled envelope) and yet CATCHES SOMETHING SLOWVAR CANNOT: a locale whose
anchor is a different MATERIAL from its reference counterpart's anchor produces
a ghat that is wrong by a REFLECTANCE RATIO, not by a field slope, and no
amount of local adjacency-checking sees that. Only the scene does.

THE RULES (every decision is a RULE -- CLAUDE.md sec 0)
-------------------------------------------------------
  l3_ghat          the per-locale illuminant estimate, made explicit.
  l3_pool          THE SCENE-LEVEL ESTIMATE: the Chebyshev center of every
                   locale's estimate. Fires once per frame, after EVERY locale
                   has an estimate (a genuine Not(Exists ...) quantifier).
  l3_corroborate   THE ANCHOR CORROBORATION: the locale's estimate must agree
                   with the scene's to within the N-scaled falls-out envelope.
  l3_recognize     THE INVARIANT: L2's verdict AND corroboration.
  l3_refuse_uncorroborated / l3_refuse_bound
                   refusal as a POSITIVE datum (sec 1.1 clause 4), and SPLIT BY
                   REASON so "the pool rejected the anchor" and "the bound
                   rejected the render" are distinguishable in the readback.
  l3_recognize_lesioned
                   THE V4 LESION, ALWAYS COMPUTED ON THE SAME GRAPH: the
                   CONSTANCY stage removed entirely -- ghat == 1, no illuminant
                   discounting at all -- with the SAME codebook, the SAME
                   L-infinity verdict and the SAME inherited bound. Under a
                   changed illuminant it must ABOLISH constancy; under the
                   reference illuminant it must leave DISCRIMINATION intact.
                   That is the biology's own dissociation, made measurable.

T3, L1, L1b AND L2 ARE NOT MODIFIED. Their seeds stay byte-identical; L3 reads
L2's stored locale statistics and writes ONLY its own l3_*/l3l_* namespace, so
all arms are readable from ONE graph.

Flag-gated on LightingL3Params.lighting_l3, OFF by default (sec 9), read
ABSENCE-TOLERANTLY via MaxOver(..., default 0) and NEVER via PickUnique.

NO new Rust: reuses Div/Times/Minus/Abs/Max/Plus/Lte/Gt/Lt/MinOver/MaxOver/
Argmin/Count/Filter/Neighbours/NodesOfType/Not/And/Exists + run_rules.

BOUNDED: ONE scene-level illuminant estimate with anchor corroboration.
Shadow-vs-reflectance EDGE ATTRIBUTION (L4) and MULTI-ILLUMINANT scenes are NOT
solved. Reflectance is GIVEN at the abstract cone-triple grain. Locale-grain
spatial registration is GIVEN (inherited from L2); adjacency is GIVEN, not
grown; IDENTITY correspondence is NOT given.

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_lighting_l3.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms) -----------------------------------
# THE KNOWN TRAP (process rule 4, and VISION_LIGHTING_RESULTS.md's central
# finding): some Terms take an `items` LIST and some take `a`/`b`. Writing a LIST
# term in a/b form parses to an EMPTY operand list -- AND AN EMPTY PRODUCT IS 1 --
# which turned T3's invariant into Eq(1,1): a UNIVERSAL CONTAINER with a flawless
# score. Every constructor below states its form and the gate is
# POSITIVE-CONTROLLED against exactly this defect (sec 12.3).
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


def Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}


def Exists(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}


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

# THE RECOGNITION BOUND -- L1's OWN falls-out ONE LATTICE STEP, INHERITED through
# L2 UNCHANGED and NOT re-derived: 1/2 (the observation's own rounding) +
# 1/2*(r/a) with r/a <= 1 because the anchor is a maximum over a set containing
# the surface itself (the locale contains its own centre).
LATTICE_STEP = 1.0

# HALF a lattice step -- the maximum displacement a single round() introduces.
# The corroboration envelope carries exactly TWO of these (the two anchors'
# observation roundings), on top of the N-scaled field-drift budget.
HALF_STEP = 0.5

# The MinOver default when the codebook is EMPTY: a value that cannot pass the
# bound, so an absent population REFUSES rather than silently admitting (an
# absence must never read as a match -- sec 1.1).
NO_CANDIDATE = 1.0e9


def ENABLED():
    """The L3 flag, read ABSENCE-TOLERANTLY.

    MaxOver with an explicit default returns 0.0 when NO LightingL3Params node
    exists, so the seed is inert in a graph that never loaded it. Deliberately
    NOT PickUnique on a params node (process rule 3): PickUnique returns None on
    an absent node, which silently changes behaviour instead of reading as OFF.
    """
    return Gt(MaxOver(NodesOf("LightingL3Params"), "lp",
                      A(V("lp"), "lighting_l3"), default=Lit(0.0)),
              Lit(0.5))


# ---------------------------------------------------------------------------
# l3_ghat -- the per-locale illuminant estimate, MADE EXPLICIT.
# ---------------------------------------------------------------------------
L3_GHAT = {
    "name": "l3_ghat",
    "comment": (
        "Writes the locale's OWN illuminant estimate ghat_loc = a_loc / ra_loc "
        "as an explicit per-channel float, from the statistics L2 ALREADY "
        "STORED on the locale (l2_a* from the locale's own membership, l2_ra* "
        "copied from its paired reference counterpart). L2 computes this same "
        "quotient INSIDE l2_recognize's render; L3 needs it as a first-class "
        "value because POOLING quantifies over it across locales, and a fold "
        "cannot reach inside another rule's expression. "
        "A REAL VALUE IS CORRECT HERE and is not a category error: ghat is a "
        "CROSS-FRAME MAP (test frame -> reference frame), and the "
        "frame/continuum invariant says in-frame coordinates are integers while "
        "the maps BETWEEN frames may be real. The surfaces' cones stay integers "
        "throughout. "
        "Guarded on l2_paired (so it only ever runs on a test locale that L2's "
        "own join has already paired -- the reference frame's locales are never "
        "paired and never get an estimate) and on ra > 0 on EVERY channel, so a "
        "degenerate reference locale REFUSES by never acquiring an estimate "
        "rather than dividing by zero. The l3_ghat_done guard makes it fire once "
        "per locale so run_rules converges. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["loc", "in_locale", "anysurf"]],
    "where": And([
        ENABLED(),
        Lt(A(V("loc"), "l3_ghat_done"), Lit(0.5)),
        Gt(A(V("loc"), "l2_paired"), Lit(0.5)),
    ] + [Gt(A(V("loc"), "l2_ra" + ch), Lit(0.0)) for ch in CH]),
    "effects": (
        [["set_attr", "loc", "l3_g" + ch,
          term(Div(A(V("loc"), "l2_a" + ch), A(V("loc"), "l2_ra" + ch)))]
         for ch in CH]
        + [["set_attr", "loc", "l3_ghat_done", term(Lit(1.0))]]
    ),
}


def _disagreement(i, j):
    """The L-infinity disagreement between two locales' illuminant estimates.

    Max over channels (not a sum, not a Euclidean norm) because each channel
    rounds INDEPENDENTLY -- the SAME L-infinity l2_recognize's verdict uses,
    reused one level up so the pooling and the verdict agree on what "far"
    means.
    """
    return Max([Abs(Minus(A(i, "l3_g" + ch), A(j, "l3_g" + ch))) for ch in CH])


# ---------------------------------------------------------------------------
# l3_pool -- THE SCENE-LEVEL ILLUMINANT ESTIMATE. This is the rung.
# ---------------------------------------------------------------------------
L3_POOL = {
    "name": "l3_pool",
    "comment": (
        "THE GLOBAL ILLUMINANT INFERENCE -- ONE scene-level estimate POOLED from "
        "every locale's local estimate. The pool is the CHEBYSHEV CENTER: "
        "Argmin over the frame's locales of (MaxOver every other locale of the "
        "L-infinity disagreement between their estimates). In words: THE LOCAL "
        "ESTIMATE THAT IS MOST CORROBORATED BY THE WHOLE SCENE -- the one whose "
        "worst disagreement with any other locale is smallest. "
        "WHY A CHEBYSHEV CENTER AND NOT A MEAN: a mean is dragged by an outlier, "
        "so a single locale with a wrong anchor would move the very estimate "
        "that is supposed to CATCH wrong anchors; the center is robust, and the "
        "corroboration it supports is therefore not self-defeating. It is also "
        "the held Argmin -- 'bins propose, continuous decides' -- applied one "
        "level up, to LOCALES rather than to prototypes, and it introduces NO "
        "NEW CONSTANT. "
        "THIS IS THE V4/PIT STEP: local double-opponent contrast (L2) is only "
        "the first step; the local estimates must be POOLED over a large "
        "receptive field into a scene-level illuminant before constancy exists. "
        "Every locale participates in every candidate's score, so this is a "
        "genuinely GLOBAL statement and not another local one. "
        "Fires ONCE per test frame, and only after EVERY one of its locales has "
        "an estimate -- a genuine Not(Exists a locale still missing one), so the "
        "pool is never formed from a partial scene. l3_n_loc records the locale "
        "COUNT from the DATA; the corroboration envelope scales with it, which "
        "is why nothing here is a magic number. Matched through compares_to so "
        "it only ever runs on a TEST frame. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "compares_to", "ref"],
              ["frame", "has_locale", "anyloc"]],
    "where": And([
        ENABLED(),
        Lt(A(V("frame"), "l3_pooled"), Lit(0.5)),
        Gt(Count(Nbrs(V("frame"), "has_locale")), Lit(0.5)),
        Not(Exists(Nbrs(V("frame"), "has_locale"), "q",
                   Lt(A(V("q"), "l3_ghat_done"), Lit(0.5)))),
    ]),
    "effects": (
        [["set_attr", "frame", "l3_G" + ch,
          term(A(Argmin(Nbrs(V("frame"), "has_locale"), "i",
                        MaxOver(Nbrs(V("frame"), "has_locale"), "j",
                                _disagreement(V("i"), V("j")),
                                default=Lit(0.0)),
                        default=Lit(0.0)),
                 "l3_g" + ch))]
         for ch in CH]
        + [["set_attr", "frame", "l3_n_loc",
            term(Count(Nbrs(V("frame"), "has_locale")))],
           ["set_attr", "frame", "l3_pooled", term(Lit(1.0))]]
    ),
}


def _corroborate_clause(frame, loc, ch):
    """THE ANCHOR CORROBORATION CLAUSE, per channel.

        ra_i,ch * | ghat_i,ch - Ghat_ch |  <=  N*LS + HS + HS

    DERIVATION (sec 13 -- every term falls out; nothing is tuned).
    Using the SCENE's estimate where locale i's is true displaces a rendered
    prototype p by p*|ghat_i - Ghat|, and p <= ra_i (the reference local anchor
    bounds every prototype the locale can contain -- L2's own l2_slowvar
    derivation, verbatim). Requiring that displacement to stay within the
    admissible drift gives the left-hand side.

    THE BUDGET: L2 derives ONE LATTICE STEP of admissible field drift PER
    ADJACENCY. The pooled center is not adjacent to locale i -- it is at most
    N-1 adjacencies away in a scene of N locales -- so the same per-adjacency
    budget accumulates along that path, and N >= N-1 is the safe over-estimate.
    N IS COUNTED FROM THE DATA (l3_n_loc), exactly as L1's in-class envelope
    counted `n` from the data. The two HS terms are the two anchors' own
    half-step observation roundings, the same pair l2_slowvar carries.

    The envelope therefore GROWS WITH SCENE EXTENT -- the same property L2
    derived for the admissible field itself. An envelope that did NOT scale with
    N would refuse L2's own headline, which is a statement about the algebra and
    not a fitted choice.
    """
    lhs = Times([A(loc, "l2_ra" + ch),
                 Abs(Minus(A(loc, "l3_g" + ch), A(frame, "l3_G" + ch)))])
    envelope = Plus([Times([A(frame, "l3_n_loc"), Lit(LATTICE_STEP)]),
                     Lit(HALF_STEP), Lit(HALF_STEP)])
    return Lte(lhs, envelope)


# ---------------------------------------------------------------------------
# l3_corroborate -- THE ANCHOR IS CHECKED, NOT ASSUMED.
# ---------------------------------------------------------------------------
L3_CORROBORATE = {
    "name": "l3_corroborate",
    "comment": (
        "CORROBORATES THE LOCAL ANCHOR AGAINST THE WHOLE SCENE -- the fix L2 "
        "NAMED and refused to bolt on (sec 5). L2's ghat_loc = a_loc/ra_loc "
        "ASSUMES the test locale's maximum is the SAME MATERIAL as the reference "
        "locale's maximum. When that assumption is wrong, ghat_loc is wrong by a "
        "REFLECTANCE RATIO, and the locale then renders its own maximum onto "
        "itself at residual EXACTLY 0.0 -- which is precisely L2's measured "
        "13/1300 leak, 12 of them local maxima. "
        "The corroboration: the locale's estimate must agree with the POOLED "
        "SCENE estimate to within the falls-out N-scaled envelope, on EVERY "
        "channel. A locale whose anchor is a different material produces an "
        "estimate the rest of the scene does not support, and is refused. "
        "WHY THIS IS NOT l2_slowvar AGAIN: slowvar is PAIRWISE and ADJACENT, and "
        "L2 measured it STRICTLY MORE CONSERVATIVE than the exact verdict, which "
        "is why it gates nothing there. This clause is LOOSER locally (the "
        "envelope scales with N) and yet catches something no amount of local "
        "adjacency-checking can see: a wrong anchor IDENTITY is a reflectance "
        "error, not a field slope, and only a GLOBAL estimate exposes it. "
        "The l3_corr guard makes it fire once per locale so run_rules converges. "
        "Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_locale", "loc"]],
    "where": And([
        ENABLED(),
        Lt(A(V("loc"), "l3_corr"), Lit(0.5)),
        Gt(A(V("frame"), "l3_pooled"), Lit(0.5)),
        Gt(A(V("loc"), "l3_ghat_done"), Lit(0.5)),
    ] + [_corroborate_clause(V("frame"), V("loc"), ch) for ch in CH]),
    "effects": [
        ["set_attr", "loc", "l3_corr", term(Lit(1.0))],
    ],
}


def _residual(surf, anch, ranch, cand, ch, akey, rkey):
    """| c_ch - p_ch * (a_ch / pa_ch) | -- the per-channel CONTINUOUS residual.

    EXTRACTED VERBATIM from l2_recognize's _render_residual (single source of
    truth). Div(a,pa) is the LOCAL illuminant estimate, Times([p, ghat]) RENDERS
    the held prototype at it, Minus + Abs give the residual on the stepped
    lattice. L3 changes NOTHING about the render -- it changes only WHETHER THE
    ANCHOR THAT PRODUCED IT WAS CORROBORATED.
    """
    ghat = Div(A(anch, akey + ch), A(ranch, rkey + ch))
    return Abs(Minus(A(surf, "c" + ch), Times([A(cand, "p" + ch), ghat])))


def _residual_lesioned(surf, cand, ch):
    """THE CONSTANCY STAGE LESIONED: ghat == 1, no illuminant discounting at all.

    | c_ch - p_ch |. The SAME codebook, the SAME L-infinity, the SAME bound --
    only the illuminant map is gone. This is the V4 lesion: it must leave
    DISCRIMINATION intact (under the reference illuminant, distinct materials
    are still told apart) while ABOLISHING CONSTANCY (under a changed
    illuminant, the same material is no longer recognized).
    """
    return Abs(Minus(A(surf, "c" + ch), A(cand, "p" + ch)))


def _verdict(surf, anch, ranch, cand, akey, rkey):
    """The L-infinity residual over the three channels -- THE CONTINUOUS VERDICT.

    Max (not a sum, not a Euclidean norm) because each channel rounds
    INDEPENDENTLY, so the per-channel ONE-LATTICE-STEP bound is also the vector
    bound. Inherited from l2_recognize (and from l1_recognize before it)
    UNCHANGED.
    """
    return Max([_residual(surf, anch, ranch, cand, ch, akey, rkey) for ch in CH])


def _verdict_lesioned(surf, cand):
    return Max([_residual_lesioned(surf, cand, ch) for ch in CH])


def _codebook(ref):
    """The reference frame's OWN identity population -- hub-scoped (sec 12.1).

    T3's INTEGER li_mint SurfaceIdentity nodes, REUSED UNMODIFIED through L2.
    The DISCRETE PROPOSAL; the continuous verdict decides among them.
    """
    return Nbrs(ref, "has_identity")


def _best(ref, surf, anch, ranch, akey, rkey):
    return MinOver(_codebook(V(ref)), "cand",
                   _verdict(V(surf), V(anch), V(ranch), V("cand"), akey, rkey),
                   default=Lit(NO_CANDIDATE))


def _best_lesioned(ref, surf):
    return MinOver(_codebook(V(ref)), "cand",
                   _verdict_lesioned(V(surf), V("cand")),
                   default=Lit(NO_CANDIDATE))


# ---------------------------------------------------------------------------
# l3_recognize -- THE INVARIANT: L2's verdict AND a CORROBORATED anchor.
# ---------------------------------------------------------------------------
L3_RECOGNIZE = {
    "name": "l3_recognize",
    "comment": (
        "THE GLOBALLY-CORROBORATED LIGHTING INVARIANT. A surface is recognized "
        "iff (a) its locale was PAIRED by L2's join, (b) THE LOCALE'S ANCHOR WAS "
        "CORROBORATED BY THE POOLED SCENE ESTIMATE, and (c) the best candidate "
        "in the reference frame's held codebook, rendered at the LOCAL "
        "illuminant estimate, lies within ONE LATTICE STEP on every channel. "
        "(c) IS L2's ENTIRE VERDICT, TERM FOR TERM. (b) IS THE ONLY ADDITION. "
        "THAT IS WHAT MAKES L2's OWN l2_* ARM THE EXACT POOLING ABLATION (sec "
        "13.2), read off the SAME graph in the SAME tick: it is this rule minus "
        "the corroboration conjunct and nothing else, so no duplicate ablation "
        "rule is shipped and the contrast is ONE measurement rather than two "
        "experiments. It also means L3 can only ever SUBTRACT claims from L2 and "
        "can NEVER widen an invariance class -- an admitted L3 row is "
        "byte-identical to L2's own answer on that row. "
        "l3_ncand records the number of candidates INSIDE the bound (rung L1b's "
        "lesson: reporting only the winner's residual hid a bound that never "
        "bound). MinOver carries an explicit NO_CANDIDATE default so an EMPTY "
        "codebook REFUSES rather than silently admitting (sec 1.1). Flag-gated, "
        "OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["R", "sits_in", "loc"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("loc"), "l2_paired"), Lit(0.5)),
        Gt(A(V("loc"), "l3_corr"), Lit(0.5)),
        Lte(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"), Lit(LATTICE_STEP)),
    ]),
    "effects": [
        ["set_attr", "R", "l3_recognized", term(Lit(1.0))],
        ["set_attr", "R", "l3_id", term(A(
            Argmin(_codebook(V("ref")), "cand",
                   _verdict(V("R"), V("loc"), V("loc"), V("cand"), "l2_a", "l2_ra"),
                   default=Lit(0.0)),
            "sid_key"))],
        ["set_attr", "R", "l3_resid",
         term(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"))],
        ["set_attr", "R", "l3_ncand", term(Count(Filter(
            _codebook(V("ref")), "cand",
            Lte(_verdict(V("R"), V("loc"), V("loc"), V("cand"), "l2_a", "l2_ra"),
                Lit(LATTICE_STEP)))))],
        ["set_attr", "R", "l3_status", term(Lit("l3_recognized"))],
    ],
}


# ---------------------------------------------------------------------------
# l3_refuse_uncorroborated -- THE REFUSAL THIS RUNG EXISTS TO PRODUCE.
# ---------------------------------------------------------------------------
L3_REFUSE_UNCORR = {
    "name": "l3_refuse_uncorroborated",
    "comment": (
        "Marks l3_status='l3_refused_uncorroborated' for a surface whose locale "
        "was paired and whose frame was pooled, but whose ANCHOR THE SCENE DOES "
        "NOT CORROBORATE. THIS IS THE RUNG'S OWN CONTRIBUTION MADE VISIBLE: it "
        "is exactly the population L2 would have admitted on an assumed anchor. "
        "Splitting refusal BY REASON (this rule) from refusal by the render's "
        "bound (l3_refuse_bound) means the readback distinguishes 'the pool "
        "rejected the anchor' from 'the bound rejected the render', so the "
        "leak-closing mechanism is auditable from the results file rather than "
        "inferred. A refusal is a POSITIVE datum (sec 1.1 clause 4): without "
        "these rules 'refused' and 'never ran' are indistinguishable. "
        "Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["R", "sits_in", "loc"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("frame"), "l3_pooled"), Lit(0.5)),
        Gt(A(V("loc"), "l2_paired"), Lit(0.5)),
        Lt(A(V("loc"), "l3_corr"), Lit(0.5)),
        Lt(A(V("R"), "l3_recognized"), Lit(0.5)),
    ]),
    "effects": [
        ["set_attr", "R", "l3_status", term(Lit("l3_refused_uncorroborated"))],
    ],
}


# ---------------------------------------------------------------------------
# l3_refuse_bound -- refusal by the render's own bound (L2's refusal, inherited).
# ---------------------------------------------------------------------------
L3_REFUSE_BOUND = {
    "name": "l3_refuse_bound",
    "comment": (
        "Marks l3_status='l3_refused_bound' for a surface whose locale WAS "
        "corroborated but whose best rendered candidate exceeds the "
        "lattice-step bound. This is L2's own refusal condition, inherited "
        "unchanged; together with l3_refuse_uncorroborated and l3_recognize it "
        "PARTITIONS every surface whose locale was paired, so the readback is "
        "total and no surface silently falls through. Flag-gated, OFF by "
        "default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["R", "sits_in", "loc"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("loc"), "l3_corr"), Lit(0.5)),
        Lt(A(V("R"), "l3_recognized"), Lit(0.5)),
        Not(Lte(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"),
                Lit(LATTICE_STEP))),
    ]),
    "effects": [
        ["set_attr", "R", "l3_status", term(Lit("l3_refused_bound"))],
        ["set_attr", "R", "l3_resid",
         term(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"))],
    ],
}


# ---------------------------------------------------------------------------
# l3_recognize_lesioned -- THE V4 DISSOCIATION, ALWAYS COMPUTED ON THE SAME GRAPH.
# ---------------------------------------------------------------------------
L3_RECOGNIZE_LESIONED = {
    "name": "l3_recognize_lesioned",
    "comment": (
        "THE V4 LESION: THE CONSTANCY STAGE REMOVED, AND NOTHING ELSE CHANGED. "
        "Identical to l3_recognize term-for-term except that the illuminant map "
        "is GONE -- the held prototype is compared to the observation RAW, "
        "ghat == 1, no anchor, no ratio, no pooling. The same codebook, the same "
        "L-infinity verdict, the same inherited ONE-LATTICE-STEP bound, the same "
        "Argmin. It writes its own l3l_* namespace and is ALWAYS computed when "
        "the flag is on, so the intact-vs-lesioned contrast is read from ONE "
        "graph in ONE run. "
        "WHAT IT IS FOR: V4 damage leaves colour DISCRIMINATION intact but "
        "ABOLISHES colour CONSTANCY -- the two are separable stages in the "
        "biology, and that dissociation is the sharpest available check that "
        "this rung built the constancy stage and not merely a stricter filter. "
        "The prediction is DOUBLE and both halves are measured: under the "
        "REFERENCE illuminant the lesioned arm must still tell distinct "
        "materials apart (discrimination INTACT -- it is the identity map, so "
        "the codebook still separates); under a CHANGED illuminant it must fail "
        "to recognize the same materials (constancy ABOLISHED) while the intact "
        "arm holds. A lesion that killed BOTH would mean the arm is simply dead "
        "(sec 1.1 clause 4) and the dissociation would be worthless -- which is "
        "exactly why the discrimination half is measured and not assumed. "
        "Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Lte(_best_lesioned("ref", "R"), Lit(LATTICE_STEP)),
    ]),
    "effects": [
        ["set_attr", "R", "l3l_recognized", term(Lit(1.0))],
        ["set_attr", "R", "l3l_id", term(A(
            Argmin(_codebook(V("ref")), "cand",
                   _verdict_lesioned(V("R"), V("cand")),
                   default=Lit(0.0)),
            "sid_key"))],
        ["set_attr", "R", "l3l_resid", term(_best_lesioned("ref", "R"))],
    ],
}


SEED = {
    "id": "vision_lighting_l3",
    "version": "1.0.0",
    "depends_on": ["vision_lighting_l2"],
    "description": (
        "ADVANCED LIGHTING RUNG L3 -- GLOBAL ILLUMINANT INFERENCE. L2 crossed "
        "the spatially-varying illuminant by LOCALIZING the anchor, and its "
        "noise floor FAILED its own pre-registered rule at 13/1300 (1.0%) with "
        "an ARCHITECTURAL diagnosis: 12 of 13 leaks are surfaces that ARE their "
        "own locale's MAXIMUM, matched at residual EXACTLY 0.0, because "
        "ghat = a_loc/ra_loc renders the reference locale's maximum prototype "
        "onto a local maximum identically -- the WHITE-PATCH (ANCHOR) "
        "ASSUMPTION, localized. L3 CORROBORATES THE ANCHOR, which L2 named as a "
        "necessarily GLOBAL statement. l3_ghat makes each locale's illuminant "
        "estimate explicit (a CROSS-FRAME map, so a real value is correct); "
        "l3_pool forms ONE SCENE-LEVEL estimate by POOLING every locale's -- the "
        "CHEBYSHEV CENTER, the local estimate MOST CORROBORATED BY THE WHOLE "
        "SCENE (Argmin over locales of the MaxOver disagreement with every other "
        "locale), robust where a mean would be dragged by the very outlier it "
        "must catch, and the V4/PIT step over L2's V1/V2 local contrast; "
        "l3_corroborate then requires each locale's estimate to agree with the "
        "scene's within an envelope that FALLS OUT of L2's own per-adjacency "
        "drift budget scaled by the locale COUNT READ FROM THE DATA; "
        "l3_recognize is L2's verdict AND corroboration -- term for term "
        "l2_recognize plus ONE conjunct, so L3 can only SUBTRACT claims and "
        "L2's own arm on the SAME graph IS the exact pooling ABLATION; "
        "l3_refuse_uncorroborated / l3_refuse_bound make refusal a POSITIVE "
        "datum SPLIT BY REASON; and l3_recognize_lesioned is THE V4 DISSOCIATION "
        "-- the constancy stage removed entirely (ghat == 1), always computed on "
        "the same graph, so that colour DISCRIMINATION surviving while CONSTANCY "
        "is ABOLISHED is a MEASUREMENT. NO NEW RUST and NO NEW CONSTANT: the "
        "literal set is {0.0, 0.5, 1.0, 1.0e9}, identical to L2's; the bound is "
        "L1's OWN falls-out ONE LATTICE STEP inherited through L2. T3, L1, L1b "
        "and L2 are NOT modified -- L3 reads L2's stored locale statistics and "
        "writes only its own l3_*/l3l_* namespace. BOUNDED: ONE scene-level "
        "illuminant estimate with anchor corroboration. Shadow-vs-reflectance "
        "EDGE ATTRIBUTION (L4) and MULTI-ILLUMINANT scenes are NOT solved; "
        "reflectance is GIVEN at the abstract cone-triple grain; locale-grain "
        "registration and adjacency are GIVEN, not grown; IDENTITY "
        "correspondence is NOT given. Flag-gated on "
        "LightingL3Params.lighting_l3, OFF by default (sec 9 -- default 0 => "
        "byte-identical, seed inert), read ABSENCE-TOLERANTLY via "
        "MaxOver(default 0), never PickUnique. See VISION_LIGHTING_L3_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_lighting_l3_mt",
        "label": ("global illuminant inference: local estimates POOLED into one "
                  "scene estimate that CORROBORATES the anchor it was built from"),
    },
    "nodes": [
        {"local_id": 0, "type": "LightingL3Params", "attrs": {"lighting_l3": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [L3_GHAT, L3_POOL, L3_CORROBORATE, L3_RECOGNIZE,
              L3_REFUSE_UNCORR, L3_REFUSE_BOUND, L3_RECOGNIZE_LESIONED],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_lighting_l3.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out, "-", len(SEED["rules"]), "rules")


if __name__ == "__main__":
    main()
