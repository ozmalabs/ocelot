"""Emit seeds/surface_persistence.json (Mary's Room stage 4.4).

Persistent surface identity across exposures by CELL-SET OVERLAP -- colour-free.
Every decision is a graph rule; this script only writes JSON. Run:

    PYTHONPATH=. python tools/build_surface_persistence_seed.py

CRITERION (track_comps, runners/dsl/src/substrate.rs `track_comps`, the
overlap pass: `2*ov >= min(count)`), made ORDER-FREE and REFUSING:

  ov(S, P) = number of member cells of current segment S whose prev_sid
             (the sid they belonged to at the previous exposure) is P.sid.
  S CLAIMS P   iff ov(S,P) > 0 and 2*ov(S,P) >= min(S.n_cells, P.n_cells).
  S ACCEPTS P  iff S claims P, P is S's UNIQUE overlap argmax (no other P'
               with ov(S,P') >= ov(S,P)), and no other current segment S'
               claims P with ov(S',P) >= ov(S,P).
  Otherwise S is BORN as a new PersistentSurface (sid = SurfaceCounter.next_sid,
  then incremented). An ambiguous split (two segments tie on the same P) or
  merge (one segment tied between two Ps) is thereby REFUSED, never guessed:
  the claimants are born new and the old P coasts; a P with >= 2 claimants
  and no acceptor is marked status 'split'.
  track_comps resolves the same situations greedily in iteration order; this
  rule set is the order-independent version (no `used` set), and drops
  track_comps' nearest-centroid and velocity fallbacks (identity here is
  overlap or nothing). There is no colour/value gate: segments come from
  luminance edges and P carries no appearance.

  A P not accepted at epoch e COASTS: coast += 1, kept, never deleted. Overlap
  is computed only from prev_sid, which is rolled from cur_sid at the next
  epoch's reset (ps_roll), so the decision reads the PREVIOUS epoch's
  assignment before it is overwritten.

PHASES (per epoch e = SegmentationState.final_epoch):
  ps_init / ps_roll -> ps_ready (one binding: every cell rolled) ->
  ps_decide_continue | ps_decide_birth (decisions only, no P mutation) ->
  ps_apply_continue | ps_apply_birth (only once ALL boundary segments of e are
  decided) -> ps_mark_cells (cur_sid) ; ps_coast.

Segments with has_boundary = 0 (ganzfeld) are never offered.

Flag SurfacePersistenceParams.enabled, OFF by default (sec 9). Manifest
latency_class hard_realtime. Depends on surface_segmentation.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "surface_persistence.json")


# --------------------------------------------------------------- AST helpers
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Ne(a, b): return Not(Eq(a, b))
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def Min(*xs): return {"type": "Min", "items": list(xs)}
def IfThenElse(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
def Nbrs(n, e):
    node = V(n) if isinstance(n, str) else n
    return {"type": "Neighbours", "node": node, "edge_type": e, "any_type": False}
def InNbrs(n, e): return {"type": "InNeighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Count(src): return {"type": "Count", "source": src}
def MaxOver(src, var, val, default=None):
    t = {"type": "MaxOver", "source": src, "var_name": var, "value": val}
    if default is not None:
        t["default"] = default
    return t
def PickUnique(src): return {"type": "PickUnique", "source": src}
def T(term): return {"__term__": term}


def seta(var, key, value):
    return ["set_attr", var, key, value]


# --------------------------------------------------------------- vocabulary
PARAMS = "SurfacePersistenceParams"
PSTATE = "PersistenceState"
COUNTER = "SurfaceCounter"
SURF = "PersistentSurface"
CELL = "RetinalColumn"
SEGSTATE = "SegmentationState"

ENABLED = Gt(MaxOver(NodesOfType(PARAMS), "pp_", A("pp_", "enabled"), L(0.0)), L(0.5))
SEG_ENABLED = Gt(MaxOver(NodesOfType("SurfaceSegmentationParams"), "sp_",
                         A("sp_", "enabled"), L(0.0)), L(0.5))
GATE = And(ENABLED, SEG_ENABLED)
READY = A(PickUnique(NodesOfType(PSTATE)), "ready_epoch")
FINAL = A(PickUnique(NodesOfType(SEGSTATE)), "final_epoch")
CUR_SEGS = Nbrs(PickUnique(NodesOfType(SEGSTATE)), "has_segment")
ALL_P = NodesOfType(SURF)


def ov(S, P, q):
    """Members of S whose previous-epoch sid is P's sid."""
    return Count(Filter(InNbrs(S, "in_segment"), q,
                        Eq(A(q, "prev_sid"), A(P, "sid"))))


