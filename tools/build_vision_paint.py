"""Emit seeds/vision_paint.json — PAINT-FROM-SAMPLE (VISION_PAINT_PREREG.md).

An authoring tool, NOT agent runtime (CLAUDE.md: `tools/*` emits seed manifests).
Every DECISION the mechanism makes lives in the emitted rules; this file only
assembles their Term-tree JSON.

THE MECHANISM (prereg §2), one rule per stage, staged by done-flag handshakes:

  pt_delta     forward |Δplum| to the east / south neighbour (sensed pairs only)
  pt_block     a link is BLOCKED iff its |Δ| is a STRICT local maximum along its
               axis — non-maximum suppression as an EXACT comparison. NO
               threshold, NO scale (PROTOCOL §13).
  pt_seed      pregion := pidx
  pt_flood     pregion := min over self + neighbours across UNBLOCKED links, to
               the run_rules fixpoint. The region's HUB falls out: the unique
               cell with pidx == pregion. No node is minted; no id is assigned
               by Python.
  pt_fit1      ORDER-1 code: the region mean of plum / papp (+ centroid).
  pt_fit2      ORDER-2 code: a separable least-squares plane about the centroid.
  pt_paint     every cell is painted with ITS hub's code at the hub's korder.
  pt_resid     presid := |observed − painted|; a cell is REFUTED iff
               presid >= pquant/2 — the paint is closer to a DIFFERENT
               representable value than to the observed one. pquant is the
               field's own integer alphabet step, not a tolerance.
  pt_escalate  korder 1 -> 2 iff ANY region cell is refuted at order 1.
  pt_verdict   at the top of the ladder: prefuted := any cell still refuted, and
               presid_mean for readout.

k is NEVER assigned outside pt_escalate. Ships PaintParams{paint: 0.0} — OFF by
default (PROTOCOL §9).

v1.1.0 — THE EDGE-ANCHORED DECAYING GRADIENT (VISION_DECAY_PREREG.md).
Three rules added and ONE line of pt_paint changed, all behind a SECOND flag
`pdecay: 0.0`, also OFF by default, so v1.0.0's every number reproduces
byte-identically:

  pt_anchor    panchor := this cell touches a BLOCKED link (a luminance edge).
               The field's outer border is NOT an anchor: it carries no |Δ|, so
               it can never be a strict maximum.
  pt_dist      pdist := geodesic distance to the nearest anchor, flooded across
               the SAME unblocked links pt_flood uses, so it never leaves the
               region. Least fixed point from 0, capped by the field's own cell
               count, monotone ⇒ terminates.
  pt_decay     plam := the region's own MEAN GEODESIC DEPTH from its own
               boundary — THE DECAY LENGTH, and it FALLS OUT (PROTOCOL §13):
               geometry only, the same kind of first moment pt_fit1 already
               takes as a centroid, but in the distance-to-boundary coordinate.
  pt_paint     the order-2 excursion is multiplied by w = plam/(plam+pdist):
               the fitted plane AT the edge, relaxing to the order-1 constant
               far from it. No boundary ⇒ no anchor ⇒ w ≡ 1 ⇒ unchanged.

THE DECAY TOUCHES ONLY THE ORDER-2 RENDERING, NEVER THE ESCALATION DECISION:
korder steps 1->2 on the residual of the FLAT code, in which no plane term
appears, so k still falls out of the residual alone and pt_escalate is still the
only writer of korder.
"""
from __future__ import annotations

import json
import os

# --------------------------------------------------------------------------- #
#  Term-tree helpers — pure JSON assembly
# --------------------------------------------------------------------------- #
def V(n):                 return {"type": "Var", "name": n}
def L(v):                 return {"type": "Lit", "value": v}
def A(n, k):              return {"type": "Attr", "node": n, "key": k}
def add(*xs):             return {"type": "Plus", "items": list(xs)}
def mul(*xs):             return {"type": "Times", "items": list(xs)}
def sub(a, b):            return {"type": "Minus", "a": a, "b": b}
def div(a, b):            return {"type": "Div", "a": a, "b": b}
def absv(x):              return {"type": "Abs", "arg": x}
def mx(*xs):              return {"type": "Max", "items": list(xs)}
def eq(a, b):             return {"type": "Eq", "a": a, "b": b}
def gt(a, b):             return {"type": "Gt", "a": a, "b": b}
def gte(a, b):            return {"type": "Gte", "a": a, "b": b}
def lt(a, b):             return {"type": "Lt", "a": a, "b": b}
def AND(*xs):             return {"type": "And", "items": list(xs)}
def OR(*xs):              return {"type": "Or", "items": list(xs)}
def NOT(x):               return {"type": "Not", "arg": x}
def ite(c, t, o):         return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def cnt(src):             return {"type": "Count", "source": src}
def summ(src, var, val):  return {"type": "Sum", "source": src, "var_name": var, "value": val}
def minover(src, var, val, dflt):
    return {"type": "MinOver", "source": src, "var_name": var, "value": val, "default": dflt}
