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

v1.1.0 COMMON-FATE MOTION (flag SurfaceSegmentationParams.motion_segments,
default 0.0; off => byte-identical to v1.0.0):
    seg_motion_ready  ONE binding: this epoch's retinal_common_fate_carve_2d task
                  is done and every component passing the carve's own criterion
                  (RetinaCarveParams2d min_coherence / min_events) has minted its
                  VisionPolygon -> state.motion_epoch := e.
    seg_motion_mark   per cell: seg_mgrp := span key of the ONE current-epoch
                  VisionPolygon containing it, if it onset this epoch; else -1.
    seg_motion_all    ONE binding: all cells marked -> state.mark_epoch := e.
    seg_motion_tag    segment.motion_group := root's seg_mgrp.
  same_surface gains AND same motion group; seg_edge / seg_flood / seg_complete
  wait on mark_epoch (Or(Not(motion_segments), ...)), so the flood runs on the
  motion-aware relation from the start. Colour-free (rod onset events, spans).

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
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def IfThenElse(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def IndexAt(seq, i): return {"type": "IndexAt", "seq": seq, "index": i}
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
# v1.1.0: COMMON-FATE MOTION SEGMENTS, its own flag (sec 9).
MOTION = Gt(MaxOver(NodesOfType(PARAMS), "sm_", A("sm_", "motion_segments"), L(0.0)),
            L(0.5))
MARK_EPOCH = A(PickUnique(NodesOfType(STATE)), "mark_epoch")


def motion_ready(c):
    """v1.1.0: with motion_segments on, c may flood / mark edges only after every
    cell carries its motion group for c's epoch. Flag off: always true."""
    return Or(Not(MOTION), Eq(MARK_EPOCH, A(c, "seg_epoch")))


def same_group(a, b):
    """v1.1.0: a and b share a motion group. seg_mgrp is written only with
    motion_segments on (by seg_motion_mark, before any flood); with the flag
    off it is absent on every cell and this is true."""
    return Or(Eq(A(a, "seg_mgrp"), L(None)), Eq(A(a, "seg_mgrp"), A(b, "seg_mgrp")))


def initialised(c):
    return Not(Eq(A(c, "seg_epoch"), L(None)))


def reset_now(c):
    """Cell c has been reset for its current input epoch."""
    return Eq(A(c, "seg_epoch"), A(c, "input_epoch"))


def same_epoch(a, b):
    return Eq(A(a, "seg_epoch"), A(b, "seg_epoch"))


def same_surface(a, b):
    """|Y_a - Y_b| <= Sqrt(Y_a + Y_b): one shot-noise s.d. of the difference.
    v1.1.0: AND the same motion group (vacuous with motion_segments off)."""
    return And(Lte(Abs(Minus(A(a, "seg_Y"), A(b, "seg_Y"))),
                   Sqrt(Plus(A(a, "seg_Y"), A(b, "seg_Y")))),
               same_group(a, b))


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
        "where": And(ENABLED, reset_now("c"), motion_ready("c"),
                     edge_pending("c", "b")),
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
            ENABLED, reset_now("c"), motion_ready("c"),
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
            Or(Not(MOTION), Eq(A("st", "mark_epoch"), EPOCH_NOW)),
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

# --------------------------------------------- v1.1.0: common-fate motion
# Flag SurfaceSegmentationParams.motion_segments (default 0.0). The rules below
# fire only with it on and write only NEW attrs (SegmentationState.motion_epoch
# / mark_epoch; cell seg_mgrp / seg_mot_epoch; segment motion_group). With it
# on, the luminance same-surface relation is intersected with "same motion
# group", so the cells of a coherent VisionPolygon that onset this epoch are
# cut out of the luminance component into their own SurfaceSegment, which the
# SAME surface_persistence rules then match by overlap. COLOUR-FREE: reads the
# rod-driven RetinalOnsetEvent stream (via the 2-D carve's VisionPolygon spans)
# and cell positions only -- no L/M/S catch, no RetinalPercept value.
CARVE_KIND = "retinal_common_fate_carve_2d"
STRIDE = 9  # retinal_carve_2d's per-cell output layout (seeds/retinal_carve_2d.json)


def carve_out(task, c, k):
    return IndexAt(A(task, "output"), Plus(Times(A(c, "cell_index"), L(STRIDE)), L(k)))


def carve_mint_pending(task, cp, x):
    """A component of `task` passing the carve's OWN criterion (is_group_start,
    coherence > min_coherence, n_events > min_events, read off
    RetinaCarveParams2d) whose VisionPolygon is not yet minted at anchor x."""
    return And(Eq(carve_out(task, x, 0), L(1.0)),
               Gt(carve_out(task, x, 7), A(cp, "min_coherence")),
               Gt(carve_out(task, x, 8), A(cp, "min_events")),
               Ne(A(x, "carve2d_epoch"), A(task, "input_epoch")))


def spans_of(c, v="v_"):
    """Current-epoch VisionPolygons whose col/row span contains cell c."""
    return Filter(Nbrs("retina", "has_vision_polygon"), v, And(
        Eq(A(v, "epoch"), A(c, "seg_epoch")),
        Lte(A(v, "col_min"), A(c, "col")), Gte(A(v, "col_max"), A(c, "col")),
        Lte(A(v, "row_min"), A(c, "row")), Gte(A(v, "row_max"), A(c, "row"))))


def span_key(v):
    """A polygon's identity = its bounding span, packed into one integer:
    (row_min*n_az + col_min) * n_cells + (row_max*n_az + col_max)."""
    n_az = A("retina", "n_columns")
    n_cells = Times(A("retina", "n_columns"), A("retina", "n_rows"))
    return Plus(Times(Plus(Times(A(v, "row_min"), n_az), A(v, "col_min")), n_cells),
                Plus(Times(A(v, "row_max"), n_az), A(v, "col_max")))


def onset_now(c, ev="ev_"):
    return Exists(Nbrs(c, "has_onset_event"), ev, Eq(A(ev, "epoch"), A(c, "seg_epoch")))


MOTION_RULES = [
    {
        "name": "seg_motion_ready",
        "comment": "MOTION (one binding): the 2-D common-fate carve task of THIS "
                   "epoch is done and every component passing the carve's own "
                   "criterion has minted its VisionPolygon -> motion_epoch := e. "
                   "Requires the adapter to settle the carve each exposure (it does "
                   "so only when motion_segments is requested).",
        "match": [["sp", "has_segmentation_state", "st"],
                  ["retina", "has_carve_task_2d", "task"],
                  ["retina", "has_carve_params_2d", "cp"]],
        "where": And(
            ENABLED, MOTION,
            Gt(EPOCH_NOW, L(0)),
            Eq(A("task", "kind"), L(CARVE_KIND)),
            Eq(A("task", "status"), L("done")),
            Eq(A("task", "input_epoch"), EPOCH_NOW),
            Ne(A("st", "motion_epoch"), EPOCH_NOW),
            Not(Exists(NodesOfType(CELL), "xm", carve_mint_pending("task", "cp", "xm")))),
        "effects": [seta("st", "motion_epoch", T(EPOCH_NOW))],
    },
    {
        "name": "seg_motion_mark",
        "comment": "MOTION: once per reset cell per epoch, after motion_epoch: the "
                   "cell's motion group seg_mgrp = the span key of the ONE "
                   "current-epoch VisionPolygon whose col/row span contains it, if "
                   "the cell also minted a RetinalOnsetEvent this epoch (polygons "
                   "carry only bounding spans, so membership = span AND onset); "
                   "-1 otherwise. A cell inside two spans is refused (-1): no "
                   "guess between polygons.",
        "match": [["sp", "has_segmentation_state", "st"],
                  ["retina", "has_column", "c"]],
        "where": And(ENABLED, MOTION, reset_now("c"),
                     Eq(A("st", "motion_epoch"), A("c", "seg_epoch")),
                     Ne(A("c", "seg_mot_epoch"), A("c", "seg_epoch"))),
        "effects": [
            seta("c", "seg_mgrp", T(IfThenElse(
                And(onset_now("c"), Eq(Count(spans_of("c", "v1_")), L(1))),
                MinOver(spans_of("c", "v2_"), "v3_", span_key("v3_"), L(-1)),
                L(-1)))),
            seta("c", "seg_mot_epoch", T(A("c", "seg_epoch"))),
        ],
    },
    {
        "name": "seg_motion_all",
        "comment": "MOTION (one binding): every cell carries its motion group for "
                   "this epoch -> mark_epoch := e; flood, boundary marks and the "
                   "completion guard wait on it (motion_ready).",
        "match": [["sp", "has_segmentation_state", "st"]],
        "where": And(ENABLED, MOTION, Eq(A("st", "motion_epoch"), EPOCH_NOW),
                     Ne(A("st", "mark_epoch"), EPOCH_NOW),
                     Not(Exists(NodesOfType(CELL), "xa",
                                Ne(A("xa", "seg_mot_epoch"), EPOCH_NOW)))),
        "effects": [seta("st", "mark_epoch", T(EPOCH_NOW))],
    },
    {
        "name": "seg_motion_tag",
        "comment": "MOTION: record on each minted segment its motion group (the "
                   "root's seg_mgrp; -1 = a luminance-only segment).",
        "match": [["st", "has_segment", "S"], ["r", "roots_segment", "S"]],
        "where": And(ENABLED, MOTION, Eq(A("S", "motion_group"), L(None)),
                     Eq(A("r", "seg_epoch"), A("S", "epoch"))),
        "effects": [seta("S", "motion_group", T(A("r", "seg_mgrp")))],
    },
]
RULES = RULES + MOTION_RULES

MANIFEST = {
    "id": "surface_segmentation",
    "version": "1.1.0",
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
        "Flag SurfaceSegmentationParams.enabled, OFF by default (sec 9). "
        "v1.1.0 COMMON-FATE MOTION SEGMENTS, its own flag "
        "SurfaceSegmentationParams.motion_segments (default 0.0; with it 0 every "
        "observable is byte-identical to v1.0.0): after the 2-D common-fate carve "
        "(retinal_carve_2d, rod-driven RetinalOnsetEvents) of the epoch is done "
        "and minted (SegmentationState.motion_epoch), each cell gets a motion "
        "group seg_mgrp = the span key of the one current-epoch VisionPolygon "
        "whose col/row span contains it if it also onset this epoch, else -1 "
        "(two spans: refused, -1); the same-surface relation becomes "
        "|dY| <= Sqrt(Y_a+Y_b) AND same motion group, so a coherent moving "
        "region is cut out of its luminance component into its own "
        "SurfaceSegment (attr motion_group) and offered to the SAME "
        "surface_persistence rules. Colour-free: onset events and spans only. "
        "Needs the adapter to settle the carve every exposure."
    ),
    "microtheory": {
        "name": "surface_segmentation",
        "description": "luminance shot-noise edges -> connected surface segments",
    },
    "nodes": [
        {"local_id": 0, "type": PARAMS, "attrs": {"enabled": 0.0, "motion_segments": 0.0}},
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
