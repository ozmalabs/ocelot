#!/usr/bin/env python3
"""Emit seeds/vision_lighting_l3b.json — ADVANCED LIGHTING RUNG L3b:
THE ANCHOR OF THE ANCHOR (LEAVE-ONE-OUT MUTUAL CORROBORATION) as pure graph
data (NO new Rust, NO new constant).

See VISION_LIGHTING_L3B_PREREG.md.

THE PROBLEM L3 HANDED THIS RUNG
--------------------------------
L3 pooled the per-locale illuminant estimates into ONE scene-level estimate
Ghat and required each locale's ghat to agree with it. The leak fell
13/1300 -> 5/1300, but did NOT close, and the residual is SELF-REFERENTIAL:

    The pool is a CHEBYSHEV CENTER, i.e. a MEDOID, so Ghat IS some locale's
    OWN ghat. That locale's deviation from the pool is EXACTLY 0, so it
    CORROBORATES UNCONDITIONALLY. The pool's own centre cannot be refused by
    the corroboration it defines.

Measured: the corroborated set == the Chebyshev-centre set in 10/10 inspected
noise scenes, and all five surviving leaks sat there at residual 0.0. THE
WHITE-PATCH ASSUMPTION WAS PUSHED UP ONE LEVEL (13 exposed locales -> 1), NOT
ELIMINATED.

THE AUDIT (prereg STEP 1) — six candidate certifiers, one survives
------------------------------------------------------------------
  C1 Chebyshev centre (L3's own pool)       CIRCULAR   (deviation == 0 by
                                                        construction)
  C2 per-channel MEDIAN                     CIRCULAR   (measured: the median
                                                        vector IS locale 6's
                                                        estimate in 5/5
                                                        headline fields)
  C3 LEAVE-ONE-OUT mutual corroboration     GENUINE    (individually) <- BUILT
  C4 cross-frame / temporal persistence     EXTERNAL   (assumes stationarity;
                                                        no temporal axis exists)
  C5 the frame's dynamic-range ceiling      EXTERNAL   (+ NON-LOCAL: already
                                                        killed by the k=1 rung)
  C6 cone-channel redundancy (achromaticity)EXTERNAL   (assumes an achromatic
                                                        illuminant; UNSOUND at
                                                        the landed operating
                                                        point — 182/325 noise
                                                        locales sit below the
                                                        landed chromatic gain)

THE MECHANISM — CERTIFY EACH LOCALE BY THE OTHERS, NEVER BY ITSELF
-------------------------------------------------------------------
`l3b_pool_loo` computes, PER LOCALE i, a LEAVE-ONE-OUT scene estimate

    Ghat^(-i) = ghat_{L*(i)},   L*(i) = Argmin_{j != i} Max_{k != i} |ghat_j - ghat_k|

i.e. the Chebyshev centre of EVERY OTHER LOCALE'S estimate. Because the
Argmin ranges over a set that EXCLUDES i, ghat_i is NEVER its own certifier
and the deviation |ghat_i - Ghat^(-i)| is not 0 by construction. The exclusion
is `Not(Eq(j, loc))`, and `Eq` compares Value::Node BY ID
(runners/dsl/src/value.rs:225) — a held primitive, no new Rust.

`l3b_corroborate` then applies L3's OWN envelope, UNCHANGED, against that
leave-one-out pool. `l3b_recognize` is `l3_recognize` with the corroboration
conjunct SWAPPED (l3_corr -> l3b_corr) and NOTHING ELSE CHANGED, so L3's own
l3_* arm READ OFF THE SAME GRAPH IN THE SAME TICK IS THE EXACT ABLATION
(sec 13.2) — exactly as L2's arm was L3's pooling ablation. No duplicate rule
ships, and L3b can only ever SUBTRACT claims from L2's verdict.

`l3b_dev` writes BOTH deviations as first-class floats so the audit's central
claim is EXHIBITED ON THE GRAPH rather than asserted: `l3b_dev_cheb` is the
locale's deviation from L3's SELF-INCLUDING pool (identically 0 at the centre —
THE CIRCULARITY, MEASURED) and `l3b_dev_loo` is its deviation from the
leave-one-out pool (the twin-locale residual is exactly the case where THIS
one is 0 too).

WHAT THIS DOES NOT DO — the SET is still uncertified
-----------------------------------------------------
Leave-one-out removes every locale's SELF-certification. It does NOT certify
the SET: a scene in which every locale's anchor is wrong IN THE SAME WAY
corroborates unanimously. The prereg's R2 arm exhibits precisely that by
measurement — reflectances scaled by kappa produce 13/13 corroboration with a
recovered Ghat that is wrong by exactly kappa. CONSTANCY ON THIS SUBSTRATE IS
ANCHOR-RELATIVE; THE ANCHOR IS A DECLARED CHOICE, NOT A MEASUREMENT.

NO NEW CONSTANT: the literal set is {0.0, 0.5, 1.0, 1.0e9} — identical to L2's
and L3's. The bound is L1's OWN falls-out ONE LATTICE STEP inherited unchanged;
the envelope N*LS + HS + HS is L3's OWN, inherited unchanged, with N counted
from the data.

T3, L1, L1b, L2 AND L3 ARE NOT MODIFIED. Their seeds stay byte-identical; L3b
reads L3's stored per-locale estimates and writes ONLY its own l3b_* namespace,
so every arm is readable from ONE graph.

Flag-gated on LightingL3bParams.lighting_l3b, OFF by default (sec 9), read
ABSENCE-TOLERANTLY via MaxOver(..., default 0) and NEVER via PickUnique.

This is a seed BUILDER (emits graph data) — admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_lighting_l3b.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms) -----------------------------------
# THE KNOWN TRAP (process rule 4): some Terms take an `items` LIST and some take
# `a`/`b`. Writing a LIST term in a/b form parses to an EMPTY operand list — AND
# AN EMPTY PRODUCT IS 1 — which turned T3's invariant into Eq(1,1): a UNIVERSAL
# CONTAINER with a flawless score. Every constructor states its form and the gate
# is POSITIVE-CONTROLLED against exactly this defect (sec 12.3).
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
    """`items` LIST (jsonio.rs:1274). NEVER a/b — that is the EMPTY-PRODUCT trap."""
    return {"type": "Times", "items": list(items)}


def Plus(items):
    """`items` LIST (jsonio.rs:1269). NEVER a/b — an empty sum is 0."""
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

# THE RECOGNITION BOUND — L1's OWN falls-out ONE LATTICE STEP, inherited through
# L2 and L3 UNCHANGED and NOT re-derived.
LATTICE_STEP = 1.0

# HALF a lattice step — the maximum displacement a single round() introduces.
# The corroboration envelope carries exactly TWO of these, exactly as L3's does.
HALF_STEP = 0.5

# The MinOver default when the codebook is EMPTY: a value that cannot pass the
# bound, so an absent population REFUSES rather than silently admitting (an
# absence must never read as a match — sec 1.1).
NO_CANDIDATE = 1.0e9


def ENABLED():
    """The L3b flag, read ABSENCE-TOLERANTLY.

    MaxOver with an explicit default returns 0.0 when NO LightingL3bParams node
    exists, so the seed is inert in a graph that never loaded it. Deliberately
    NOT PickUnique on a params node (process rule 3): PickUnique returns None on
    an absent node, which silently changes behaviour instead of reading as OFF.
    """
    return Gt(MaxOver(NodesOf("LightingL3bParams"), "lp",
                      A(V("lp"), "lighting_l3b"), default=Lit(0.0)),
              Lit(0.5))


def _disagreement(i, j):
    """The L-infinity disagreement between two locales' illuminant estimates.

    EXTRACTED VERBATIM from L3's `_disagreement` (single source of truth): Max
    over channels, because each channel rounds INDEPENDENTLY — the SAME
    L-infinity the verdict uses, so pooling and verdict agree on what "far"
    means. L3b changes NOTHING about the metric; it changes only WHICH SET the
    fold ranges over.
    """
    return Max([Abs(Minus(A(i, "l3_g" + ch), A(j, "l3_g" + ch))) for ch in CH])


def _others(frame, loc, var):
    """EVERY LOCALE OF THIS FRAME **EXCEPT** `loc` — the leave-one-out set.

    THIS IS THE WHOLE RUNG. `Eq` compares Value::Node BY ID
    (runners/dsl/src/value.rs:225), so `Not(Eq(var, loc))` excludes exactly the
    locale being certified and nothing else. Because the Argmin below ranges
    over THIS set, `ghat_loc` can NEVER be its own certifier — which is the one
    structural property the audit found that no other candidate has.
    """
    return Filter(Nbrs(frame, "has_locale"), var, Not(Eq(V(var), loc)))


# ---------------------------------------------------------------------------
# l3b_pool_loo — THE LEAVE-ONE-OUT SCENE ESTIMATE, ONE PER LOCALE.
# ---------------------------------------------------------------------------
L3B_POOL_LOO = {
    "name": "l3b_pool_loo",
    "comment": (
        "THE ANCHOR OF THE ANCHOR. For EACH locale i, forms a scene-level "
        "illuminant estimate from EVERY OTHER LOCALE'S estimate and NOT its own: "
        "Ghat^(-i) = the Chebyshev centre of {ghat_j : j != i}. "
        "WHY: L3's pool is a MEDOID, so Ghat IS some locale's own ghat and that "
        "locale's deviation is EXACTLY 0 — it corroborates UNCONDITIONALLY, and "
        "all five of L3's surviving leaks sat exactly there. Excluding i from "
        "its own pool BREAKS THAT SELF-MEMBERSHIP BY CONSTRUCTION. This is the "
        "only one of the six audited candidate certifiers that does so without "
        "importing a new assumption (the median is measurably still circular; "
        "temporal persistence, the dynamic-range ceiling and cone-channel "
        "achromaticity are each an external assumption — a new white patch). "
        "The metric, the fold and the Argmin are L3's OWN, reused verbatim; the "
        "ONLY change is the SET the fold ranges over. NO new constant. "
        "Guarded on Count(others) > 0 so a degenerate single-locale frame "
        "REFUSES by never acquiring a leave-one-out estimate rather than folding "
        "over an empty set (sec 1.1 — an absence must never read as a value). "
        "The l3b_pooled guard makes it fire once per locale so run_rules "
        "converges. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_locale", "loc"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Lt(A(V("loc"), "l3b_pooled"), Lit(0.5)),
        Gt(A(V("frame"), "l3_pooled"), Lit(0.5)),
        Gt(A(V("loc"), "l3_ghat_done"), Lit(0.5)),
        Gt(Count(_others(V("frame"), V("loc"), "cnt")), Lit(0.5)),
    ]),
    "effects": (
        [["set_attr", "loc", "l3b_G" + ch,
          term(A(Argmin(_others(V("frame"), V("loc"), "i"), "i2",
                        MaxOver(_others(V("frame"), V("loc"), "j"), "j2",
                                _disagreement(V("i2"), V("j2")),
                                default=Lit(0.0)),
                        default=Lit(0.0)),
                 "l3_g" + ch))]
         for ch in CH]
        + [["set_attr", "loc", "l3b_pooled", term(Lit(1.0))]]
    ),
}


def _dev(loc, pool_node, pool_prefix):
    """ra_i,ch * |ghat_i,ch - POOL_ch|, maximised over channels.

    The SAME left-hand side L3's corroboration clause uses — written out as a
    first-class float so the audit's claims are READ OFF THE GRAPH rather than
    inferred from which rows were admitted.
    """
    return Max([Times([A(loc, "l2_ra" + ch),
                       Abs(Minus(A(loc, "l3_g" + ch),
                                 A(pool_node, pool_prefix + ch)))])
                for ch in CH])


# ---------------------------------------------------------------------------
# l3b_dev — THE CIRCULARITY, EXHIBITED ON THE GRAPH RATHER THAN ASSERTED.
# ---------------------------------------------------------------------------
L3B_DEV = {
    "name": "l3b_dev",
    "comment": (
        "Writes BOTH deviations as first-class floats so the audit is a "
        "MEASUREMENT and not a claim: "
        "l3b_dev_cheb is the locale's deviation from L3's SELF-INCLUDING pool — "
        "IDENTICALLY 0 AT THE CHEBYSHEV CENTRE, BY CONSTRUCTION, which is "
        "exactly the circularity this rung exists to expose (prereg arm R1, "
        "declared ENTAILED: the measurement makes it VISIBLE, it does not make "
        "it surprising); "
        "l3b_dev_loo is the deviation from the LEAVE-ONE-OUT pool, whose "
        "remaining zeros are the TWIN-LOCALE residual (two locales sharing an "
        "estimate, so leave-one-out can still return ghat_i) — the honest limit "
        "of C3, reported with its count (prereg arm R3). "
        "This rule DECIDES NOTHING; it records. Flag-gated, OFF by default."
    ),
    "match": [["frame", "has_locale", "loc"]],
    "where": And([
        ENABLED(),
        Lt(A(V("loc"), "l3b_dev_done"), Lit(0.5)),
        Gt(A(V("loc"), "l3b_pooled"), Lit(0.5)),
        Gt(A(V("frame"), "l3_pooled"), Lit(0.5)),
    ]),
    "effects": [
        ["set_attr", "loc", "l3b_dev_cheb",
         term(_dev(V("loc"), V("frame"), "l3_G"))],
        ["set_attr", "loc", "l3b_dev_loo",
         term(_dev(V("loc"), V("loc"), "l3b_G"))],
        ["set_attr", "loc", "l3b_dev_done", term(Lit(1.0))],
    ],
}


def _corroborate_clause(frame, loc, ch):
    """THE LEAVE-ONE-OUT CORROBORATION CLAUSE, per channel.

        ra_i,ch * | ghat_i,ch - Ghat^(-i)_ch |  <=  N*LS + HS + HS

    THE ENVELOPE IS L3's OWN, INHERITED UNCHANGED AND NOT RE-DERIVED — the same
    N-scaled per-adjacency drift budget with N counted from the DATA
    (l3_n_loc), and the same two half-step anchor roundings. The ONLY difference
    from L3 is WHICH POOL the deviation is taken against: the locale's own
    leave-one-out estimate instead of the scene-wide self-including one.

    NOTHING HERE IS TUNED AND NOTHING IS NEW. Had the envelope been widened to
    accommodate leave-one-out's necessarily larger deviations, that would be
    exactly the metric surgery sec 5 forbids; it was not, and the build-phase
    probe confirmed the headline fields clear it with margin (max deviation
    5.273 against an envelope of 14.0) BEFORE the rule was written.
    """
    lhs = Times([A(loc, "l2_ra" + ch),
                 Abs(Minus(A(loc, "l3_g" + ch), A(loc, "l3b_G" + ch)))])
    envelope = Plus([Times([A(frame, "l3_n_loc"), Lit(LATTICE_STEP)]),
                     Lit(HALF_STEP), Lit(HALF_STEP)])
    return Lte(lhs, envelope)


# ---------------------------------------------------------------------------
# l3b_corroborate — THE ANCHOR IS CERTIFIED BY THE OTHERS, NEVER BY ITSELF.
# ---------------------------------------------------------------------------
L3B_CORROBORATE = {
    "name": "l3b_corroborate",
    "comment": (
        "CORROBORATES THE LOCAL ANCHOR AGAINST EVERY OTHER LOCALE BUT ITSELF. "
        "L3's corroboration could not refuse its own pool's centre; this one "
        "has no centre to be. The envelope is L3's, verbatim. A locale whose "
        "anchor is a different MATERIAL from its reference counterpart's "
        "produces an estimate the REST of the scene does not support, and is "
        "now refused even when it happens to be the scene's medoid. "
        "The l3b_corr guard makes it fire once per locale so run_rules "
        "converges. Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_locale", "loc"]],
    "where": And([
        ENABLED(),
        Lt(A(V("loc"), "l3b_corr"), Lit(0.5)),
        Gt(A(V("loc"), "l3b_pooled"), Lit(0.5)),
        Gt(A(V("loc"), "l3_ghat_done"), Lit(0.5)),
    ] + [_corroborate_clause(V("frame"), V("loc"), ch) for ch in CH]),
    "effects": [
        ["set_attr", "loc", "l3b_corr", term(Lit(1.0))],
    ],
}


def _residual(surf, anch, ranch, cand, ch, akey, rkey):
    """| c_ch - p_ch * (a_ch / pa_ch) | — EXTRACTED VERBATIM from l3_recognize,
    which extracted it verbatim from l2_recognize. Single source of truth. L3b
    changes NOTHING about the render — only WHICH CERTIFIER cleared the anchor."""
    ghat = Div(A(anch, akey + ch), A(ranch, rkey + ch))
    return Abs(Minus(A(surf, "c" + ch), Times([A(cand, "p" + ch), ghat])))


def _verdict(surf, anch, ranch, cand, akey, rkey):
    """The L-infinity residual over the three channels — THE CONTINUOUS VERDICT,
    inherited from l3_recognize (and l2/l1 before it) UNCHANGED."""
    return Max([_residual(surf, anch, ranch, cand, ch, akey, rkey) for ch in CH])


def _codebook(ref):
    """The reference frame's OWN identity population — hub-scoped (sec 12.1).
    T3's INTEGER li_mint SurfaceIdentity nodes, REUSED UNMODIFIED through L2/L3."""
    return Nbrs(ref, "has_identity")