def offered(S):
    """S is a current boundary segment of the ready epoch."""
    return And(Eq(A(S, "epoch"), READY), Gt(A(S, "has_boundary"), L(0.5)),
               Gt(A(S, "current"), L(0.5)))


def claims(S, P, q):
    o = ov(S, P, q)
    return And(Gt(o, L(0)),
               Gte(Times(L(2), o), Min(A(S, "n_cells"), A(P, "n_cells"))))


def accepts(S, P, tag):
    """S accepts P: claim + unique argmax over P + no rival claimant >= ov."""
    o = ov(S, P, "q" + tag)
    return And(
        claims(S, P, "qc" + tag),
        Not(Exists(ALL_P, "P2" + tag, And(
            Ne(A("P2" + tag, "sid"), A(P, "sid")),
            Gte(ov(S, "P2" + tag, "q2" + tag), o)))),
        Not(Exists(CUR_SEGS, "S2" + tag, And(
            offered("S2" + tag),
            Ne(A("S2" + tag, "root"), A(S, "root")),
            claims("S2" + tag, P, "q3" + tag),
            Gte(ov("S2" + tag, P, "q4" + tag), o)))),
    )


ALL_DECIDED = Not(Exists(CUR_SEGS, "u_", And(
    offered("u_"), Eq(A("u_", "decision"), L(None)))))

SEG_MATCH = ["st", "has_segment", "S"]

