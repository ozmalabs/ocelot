#!/usr/bin/env python3
"""Emit seeds/vision_colour_identity.json — COLOUR IDENTITY: categorical colour as
a MINTED, MDL-GATED SIGN over the opponent-colour VALUE, as pure graph data (NO new
Rust).

See VISION_COLOUR_IDENTITY_PREREG.md. Builds DIRECTLY on the colour-salience rung:
salience answered WHERE to look (surround-relative opponent CONTRAST); this rung
answers WHAT COLOUR IT IS (a categorical SIGN over the opponent-colour VALUE). It
instantiates the sd loop's DYNAMIC-QUANTIZATION pattern
(decode -> recognize -> mint -> re-decode on codebook_epoch growth) for the 2-D
opponent-colour subspace:

  ci_opponent      computes the integer opponent coordinate (rg=cL-cM, by=cS-(cL+cM))
  ci_mint_category MINTS a ColourCategory quantum where a colour value CLUSTERS and
                   MDL COMPRESSES (Count(same exact colour) >= 3 = m_min, which FALLS
                   OUT of d=2: a category pays iff m*d > d+m, i.e. m > d/(d-1) = 2)
  ci_assign        writes each region's categorical SIGN = its NEAREST minted quantum
                   (Argmin over categories by opponent distance) and re-decodes on
                   codebook growth (Scene.epoch != Region.assigned_epoch)

Flag-gated on ColourIdentityParams.identity, OFF by default (§9). NO new Rust:
reuses Count/Filter/NodesOfType/Argmin/Exists/Sqrt/Minus/Times/Plus/Gte + run_rules.
In-frame colour coordinate is integer; the continuous lives ONLY in the cross-frame
Sqrt-distance used to assign a sign (the frame/continuum invariant).

This is a seed BUILDER (emits graph data) -- admissible under CLAUDE.md.
Run from the gamma-substrate dir:  python tools/build_vision_colour_identity.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms, same as build_vision_colour.py) ----
def V(name):            return {"type": "Var", "name": name}
def Lit(v):             return {"type": "Lit", "value": v}
def A(node, key):       return {"type": "Attr", "node": node, "key": key}
def Gt(a, b):           return {"type": "Gt", "a": a, "b": b}
def Lt(a, b):           return {"type": "Lt", "a": a, "b": b}
def Gte(a, b):          return {"type": "Gte", "a": a, "b": b}
def Lte(a, b):          return {"type": "Lte", "a": a, "b": b}
def Eq(a, b):           return {"type": "Eq", "a": a, "b": b}
def Not(x):             return {"type": "Not", "arg": x}
def And(items):         return {"type": "And", "items": items}
def Or(items):          return {"type": "Or", "items": items}
def Plus(items):        return {"type": "Plus", "items": items}
def Minus(a, b):        return {"type": "Minus", "a": a, "b": b}
def Times(items):       return {"type": "Times", "items": items}
def Sqrt(arg):          return {"type": "Sqrt", "arg": arg}
def NodesOf(t):         return {"type": "NodesOfType", "node_type": t}
def Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Count(src):         return {"type": "Count", "source": src}
def Exists(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Argmin(src, var, value):
    return {"type": "Argmin", "source": src, "var_name": var, "value": value,
            "default": None}
def PickCIP():
    return {"type": "PickUnique", "source": NodesOf("ColourIdentityParams")}
def term(x):            return {"__term__": x}


# --- ACHROMATOPSIA LESION guard (VISION_ACHROMATOPSIA_PREREG.md) ----------------
# The colour-SIGN (categorical NAMING) layer -- ci_mint_category + ci_assign -- is
# suppressible by an `achromatopsia` flag on ColourIdentityParams (OFF by default =
# INTACT, §9). It guards ONLY minting + assignment; ci_opponent (the chromatic
# SIGNAL crg/cby) and the whole vision_colour salience seed (chromatic contrast /
# border / shape-from-colour) are UNTOUCHED -- faithful to cerebral achromatopsia
# (Heywood & Cowey 1997): the cone-opponent SIGNAL is preserved while conscious
# colour categorization is abolished. This is GRAPH DATA (a flag on a params node),
# not a Python code path (PROTOCOL §0). When achromatopsia<0.5 (the default, and any
# unset node) the guard is always-true and the rules are byte-identical to v1.0.0.
def NoAchromatopsia():
    return Lt(A(PickCIP(), "achromatopsia"), Lit(0.5))


R = V("R")

# --- per-cell opponent coordinates (integer, in-frame) -------------------------
def RG(node):   return Minus(A(node, "cL"), A(node, "cM"))                       # L-M
def BY(node):   return Minus(A(node, "cS"), Plus([A(node, "cL"), A(node, "cM")]))  # S-(L+M)


# ---------------------------------------------------------------------------
# ci_opponent -- compute the integer opponent coordinate from the raw cones.
# Reads only self (raw cones), so firing order is irrelevant. Once per cell.
# ---------------------------------------------------------------------------
CI_OPPONENT = {
    "name": "ci_opponent",
    "comment": (
        "Compute the in-frame INTEGER opponent coordinate of a cell from its raw "
        "cone attrs: crg = cL-cM (red-green), cby = cS-(cL+cM) (blue-yellow), the "
        "two chromatic opponent axes orthogonal to luminance -- the SAME axes the "
        "colour-salience rung used, but here the VALUE (identity), not the "
        "surround-relative contrast (salience). Reads ONLY self raw cones so firing "
        "order is irrelevant. The coordinate is INTEGER (the frame/continuum "
        "invariant: in-frame is the integer lattice; the continuous appears only in "
        "the cross-frame distance ci_assign uses). Flag-gated on "
        "ColourIdentityParams.identity>0.5, OFF by default (§9). Once (op_done)."
    ),
    "match": [["scene", "has_region", "R"]],
    "where": And([
        Gt(A(PickCIP(), "identity"), Lit(0.5)),
        Lt(A(R, "op_done"), Lit(0.5)),
    ]),
    "effects": [
        ["set_attr", "R", "crg", term(RG(R))],
        ["set_attr", "R", "cby", term(BY(R))],
        ["set_attr", "R", "op_done", term(Lit(1.0))],
    ],
}


# ---------------------------------------------------------------------------
# ci_mint_category -- DYNAMIC QUANTIZATION (mint), MDL count-gated.
#   A ColourCategory quantum is minted for an exact opponent colour value iff
#   (a) the opponent field is fully computed (no transient undercount),
#   (b) that exact colour value RECURS >= m_min = 3 times  -- the MDL gate that
#       FALLS OUT of d=2 (a category pays iff m*d > d+m, i.e. m > d/(d-1) = 2 for
#       d=2 chromatic dims, so m >= 3), and
#   (c) no category has been minted for this colour yet (fixpoint safety +
#       recognize-not-re-mint -- the sd has-guard).
#   Bumps Scene.epoch (the codebook_epoch re-arm) so ci_assign re-decodes.
#   Non-batch one-binding-per-pass + this Not(Exists) guard => exactly ONE category
#   per clustered colour (rewrite.rs re-derives the guard between applications).
# ---------------------------------------------------------------------------
_same_colour_q = And([
    Eq(A(V("q"), "crg"), A(R, "crg")),
    Eq(A(V("q"), "cby"), A(R, "cby")),
])
_member_count = Count(Filter(NodesOf("Region"), "q", _same_colour_q))
_cat_exists_here = Exists(NodesOf("ColourCategory"), "cat", And([
    Eq(A(V("cat"), "crg"), A(R, "crg")),
    Eq(A(V("cat"), "cby"), A(R, "cby")),
]))
_all_op_done = Not(Exists(NodesOf("Region"), "z", Lt(A(V("z"), "op_done"), Lit(0.5))))

# CANONICAL REPRESENTATIVE guard (batch-safe by construction). s.tick() applies
# batch-safe rules by snapshotting ALL matching bindings BEFORE any effect, so a
# Not(Exists ColourCategory@this colour) guard alone reads the pre-mint state for
# every same-colour region and mints one category PER REGION. The fix: only the
# canonical (top-left, lexicographic (rrow,rcol)) region of a colour may mint, so
# even under batch exactly ONE region per DISTINCT colour passes the guard -> one
# category per colour. This is picking a canonical member (the ground rung's
# "single unified rule" lesson), NOT a magic threshold.
_is_representative = Not(Exists(NodesOf("Region"), "p", And([
    Eq(A(V("p"), "crg"), A(R, "crg")),
    Eq(A(V("p"), "cby"), A(R, "cby")),
    Or([
        Lt(A(V("p"), "rrow"), A(R, "rrow")),
        And([Eq(A(V("p"), "rrow"), A(R, "rrow")),
             Lt(A(V("p"), "rcol"), A(R, "rcol"))]),
    ]),
])))

CI_MINT = {
    "name": "ci_mint_category",
    "comment": (
        "DYNAMIC QUANTIZATION (the sd loop's sd_mint_quantum pattern for the colour "
        "subspace): MINT a ColourCategory quantum at an exact opponent colour value "
        "where the value CLUSTERS and MDL COMPRESSES. Gates: (1) identity>0.5; (2) "
        "the opponent field is complete (Not Exists Region with op_done<0.5) so the "
        "member count is exact, never a transient undercount; (3) THE MDL GATE -- "
        "Count(Filter(Region, same exact crg&cby)) >= 3: this colour recurs >= "
        "m_min times. m_min=3 FALLS OUT of the coordinate dimensionality d=2 (§13, "
        "NOT tuned): a category costs a d-integer prototype and saves 1 label per "
        "member vs a d-integer raw coord, so it pays iff m*d > d+m, i.e. m > "
        "d/(d-1); for d=2 that is m>2 <=> m>=3 (at m=2: raw 4 vs categorized "
        "2+2=4, equal, refuse); (4) the CANONICAL-REPRESENTATIVE guard -- only the "
        "top-left (lexicographic (rrow,rcol)) region of a colour may mint, so under "
        "s.tick()'s batch application (all bindings snapshotted before any effect) "
        "exactly ONE region per DISTINCT colour passes and mints exactly ONE "
        "category per colour (picking a canonical member, the ground rung's 'single "
        "unified rule' lesson -- NOT a magic threshold); (5) Not(Exists "
        "ColourCategory at this colour) -- recognize-not-re-mint across passes / "
        "re-presentations (a seen colour is never re-minted). Effects: add the "
        "ColourCategory{crg,cby,members,minted:1}, link it has_category from the "
        "scene, and bump Scene.epoch (the codebook_epoch re-arm so ci_assign "
        "re-decodes on growth). Flag-gated on identity>0.5, OFF by default (§9)."
    ),
    "match": [["scene", "has_region", "R"]],
    "where": And([
        Gt(A(PickCIP(), "identity"), Lit(0.5)),
        NoAchromatopsia(),                       # LESION: OFF by default = intact
        _all_op_done,
        Gte(_member_count, Lit(3)),
        _is_representative,
        Not(_cat_exists_here),
    ]),
    "effects": [
        ["add_node", "cat", "ColourCategory", {
            "crg": term(A(R, "crg")),
            "cby": term(A(R, "cby")),
            "members": term(_member_count),
            "minted": term(Lit(1.0)),
        }],
        ["add_edge", "scene", "has_category", "cat"],
        ["set_attr", "scene", "epoch",
         term(Plus([A(V("scene"), "epoch"), Lit(1.0)]))],
    ],
}


# ---------------------------------------------------------------------------
# ci_assign -- DEQUANTIZATION (decode/recognize): a region's categorical SIGN is
#   its NEAREST minted quantum. Re-decodes on codebook growth (assigned_epoch !=
#   Scene.epoch, the sd_redecode idiom). A region whose colour EXACTLY equals a
#   prototype gets sign_dist=0 and that category's sign (recognize); an
#   off-prototype region gets its nearest quantum (the nearest sign).
# ---------------------------------------------------------------------------
def _opp_dist(p, q):
    """Cross-frame opponent distance between any two opponent-coordinate carriers.
    Generalises the original _dist(cat) (which was R-to-category) to prototype-to-
    prototype WITHOUT changing the emitted JSON for the R-to-category uses: the term
    structure is identical, only the left operand is now a parameter."""
    drg = Minus(A(p, "crg"), A(q, "crg"))
    dby = Minus(A(p, "cby"), A(q, "cby"))
    return Sqrt(Plus([Times([drg, drg]), Times([dby, dby])]))


def _dist(cat):
    return _opp_dist(R, cat)


_nearest_cat = Argmin(NodesOf("ColourCategory"), "c", _dist(V("c")))


# --- THE REFUSAL BOUND: the minted codebook's PACKING RADIUS -------------------
# VISION_COLOUR_BOUND_PREREG.md. L1b (VISION_UNIQUENESS_RESULTS.md) found ci_assign
# to be the worst case in its audit table: an Argmin over ColourCategory with ZERO
# Lte -- no admission bound at all, so a probe at opponent distance 269.52 is
# confidently assigned and the equidistant probe is decided by a margin of exactly
# 0.0000. It cannot refuse, ever.
#
# THE DERIVATION (falls out, PROTOCOL §13 -- NOT tuned). ci_assign is a DEQUANTIZER:
# it decodes an observation against a codebook of minted quanta. For a codebook {c_i}
# the largest ball around a prototype guaranteed to lie inside that prototype's own
# Voronoi cell -- equivalently the largest radius at which the codebook's own quanta
# DO NOT OVERLAP -- is the PACKING RADIUS
#
#     r_i = 1/2 * min_{j != i} ||c_i - c_j||
#
# Two balls of radius r around prototypes separated by D are disjoint iff 2r <= D.
# That is the DEFINITION of non-overlapping quanta, not a chosen threshold. So:
#
#     admit iff  2 * dist(R, winner)  <=  min_{c != winner} dist(winner, c)
#
# Why it falls out rather than going in: it is a FUNCTION OF THE MINTED CODEBOOK, not
# a literal -- it yields 7.8102 on colour identity's 3-category codebook and 10.0 on
# achromatopsia's 2-category codebook, and neither value was chosen; it is recomputed
# as the codebook grows (the existing codebook_epoch re-arm already re-decodes); and
# it reuses the EXACT distance ci_assign already computes, now applied prototype-to-
# prototype (no new metric, no new frame -- coordinates stay integer, the continuous
# stays in the cross-frame comparison). The only literal is the 2 of 2r <= D, the
# definitional non-overlap factor (the sense in which L1b's Gte(count,2) is "the
# definition of more than one", not a threshold).
#
# THREE RIVAL DERIVATIONS WERE AUDITED AND REJECTED ON MEASUREMENT, not taste:
#   * the mint's cluster extent -- ci_mint_category clusters by EXACT value, so every
#     member sits at distance 0 and the empirical extent is identically 0. A bound of
#     0 refuses colour identity's own landed off-prototype probe at dist 4. REGRESSES.
#   * the lattice step 1.0 (L1's falls-out bound) -- 1.0 < 4. REGRESSES.
#   * an MDL radius from m_min/d -- m_min=3 is a COUNT gate (m > d/(d-1)); the cost
#     model k*d + N charges 1 per label and treats the residual as free, so it
#     constrains how MANY members a category needs and never how far one may lie.
#     There is no radius in the accounting at all. NOT DERIVABLE.
#
# EXPRESSED AS Not(Exists ...) -- "no OTHER prototype is closer to the winner than
# twice the observation's residual". This is exactly 2*d_win <= min_o dist(win,o), and
# because Exists over an EMPTY source is false, Not(Exists) is TRUE when there is no
# other prototype -- so the k=1 case (packing radius undefined; a lone quantum owns
# all of space) falls out STRUCTURALLY with no default and no separate Count guard.
# Absence-tolerant by construction, and never PickUnique on a params node.
#
# HONEST RESIDUAL (§8): at k=1 the bound is therefore VACUOUS -- the defect is NOT
# fixed in the single-quantum regime. Correct vector-quantization semantics, stated in
# advance in the prereg, and the reason achromatopsia's k=1 arms are predicted
# unchanged.
#
# Times uses the ITEMS LIST form throughout. The a/b form parses to an EMPTY PRODUCT
# = 1, which would silently turn the bound into the constant 1.0 and refuse the landed
# dist-4 probe -- positive-controlled in the gate.
def BoundOff():  return Lt(A(PickCIP(), "bound"), Lit(0.5))
def BoundOn():   return Gt(A(PickCIP(), "bound"), Lit(0.5))


_bound_ok = Not(Exists(NodesOf("ColourCategory"), "o", And([
    Not(Eq(V("o"), _nearest_cat)),                       # a DIFFERENT prototype
    Lt(_opp_dist(_nearest_cat, V("o")),                  # ...closer to the winner
       Times([Lit(2.0), _dist(_nearest_cat)])),          # ...than 2 * the residual
])))

CI_ASSIGN = {
    "name": "ci_assign",
    "comment": (
        "DEQUANTIZATION (the sd loop's decode/recognize pattern): a region's "
        "categorical colour SIGN is its NEAREST minted ColourCategory quantum -- "
        "Argmin over ColourCategory by the cross-frame opponent distance "
        "dist(R,c)=Sqrt((R.crg-c.crg)^2+(R.cby-c.cby)^2) (the ONLY continuous "
        "quantity, living in the cross-frame comparison, never in a frame's "
        "coordinate -- the frame/continuum invariant). Writes sign_rg/sign_by (the "
        "assigned quantum's coordinate) and sign_dist (the residual to it). A cell "
        "whose colour EXACTLY equals a prototype gets sign_dist=0 and that "
        "category's sign (recognize); an off-prototype cell gets its nearest "
        "quantum. Re-decodes on codebook growth: gated on assigned_epoch != "
        "Scene.epoch (the sd_redecode re-arm), so every sign reflects the FINAL "
        "codebook once minting settles. Gated on Count(ColourCategory)>0 so it "
        "never fires before any quantum exists. Flag-gated on identity>0.5, OFF by "
        "default (§9)."
    ),
    "match": [["scene", "has_region", "R"]],
    "where": And([
        Gt(A(PickCIP(), "identity"), Lit(0.5)),
        NoAchromatopsia(),                       # LESION: OFF by default = intact
        _all_op_done,
        Gt(Count(NodesOf("ColourCategory")), Lit(0)),
        Not(Eq(A(R, "assigned_epoch"), A(V("scene"), "epoch"))),
        # THE REFUSAL BOUND (v1.2.0), flag-gated OFF by default: admit only inside the
        # codebook's packing radius. When bound=0 (the default) the first disjunct is
        # true, so this clause is vacuous and behaviour is byte-identical to v1.1.0.
        Or([BoundOff(), _bound_ok]),
    ]),
    "effects": [
        ["set_attr", "R", "sign_rg", term(A(_nearest_cat, "crg"))],
        ["set_attr", "R", "sign_by", term(A(_nearest_cat, "cby"))],
        ["set_attr", "R", "sign_dist", term(_dist(_nearest_cat))],
        ["set_attr", "R", "assigned_epoch", term(A(V("scene"), "epoch"))],
    ],
}


# ---------------------------------------------------------------------------
# ci_refuse -- the EXPLICIT REFUSAL (v1.2.0). Fires on exactly the complement of
#   ci_assign's bound clause: an observation that lies OUTSIDE the winner's packing
#   ball gets no categorical sign, and says so.
#
#   Following L1b's load-bearing lesson (VISION_UNIQUENESS_RESULTS.md, "why the gate
#   writes only uq_* and never l1_*") it writes ONLY NEW attributes and never touches
#   sign_rg / sign_by / sign_dist. A refused region therefore keeps the adapter's
#   initial sign_dist = -1.0, which is exactly the `refused` readout L1b's own audit
#   already used (sign_dist < 0). Clearing an assignment instead would let ci_assign
#   re-fire on the next sweep and flip the attribute forever -- and run_rules
#   terminates on exact value equality, so that build would not terminate.
#
#   It sets assigned_epoch, so its own re-arm guard goes false and it fires exactly
#   once per epoch; on codebook growth both ci_assign and ci_refuse re-arm together,
#   so a region refused against a small codebook can be admitted once a nearer
#   quantum is minted.
# ---------------------------------------------------------------------------
CI_REFUSE = {
    "name": "ci_refuse",
    "comment": (
        "THE REFUSAL (VISION_COLOUR_BOUND_PREREG.md): a region whose nearest minted "
        "quantum lies OUTSIDE that quantum's PACKING RADIUS gets NO categorical sign. "
        "The packing radius r_i = 1/2 min_{j!=i} ||c_i-c_j|| is the largest radius at "
        "which the codebook's own quanta do not overlap; two balls of radius r around "
        "prototypes separated by D are disjoint iff 2r <= D, so admission is 2*dist(R,"
        "winner) <= min_{c!=winner} dist(winner,c) and this rule fires on its exact "
        "complement. The bound FALLS OUT of the codebook (§13): it is a function of "
        "the minted prototypes, not a literal -- 7.8102 on a 3-category codebook, "
        "10.0 on a 2-category one, neither chosen -- and it reuses the very distance "
        "ci_assign already computes, applied prototype-to-prototype. Expressed as "
        "Not(Exists other prototype closer than 2*residual), so the k=1 case (no "
        "other prototype; packing radius undefined) is absence-tolerant BY "
        "CONSTRUCTION and admits -- the honest residual: the bound is vacuous at k=1. "
        "Writes ONLY new attrs (ci_refused, ci_refused_dist) and never clears "
        "sign_*, so a refused region keeps sign_dist=-1.0 (the refused readout) and "
        "every effect value is constant once set (run_rules terminates on exact value "
        "equality). Sets assigned_epoch so it fires once per epoch and re-arms with "
        "ci_assign on codebook growth. Flag-gated on ColourIdentityParams.bound>0.5, "
        "OFF by default (§9) -- at the default this rule can never fire."
    ),
    "match": [["scene", "has_region", "R"]],
    "where": And([
        Gt(A(PickCIP(), "identity"), Lit(0.5)),
        NoAchromatopsia(),                       # LESION: OFF by default = intact
        _all_op_done,
        Gt(Count(NodesOf("ColourCategory")), Lit(0)),
        Not(Eq(A(R, "assigned_epoch"), A(V("scene"), "epoch"))),
        BoundOn(),                               # OFF by default => never fires
        Not(_bound_ok),                          # the exact complement of ci_assign
    ]),
    "effects": [
        ["set_attr", "R", "ci_refused", term(Lit(1.0))],
        ["set_attr", "R", "ci_refused_dist", term(_dist(_nearest_cat))],
        ["set_attr", "R", "assigned_epoch", term(A(V("scene"), "epoch"))],
    ],
}


SEED = {
    "id": "vision_colour_identity",
    "version": "1.3.0",
    "depends_on": [],
    "description": (
        "COLOUR IDENTITY -- categorical colour as a MINTED, MDL-GATED SIGN over the "
        "opponent-colour VALUE. Builds DIRECTLY on colour-salience: salience "
        "answered WHERE to look (surround-relative opponent CONTRAST); this rung "
        "answers WHAT COLOUR IT IS (a categorical SIGN for the colour VALUE, "
        "downstream of salience). It instantiates the sd loop's DYNAMIC-QUANTIZATION "
        "pattern (decode -> recognize -> mint -> re-decode on codebook_epoch growth) "
        "for the 2-D integer opponent-colour subspace, with NO new Rust: ci_opponent "
        "computes the integer opponent coordinate (crg=cL-cM, cby=cS-(cL+cM)); "
        "ci_mint_category MINTS a ColourCategory quantum where a colour value "
        "CLUSTERS and MDL COMPRESSES (Count(same exact colour) >= 3 = m_min, which "
        "FALLS OUT of d=2: a category pays iff m*d > d+m <=> m > d/(d-1) = 2, so "
        "m>=3 -- no magic number); ci_assign writes each region's SIGN = its NEAREST "
        "minted quantum (Argmin by opponent Sqrt-distance) and re-decodes on codebook "
        "growth. So a scene with a few colour clusters mints ~that-many category "
        "quanta (k << N, MDL down), a seen colour is RECOGNIZED not re-minted (the "
        "has-guard), and a smooth gradient / iid noise mints ZERO (a category is "
        "minted ONLY if it compresses). Categories emerge from the colour "
        "distribution via MDL -- they are NOT hand-set (Witzel & Gegenfurtner). "
        "In-frame colour coordinate is INTEGER; the continuous lives ONLY in the "
        "cross-frame assignment distance (the frame/continuum invariant). NOT object "
        "colour re-ID / constancy / the 'what' layer -- that needs a bound object "
        "(the objecthood wall), the named frontier, out of scope. Reuses "
        "Count/Filter/NodesOfType/Argmin/Exists/Sqrt/Minus/Times/Plus/Gte + "
        "run_rules. Flag-gated on ColourIdentityParams.identity, OFF by default "
        "(§9). See VISION_COLOUR_IDENTITY_PREREG.md. "
        "v1.1.0 adds the ACHROMATOPSIA LESION flag "
        "(ColourIdentityParams.achromatopsia, OFF by default = INTACT): when armed "
        "it suppresses ONLY ci_mint_category + ci_assign (the categorical colour "
        "SIGN / naming), leaving ci_opponent (the chromatic SIGNAL) and the whole "
        "vision_colour salience seed (chromatic contrast / border / shape-from-"
        "colour) intact -- the colour-STRUCTURE / colour-SIGN dissociation of "
        "cerebral achromatopsia (Heywood & Cowey 1997). Default 0 => byte-identical "
        "to v1.0.0. See VISION_ACHROMATOPSIA_PREREG.md. "
        "v1.2.0 adds the REFUSAL BOUND (ColourIdentityParams.bound, OFF by default): "
        "L1b's uniqueness audit (VISION_UNIQUENESS_RESULTS.md) found ci_assign to be "
        "the worst case in its table -- an Argmin with ZERO Lte, no admission bound at "
        "all, so a probe at opponent distance 269.52 is confidently assigned and the "
        "equidistant probe is decided by a margin of exactly 0.0000; it cannot refuse, "
        "ever. When armed, ci_assign admits only INSIDE the minted codebook's PACKING "
        "RADIUS (r_i = 1/2 min_{j!=i} ||c_i-c_j||, the largest radius at which the "
        "codebook's own quanta do not overlap: 2r <= D), and the new ci_refuse rule "
        "fires on the exact complement, writing ci_refused instead of a sign. The "
        "bound FALLS OUT of the codebook (§13) -- a function of the minted prototypes, "
        "not a literal (7.8102 on a 3-category codebook, 10.0 on a 2-category one, "
        "neither chosen), reusing the distance ci_assign already computes; rival "
        "derivations (exact cluster extent = 0, the lattice step 1.0, an MDL radius "
        "from m_min/d) were audited and rejected ON MEASUREMENT. Absence-tolerant at "
        "k=1 by construction (Not(Exists) over an empty codebook-complement is true), "
        "where the packing radius is undefined and the bound is honestly VACUOUS. "
        "Default 0 => byte-identical to v1.1.0. See VISION_COLOUR_BOUND_PREREG.md. "
        "v1.3.0 FLIPS THAT DEFAULT: bound now ships ARMED (1.0). The k=1 rung "
        "(VISION_COLOUR_BOUND_K1_PREREG.md) asked whether a k=1 bound FALLS OUT and "
        "measured that NONE DOES -- and, more strongly, that none CAN: the packing "
        "radius is NON-INCREASING under codebook growth (a min over a superset cannot "
        "increase), so the k=1 radius upper-bounds every radius reachable by growth, "
        "and that supremum is UNBOUNDED. r(k=1) = +inf (admit everything) is this "
        "derivation's own limit, NOT a missing piece. Five rivals were audited and "
        "rejected, three ON MEASUREMENT: the mint's cluster extent (identically 0 -- "
        "exact-value minting gives a quantum ZERO intrinsic extent, so every length "
        "scale in this seed lives BETWEEN prototypes and at k=1 there is no between); "
        "the sqrt(2)/2 observational-resolution floor (indistinguishable from 0 on an "
        "integer lattice -- 100/100 observed coordinates integral); the lattice step "
        "1.0 (regresses, injected and measured by the previous rung); the scene's "
        "measured dynamic range (0.0 in BOTH landed k=1 scenes, and NON-LOCAL -- the "
        "same observation against the same codebook flips verdict when an UNRELATED "
        "patch is added elsewhere); and observed-separation, the ONLY rival CONSISTENT "
        "with the landed bound (0 disagreements at k>=2) and UNDEFINED at k=1. The "
        "crux: the rivals DEFINED at k=1 are INCONSISTENT with the landed bound; the "
        "one that is CONSISTENT is UNDEFINED. CAVEAT, EXPLICIT AND NOT IMPLIED AWAY: "
        "arming the bound guarantees refusal for k>=2 ONLY. A single-quantum codebook "
        "still admits any colour at any distance (correct VQ semantics: a lone quantum "
        "owns all of space). The flip is a STRICT improvement -- measured DELTA-ON "
        "EMPTY across all five landed scenes and the k=1 regime byte-identical ON vs "
        "OFF -- never a total guarantee. Closing the k=1 regime needs a mint with "
        "INTRINSIC EXTENT, i.e. colour identity's own NAMED FRONTIER (perceptual "
        "NEARNESS in minting). See VISION_COLOUR_BOUND_K1_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_colour_identity_mt",
        "label": "colour identity: categorical colour as an MDL-gated quantum "
                 "minted from the opponent-colour value subspace",
    },
    "nodes": [
        {"local_id": 0, "type": "ColourIdentityParams",
         # v1.3.0: `bound` ships ARMED (1.0). See VISION_COLOUR_BOUND_K1_PREREG.md §5:
         # the flip is gated on DELTA-ON-FLIPPED measuring EMPTY across all five landed
         # scenes AND on the k=1 regime being byte-identical ON vs OFF, so arming the
         # bound is a STRICT improvement -- refusal gained at k>=2, nothing lost at k=1.
         # CAVEAT, DELIBERATE AND NOT IMPLIED AWAY: the guarantee is k>=2 ONLY.
         "attrs": {"identity": 0.0, "achromatopsia": 0.0, "bound": 1.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [CI_OPPONENT, CI_MINT, CI_ASSIGN, CI_REFUSE],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_colour_identity.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
