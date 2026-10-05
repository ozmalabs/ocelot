"""Emit seeds/colour_property.json (Mary's Room stage 4.5, seed 3).

The COLOUR PROPERTY of a perceived, persistent surface: von Kries
(anchor-relative) reflectance from linear cone catches, discounted against the
frame's own anchor -- the vision_lighting T3 / L1 arithmetic applied to
PersistentSurfaces (surface_persistence) instead of synthetic ObjSurfaces.
Every decision is a graph rule; this script only writes JSON. Run:

    PYTHONPATH=. python tools/build_colour_property_seed.py

INPUT (linear by construction): `caught_quanta` of each cell's L/M/S
Photoreceptor. The engine's `photon_transduce` (runners/dsl/src/cognitive_tasks.rs
"photon_transduce") computes caught = dark + sum count*exp(-z^2/2) -- LINEAR in
the photons -- and only `response` (the activation) sees half_saturation and
the carried `adaptation`. Cone dark current is 0 (spectral_forward.EYE_RECEPTORS).
So adaptation changes the percept, never the catch.

THE IN-FRAME LATTICE (declared): the per-surface mean catch is put on the
INTEGER QUANTA lattice inside the rule, c_ch = Round(Sum(member catches)/n, 0)
(engine Round = round-half-even, |eps| <= 1/2). This plays the role T3/L1's
integer cone triples play; the rounding is the observation's grain.

PIPELINE per persistence epoch e (= PersistenceState.ready_epoch):
  cp_catch        per segment S applied at e: P.cL,cM,cS on the lattice, cp_epoch:=e.
  cp_frame        ONE FrameStats{epoch, aL,aM,aS, n} per epoch once every applied
                  surface of e has its catch: a_ch = MaxOver(matched surfaces,
                  c_ch) -- T3's anchor (li_frame_stats), constant-free: the
                  brightest surface per channel is the scene white.
  cp_mint         first epoch a P is seen: ONE ColourProperty{pL,pM,pS = c,
                  paL,paM,paS = a, minted_epoch, sid} via has_colour_property,
                  plus a PropertyCheck{status 'minted', resid 0}. Descriptor:
                  anchor-relative reflectance p/pa.
  cp_check        RUNG 1 (L1 bound) at every later matched epoch, see below;
                  writes PropertyCheck{epoch, sid, status 'holds'|'refused',
                  resid_*, bound_*, resid_max, margin}. A refusal is a POSITIVE
                  datum (l1_refuse). The property is never modified.
  cp_pool / cp_pool_none / cp_corroborate   RUNG 2 (declared second rung,
                  ColourPropertyParams.pooled) -- L3b leave-one-out, see below.

RUNG 1 BOUND (derived, VISION_PROTOCOL sec 13 -- nothing tuned). Per channel,
held property (p, pa) from epoch e0, observation (c, a) at epoch e. Diagonal
(von Kries) class: true catches p* = r g0, pa* = M g0, c* = r g1, a* = M g1,
M = max reflectance (round is monotone, so the max surface is the same material
and the max commutes with rounding), hence c* pa* = p* a* EXACTLY. Unlike L1
the reference is NOT exact (both frames are real-valued and rounded), so all
four values carry |eps| <= 1/2:
    D := c pa - p a
       = [c eps_pa + pa eps_c - eps_c eps_pa] - [p eps_a + a eps_p - eps_p eps_a]
(substituting c* = c - eps_c etc.; observed quantities only). Each bracket is
bilinear in its two independent eps on [-1/2,1/2]^2, so its extremes are at the
corners: for x, y >= 1/2 the first bracket lies in [-(x+y)/2 - 1/4,
(x+y)/2 - 1/4], so the two -1/4 corner terms CANCEL in the difference and
    |D| <= 1/2 (c + pa + p + a)                       (tight; all four >= 1)
A lattice value of 0 widens its own bracket to (x+y)/2 + 1/4 (eps x - eps y
products no longer cancel), so the derived envelope is
    bound_ch = 1/2 (c + pa + p + a) + 1/4 [min(c,pa) < 1] + 1/4 [min(p,a) < 1].
Every term is a half-step rounding scaled by its own cross-multiplier (L1
PREREG sec 2.1/2.2); the 1/4 is the product of two half steps. HOLDS iff
|D_ch| <= bound_ch on all three channels (L-infinity, channels rounded
independently). This bounds ROUNDING ONLY: model error from this eye's
broadband, non-diagonal Gaussian sensors (measured: up to 4 quanta under D65,
13.5 under A at 100 td; stage4-scope) is NOT in it, so refusals under A are the
expected, reported result (decision 3).

RUNG 2 (L3b leave-one-out, seeds/vision_lighting_l3b.json l3b_pool_loo /
l3b_corroborate; surfaces play the locales). Per check K at epoch e with
reference epoch e0 = its property's minted_epoch, the anchor-free per-surface
gain g_ch = c_ch / p_ch. The pool of K is every OTHER check of the same frame
with the same reference epoch (a gain is only comparable across surfaces that
share the reference frame) and status holds/refused. G^(-K) = the Chebyshev
centre of the pool's gains (L3b verbatim: Argmin over i of MaxOver j of the
L-infinity distance |g_i - g_j|; stable node-id tie-break), and the tolerance
is the pool's OWN spread, spread_ch = MaxOver(pool, |g_j,ch - G_ch|) -- the
non-diagonality measured from the scene itself, not tuned. holds_pooled iff
|g_K,ch - G_ch| <= spread_ch on all three channels. K is never its own
certifier (Not(Eq(j, K))). DECLARED LIMITS: K's own rounding is not added to
the tolerance; a pool of ONE gives spread 0 (exact agreement required); an
empty pool, or a zero lattice value in p, REFUSES ('refused_pooled',
pooled_reason 'no_pool' / 'no_gain'); a scene whose surfaces are all wrong the
same way corroborates (L3b's kappa result).

Flags ColourPropertyParams{enabled 0.0, pooled 0.0}, OFF by default (sec 9);
also gated on the segmentation and persistence flags. Manifest latency_class
hard_realtime. Depends on surface_persistence.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "colour_property.json")


# --------------------------------------------------------------- AST helpers
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Ne(a, b): return Not(Eq(a, b))
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
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
def Max(*xs): return {"type": "Max", "items": list(xs)}
def Min(*xs): return {"type": "Min", "items": list(xs)}
def Round(x): return {"type": "Round", "value": x, "ndigits": L(0)}
def IfThenElse(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
def Nbrs(n, e):
    node = V(n) if isinstance(n, str) else n
    return {"type": "Neighbours", "node": node, "edge_type": e, "any_type": False}
def InNbrs(n, e): return {"type": "InNeighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Count(src): return {"type": "Count", "source": src}
def Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var, "value": val}
def MaxOver(src, var, val, default=None):
    t = {"type": "MaxOver", "source": src, "var_name": var, "value": val}
    if default is not None:
        t["default"] = default
    return t
def Argmin(src, var, val):
    return {"type": "Argmin", "source": src, "var_name": var, "value": val}
def PickUnique(src): return {"type": "PickUnique", "source": src}
def T(term): return {"__term__": term}


def seta(var, key, value):
    return ["set_attr", var, key, value]


# --------------------------------------------------------------- vocabulary
PARAMS = "ColourPropertyParams"
CSTATE = "ColourState"
FRAME = "FrameStats"
PROP = "ColourProperty"
CHECK = "PropertyCheck"
SURF = "PersistentSurface"
CHANNELS = ("L", "M", "S")
RECEPTOR = {"L": "l_receptor", "M": "m_receptor", "S": "s_receptor"}
HALF = L(0.5)
QUARTER = L(0.25)  # product of two half-step roundings (see module docstring)


def flag(node_type, key, var):
    return Gt(MaxOver(NodesOfType(node_type), var, A(var, key), L(0.0)), HALF)


CP_ON = flag(PARAMS, "enabled", "cpp_")
POOLED_ON = flag(PARAMS, "pooled", "cpq_")
SEG_ON = flag("SurfaceSegmentationParams", "enabled", "sp_")
PS_ON = flag("SurfacePersistenceParams", "enabled", "pp_")
GATE = And(CP_ON, SEG_ON, PS_ON)
READY = A(PickUnique(NodesOfType("PersistenceState")), "ready_epoch")
CUR_SEGS = Nbrs(PickUnique(NodesOfType("SegmentationState")), "has_segment")
ALL_P = NodesOfType(SURF)


def applied_at_ready(s):
    return And(Eq(A(s, "epoch"), READY), Gt(A(s, "current"), HALF),
               Eq(A(s, "applied"), L(1.0)))


def member_catch_sum(S, ch, m):
    return Sum(InNbrs(S, "in_segment"), m,
               A(PickUnique(Nbrs(m, RECEPTOR[ch])), "caught_quanta"))


def receptors_at(S, m):
    """Every member's L, M and S receptor has transduced S's epoch."""
    return Not(Exists(InNbrs(S, "in_segment"), m, Or(*[
        Ne(A(PickUnique(Nbrs(m, RECEPTOR[ch])), "input_epoch"), A(S, "epoch"))
        for ch in CHANNELS])))


# rung-1 per-channel terms for (P observation, CP property, F frame)
def c_(ch): return A("P", "c" + ch)
def a_(ch): return A("F", "a" + ch)
def p_(ch): return A("CP", "p" + ch)
def pa_(ch): return A("CP", "pa" + ch)


def resid(ch):
    return Abs(Minus(Times(c_(ch), pa_(ch)), Times(p_(ch), a_(ch))))


def bound(ch):
    return Plus(
        Times(HALF, Plus(c_(ch), pa_(ch), p_(ch), a_(ch))),
        IfThenElse(Lt(Min(c_(ch), pa_(ch)), L(1.0)), QUARTER, L(0.0)),
        IfThenElse(Lt(Min(p_(ch), a_(ch)), L(1.0)), QUARTER, L(0.0)),
    )


HOLDS = And(*[Lte(resid(ch), bound(ch)) for ch in CHANNELS])
G_OK = And(*[Gte(p_(ch), L(1.0)) for ch in CHANNELS])


def pool(K, j):
    """L3b leave-one-out pool of check K: the frame's other rung-1 checks with
    the same reference (minted) epoch and an identifiable gain."""
    return Filter(Nbrs("F", "has_check"), j, And(
        Not(Eq(V(j), V(K))),
        Ne(A(j, "status"), L("minted")),
        Eq(A(j, "minted_epoch"), A(K, "minted_epoch")),
        Gt(A(j, "g_ok"), HALF)))


def linf_gain(i, j):
    return Max(*[Abs(Minus(A(i, "g" + ch), A(j, "g" + ch))) for ch in CHANNELS])


def cheb_centre(K, ch):
    return A(Argmin(pool(K, "pi_"), "pi2_",
                    MaxOver(pool(K, "pj_"), "pj2_", linf_gain("pi2_", "pj2_"), L(0.0))),
             "g" + ch)


ALL_CHECKED = Not(Exists(ALL_P, "u_", And(
    Eq(A("u_", "cp_epoch"), A("F", "epoch")),
    Ne(A("u_", "chk_epoch"), A("F", "epoch")))))

FRAME_MATCH = ["cs", "current_frame", "F"]

RULES = [
    {
        "name": "cp_catch",
        "comment": "Per segment S applied by persistence at the ready epoch (so "
                   "S -segment_of-> P exists): the surface's mean LINEAR cone "
                   "catch per channel over its member cells, put on the integer "
                   "quanta lattice: c_ch = Round(Sum(member caught_quanta)/n, 0). "
                   "Gated on every member's L/M/S receptor carrying this epoch.",
        "match": [["st", "has_segment", "S"], ["S", "segment_of", "P"]],
        "where": And(GATE, applied_at_ready("S"),
                     Ne(A("P", "cp_epoch"), A("S", "epoch")),
                     receptors_at("S", "m_")),
        "effects": [
            *[seta("P", "c" + ch, T(Round(Div(member_catch_sum("S", ch, "m" + ch),
                                               A("S", "n_cells")))))
              for ch in CHANNELS],
            seta("P", "cp_n", T(A("S", "n_cells"))),
            seta("P", "cp_epoch", T(A("S", "epoch"))),
        ],
    },
    {
        "name": "cp_frame",
        "comment": "ONE FrameStats per epoch, once every applied boundary segment "
                   "of the ready epoch has its surface's catch: the anchor a_ch = "
                   "MaxOver(surfaces matched this epoch, c_ch) -- T3's "
                   "li_frame_stats anchor, constant-free (the brightest surface "
                   "per channel acts as the scene white). No frame for an epoch "
                   "with no surface (ganzfeld).",
        "match": [["cpp", "has_colour_state", "cs"]],
        "where": And(
            GATE, Gt(READY, A("cs", "frame_epoch")),
            Exists(CUR_SEGS, "s_", applied_at_ready("s_")),
            Not(Exists(CUR_SEGS, "s2_", And(
                Eq(A("s2_", "epoch"), READY), Gt(A("s2_", "has_boundary"), HALF),
                Gt(A("s2_", "current"), HALF),
                Not(And(Eq(A("s2_", "applied"), L(1.0)),
                        Eq(A(PickUnique(Nbrs("s2_", "segment_of")), "cp_epoch"),
                           READY))))))),
        "effects": [
            ["add_node", "F", FRAME, {
                "epoch": T(READY),
                **{"a" + ch: T(MaxOver(Filter(ALL_P, "f_", Eq(A("f_", "cp_epoch"), READY)),
                                       "f2_", A("f2_", "c" + ch), L(0.0)))
                   for ch in CHANNELS},
                "n_surfaces": T(Count(Filter(ALL_P, "f3_", Eq(A("f3_", "cp_epoch"), READY)))),
            }],
            ["add_edge", "cs", "has_frame", "F"],
            ["add_edge", "cs", "current_frame", "F"],
            seta("cs", "frame_epoch", T(READY)),
        ],
    },
    {
        "name": "cp_frame_retire",
        "comment": "Keep old FrameStats as history (has_frame) but drop the live "
                   "current_frame edge once a newer frame exists.",
        "match": [FRAME_MATCH],
        "where": And(GATE, Lt(A("F", "epoch"), A("cs", "frame_epoch"))),
        "effects": [["del_edge", "cs", "current_frame", "F"]],
    },
    {
        "name": "cp_mint",
        "comment": "The FIRST epoch a PersistentSurface is seen it gets ONE "
                   "ColourProperty: p_ch = its lattice catch, pa_ch = that frame's "
                   "anchor (descriptor = anchor-relative reflectance p/pa), via "
                   "P -has_colour_property-> CP. A PropertyCheck{status 'minted', "
                   "resid 0} records the epoch. Never re-minted.",
        "match": [FRAME_MATCH, ["sc", "has_surface", "P"]],
        "where": And(GATE, Eq(A("P", "cp_epoch"), A("F", "epoch")),
                     Not(Exists(Nbrs("P", "has_colour_property"), "x_", L(True)))),
        "effects": [
            ["add_node", "CP", PROP, {
                "sid": T(A("P", "sid")),
                "minted_epoch": T(A("F", "epoch")),
                **{"p" + ch: T(A("P", "c" + ch)) for ch in CHANNELS},
                **{"pa" + ch: T(A("F", "a" + ch)) for ch in CHANNELS},
            }],
            ["add_edge", "P", "has_colour_property", "CP"],
            ["add_node", "K", CHECK, {
                "epoch": T(A("F", "epoch")),
                "sid": T(A("P", "sid")),
                "minted_epoch": T(A("F", "epoch")),
                "status": T(L("minted")),
                **{"c" + ch: T(A("P", "c" + ch)) for ch in CHANNELS},
                **{"a" + ch: T(A("F", "a" + ch)) for ch in CHANNELS},
                "resid_max": T(L(0.0)),
            }],
            ["add_edge", "F", "has_check", "K"],
            ["add_edge", "K", "check_of", "CP"],
            seta("P", "chk_epoch", T(A("F", "epoch"))),
        ],
    },
    {
        "name": "cp_check",
        "comment": "RUNG 1 (L1 bound). At a later matched epoch the property "
                   "HOLDS iff for every channel |c*pa - p*a| <= 1/2(c+pa+p+a) "
                   "(+1/4 per cross-term with a zero lattice value) -- the "
                   "rounding envelope derived in the seed description; no tuned "
                   "constant. Verdict written on a PropertyCheck (refusal is a "
                   "positive datum, l1_refuse). The property is NOT changed. Also "
                   "writes the anchor-free gain g_ch = c/p for rung 2 (g_ok = 0 "
                   "if some p_ch is 0: gain unidentifiable).",
        "match": [FRAME_MATCH, ["sc", "has_surface", "P"],
                  ["P", "has_colour_property", "CP"]],
        "where": And(GATE, Eq(A("P", "cp_epoch"), A("F", "epoch")),
                     Ne(A("P", "chk_epoch"), A("F", "epoch"))),
        "effects": [
            ["add_node", "K", CHECK, {
                "epoch": T(A("F", "epoch")),
                "sid": T(A("P", "sid")),
                "minted_epoch": T(A("CP", "minted_epoch")),
                "status": T(IfThenElse(HOLDS, L("holds"), L("refused"))),
                **{"c" + ch: T(c_(ch)) for ch in CHANNELS},
                **{"a" + ch: T(a_(ch)) for ch in CHANNELS},
                **{"resid_" + ch: T(resid(ch)) for ch in CHANNELS},
                **{"bound_" + ch: T(bound(ch)) for ch in CHANNELS},
                "resid_max": T(Max(*[resid(ch) for ch in CHANNELS])),
                "margin": T(Max(*[Minus(resid(ch), bound(ch)) for ch in CHANNELS])),
                **{"g" + ch: T(Div(c_(ch), p_(ch))) for ch in CHANNELS},
                "g_ok": T(IfThenElse(G_OK, L(1.0), L(0.0))),
            }],
            ["add_edge", "F", "has_check", "K"],
            ["add_edge", "K", "check_of", "CP"],
            seta("P", "chk_epoch", T(A("F", "epoch"))),
        ],
    },
    {
        "name": "cp_pool",
        "comment": "RUNG 2 (pooled flag): L3b l3b_pool_loo with surfaces as "
                   "locales. Once every surface of the frame is checked, K's "
                   "leave-one-out pool (same frame, same reference epoch, not K) "
                   "gives G^(-K) = the Chebyshev centre of the pool's gains "
                   "(Argmin_i MaxOver_j L-inf |g_i - g_j|). Fires once per check.",
        "match": [FRAME_MATCH, ["F", "has_check", "K"]],
        "where": And(GATE, POOLED_ON, ALL_CHECKED,
                     Ne(A("K", "status"), L("minted")),
                     Eq(A("K", "pool_done"), L(None)),
                     Gt(A("K", "g_ok"), HALF),
                     Gt(Count(pool("K", "pc_")), L(0))),
        "effects": [
            *[seta("K", "G" + ch, T(cheb_centre("K", ch))) for ch in CHANNELS],
            seta("K", "pool_n", T(Count(pool("K", "pn_")))),
            seta("K", "pool_done", 1.0),
        ],
    },
    {
        "name": "cp_pool_none",
        "comment": "RUNG 2 refusal by construction: an empty leave-one-out pool, "
                   "or an unidentifiable own gain, can never acquire an estimate "
                   "(L3b: an absence must not read as a value) -> refused_pooled "
                   "with its reason.",
        "match": [FRAME_MATCH, ["F", "has_check", "K"]],
        "where": And(GATE, POOLED_ON, ALL_CHECKED,
                     Ne(A("K", "status"), L("minted")),
                     Eq(A("K", "pooled_status"), L(None)),
                     Eq(A("K", "pool_done"), L(None)),
                     Or(Lt(A("K", "g_ok"), HALF),
                        Lt(Count(pool("K", "pz_")), L(1)))),
        "effects": [
            seta("K", "pooled_status", "refused_pooled"),
            seta("K", "pooled_reason", T(IfThenElse(
                Lt(A("K", "g_ok"), HALF), L("no_gain"), L("no_pool")))),
            seta("K", "pool_done", 0.0),
        ],
    },
    {
        "name": "cp_corroborate",
        "comment": "RUNG 2 verdict: holds_pooled iff |g_K,ch - G_ch| <= spread_ch "
                   "on every channel, spread_ch = MaxOver(pool, |g_j,ch - G_ch|) "
                   "-- the pool's own non-diagonality, data-derived, not tuned. "
                   "Writes dev_* and spread_* so the verdict is a measurement.",
        "match": [FRAME_MATCH, ["F", "has_check", "K"]],
        "where": And(GATE, POOLED_ON, Eq(A("K", "pool_done"), L(1.0)),
                     Eq(A("K", "pooled_status"), L(None))),
        "effects": [
            *[seta("K", "dev_" + ch, T(Abs(Minus(A("K", "g" + ch), A("K", "G" + ch)))))
              for ch in CHANNELS],
            *[seta("K", "spread_" + ch, T(MaxOver(
                pool("K", "ps" + ch), "ps2" + ch,
                Abs(Minus(A("ps2" + ch, "g" + ch), A("K", "G" + ch))), L(0.0))))
              for ch in CHANNELS],
            seta("K", "pooled_status", T(IfThenElse(And(*[
                Lte(Abs(Minus(A("K", "g" + ch), A("K", "G" + ch))),
                    MaxOver(pool("K", "pv" + ch), "pv2" + ch,
                            Abs(Minus(A("pv2" + ch, "g" + ch), A("K", "G" + ch))),
                            L(0.0)))
                for ch in CHANNELS]), L("holds_pooled"), L("refused_pooled")))),
        ],
    },
]

DESCRIPTION = (
    "Mary's Room stage 4.5 (seed 3): the COLOUR PROPERTY of a perceived "
    "PersistentSurface (surface_persistence), by the vision_lighting T3/L1 von "
    "Kries arithmetic. Per surface matched at epoch e: c_ch = Round(mean member "
    "L/M/S caught_quanta, 0) -- LINEAR catches (photon_transduce: adaptation "
    "enters only the activation; cone dark current 0), on a declared integer "
    "quanta lattice (|eps|<=1/2). FrameStats anchor a_ch = MaxOver(matched "
    "surfaces, c_ch) (T3's anchor, constant-free). First sight mints ONE "
    "ColourProperty{p=c, pa=a, minted_epoch} via has_colour_property "
    "(descriptor p/pa). RUNG 1 (L1 bound): later, HOLDS iff per channel "
    "|c*pa - p*a| <= 1/2(c+pa+p+a) (+1/4 per bracket with a zero lattice "
    "value). DERIVATION: in-class (diagonal) change gives c*pa* = p*a* exactly "
    "(round is monotone so the anchor is the same material); with all four "
    "observed values rounded, D = c pa - p a = [c e_pa + pa e_c - e_c e_pa] - "
    "[p e_a + a e_p - e_p e_a]; each bracket is bilinear on [-1/2,1/2]^2 so its "
    "range is [-(x+y)/2 - 1/4, (x+y)/2 - 1/4] for x,y >= 1/2 and the -1/4 "
    "corner terms cancel in the difference: |D| <= (c+pa+p+a)/2; a zero "
    "lattice value widens its bracket by 1/4. Every term is a half-step "
    "rounding times its own cross-multiplier (L1 PREREG 2.1/2.2); nothing "
    "tuned. It bounds rounding only, NOT the model error of this eye's "
    "non-diagonal sensors, so refusals under illuminant A are the reported "
    "result. Verdict on PropertyCheck{epoch, sid, status holds|refused, "
    "resid_*, bound_*, resid_max, margin}; the property is never changed. "
    "RUNG 2 (flag pooled; L3b leave-one-out with surfaces as locales): gain "
    "g_ch = c/p; G^(-K) = Chebyshev centre of the other checks' gains (same "
    "frame, same reference epoch), tolerance = their own spread "
    "MaxOver|g_j - G|; pooled_status holds_pooled|refused_pooled (empty pool / "
    "zero p refuse). Flags ColourPropertyParams{enabled, pooled}, OFF by "
    "default (sec 9). See tools/build_colour_property_seed.py."
)

MANIFEST = {
    "id": "colour_property",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["surface_persistence"],
    "latency_class": "hard_realtime",
    "description": DESCRIPTION,
    "microtheory": {
        "name": "colour_property",
        "description": "persistent surfaces -> anchor-relative colour properties",
    },
    "nodes": [
        {"local_id": 0, "type": PARAMS, "attrs": {"enabled": 0.0, "pooled": 0.0}},
        {"local_id": 1, "type": CSTATE, "attrs": {"frame_epoch": -1}},
    ],
    "edges": [
        {"src": {"role": "agent_root"}, "type": "has_colour_property_params",
         "tgt": {"local": 0}, "attrs": {}},
        {"src": {"local": 0}, "type": "has_colour_state",
         "tgt": {"local": 1}, "attrs": {}},
    ],
    "productions": [],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
        f.write("\n")
    print(f"wrote {OUT} with {len(RULES)} rules")