def _best(ref, surf, anch, ranch, akey, rkey):
    return MinOver(_codebook(V(ref)), "cand",
                   _verdict(V(surf), V(anch), V(ranch), V("cand"), akey, rkey),
                   default=Lit(NO_CANDIDATE))


# ---------------------------------------------------------------------------
# l3b_recognize — L3's INVARIANT WITH THE CORROBORATION CONJUNCT SWAPPED.
# ---------------------------------------------------------------------------
L3B_RECOGNIZE = {
    "name": "l3b_recognize",
    "comment": (
        "THE MUTUALLY-CORROBORATED LIGHTING INVARIANT. A surface is recognized "
        "iff (a) its locale was PAIRED by L2's join, (b) THE LOCALE'S ANCHOR WAS "
        "CORROBORATED BY EVERY OTHER LOCALE BUT ITSELF, and (c) the best "
        "candidate in the reference frame's held codebook, rendered at the LOCAL "
        "illuminant estimate, lies within ONE LATTICE STEP on every channel. "
        "(a) and (c) ARE L3's, TERM FOR TERM — which are L2's, term for term. "
        "(b) IS THE ONLY CHANGE, AND IT IS A SWAP, NOT AN ADDITION: l3_corr "
        "becomes l3b_corr. THAT IS WHAT MAKES L3's OWN l3_* ARM, READ OFF THE "
        "SAME GRAPH IN THE SAME TICK, THE EXACT LEAVE-ONE-OUT ABLATION (sec "
        "13.2) — no duplicate rule ships and the contrast is ONE measurement "
        "rather than two experiments. Since (c) is unchanged, L3b remains a "
        "SUBSET of L2's verdict and can NEVER widen an invariance class. "
        "l3b_ncand records the number of candidates INSIDE the bound (rung L1b's "
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
        Gt(A(V("loc"), "l3b_corr"), Lit(0.5)),
        Lte(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"), Lit(LATTICE_STEP)),
    ]),
    "effects": [
        ["set_attr", "R", "l3b_recognized", term(Lit(1.0))],
        ["set_attr", "R", "l3b_id", term(A(
            Argmin(_codebook(V("ref")), "cand",
                   _verdict(V("R"), V("loc"), V("loc"), V("cand"), "l2_a", "l2_ra"),
                   default=Lit(0.0)),
            "sid_key"))],
        ["set_attr", "R", "l3b_resid",
         term(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"))],
        ["set_attr", "R", "l3b_ncand", term(Count(Filter(
            _codebook(V("ref")), "cand",
            Lte(_verdict(V("R"), V("loc"), V("loc"), V("cand"), "l2_a", "l2_ra"),
                Lit(LATTICE_STEP)))))],
        ["set_attr", "R", "l3b_status", term(Lit("l3b_recognized"))],
    ],
}


# ---------------------------------------------------------------------------
# l3b_refuse_uncorroborated / l3b_refuse_bound — REFUSAL AS A POSITIVE DATUM.
# ---------------------------------------------------------------------------
L3B_REFUSE_UNCORR = {
    "name": "l3b_refuse_uncorroborated",
    "comment": (
        "Marks l3b_status='l3b_refused_uncorroborated' for a surface whose "
        "locale was paired and pooled, but whose anchor THE OTHER LOCALES DO NOT "
        "CORROBORATE. THIS IS THE RUNG'S OWN CONTRIBUTION MADE VISIBLE — it "
        "includes, crucially, the scene's own medoid, which L3's corroboration "
        "could not refuse. Splitting refusal BY REASON from refusal by the "
        "render's bound means the readback distinguishes 'the others rejected "
        "the anchor' from 'the bound rejected the render'. A refusal is a "
        "POSITIVE datum (sec 1.1 clause 4): without these rules 'refused' and "
        "'never ran' are indistinguishable. Flag-gated, OFF by default."
    ),
    "match": [["frame", "has_surface", "R"],
              ["R", "sits_in", "loc"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("loc"), "l3b_pooled"), Lit(0.5)),
        Gt(A(V("loc"), "l2_paired"), Lit(0.5)),
        Lt(A(V("loc"), "l3b_corr"), Lit(0.5)),
        Lt(A(V("R"), "l3b_recognized"), Lit(0.5)),
    ]),
    "effects": [
        ["set_attr", "R", "l3b_status", term(Lit("l3b_refused_uncorroborated"))],
    ],
}