def filt(src, var, pred): return {"type": "Filter", "source": src, "var_name": var,
                                  "predicate": pred}
def exists(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def nbrs(node):           return {"type": "Neighbours", "node": node,
                                  "edge_type": "neighbour", "any_type": False}
def cells_of(field):      return {"type": "Neighbours", "node": field,
                                  "edge_type": "has_pcell", "any_type": False}
def puniq(src):           return {"type": "PickUnique", "source": src}
def params(key):
    return A(puniq({"type": "NodesOfType", "node_type": "PaintParams"}), key)


def T(t):                 return {"__term__": t}


ARMED = gt(params("paint"), L(0.5))
# The SECOND flag (v1.1.0). Ships 0.0; with it off every v1.0.0 number is
# reproduced byte-identically, because w collapses to the literal 1.0.
DECAY_ARMED = gt(params("pdecay"), L(0.5))


# --------------------------------------------------------------------------- #
#  Geometric neighbour selectors (all 1-hop over the `neighbour` edge)
# --------------------------------------------------------------------------- #
def _dir_filter(c, drow, dcol, *, sensed_only):
    """The (0 or 1)-element set of `c`'s neighbour at offset (drow, dcol)."""
    pred = [eq(A(V("n"), "prow"), add(A(V(c), "prow"), L(float(drow)))),
            eq(A(V("n"), "pcol"), add(A(V(c), "pcol"), L(float(dcol))))]
    if sensed_only:
        pred.append(gt(A(V("n"), "psensed"), L(0.5)))
    return filt(nbrs(V(c)), "n", AND(*pred))


def _delta_to(c, drow, dcol):
    """|Δplum| to the neighbour at (drow, dcol); 0.0 when EITHER endpoint carries
    no observation (an unsensed cell, i.e. the optic disc) or the neighbour is
    absent. A link with no data has no |Δ|, so the blind spot can never mint an
    edge — which is what lets its cells join the surround's region."""
    return ite(gt(A(V(c), "psensed"), L(0.5)),
               summ(_dir_filter(c, drow, dcol, sensed_only=True), "n",
                    absv(sub(A(V("n"), "plum"), A(V(c), "plum")))),
               L(0.0))


def _flank_delta(c, drow, dcol, key):
    """The neighbour-at-(drow,dcol)'s own `key` delta; 0.0 if that neighbour is
    absent. Used to compare a link's |Δ| against the links flanking it."""
    return summ(_dir_filter(c, drow, dcol, sensed_only=False), "n", A(V("n"), key))


# --------------------------------------------------------------------------- #
#  The region set, anchored to the field hub (NOT a global NodesOfType grab)
# --------------------------------------------------------------------------- #
def _region_cells(hubvar, *, sensed_only):
    pred = [eq(A(V("v"), "pregion"), A(V(hubvar), "pregion"))]
    if sensed_only:
        pred.append(gt(A(V("v"), "psensed"), L(0.5)))
    return filt(cells_of(V("field")), "v", AND(*pred))


def _mean(hubvar, key):
    obs = _region_cells(hubvar, sensed_only=True)
    return div(summ(obs, "v", A(V("v"), key)), mx(cnt(obs), L(1.0)))


def _cov(hubvar, coord, cen_key, val, mean_key):
    """Σ (coord − centroid)·(value − mean) over the region's OBSERVED cells."""
    obs = _region_cells(hubvar, sensed_only=True)
    return summ(obs, "v", mul(sub(A(V("v"), coord), A(V(hubvar), cen_key)),
                              sub(A(V("v"), val), A(V(hubvar), mean_key))))


def _var(hubvar, coord, cen_key):
    obs = _region_cells(hubvar, sensed_only=True)
    return summ(obs, "v", mul(sub(A(V("v"), coord), A(V(hubvar), cen_key)),
                              sub(A(V("v"), coord), A(V(hubvar), cen_key))))


# --------------------------------------------------------------------------- #
#  THE RULES
# --------------------------------------------------------------------------- #
def _rules():
    R = []

    # ---- pt_delta ---------------------------------------------------------- #
    R.append({
        "name": "pt_delta",
        "comment":
            "Per cell: the forward |Δplum| to the east (pd_e) and south "
            "(pd_s) neighbour, and whether that link exists at all (pd_has_e / "
            "pd_has_s). Luminance is STRUCTURE — it is what defines the regions; "
            "appearance is a SIGN and is only ever sampled and painted. A link to "
            "an ABSENT or UNSENSED neighbour contributes nothing (Sum over the "
            "empty set = 0), which is why the blind spot never invents an edge. "
            "Reads ONLY raw plum/prow/pcol/psensed on self and neighbours — NO "
            "cross-node computed dependency, so firing order is irrelevant. Fires "
            "once (pdelta_done).",
        "match": [["field", "has_pcell", "c"]],
        "where": AND(ARMED, lt(A(V("c"), "pdelta_done"), L(0.5))),
        "batch": True,
        "effects": [
            ["set_attr", "c", "pd_e", T(_delta_to("c", 0, 1))],
            ["set_attr", "c", "pd_s", T(_delta_to("c", 1, 0))],
            ["set_attr", "c", "pd_has_e", T(cnt(_dir_filter("c", 0, 1, sensed_only=True)))],
            ["set_attr", "c", "pd_has_s", T(cnt(_dir_filter("c", 1, 0, sensed_only=True)))],
            ["set_attr", "c", "pdelta_done", 1.0],
        ],
    })

    # ---- pt_block ---------------------------------------------------------- #
    # A link is BLOCKED iff its |Δ| is a STRICT local maximum along its own axis.
    def _blk(key, back, fwd):
        return ite(AND(gt(A(V("c"), "pd_has_" + key[-1]), L(0.5)),
                       gt(A(V("c"), "pd_" + key[-1]), _flank_delta("c", *back, "pd_" + key[-1])),
                       gt(A(V("c"), "pd_" + key[-1]), _flank_delta("c", *fwd, "pd_" + key[-1]))),
                   L(1.0), L(0.0))

    R.append({
        "name": "pt_block",
        "comment":
            "THE BOUNDARY, and it carries NO threshold and NO scale (PROTOCOL "
            "§13): the link east of c is BLOCKED iff its |Δ| is STRICTLY GREATER "
            "than the |Δ| of the link on either side of it along the same axis — "
            "non-maximum suppression written as an exact comparison. A uniform "
            "field (all Δ equal 0) and a LINEAR RAMP (all Δ equal) therefore have "
            "NO boundary anywhere and stay ONE region; a step has one; a "
            "Craik-O'Brien cusp has one AT THE CUSP and none at its shoulders, so "
            "each flat region KEEPS its ramp. A missing flank contributes 0 "
            "(Sum over the empty set). Fires once all neighbours' deltas are in "
            "(the handshake — never an ordering assumption).",
        "match": [["field", "has_pcell", "c"]],
        "where": AND(ARMED,
                     gt(A(V("c"), "pdelta_done"), L(0.5)),
                     lt(A(V("c"), "pblock_done"), L(0.5)),
                     NOT(exists(nbrs(V("c")), "n",
                                lt(A(V("n"), "pdelta_done"), L(0.5))))),
        "batch": True,
        "effects": [
            ["set_attr", "c", "pblk_e", T(_blk("pblk_e", (0, -1), (0, 1)))],
            ["set_attr", "c", "pblk_s", T(_blk("pblk_s", (-1, 0), (1, 0)))],
            ["set_attr", "c", "pblock_done", 1.0],
        ],
    })

    # ---- pt_seed ----------------------------------------------------------- #
    R.append({
        "name": "pt_seed",
        "comment":
            "pregion := pidx. Every cell starts as its own region; the flood then "
            "merges. Fires once (pseed_done).",
        "match": [["field", "has_pcell", "c"]],
        "where": AND(ARMED, lt(A(V("c"), "pseed_done"), L(0.5))),
        "batch": True,
        "effects": [
            ["set_attr", "c", "pregion", T(A(V("c"), "pidx"))],
            ["set_attr", "c", "pseed_done", 1.0],
        ],
    })

    # ---- pt_flood ---------------------------------------------------------- #
    # A neighbour n is REACHABLE from c iff the link between them is unblocked.
    # The block flag lives on the WEST/NORTH cell of each pair, so the direction
    # decides which of the two cells carries it.
    reachable = filt(nbrs(V("c")), "n", OR(
        AND(eq(A(V("n"), "prow"), A(V("c"), "prow")),
            eq(A(V("n"), "pcol"), add(A(V("c"), "pcol"), L(1.0))),
            lt(A(V("c"), "pblk_e"), L(0.5))),
        AND(eq(A(V("n"), "prow"), A(V("c"), "prow")),
            eq(A(V("n"), "pcol"), sub(A(V("c"), "pcol"), L(1.0))),
            lt(A(V("n"), "pblk_e"), L(0.5))),
        AND(eq(A(V("n"), "pcol"), A(V("c"), "pcol")),
            eq(A(V("n"), "prow"), add(A(V("c"), "prow"), L(1.0))),
            lt(A(V("c"), "pblk_s"), L(0.5))),
        AND(eq(A(V("n"), "pcol"), A(V("c"), "pcol")),
            eq(A(V("n"), "prow"), sub(A(V("c"), "prow"), L(1.0))),
            lt(A(V("n"), "pblk_s"), L(0.5)))))

    R.append({
        "name": "pt_flood",
        "comment":
            "THE REGION: pregion := min(self, every neighbour reachable across an "
            "UNBLOCKED link), to the run_rules fixpoint. Monotone non-increasing "
            "and bounded below by the region's minimum pidx, so it terminates. "
            "The HUB FALLS OUT — the unique cell with pidx == pregion — so no "
            "region node is minted and no id is assigned by the adapter. An "
            "UNSENSED cell (the optic disc) has no blocked links, so it joins the "
            "surround's region and is painted from it.",
        "match": [["field", "has_pcell", "c"]],
        "where": AND(ARMED,
                     gt(A(V("c"), "pblock_done"), L(0.5)),
                     NOT(exists(nbrs(V("c")), "n", lt(A(V("n"), "pseed_done"), L(0.5))))),
        "batch": True,
        "effects": [
            ["set_attr", "c", "pregion",
             T({"type": "Min", "items": [
                 A(V("c"), "pregion"),
                 minover(reachable, "n", A(V("n"), "pregion"),
                         A(V("c"), "pregion"))]})],
        ],
    })

    # ---- pt_hub ------------------------------------------------------------ #
    R.append({
        "name": "pt_hub",
        "comment":
            "MARK the region's representative. The hub already FALLS OUT of the "
            "flood (pidx == pregion); this rule only writes that fact onto the "
            "graph as `phub`, so the ADAPTER never has to compute it. Without "
            "this the read-back would need an `if` comparing two graph "
            "attributes in Python — a query, but one the graph can just as "
            "easily answer itself (CLAUDE.md).",
        "match": [["field", "has_pcell", "c"]],
        "where": AND(ARMED, gt(A(V("c"), "pblock_done"), L(0.5))),
        "batch": True,
        "effects": [
            ["set_attr", "c", "phub",
             T(ite(eq(A(V("c"), "pidx"), A(V("c"), "pregion")), L(1.0), L(0.0)))],
        ],
    })

    # ---- pt_fit1 ----------------------------------------------------------- #
    obs = _region_cells("h", sensed_only=True)
    R.append({
        "name": "pt_fit1",
        "comment":
            "THE SAMPLE, order 1: on the region's hub, the region mean of plum and "
            "papp plus the centroid — pooled over the field-anchored set of cells "
            "sharing this hub's pregion, counting ONLY cells that carry an "
            "observation (psensed). ONE sampling rule, applied to every stimulus "
            "identically; there is no per-stimulus branch anywhere in this seed. "
            "NOT done-flagged: the flood may still be merging, so the fit is "
            "idempotent and re-settles with it (it is a pure function of its "
            "inputs, so it cannot dither).",
        "match": [["field", "has_pcell", "h"]],
        "where": AND(ARMED,
                     gt(A(V("h"), "pblock_done"), L(0.5)),
                     eq(A(V("h"), "pidx"), A(V("h"), "pregion"))),
        "batch": True,
        "effects": [
            ["set_attr", "h", "pn", T(cnt(obs))],
            ["set_attr", "h", "pmean_lum", T(_mean("h", "plum"))],
            ["set_attr", "h", "pmean_app", T(_mean("h", "papp"))],
            ["set_attr", "h", "pcen_r", T(_mean("h", "prow"))],
            ["set_attr", "h", "pcen_c", T(_mean("h", "pcol"))],
            ["set_attr", "h", "pnall", T(cnt(_region_cells("h", sensed_only=False)))],
        ],
    })

    # ---- pt_fit2 ----------------------------------------------------------- #
    fx = []
    for coord, cen, tag in (("prow", "pcen_r", "r"), ("pcol", "pcen_c", "c")):
        fx.append(["set_attr", "h", "pvar_" + tag, T(_var("h", coord, cen))])
        for chan, mk in (("plum", "pmean_lum"), ("papp", "pmean_app")):
            fx.append(["set_attr", "h", "pslope_%s_%s" % (tag, chan),
                       T(div(_cov("h", coord, cen, chan, mk),
                             A(V("h"), "pvar_" + tag)))])
    R.append({
        "name": "pt_fit2",
        "comment":
            "THE SAMPLE, order 2: a separable least-squares plane about the "
            "region centroid — one slope per coordinate per channel. Declared as "
            "a SEPARABLE estimate, not an optimal joint fit: for a region whose "
            "row and column coordinates are correlated it is the marginal slope. "
            "`Div` returns 0.0 on a zero denominator, which is exactly right here "
            "— a single-row region HAS no row slope — and is the reason no "
            "epsilon appears. Reads pmean_*/pcen_* written by pt_fit1 on the SAME "
            "node; pt_fit1 does not read anything pt_fit2 writes, so the pair has "
            "no cycle and the fixpoint settles it.",
        "match": [["field", "has_pcell", "h"]],
        "where": AND(ARMED,
                     gt(A(V("h"), "pblock_done"), L(0.5)),
                     eq(A(V("h"), "pidx"), A(V("h"), "pregion")),
                     gt(A(V("h"), "pn"), L(0.5))),
        "batch": True,
        "effects": fx,
    })

    # ---- pt_anchor (v1.1.0) ------------------------------------------------- #
    R.append({
        "name": "pt_anchor",
        "comment":
            "THE ANCHOR. panchor := 1 iff this cell touches a BLOCKED link — its "
            "own east/south link, or the east link of its west neighbour, or the "
            "south link of its north neighbour. A blocked link IS a strict-|Δ| "
            "maximum, i.e. a luminance edge, so 'edge-anchored' here means "
            "anchored at a luminance discontinuity and NOTHING ELSE. In "
            "particular THE FIELD'S OUTER BORDER IS NOT AN ANCHOR: a border link "
            "does not exist (pd_has_* = 0), so pt_block can never call it a "
            "maximum. Fires once all neighbours' block flags are in (the same "
            "handshake pt_block itself uses — never an ordering assumption).",
        "match": [["field", "has_pcell", "c"]],
        "where": AND(ARMED, DECAY_ARMED,
                     gt(A(V("c"), "pblock_done"), L(0.5)),
                     lt(A(V("c"), "panchor_done"), L(0.5)),
                     NOT(exists(nbrs(V("c")), "n",
                                lt(A(V("n"), "pblock_done"), L(0.5))))),
        "batch": True,
        "effects": [
            ["set_attr", "c", "panchor",
             T(ite(OR(gt(A(V("c"), "pblk_e"), L(0.5)),
                      gt(A(V("c"), "pblk_s"), L(0.5)),
                      gt(_flank_delta("c", 0, -1, "pblk_e"), L(0.5)),
                      gt(_flank_delta("c", -1, 0, "pblk_s"), L(0.5))),
                   L(1.0), L(0.0)))],
            ["set_attr", "c", "panchor_done", 1.0],
        ],
    })

    # ---- pt_dist (v1.1.0) --------------------------------------------------- #
    # The cap is the FIELD'S OWN CELL COUNT: no geodesic inside a region can
    # reach it, so it never binds on an anchored region. It is present only so
    # that an UNANCHORED region's iteration provably terminates instead of
    # climbing forever (that region's weight is 1.0 regardless — see pt_paint).
    cap = mul(A(V("field"), "prows"), A(V("field"), "pcols"))
    R.append({
        "name": "pt_dist",
        "comment":
            "THE DISTANCE FROM THE EDGE: pdist := 0 on an anchor, else 1 + the "
            "min over neighbours reachable across an UNBLOCKED link — THE SAME "
            "reachability pt_flood uses, so the distance is geodesic WITHIN the "
            "region and never crosses a boundary (Arend & Goldstein 1987: the "
            "code's domain of validity is its own compartment). Least fixed "
            "point from 0: monotone NON-DECREASING and bounded by the field's "
            "cell count, so it terminates. No threshold, no scale, no "
            "coordinate — a pure graph quantity.",
        "match": [["field", "has_pcell", "c"]],
        "where": AND(ARMED, DECAY_ARMED,
                     gt(A(V("c"), "panchor_done"), L(0.5)),
                     NOT(exists(nbrs(V("c")), "n",
                                lt(A(V("n"), "panchor_done"), L(0.5))))),
        "batch": True,
        "effects": [
            ["set_attr", "c", "pdist",
             T(ite(gt(A(V("c"), "panchor"), L(0.5)),
                   L(0.0),
                   {"type": "Min", "items": [
                       cap,
                       add(L(1.0), minover(reachable, "n", A(V("n"), "pdist"), cap))]}))],
        ],
    })

    # ---- pt_decay (v1.1.0) -------------------------------------------------- #
    allc = _region_cells("h", sensed_only=False)
    anch = filt(cells_of(V("field")), "v",
                AND(eq(A(V("v"), "pregion"), A(V("h"), "pregion")),
                    gt(A(V("v"), "panchor"), L(0.5))))
    R.append({
        "name": "pt_decay",
        "comment":
            "THE DECAY LENGTH, AND IT FALLS OUT (PROTOCOL §13). plam := the "
            "region's own MEAN GEODESIC DEPTH from its own boundary, Σpdist/n. "
            "It is GEOMETRY ONLY — no tuning, no threshold, no imported "
            "constant, no reference to any target output — and it is the SAME "
            "KIND OF OBJECT pt_fit1 already computes: pcen_r/pcen_c are the "
            "region's first moment in the row/column coordinate; plam is its "
            "first moment in the DISTANCE-TO-ITS-OWN-BOUNDARY coordinate. It is "
            "RELATIVE, not absolute: the code depends only on the dimensionless "
            "pdist/plam, so it rescales with the lattice. CLOSED FORM: a region "
            "anchored on ONE side has pdist uniform on 0..d_max, so plam = "
            "d_max/2 EXACTLY and the far-edge weight is plam/(plam+d_max) = 1/3, "
            "INDEPENDENT OF REGION WIDTH — the decay cuts the plane's far-field "
            "excursion to exactly one third. Nothing was chosen to make that 1/3. "
            "panch_n counts the region's anchors, so a region with NO boundary "
            "can be told apart from one whose boundary is everywhere. Geometry "
            "is counted over ALL the region's cells, sensed or not: depth does "
            "not need an observation.",
        "match": [["field", "has_pcell", "h"]],
        "where": AND(ARMED, DECAY_ARMED,
                     gt(A(V("h"), "panchor_done"), L(0.5)),
                     eq(A(V("h"), "pidx"), A(V("h"), "pregion"))),
        "batch": True,
        "effects": [
            ["set_attr", "h", "panch_n", T(cnt(anch))],
            ["set_attr", "h", "plam",
             T(div(summ(allc, "v", A(V("v"), "pdist")), mx(cnt(allc), L(1.0))))],
        ],
    })

    # ---- pt_paint ---------------------------------------------------------- #
    hub_of_c = puniq(filt(cells_of(V("field")), "v",
                          eq(A(V("v"), "pidx"), A(V("c"), "pregion"))))

    def _painted(chan, mk):
        h = hub_of_c
        flat = A(h, mk)
        # THE DECAY (v1.1.0). w(0) = 1 — at the edge the code IS the fitted
        # plane; w strictly decreasing; w -> 0 far away — the code relaxes to
        # the order-1 constant. NO BOUNDARY => NO ANCHOR => NO DECAY: a region
        # with panch_n == 0 takes the literal 1.0 and is painted exactly as in
        # v1.0.0, which is why a linear ramp (a strict-max-free field, hence
        # boundary-free) is byte-identical. plam == 0 <=> pdist == 0 everywhere
        # <=> the region is ALL boundary; Div's documented 0/0 = 0 then kills
        # the order-2 term, which is right: a region that is all boundary has no
        # room for a gradient.
        wgt = ite(AND(DECAY_ARMED, gt(A(h, "panch_n"), L(0.5))),
                  div(A(h, "plam"), add(A(h, "plam"), A(V("c"), "pdist"))),
                  L(1.0))
        # `wgt` is folded into each slope term rather than around their sum, so
        # that with the flag OFF the arithmetic is the SAME EXPRESSION TREE as
        # v1.0.0 up to an exact multiplication by the literal 1.0 — floating
        # point re-association would otherwise put §9's byte-identity at the
        # mercy of the last ULP.
        plane = add(A(h, mk),
                    mul(wgt, A(h, "pslope_r_" + chan),
                        sub(A(V("c"), "prow"), A(h, "pcen_r"))),
                    mul(wgt, A(h, "pslope_c_" + chan),
                        sub(A(V("c"), "pcol"), A(h, "pcen_c"))))
        return ite(gte(A(h, "korder"), L(1.5)), plane, flat)

    R.append({
        "name": "pt_paint",
        "comment":
            "THE PAINT: every cell — sensed or not — takes ITS OWN hub's code at "
            "the hub's current korder. korder is read here and assigned NOWHERE "
            "but pt_escalate. The hub is found by pidx == this cell's pregion, "
            "which is unique by construction, so PickUnique is the honest read "
            "(PROTOCOL §12.3: `Pick` would silently return one of N). "
            "v1.1.0 — THE DECAY: the order-2 excursion is multiplied by "
            "w = plam/(plam+pdist), which is 1 AT the anchoring edge and "
            "STRICTLY DECREASING to 0 away from it, so the code is the fitted "
            "plane at the edge and relaxes to the order-1 constant far from it "
            "— never a constant-slope extrapolation across the far field, which "
            "is the operation Arend & Goldstein 1987 show is ill-posed and "
            "Cohen-Duwek & Spitzer 2019 show reconstructs the veridical image. "
            "DECLARED (PROTOCOL §13.1): the decay LENGTH falls out of the "
            "region's geometry, but the FALLOFF'S FORM is ARCHITECTURE — w is "
            "monotone BY CONSTRUCTION, so a decline-with-distance signature "
            "cannot fail to appear and is not evidence that one emerged.",
        "match": [["field", "has_pcell", "c"]],
        "where": AND(ARMED, gt(A(V("c"), "pblock_done"), L(0.5))),
        "batch": True,
        "effects": [
            ["set_attr", "c", "ppaint_lum", T(_painted("plum", "pmean_lum"))],
            ["set_attr", "c", "ppaint_app", T(_painted("papp", "pmean_app"))],
            ["set_attr", "c", "pkorder_seen", T(A(hub_of_c, "korder"))],
        ],
    })

    # ---- pt_resid ---------------------------------------------------------- #
    quant = A(V("field"), "pquant")
    rl = absv(sub(A(V("c"), "plum"), A(V("c"), "ppaint_lum")))
    ra = absv(sub(A(V("c"), "papp"), A(V("c"), "ppaint_app")))
    R.append({
        "name": "pt_resid",
        "comment":
            "SUBTRACT. presid := |observed − painted| per channel, on OBSERVED "
            "cells only. A cell is REFUTED iff its residual reaches pquant/2 — "
            "the paint is then closer to a DIFFERENT representable value than to "
            "the observed one. pquant is the field's OWN integer alphabet step "
            "(in-frame is INTEGER; the paint is a cross-frame rendering and may "
            "be real). It is a RESOLUTION, not a tolerance: nothing is tuned, and "
            "a scale-invariance arm re-runs the whole battery at a ×4 alphabet.",
        "match": [["field", "has_pcell", "c"]],
        "where": AND(ARMED,
                     gt(A(V("c"), "psensed"), L(0.5)),
                     gt(A(V("c"), "pblock_done"), L(0.5))),
        "batch": True,
        "effects": [
            ["set_attr", "c", "presid_lum", T(rl)],
            ["set_attr", "c", "presid_app", T(ra)],
            ["set_attr", "c", "prefuted_cell",
             T(ite(gte(mx(rl, ra), div(quant, L(2.0))), L(1.0), L(0.0)))],
            ["set_attr", "c", "presid_order", T(A(V("c"), "pkorder_seen"))],
        ],
    })

    # ---- pt_escalate ------------------------------------------------------- #
    obs_h = _region_cells("h", sensed_only=True)
    settled = NOT(exists(obs_h, "v", NOT(eq(A(V("v"), "presid_order"), A(V("h"), "korder")))))
    R.append({
        "name": "pt_escalate",
        "comment":
            "K FALLS OUT OF THE RESIDUAL, and this is the ONLY rule that assigns "
            "korder. The region's order steps 1 -> 2 iff ANY of its observed "
            "cells is REFUTED at the order the residual was actually computed at "
            "(the presid_order handshake — never an ordering assumption). Nothing "
            "in the seed, the adapter or the tests chooses k: a flat surface stops "
            "at 1, a vague pattern reaches 2, and a surface the ladder cannot "
            "express reaches 2 and STAYS refuted. Monotone and capped by the "
            "built ladder, so it terminates.",
        "match": [["field", "has_pcell", "h"]],
        "where": AND(ARMED,
                     eq(A(V("h"), "pidx"), A(V("h"), "pregion")),
                     lt(A(V("h"), "korder"), L(1.5)),
                     gt(A(V("h"), "pn"), L(0.5)),
                     settled,
                     exists(obs_h, "v", gt(A(V("v"), "prefuted_cell"), L(0.5)))),
        "batch": True,
        "effects": [["set_attr", "h", "korder", 2.0]],
    })

    # ---- pt_verdict -------------------------------------------------------- #
    R.append({
        "name": "pt_verdict",
        "comment":
            "THE MECHANISM SAYS WHETHER IT IS WRONG. At the top of the built "
            "ladder, prefuted := 1 iff some observed cell is STILL refuted — the "
            "ladder EXHAUSTED and the paint does not describe this surface. "
            "presid_mean is the readout (a measured magnitude, never a threshold).",
        "match": [["field", "has_pcell", "h"]],
        "where": AND(ARMED,
                     eq(A(V("h"), "pidx"), A(V("h"), "pregion")),
                     gte(A(V("h"), "korder"), L(1.5)),
                     gt(A(V("h"), "pn"), L(0.5)),
                     settled),
        "batch": True,
        "effects": [
            ["set_attr", "h", "prefuted",
             T(ite(exists(obs_h, "v", gt(A(V("v"), "prefuted_cell"), L(0.5))),
                   L(1.0), L(0.0)))],
            ["set_attr", "h", "presid_mean",
             T(div(summ(obs_h, "v", mx(A(V("v"), "presid_lum"), A(V("v"), "presid_app"))),
                   mx(cnt(obs_h), L(1.0))))],
            ["set_attr", "h", "pverdict_done", 1.0],
        ],
    })
    return R


def build() -> dict:
    return {
        "id": "vision_paint",
        "version": "1.1.0",
        "depends_on": [],
        "description":
            "PAINT-FROM-SAMPLE — appearance as an order-k code sampled from a "
            "contour-bounded region, painted over the whole region as a cheap "
            "pass, and the residual taken where the paint was wrong. The order k "
            "FALLS OUT of the residual (PROTOCOL §13): paint flat, and escalate "
            "only where the paint is refuted at the field's own alphabet "
            "resolution. Boundaries are strict local maxima of |Δ| — an exact "
            "comparison with NO threshold and NO scale. Luminance is STRUCTURE "
            "(it defines the regions); appearance is a SIGN (it is sampled and "
            "painted). v1.1.0 adds the EDGE-ANCHORED DECAYING GRADIENT behind a "
            "second flag: the order-2 excursion is anchored at the boundary that "
            "sourced it and decays over the region's OWN mean geodesic depth, so "
            "the code is the fitted plane AT the edge and the order-1 constant "
            "FAR from it — never an extrapolation across the far field. Ships "
            "INERT (paint=0, pdecay=0) so every committed result reproduces "
            "(PROTOCOL §9).",
        "microtheory": {
            "name": "paint_from_sample",
            "description":
                "A surface's appearance is not computed per cell. It is SAMPLED "
                "as an order-k code over a region and PAINTED; the residual is "
                "where the paint was wrong, and it is the residual — not a "
                "parameter — that decides the order.",
        },
        "nodes": [{"local_id": 0, "type": "PaintParams",
                   "attrs": {"paint": 0.0, "pdecay": 0.0}}],
        "edges": [],
        "productions": [
            {"provenance": "seed:vision_paint:has_pcell",
             "src": {"type": "PaintField", "var": "f"},
             "edge_type": "has_pcell",
             "tgt": {"type": "PaintCell", "var": "c"}},
            {"provenance": "seed:vision_paint:neighbour",
             "src": {"type": "PaintCell", "var": "a"},
             "edge_type": "neighbour",
             "tgt": {"type": "PaintCell", "var": "b"}},
        ],
        "rules": _rules(),
    }


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_paint.json")
    with open(out, "w") as fh:
        json.dump(build(), fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote", out)