RULES = [
    {
        "name": "ps_init",
        "comment": "First sight of a cell: no persistent surface yet (sid -1).",
        "match": [["retina", "has_column", "c"]],
        "where": And(GATE, Eq(A("c", "ps_epoch"), L(None))),
        "effects": [seta("c", "ps_epoch", -1), seta("c", "prev_sid", -1),
                    seta("c", "cur_sid", -1)],
    },
    {
        "name": "ps_roll",
        "comment": "When segmentation resets a cell for a new epoch, roll its "
                   "identity clock: prev_sid := cur_sid (the sid assigned at the "
                   "previous exposure; -1 if that exposure offered no surface, "
                   "e.g. a ganzfeld), cur_sid := -1. Overlap is computed ONLY "
                   "from prev_sid, so it always reads the previous epoch.",
        "match": [["retina", "has_column", "c"]],
        "where": And(GATE, Not(Eq(A("c", "ps_epoch"), L(None))),
                     Gt(A("c", "seg_epoch"), A("c", "ps_epoch"))),
        "effects": [seta("c", "prev_sid", T(A("c", "cur_sid"))),
                    seta("c", "cur_sid", -1),
                    seta("c", "ps_epoch", T(A("c", "seg_epoch")))],
    },
    {
        "name": "ps_ready",
        "comment": "One binding: segmentation has published final_epoch e and "
                   "every cell has rolled to e -> ready_epoch := e.",
        "match": [["pp", "has_persistence_state", "ps"]],
        "where": And(
            GATE, Gt(FINAL, A("ps", "ready_epoch")),
            Not(Exists(NodesOfType(CELL), "x", Ne(A("x", "ps_epoch"), FINAL)))),
        "effects": [seta("ps", "ready_epoch", T(FINAL))],
    },
    {
        "name": "ps_decide_continue",
        "comment": "DECISION ONLY (no P mutation, so every segment's decision is "
                   "made against the same previous-epoch state): S accepts P "
                   "(track_comps overlap 2*ov >= min(count), unique argmax, no "
                   "rival claimant with >= overlap).",
        "match": [SEG_MATCH, ["sc", "has_surface", "P"]],
        "where": And(GATE, offered("S"), Eq(A("S", "decision"), L(None)),
                     accepts("S", "P", "a")),
        "effects": [seta("S", "decision", "continue"),
                    seta("S", "cand_sid", T(A("P", "sid")))],
    },
    {
        "name": "ps_decide_birth",
        "comment": "DECISION ONLY: S accepts no existing P -> birth. "
                   "birth_reason records whether S claimed some P (overlap passed "
                   "but the match was ambiguous -> REFUSED) or claimed none.",
        "match": [SEG_MATCH],
        "where": And(GATE, offered("S"), Eq(A("S", "decision"), L(None)),
                     Not(Exists(ALL_P, "Pb", accepts("S", "Pb", "b")))),
        "effects": [
            seta("S", "decision", "birth"),
            seta("S", "birth_reason", T(IfThenElse(
                Exists(ALL_P, "Pr", claims("S", "Pr", "qr")),
                L("refused_ambiguous"), L("no_overlap")))),
        ],
    },
    {
        "name": "ps_apply_continue",
        "comment": "After ALL offered segments of the epoch are decided: link "
                   "S -segment_of-> P and update P (n_cells, last_epoch, coast 0, "
                   "status tracked).",
        "match": [SEG_MATCH, ["sc", "has_surface", "P"]],
        "where": And(GATE, ALL_DECIDED, offered("S"),
                     Eq(A("S", "decision"), L("continue")),
                     Eq(A("S", "applied"), L(None)),
                     Eq(A("P", "sid"), A("S", "cand_sid"))),
        "effects": [
            ["add_edge", "S", "segment_of", "P"],
            seta("S", "sid", T(A("P", "sid"))),
            seta("S", "applied", 1.0),
            seta("P", "n_cells", T(A("S", "n_cells"))),
            seta("P", "last_epoch", T(A("S", "epoch"))),
            seta("P", "status_epoch", T(A("S", "epoch"))),
            seta("P", "coast", 0),
            seta("P", "claims", 1),
            seta("P", "status", "tracked"),
        ],
    },
    {
        "name": "ps_apply_birth",
        "comment": "After ALL offered segments are decided: mint a "
                   "PersistentSurface with sid = SurfaceCounter.next_sid, then "
                   "increment the counter (effects apply in order per binding, so "
                   "concurrent births get distinct sids).",
        "match": [SEG_MATCH, ["pp", "has_surface_counter", "sc"]],
        "where": And(GATE, ALL_DECIDED, offered("S"),
                     Eq(A("S", "decision"), L("birth")),
                     Eq(A("S", "applied"), L(None))),
        "effects": [
            ["add_node", "P", SURF, {
                "sid": T(A("sc", "next_sid")),
                "n_cells": T(A("S", "n_cells")),
                "born_epoch": T(A("S", "epoch")),
                "last_epoch": T(A("S", "epoch")),
                "status_epoch": T(A("S", "epoch")),
                "coast": T(L(0)),
                "claims": T(L(0)),
                "status": T(L("tracked")),
            }],
            ["add_edge", "sc", "has_surface", "P"],
            ["add_edge", "S", "segment_of", "P"],
            seta("S", "sid", T(A("sc", "next_sid"))),
            seta("S", "applied", 1.0),
            seta("sc", "next_sid", T(Plus(A("sc", "next_sid"), L(1)))),
        ],
    },
    {
        "name": "ps_mark_cells",
        "comment": "Each member cell records its surface for THIS epoch in cur_sid "
                   "(prev_sid untouched until the next roll).",
        "match": [["c", "in_segment", "S"]],
        "where": And(GATE, Eq(A("S", "applied"), L(1.0)),
                     Eq(A("S", "epoch"), A("c", "seg_epoch")),
                     Ne(A("c", "cur_sid"), A("S", "sid"))),
        "effects": [seta("c", "cur_sid", T(A("S", "sid")))],
    },
    {
        "name": "ps_coast",
        "comment": "After ALL offered segments are decided, a P not accepted at the "
                   "ready epoch COASTS (coast += 1; kept, never deleted). status = "
                   "'split' if >= 2 current segments claimed it (ambiguous split, "
                   "refused), else 'coasting'; claims = the claimant count.",
        "match": [["sc", "has_surface", "P"]],
        "where": And(GATE, ALL_DECIDED,
                     Gt(READY, L(0)),
                     Lt(A("P", "last_epoch"), READY),
                     Lt(A("P", "status_epoch"), READY),
                     Not(Exists(CUR_SEGS, "w_", And(
                         offered("w_"), Eq(A("w_", "decision"), L("continue")),
                         Eq(A("w_", "cand_sid"), A("P", "sid")))))),
        "effects": [
            seta("P", "coast", T(Plus(A("P", "coast"), L(1)))),
            seta("P", "status_epoch", T(READY)),
            seta("P", "claims", T(Count(Filter(CUR_SEGS, "k_", And(
                offered("k_"), claims("k_", "P", "qk")))))),
            seta("P", "status", T(IfThenElse(
                Gte(Count(Filter(CUR_SEGS, "k2_", And(
                    offered("k2_"), claims("k2_", "P", "qk2")))), L(2)),
                L("split"), L("coasting")))),
        ],
    },
]