L3B_REFUSE_BOUND = {
    "name": "l3b_refuse_bound",
    "comment": (
        "Marks l3b_status='l3b_refused_bound' for a surface whose locale WAS "
        "corroborated but whose best rendered candidate exceeds the "
        "lattice-step bound. This is L2's own refusal condition, inherited "
        "through L3 unchanged; together with l3b_refuse_uncorroborated and "
        "l3b_recognize it PARTITIONS every surface whose locale was paired, so "
        "the readback is total and no surface silently falls through. "
        "Flag-gated, OFF by default (sec 9)."
    ),
    "match": [["frame", "has_surface", "R"],
              ["R", "sits_in", "loc"],
              ["frame", "compares_to", "ref"]],
    "where": And([
        ENABLED(),
        Gt(A(V("loc"), "l3b_corr"), Lit(0.5)),
        Lt(A(V("R"), "l3b_recognized"), Lit(0.5)),
        Not(Lte(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"),
                Lit(LATTICE_STEP))),
    ]),
    "effects": [
        ["set_attr", "R", "l3b_status", term(Lit("l3b_refused_bound"))],
        ["set_attr", "R", "l3b_resid",
         term(_best("ref", "R", "loc", "loc", "l2_a", "l2_ra"))],
    ],
}


SEED = {
    "id": "vision_lighting_l3b",
    "version": "1.0.0",
    "depends_on": ["vision_lighting_l3"],
    "description": (
        "ADVANCED LIGHTING RUNG L3b — THE ANCHOR OF THE ANCHOR. L3 pooled the "
        "per-locale illuminant estimates into one scene estimate and CORROBORATED "
        "the anchor against it, cutting the leak 13/1300 -> 5/1300 — but the "
        "residual was SELF-REFERENTIAL: the pool is a CHEBYSHEV CENTRE (a "
        "MEDOID), so Ghat IS some locale's own ghat, that locale's deviation is "
        "EXACTLY 0, and it corroborates UNCONDITIONALLY. All five surviving leaks "
        "sat exactly there. The white-patch assumption had been PUSHED UP ONE "
        "LEVEL, not eliminated. This rung audits SIX candidate certifiers for "
        "Ghat and finds exactly ONE that is neither CIRCULAR (the Chebyshev "
        "centre; the per-channel MEDIAN, measurably still self-membered on every "
        "coherent scene) nor EXTERNAL (temporal persistence assumes stationarity; "
        "the dynamic-range ceiling is a white patch under another name and was "
        "already killed as NON-LOCAL by the k=1 rung; cone-channel achromaticity "
        "assumes an achromatic illuminant and is UNSOUND at the substrate's own "
        "landed chromatic gain): LEAVE-ONE-OUT MUTUAL CORROBORATION. l3b_pool_loo "
        "forms, PER LOCALE, the Chebyshev centre of EVERY OTHER locale's estimate "
        "(the exclusion is Not(Eq(j,loc)), Eq comparing Value::Node by id), so a "
        "locale can NEVER be its own certifier — self-membership is broken BY "
        "CONSTRUCTION. l3b_corroborate applies L3's OWN envelope, UNCHANGED, "
        "against that pool; l3b_recognize is l3_recognize with the corroboration "
        "conjunct SWAPPED and nothing else, so L3's own l3_* arm on the SAME "
        "graph IS the exact ABLATION and L3b can only ever SUBTRACT claims; "
        "l3b_dev writes BOTH deviations as floats so the circularity (dev_cheb "
        "identically 0 at the centre) and leave-one-out's own TWIN-LOCALE "
        "residual (dev_loo == 0 when two locales share an estimate) are EXHIBITED "
        "ON THE GRAPH rather than asserted; l3b_refuse_* make refusal a POSITIVE "
        "datum SPLIT BY REASON. WHAT IT DOES NOT DO: leave-one-out removes every "
        "locale's SELF-certification but does NOT certify the SET — a scene whose "
        "locales are all wrong IN THE SAME WAY corroborates unanimously, measured "
        "by scaling reflectances by kappa (13/13 corroboration with a recovered "
        "Ghat wrong by exactly kappa). CONSTANCY ON THIS SUBSTRATE IS "
        "ANCHOR-RELATIVE AND THE ANCHOR IS A DECLARED CHOICE, NOT A MEASUREMENT. "
        "NO NEW RUST and NO NEW CONSTANT: the literal set is {0.0, 0.5, 1.0, "
        "1.0e9}, identical to L2's and L3's; the bound is L1's own falls-out ONE "
        "LATTICE STEP and the envelope is L3's own, both inherited unchanged with "
        "N counted from the data. T3, L1, L1b, L2 and L3 are NOT modified. "
        "BOUNDED: MULTI-ILLUMINANT scenes remain unsolved; shadow-vs-reflectance "
        "edge attribution is L4's; reflectance is GIVEN at the abstract "
        "cone-triple grain; locale-grain registration and adjacency are GIVEN, "
        "not grown; IDENTITY correspondence is NOT given. Flag-gated on "
        "LightingL3bParams.lighting_l3b, OFF by default (sec 9 — default 0 => "
        "byte-identical, seed inert), read ABSENCE-TOLERANTLY via "
        "MaxOver(default 0), never PickUnique. See VISION_LIGHTING_L3B_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_lighting_l3b_mt",
        "label": ("the anchor of the anchor: each locale's estimate certified by "
                  "every OTHER locale and never by itself — and the set still is not"),
    },
    "nodes": [
        {"local_id": 0, "type": "LightingL3bParams", "attrs": {"lighting_l3b": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [L3B_POOL_LOO, L3B_DEV, L3B_CORROBORATE, L3B_RECOGNIZE,
              L3B_REFUSE_UNCORR, L3B_REFUSE_BOUND],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_lighting_l3b.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out, "-", len(SEED["rules"]), "rules")


if __name__ == "__main__":
    main()
