"""Emit seeds/surface_segmentation.json (Mary's Room stage 4.3).

Colour-free, constant-free surface segmentation on the 2-D photon sheet
(`GraphEye` with `retina_2d_cones`). Every decision is a graph rule; this
script only writes JSON. Run:

    PYTHONPATH=. python tools/build_surface_segmentation_seed.py

CRITERION (declared, sec 13 -- no tuned constant):
    luminance  Y = L.caught_quanta + M.caught_quanta   (no S, no opponent value)
    two 4-adjacent cells a, b are the SAME SURFACE iff
        |Y_a - Y_b| <= Sqrt(Y_a + Y_b)
    i.e. the difference is within ONE standard deviation of its own photon shot
    noise (Var(Y_a - Y_b) = Y_a + Y_b for Poisson catches). No multiplier.

PIPELINE (per epoch e = the cells' shared input_epoch):
    seg_init      first sight of a cell: write the seg_* defaults.
    seg_reset     once per cell per epoch, after its L and M receptors have
                  transduced epoch e: seg_epoch:=e, seg_label:=cell_index,
                  seg_Y:=Y, seg_has_edge:=0.
    seg_edge      a cell with a reset neighbour that is NOT same-surface marks
                  seg_has_edge:=1 (it sits on a boundary).
    seg_flood     min-label flood over same-surface neighbours (the
                  vision_lighting_l4 `l4_flood` / bo_label idiom; fixpoint =
                  connected components, label = min cell_index).
    seg_complete  ONE binding (params -> state): when every cell is reset to e,
                  no same-surface adjacent pair has differing labels (flood
                  fixpoint, by symmetry of adjacent_receptor) and no boundary
                  mark is pending, set state.done_epoch := e.
    seg_mint      per root cell (seg_label == cell_index) of epoch done_epoch:
                  mint ONE SurfaceSegment{epoch, root, n_cells, has_boundary}
                  unless the root already roots one for that epoch.
    seg_join      each cell of epoch e joins its root's segment (in_segment).
    seg_final     ONE binding: when every cell has joined, final_epoch := e.
                  Downstream (surface_persistence) gates on final_epoch.
    seg_retire    when done_epoch passes a segment's epoch, the segment is
                  kept as history (current:=0) but its live edges
                  (state-has_segment, root-roots_segment) are removed;
    seg_retire_member  and so are its cell in_segment edges, so per-epoch
                  join cost stays flat.

GANZFELD: a component none of whose cells has a boundary mark gets
has_boundary=0 (declared: a surface needs a boundary); persistence does not
take it up.

Flag-gated on SurfaceSegmentationParams.enabled > 0.5, OFF by default (sec 9).
Manifest latency_class hard_realtime (early vision; see
docs/research/marys-room-stage4-scope.md decision 1).
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "surface_segmentation.json")


# --------------------------------------------------------------- AST helpers
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Ne(a, b): return Not(Eq(a, b))
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Lte(a, b): return {"type": "Lte", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Abs(x): return {"type": "Abs", "arg": x}
def Sqrt(x): return {"type": "Sqrt", "arg": x}
def Min(*xs): return {"type": "Min", "items": list(xs)}
def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
def Nbrs(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Count(src): return {"type": "Count", "source": src}
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
def PickUnique(src): return {"type": "PickUnique", "source": src}
def T(term): return {"__term__": term}


def set_if(var, key, value):
    return ["set_attr_if_different", var, key, value]


def seta(var, key, value):
    return ["set_attr", var, key, value]


# --------------------------------------------------------------- vocabulary
PARAMS = "SurfaceSegmentationParams"
STATE = "SegmentationState"
CELL = "RetinalColumn"
SEGMENT = "SurfaceSegment"
ADJ = "adjacent_receptor"

ENABLED = Gt(MaxOver(NodesOfType(PARAMS), "sp_", A("sp_", "enabled"), L(0.0)), L(0.5))
DONE_EPOCH = A(PickUnique(NodesOfType(STATE)), "done_epoch")


def initialised(c):
    return Not(Eq(A(c, "seg_epoch"), L(None)))


def reset_now(c):
    """Cell c has been reset for its current input epoch."""
    return Eq(A(c, "seg_epoch"), A(c, "input_epoch"))


def same_epoch(a, b):
    return Eq(A(a, "seg_epoch"), A(b, "seg_epoch"))


def same_surface(a, b):
    """|Y_a - Y_b| <= Sqrt(Y_a + Y_b): one shot-noise s.d. of the difference."""
    return Lte(Abs(Minus(A(a, "seg_Y"), A(b, "seg_Y"))),
               Sqrt(Plus(A(a, "seg_Y"), A(b, "seg_Y"))))


def flood_pending(x, y="y_"):
    """x has a same-epoch same-surface neighbour with a different label."""
    return Exists(Nbrs(x, ADJ), y, And(
        same_epoch(x, y), same_surface(x, y),
        Ne(A(y, "seg_label"), A(x, "seg_label"))))


def edge_pending(x, y="y_"):
    """x has a same-epoch non-same-surface neighbour but no boundary mark."""
    return And(Lt(A(x, "seg_has_edge"), L(0.5)),
               Exists(Nbrs(x, ADJ), y, And(same_epoch(x, y),
                                           Not(same_surface(x, y)))))


def members_of(r, q="q_"):
    """Cells of root r's component at r's epoch."""
    return Filter(NodesOfType(CELL), q, And(
        Eq(A(q, "seg_epoch"), A(r, "seg_epoch")),
        Eq(A(q, "seg_label"), A(r, "seg_label"))))


EPOCH_NOW = MaxOver(NodesOfType(CELL), "e_", A("e_", "input_epoch"), L(0))

CELL_MATCH = [["retina", "has_column", "c"]]

RULES = [
    {
        "name": "seg_init",
        "comment": "First sight of a cell: write the seg_* defaults (label = own "
                   "cell_index, epoch -1 = never segmented). Mechanical; once per cell.",
        "match": CELL_MATCH,
        "where": And(ENABLED, Eq(A("c", "seg_epoch"), L(None))),
        "effects": [
            seta("c", "seg_epoch", -1),
            seta("c", "seg_label", T(A("c", "cell_index"))),
            seta("c", "seg_Y", 0.0),
            seta("c", "seg_has_edge", 0.0),
            seta("c", "seg_joined", -1),
        ],
    },
    {
        "name": "seg_reset",
        "comment": "Once per cell per epoch, after BOTH the L and M receptors carry "
                   "this epoch's transduction: copy the colour-free luminance "
                   "Y = L.caught_quanta + M.caught_quanta (linear catches, no S, no "
                   "opponent value) onto the cell, and restart the flood from the "
                   "cell's own index. Epoch 0 is the eye's pre-exposure clock and is "
                   "never segmented.",
        "match": [["retina", "has_column", "c"],
                  ["c", "l_receptor", "l"],
                  ["c", "m_receptor", "m"]],
        "where": And(
            ENABLED, initialised("c"),
            Gt(A("c", "input_epoch"), L(0)),
            Gt(A("c", "input_epoch"), A("c", "seg_epoch")),
            Eq(A("l", "input_epoch"), A("c", "input_epoch")),
            Eq(A("m", "input_epoch"), A("c", "input_epoch")),
        ),
        "effects": [
            seta("c", "seg_epoch", T(A("c", "input_epoch"))),
            seta("c", "seg_label", T(A("c", "cell_index"))),
            seta("c", "seg_Y", T(Plus(A("l", "caught_quanta"), A("m", "caught_quanta")))),
            seta("c", "seg_has_edge", 0.0),
        ],
    },
    {
        "name": "seg_edge",
        "comment": "A boundary exists at c if some reset neighbour of the same epoch "
                   "is NOT the same surface (|dY| > Sqrt(Y_a+Y_b)). Monotone 0->1 "
                   "within an epoch; reset clears it.",
        "match": CELL_MATCH,
        "where": And(ENABLED, reset_now("c"), edge_pending("c", "b")),
        "effects": [seta("c", "seg_has_edge", 1.0)],
    },
    {
        "name": "seg_flood",
        "comment": "l4_flood's min-flood with its predicate replaced by the shot-noise "
                   "same-surface test: seg_label := min label over same-epoch "
                   "same-surface neighbours, fired only when one is STRICTLY smaller, "
                   "so labels decrease monotonically and the flood terminates. At the "
                   "run_rules fixpoint every connected same-surface component carries "
                   "its minimum cell_index. DECLARED (as in l4): same-surface is not "
                   "transitive; the flood takes its transitive closure, so a chain of "
                   "sub-sigma steps (a smooth luminance ramp) merges.",
        "match": CELL_MATCH,
        "where": And(
            ENABLED, reset_now("c"),
            Exists(Nbrs("c", ADJ), "b", And(
                same_epoch("c", "b"), same_surface("c", "b"),
                Lt(A("b", "seg_label"), A("c", "seg_label")))),
        ),
        "effects": [
            seta("c", "seg_label", T(Min(
                A("c", "seg_label"),
                MinOver(Filter(Nbrs("c", ADJ), "b", And(
                    same_epoch("c", "b"), same_surface("c", "b"))),
                    "b2", A("b2", "seg_label"), A("c", "seg_label"))))),
        ],
    },
    {
        "name": "seg_complete",
        "comment": "THE MINT GUARD (one binding: params -has_segmentation_state-> "
                   "state). Epoch e = the sheet's input_epoch. Fires when (1) every "
                   "cell is reset to e, (2) NO adjacent same-epoch same-surface pair "
                   "has differing labels -- adjacency is symmetric, so this is "
                   "exactly the flood's fixpoint (no cell has a strictly smaller "
                   "same-surface neighbour), and (3) no boundary mark is pending. "
                   "Only then is done_epoch := e, so n_cells / has_boundary read at "
                   "mint time are final, never a transient undercount.",
        "match": [["sp", "has_segmentation_state", "st"]],
        "where": And(
            ENABLED,
            Gt(EPOCH_NOW, L(0)),
            Gt(EPOCH_NOW, A("st", "done_epoch")),
            Not(Exists(NodesOfType(CELL), "x", Ne(A("x", "seg_epoch"), EPOCH_NOW))),
            Not(Exists(NodesOfType(CELL), "x", flood_pending("x"))),
            Not(Exists(NodesOfType(CELL), "x", edge_pending("x"))),
        ),
        "effects": [seta("st", "done_epoch", T(EPOCH_NOW))],
    },
    {
        "name": "seg_mint",
        "comment": "Per ROOT cell (seg_label == cell_index) of the completed epoch: "
                   "mint ONE SurfaceSegment unless this root already roots one for "
                   "this epoch (local Not-Exists over roots_segment). Each root is a "
                   "distinct binding, so exactly one segment per component. "
                   "n_cells = Count(cells with this label at this epoch); "
                   "has_boundary = any member carries seg_has_edge (0 = ganzfeld: "
                   "declared not a surface).",
        "match": [["sp", "has_segmentation_state", "st"],
                  ["retina", "has_column", "r"]],
        "where": And(
            ENABLED,
            Eq(A("r", "seg_epoch"), A("st", "done_epoch")),
            Eq(A("r", "seg_label"), A("r", "cell_index")),
            Not(Exists(Nbrs("r", "roots_segment"), "z",
                       Eq(A("z", "epoch"), A("r", "seg_epoch")))),
        ),
        "effects": [
            ["add_node", "S", SEGMENT, {
                "epoch": T(A("r", "seg_epoch")),
                "root": T(A("r", "cell_index")),
                "n_cells": T(Count(members_of("r"))),
                "has_boundary": T(MaxOver(members_of("r"), "h_",
                                          A("h_", "seg_has_edge"), L(0.0))),
                "current": T(L(1.0)),
            }],
            ["add_edge", "st", "has_segment", "S"],
            ["add_edge", "r", "roots_segment", "S"],
            # the root is a member too; seg_join cannot bind it because the
            # matcher binds distinct pattern variables to distinct nodes.
            ["add_edge", "r", "in_segment", "S"],
            seta("r", "seg_joined", T(A("r", "seg_epoch"))),
        ],
    },
    {
        "name": "seg_join",
        "comment": "Each non-root cell of the segment's epoch whose label is the "
                   "segment's root joins it (cell -in_segment-> segment), once per "
                   "epoch (the root joined at mint: pattern variables bind "
                   "distinct nodes, so c can never be r here).",
        "match": [["r", "roots_segment", "S"],
                  ["retina", "has_column", "c"]],
        "where": And(
            ENABLED,
            Gt(A("S", "current"), L(0.5)),
            Eq(A("c", "seg_epoch"), A("S", "epoch")),
            Eq(A("c", "seg_label"), A("S", "root")),
            Lt(A("c", "seg_joined"), A("S", "epoch")),
        ),
        "effects": [
            ["add_edge", "c", "in_segment", "S"],
            seta("c", "seg_joined", T(A("S", "epoch"))),
        ],
    },
    {
        "name": "seg_final",
        "comment": "One binding: when every cell has joined its segment for "
                   "done_epoch (so every component has been minted), publish "
                   "final_epoch := done_epoch. The downstream gate.",
        "match": [["sp", "has_segmentation_state", "st"]],
        "where": And(
            ENABLED,
            Gt(A("st", "done_epoch"), A("st", "final_epoch")),
            Not(Exists(NodesOfType(CELL), "x",
                       Ne(A("x", "seg_joined"), A("st", "done_epoch")))),
        ),
        "effects": [seta("st", "final_epoch", T(A("st", "done_epoch")))],
    },
    {
        "name": "seg_retire",
        "comment": "HISTORY, NOT DELETION: once a newer epoch is complete, a segment "
                   "is kept (epoch/root/n_cells/has_boundary and any persistence "
                   "edge survive) but marked current=0 and unhooked from the live "
                   "state/root edges, so joins over current segments stay flat. "
                   "Persistence reads the previous epoch through each cell's own "
                   "prev_sid, not through old segments.",
        "match": [["st", "has_segment", "S"],
                  ["r", "roots_segment", "S"]],
        "where": And(ENABLED, Lt(A("S", "epoch"), A("st", "done_epoch"))),
        "effects": [
            seta("S", "current", 0.0),
            ["del_edge", "st", "has_segment", "S"],
            ["del_edge", "r", "roots_segment", "S"],
        ],
    },
    {
        "name": "seg_retire_member",
        "comment": "Drop a retired segment's cell membership edges (its n_cells is "
                   "kept on the node).",
        "match": [["c", "in_segment", "S"]],
        "where": And(ENABLED, Lt(A("S", "current"), L(0.5))),
        "effects": [["del_edge", "c", "in_segment", "S"]],
    },
]

MANIFEST = {
    "id": "surface_segmentation",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["photon_retina"],
    "latency_class": "hard_realtime",
    "description": (
        "Mary's Room stage 4.3: colour-free surface segmentation of the 2-D photon "
        "sheet (GraphEye retina_2d + retina_2d_cones, adjacent_receptor edges). "
        "Luminance Y = L.caught_quanta + M.caught_quanta (no S, no opponent "
        "channel). Two adjacent cells are the SAME SURFACE iff "
        "|Y_a - Y_b| <= Sqrt(Y_a + Y_b): one standard deviation of the photon shot "
        "noise of the difference, a physical grain with no tuned multiplier "
        "(VISION_PROTOCOL sec 13). Components are found by the l4_flood min-label "
        "flood to the run_rules fixpoint; a per-epoch completion guard "
        "(SegmentationState.done_epoch) admits minting only after the fixpoint, "
        "then ONE SurfaceSegment{epoch, root, n_cells, has_boundary, current} per "
        "component, with cell -in_segment-> segment membership, and "
        "SegmentationState.final_epoch once every cell has joined. A component "
        "with no boundary (ganzfeld) has has_boundary=0 and is not a surface. "
        "Isoluminant chromatic edges are invisible to this criterion BY DESIGN "
        "(they merge; reported, not patched). Superseded segments are kept as "
        "history (current=0) with their live edges removed. Feeds "
        "surface_persistence, whose identity criterion is the track_comps cell "
        "overlap 2*ov >= min(count) (runners/dsl/src/substrate.rs track_comps). "
        "Flag SurfaceSegmentationParams.enabled, OFF by default (sec 9)."
    ),
    "microtheory": {
        "name": "surface_segmentation",
        "description": "luminance shot-noise edges -> connected surface segments",
    },
    "nodes": [
        {"local_id": 0, "type": PARAMS, "attrs": {"enabled": 0.0}},
        {"local_id": 1, "type": STATE, "attrs": {"done_epoch": -1, "final_epoch": -1}},
    ],
    "edges": [
        {"src": {"role": "agent_root"}, "type": "has_surface_segmentation_params",
         "tgt": {"local": 0}, "attrs": {}},
        {"src": {"local": 0}, "type": "has_segmentation_state",
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
