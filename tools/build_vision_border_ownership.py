#!/usr/bin/env python3
"""Emit seeds/vision_border_ownership.json — BORDER-OWNERSHIP / PROTO-OBJECT: a
local edge becomes a DIRECTED boundary that OWNS its figure, and a bounded, owned,
PRE-IDENTITY region is minted as a ProtoObject. Pure graph data (NO new Rust).

See VISION_BORDER_OWNERSHIP_PREREG.md. The mechanism (all SEED RULES; the adapter
supplies only a Cell grid + neighbour edges, mechanical geometry like vision_ground):

  bo_bgflood  SURROUNDEDNESS as reachability (the recurrence): bg=1 iff a frame cell
              OR a same-val neighbour has bg=1 -> iterated by run_rules to a fixpoint,
              bg=1 == reachable from the frame without crossing a contour == GROUND;
              bg=0 == ENCLOSED (figure). Never crosses a contour (same-val only).
  bo_label    COMPONENT LABEL: glabel = min over same-val neighbours' glabel (init cid)
              -> each same-value connected component shares its root's cid.
  bo_mint_enclosed  PROTO-OBJECT from a CLOSED, SINGLY-SURROUNDED figure: a component
              ROOT that is enclosed mints ONE ProtoObject (NO identity) iff it is
              bordered by a SINGLE ground component (the closure test that refuses iid
              speckle) -- no size threshold, closure FALLS OUT of "a hole in one
              surface" (PROTOCOL §13).
  bo_mint_gestalt  GESTALT figure-ground on an AMBIGUOUS bipartition (surroundedness
              silent): no enclosed component AND Count(components)==2 -> figure = the
              SMALLER (Argmin by size); a size TIE is HELD OPEN (no proto).
  bo_own      DIRECTED OWNERSHIP: a figure boundary cell (adjacent across a contour)
              sets owns=1 and adds a directed owns_figure edge -> its ProtoObject.

run_rules runs all five to a JOINT fixpoint: flood <-> label <-> mint <-> own iterated
to convergence -- the grouping<->ownership recurrence (the substrate is architecturally
AHEAD of the feedforward account here). In-frame integer coords; ownership is a
RELATION; surroundedness is discrete reachability (the frame/continuum invariant).
Flag-gated on BorderOwnParams.bown, OFF by default (§9).

NO new Rust: reuses Neighbours/Filter/Count/Exists/Argmin/NodesOfType/IfThenElse-free
And/Or/Not/Eq/Gt/Lt + run_rules. This is a seed BUILDER (emits graph data) --
admissible under CLAUDE.md.  Run:  python tools/build_vision_border_ownership.py
"""
from __future__ import annotations
import json
import os


# --- term constructors (the DSL JSON forms, same as build_vision_colour_identity) --
def V(name):            return {"type": "Var", "name": name}
def Lit(v):             return {"type": "Lit", "value": v}
def A(node, key):       return {"type": "Attr", "node": node, "key": key}
def Gt(a, b):           return {"type": "Gt", "a": a, "b": b}
def Lt(a, b):           return {"type": "Lt", "a": a, "b": b}
def Gte(a, b):          return {"type": "Gte", "a": a, "b": b}
def Eq(a, b):           return {"type": "Eq", "a": a, "b": b}
def Not(x):             return {"type": "Not", "arg": x}
def And(items):         return {"type": "And", "items": items}
def Or(items):          return {"type": "Or", "items": items}
def NodesOf(t):         return {"type": "NodesOfType", "node_type": t}
def Neigh(node):        return {"type": "Neighbours", "node": node,
                                "edge_type": "neighbour", "any_type": False}