MANIFEST = {
    "id": "surface_persistence",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["surface_segmentation"],
    "latency_class": "hard_realtime",
    "description": (
        "Mary's Room stage 4.4: persistent surface identity across exposures by "
        "cell-set overlap, colour-free. A current SurfaceSegment S (from "
        "surface_segmentation, has_boundary=1) continues PersistentSurface P iff "
        "ov = #members of S whose prev_sid == P.sid satisfies the track_comps "
        "overlap criterion 2*ov >= min(S.n_cells, P.n_cells) "
        "(runners/dsl/src/substrate.rs track_comps), P is S's unique overlap "
        "argmax, and no other current segment claims P with >= overlap. "
        "Otherwise S is born as a new P (sid from SurfaceCounter.next_sid): an "
        "ambiguous split/merge is REFUSED rather than guessed, and a P claimed by "
        ">= 2 segments with no acceptor is marked 'split'. Unmatched P coast "
        "(coast += 1; never deleted). Unlike track_comps the match is "
        "order-independent and has no centroid/velocity fallback and no value "
        "gate: identity never reads colour. Each cell keeps prev_sid (previous "
        "exposure) and cur_sid (this exposure); prev_sid is rolled at the next "
        "segmentation reset so overlap always reads the previous epoch. Ganzfeld "
        "(has_boundary=0) segments are not offered. Flag "
        "SurfacePersistenceParams.enabled, OFF by default (sec 9)."
    ),
    "microtheory": {
        "name": "surface_persistence",
        "description": "surface segments -> persistent surfaces by cell overlap",
    },
    "nodes": [
        {"local_id": 0, "type": PARAMS, "attrs": {"enabled": 0.0}},
        {"local_id": 1, "type": PSTATE, "attrs": {"ready_epoch": -1}},
        {"local_id": 2, "type": COUNTER, "attrs": {"next_sid": 0}},
    ],
    "edges": [
        {"src": {"role": "agent_root"}, "type": "has_surface_persistence_params",
         "tgt": {"local": 0}, "attrs": {}},
        {"src": {"local": 0}, "type": "has_persistence_state",
         "tgt": {"local": 1}, "attrs": {}},
        {"src": {"local": 0}, "type": "has_surface_counter",
         "tgt": {"local": 2}, "attrs": {}},
    ],
    "productions": [],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
        f.write("\n")
    print(f"wrote {OUT} with {len(RULES)} rules")