def Filter(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Count(src):         return {"type": "Count", "source": src}
def Exists(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Argmin(src, var, value):
    return {"type": "Argmin", "source": src, "var_name": var, "value": value,
            "default": None}
def PickP():
    return {"type": "PickUnique", "source": NodesOf("BorderOwnParams")}
def term(x):            return {"__term__": x}


R = V("R")
CELLS = NodesOf("Cell")


def _bown_on():
    return Gt(A(PickP(), "bown"), Lit(0.5))


# same-val neighbour of node with bg=1 (flood source)
def _has_bg_sameval_neigh(node):
    return Exists(Neigh(node), "m",
                  And([Eq(A(V("m"), "val"), A(node, "val")),
                       Gt(A(V("m"), "bg"), Lit(0.5))]))


# same-val neighbour of node with a SMALLER glabel (label flood source)
def _has_smaller_sameval_neigh(node):
    return Exists(Neigh(node), "m",
                  And([Eq(A(V("m"), "val"), A(node, "val")),
                       Lt(A(V("m"), "glabel"), A(node, "glabel"))]))


# --- floods settled? (no cell can still change) --------------------------------
_bg_unsettled = Exists(CELLS, "z",
                       And([Lt(A(V("z"), "bg"), Lit(0.5)),
                            Or([Gt(A(V("z"), "frame"), Lit(0.5)),
                                _has_bg_sameval_neigh(V("z"))])]))
_label_unsettled = Exists(CELLS, "z", _has_smaller_sameval_neigh(V("z")))
_SETTLED = And([Not(_bg_unsettled), Not(_label_unsettled)])


# --- component size and roots --------------------------------------------------
def _size(node):
    return Count(Filter(CELLS, "z", Eq(A(V("z"), "glabel"), A(node, "glabel"))))


_ROOTS = Filter(CELLS, "q", Eq(A(V("q"), "glabel"), A(V("q"), "cid")))


# --- closure / objecthood test (the constraint that makes a proto an OBJECT) ----
# A proto-object is a figure that is a HOLE IN ONE SURFACE. Two conjuncts:
#   (a) SURROUNDED ONLY BY GROUND: no figure cell borders a DIFFERENT enclosed
#       (bg=0) component. This rejects iid speckle (an interior noise cell whose
#       neighbours are other enclosed singletons of different glabel is NOT a hole
#       in a surface) and its vacuous-closure trap (a figure with no ground
#       neighbour at all). It also makes surroundedness real: the figure's whole
#       outer contour is ground.
#   (b) SINGLE GROUND: those ground cells all share one glabel (one surface).
# Cells of R's figure:
def _figure_cells():
    return Filter(CELLS, "f", And([Eq(A(V("f"), "glabel"), A(R, "glabel")),
                                   Lt(A(V("f"), "bg"), Lit(0.5))]))


# (a) no figure cell has a neighbour that is a different component AND still enclosed.
_SURROUNDED_BY_GROUND = Not(Exists(
    _figure_cells(), "f",
    Exists(Neigh(V("f")), "n",
           And([Not(Eq(A(V("n"), "glabel"), A(R, "glabel"))),
                Lt(A(V("n"), "bg"), Lit(0.5))]))))


# (b) ground-border cells (bg=1, adjacent to a figure cell) all share one glabel.
def _ground_border_cells():
    return Filter(CELLS, "g",
                  And([Gt(A(V("g"), "bg"), Lit(0.5)),
                       Exists(Neigh(V("g")), "f",
                              And([Lt(A(V("f"), "bg"), Lit(0.5)),
                                   Eq(A(V("f"), "glabel"), A(R, "glabel"))]))]))


_SINGLE_GROUND = Not(Exists(
    _ground_border_cells(), "g1",
    Exists(_ground_border_cells(), "g2",
           Not(Eq(A(V("g1"), "glabel"), A(V("g2"), "glabel"))))))

_CLOSED = And([_SURROUNDED_BY_GROUND, _SINGLE_GROUND])


# ---------------------------------------------------------------------------
# bo_bgflood -- SURROUNDEDNESS as reachability (the recurrence). Monotone 0->1.
# ---------------------------------------------------------------------------
BO_BGFLOOD = {
    "name": "bo_bgflood",
    "comment": (
        "SURROUNDEDNESS as discrete REACHABILITY (the run_rules recurrence). Set bg=1 "
        "on a cell that is a frame cell OR has a same-VAL 4-neighbour with bg=1 -- so "
        "bg floods from the frame INWARD along equal-value adjacency and NEVER crosses "
        "a contour (a value change). Iterated by run_rules to a fixpoint, bg=1 means "
        "the cell's same-value region is reachable from the frame == GROUND/background; "
        "bg=0 means ENCLOSED (a figure candidate). Monotone 0->1 (guarded bg<0.5) so "
        "the flood terminates. The vision_ground/vision_lateral local-neighbour-fold "
        "idiom, O(N) per sweep under run_rules (NOT the O(N^2) apply_rule_once drive). "
        "Flag-gated on BorderOwnParams.bown>0.5, OFF by default (§9)."
    ),
    "match": [["field", "has_cell", "R"]],
    "where": And([
        _bown_on(),
        Lt(A(R, "bg"), Lit(0.5)),
        Or([Gt(A(R, "frame"), Lit(0.5)), _has_bg_sameval_neigh(R)]),
    ]),
    "effects": [["set_attr", "R", "bg", term(Lit(1.0))]],
}


# ---------------------------------------------------------------------------
# bo_label -- COMPONENT LABEL. Monotone decreasing glabel -> min cid per component.
# ---------------------------------------------------------------------------
BO_LABEL = {
    "name": "bo_label",
    "comment": (
        "COMPONENT LABEL (the grouping substrate): glabel := the minimum glabel among "
        "this cell's same-VAL 4-neighbours (init cid = crow*W+ccol). Fires only when a "
        "same-val neighbour has a SMALLER glabel, so glabel decreases monotonically and "
        "the flood terminates; at the fixpoint every same-value connected component "
        "shares its ROOT's cid (its minimum). A cell is a component ROOT iff "
        "glabel==cid. This is the canonical-representative substrate for minting ONE "
        "proto per component (batch-safe: exactly one root per component). O(N) per "
        "sweep. Flag-gated on bown>0.5, OFF by default (§9)."
    ),
    "match": [["field", "has_cell", "R"]],
    "where": And([
        _bown_on(),
        _has_smaller_sameval_neigh(R),
    ]),
    "effects": [
        ["set_attr", "R", "glabel",
         term(A(Argmin(Filter(Neigh(R), "n", Eq(A(V("n"), "val"), A(R, "val"))),
                       "n", A(V("n"), "glabel")), "glabel"))],
    ],
}


# ---------------------------------------------------------------------------
# bo_mint_enclosed -- PROTO-OBJECT from a closed, singly-surrounded figure.
# ---------------------------------------------------------------------------
BO_MINT_ENCLOSED = {
    "name": "bo_mint_enclosed",
    "comment": (
        "MINT a ProtoObject (NO identity/category -- the PRE-IDENTITY stage) for an "
        "ENCLOSED, CLOSED, SINGLY-SURROUNDED figure component. Gates (cheap self-attr "
        "first, expensive graph aggregates last): (1) bown>0.5; (2) R.bg<0.5 -- "
        "enclosed; (3) R.glabel==R.cid -- R is the component ROOT (canonical "
        "representative, batch-safe: exactly one per component); (4) floods SETTLED (no "
        "cell can still flood) so member count and closure are exact, never a transient "
        "undercount; (5) SINGLE-GROUND CLOSURE -- Not two ground-side neighbours of the "
        "figure with different glabel, i.e. the figure is a hole in ONE surface. This "
        "closure test is what makes a proto an OBJECT and what refuses iid speckle (an "
        "interior noise cell is bordered by many distinct components -> not singly "
        "surrounded -> no proto); it needs NO size threshold -- closure FALLS OUT of "
        "'enclosed by one ground' (§13); (6) Not Exists a ProtoObject already at this "
        "root (recognize-not-re-mint). members = Count(cells with this glabel). "
        "Flag-gated on bown>0.5, OFF by default (§9)."
    ),
    "match": [["field", "has_cell", "R"]],
    "where": And([
        _bown_on(),
        Lt(A(R, "bg"), Lit(0.5)),
        Eq(A(R, "glabel"), A(R, "cid")),
        _SETTLED,
        _CLOSED,
        Not(Exists(NodesOf("ProtoObject"), "p", Eq(A(V("p"), "root"), A(R, "cid")))),
    ]),
    "effects": [
        ["add_node", "po", "ProtoObject", {
            "root": term(A(R, "cid")),
            "members": term(_size(R)),
            "minted": term(Lit(1.0)),
            "gestalt": term(Lit(0.0)),
        }],
        ["add_edge", "field", "has_proto", "po"],
    ],
}


# ---------------------------------------------------------------------------
# bo_mint_gestalt -- Gestalt figure-ground on an ambiguous bipartition.
# ---------------------------------------------------------------------------
_OTHER_ROOT_SAME_SIZE = Exists(_ROOTS, "q2", And([
    Not(Eq(A(V("q2"), "cid"), A(R, "cid"))),
    Eq(_size(V("q2")), _size(R)),
]))

BO_MINT_GESTALT = {
    "name": "bo_mint_gestalt",
    "comment": (
        "GESTALT figure-ground when SURROUNDEDNESS is SILENT (no enclosed component) "
        "and the display is a single-contour BIPARTITION (Count(components)==2 -- the "
        "definition of one contour splitting the field into figure+ground, NOT a tuned "
        "number: an open/partial contour makes >=3 components and this rule never "
        "fires). Figure = the SMALLER component (Argmin over the two roots by size = "
        "Count of members). A size TIE (Exists the other root with equal size) is HELD "
        "OPEN -- no figure, no proto (anti-confabulation; the symmetric bistable Rubin "
        "case). Mints a ProtoObject (gestalt:1) for the smaller. Gates ordered "
        "cheap-first: bown; R.bg>0.5 (non-enclosed); R is a ROOT; then the O(N) "
        "aggregates. Flag-gated on bown>0.5, OFF by default (§9)."
    ),
    "match": [["field", "has_cell", "R"]],
    "where": And([
        _bown_on(),
        Gt(A(R, "bg"), Lit(0.5)),
        Eq(A(R, "glabel"), A(R, "cid")),
        _SETTLED,
        Not(Exists(CELLS, "z", Lt(A(V("z"), "bg"), Lit(0.5)))),
        Eq(Count(_ROOTS), Lit(2)),
        Eq(V("R"), Argmin(_ROOTS, "q", _size(V("q")))),
        Not(_OTHER_ROOT_SAME_SIZE),
        Not(Exists(NodesOf("ProtoObject"), "p", Eq(A(V("p"), "root"), A(R, "cid")))),
    ]),
    "effects": [
        ["add_node", "po", "ProtoObject", {
            "root": term(A(R, "cid")),
            "members": term(_size(R)),
            "minted": term(Lit(1.0)),
            "gestalt": term(Lit(1.0)),
        }],
        ["add_edge", "field", "has_proto", "po"],
    ],
}


# ---------------------------------------------------------------------------
# bo_own -- DIRECTED OWNERSHIP (unified: enclosed OR gestalt figure).
# ---------------------------------------------------------------------------
BO_OWN = {
    "name": "bo_own",
    "comment": (
        "DIRECTED BORDER-OWNERSHIP. A figure BOUNDARY cell -- one whose component has a "
        "ProtoObject (p.root == R.glabel) and which is adjacent across a contour to a "
        "cell of a DIFFERENT component (Exists a neighbour with a different glabel) -- "
        "sets owns=1 and adds a directed owns_figure edge to its ProtoObject p. The "
        "border OWNS the figure side; the ground side is never owned. This is the "
        "grounded directed CONTOUR RELATION (a typed edge from the border to the region "
        "it owns), covering both the enclosed proto (figure = the hole) and the gestalt "
        "proto (figure = the smaller region). Monotone (owns<0.5) so it terminates. p "
        "is bound by a has_proto match edge (add_edge needs a bound target). Gates "
        "cheap-first; SETTLED last. Flag-gated on bown>0.5, OFF by default (§9)."
    ),
    "match": [["field", "has_cell", "R"], ["field", "has_proto", "p"]],
    "where": And([
        _bown_on(),
        Lt(A(R, "owns"), Lit(0.5)),
        Eq(A(V("p"), "root"), A(R, "glabel")),
        Exists(Neigh(R), "n", Not(Eq(A(V("n"), "glabel"), A(R, "glabel")))),
        _SETTLED,
    ]),
    "effects": [
        ["set_attr", "R", "owns", term(Lit(1.0))],
        ["add_edge", "R", "owns_figure", "p"],
    ],
}


SEED = {
    "id": "vision_border_ownership",
    "version": "1.0.0",
    "depends_on": [],
    "description": (
        "BORDER-OWNERSHIP / PROTO-OBJECT -- a local edge becomes a DIRECTED boundary "
        "that OWNS its figure, and a bounded, owned, PRE-IDENTITY region is minted as a "
        "ProtoObject (NO category/recognition -- the NEAR side of the objecthood 'what' "
        "wall). The Zhou/Friedman/von der Heydt 2000 signature: for an IDENTICAL local "
        "edge, ownership FLIPS with the GLOBAL figure -- it is CONTEXTUAL, not local. "
        "Mechanism (all seed rules; NO new Rust): bo_bgflood computes SURROUNDEDNESS as "
        "a same-value reachability flood from the frame (bg=1 == ground reachable "
        "without crossing a contour; bg=0 == enclosed figure) -- iterated by run_rules "
        "to a fixpoint, the grouping<->ownership RECURRENCE (grounding doc #4, where the "
        "substrate is AHEAD of the feedforward account); bo_label labels same-value "
        "components; bo_mint_enclosed mints ONE ProtoObject per enclosed, CLOSED, "
        "SINGLY-SURROUNDED figure (the closure test refuses iid speckle -- no size "
        "threshold, closure FALLS OUT of 'a hole in one surface', §13); bo_mint_gestalt "
        "handles the ambiguous bipartition where surroundedness is silent (figure = the "
        "smaller region; a size tie held open); bo_own adds the directed owns_figure "
        "edge from a figure boundary cell to its ProtoObject. In-frame integer coords; "
        "ownership is a RELATION; surroundedness is discrete reachability (the "
        "frame/continuum invariant). NOT object identity/recognition (the 'what' wall, "
        "the named frontier). Reuses Neighbours/Filter/Count/Exists/Argmin/NodesOfType "
        "+ run_rules. Flag-gated on BorderOwnParams.bown, OFF by default (§9). See "
        "VISION_BORDER_OWNERSHIP_PREREG.md."
    ),
    "microtheory": {
        "id": "vision_border_ownership_mt",
        "label": "border-ownership: a directed boundary that owns its figure, and the "
                 "proto-object as the pre-identity stage",
    },
    "nodes": [
        {"local_id": 0, "type": "BorderOwnParams", "attrs": {"bown": 0.0}},
    ],
    "edges": [],
    "productions": [],
    "rules": [BO_BGFLOOD, BO_LABEL, BO_MINT_ENCLOSED, BO_MINT_GESTALT, BO_OWN],
}


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "seeds", "vision_border_ownership.json")
    with open(out, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
