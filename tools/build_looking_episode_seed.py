"""Emit seeds/looking_episode.json (Mary's Room stage 4.5, seed 4).

THE LOOKING EPISODE: what it was like to look, per exposure -- kept apart from
the surface's colour PROPERTY (seed colour_property). Every decision is a graph
rule; this script only writes JSON. Run:

    PYTHONPATH=. python tools/build_looking_episode_seed.py

  le_mint          per exposure (Retina.input_epoch advances past
                   LookingState.last_epoch) mint ONE durable
                   LookingEpisode{epoch, status 'observed'} with
                   Retina -had_episode-> episode and episode -observed_by->
                   Observer. The Observer is a node this seed itself declares
                   (agent_root -has_observer-> Observer{role 'observer'}): the
                   eye's Agent is the vision root shared by every seed, so a
                   distinct observer node keeps 'who looked' a first-class,
                   seed-owned referent. LookingState -current_episode-> is the
                   live pointer (retired by le_retire; episodes are never deleted).
  le_surface_look  per (current episode, PersistentSurface matched at that
                   epoch): SurfaceLook{epoch, sid, rg, by, intensity, n_cells} =
                   the mean over the surface's member cells of the cell's
                   RetinalPercept red_green / blue_yellow / intensity (the
                   photon_retina opponent percept: ACTIVATIONS, so adaptation
                   shows up here), with episode -includes_look-> look and
                   look -look_of-> PersistentSurface. Gated on every member's
                   percept carrying this epoch.
  le_field_look    an epoch whose segmentation offered NO boundary segment
                   (ganzfeld / eyelid) gets ONE FieldLook (whole-field mean,
                   episode -has_field_look-> look) and no SurfaceLook.

PROVENANCE: episodic_working_memory_core binds observed events with schema,
context, salience and working-memory gates (EpisodicMemoryPolicy /
WorkingMemoryPolicy, enabled 1.0 by default in that seed) -- not cheap to reuse
here without importing its policies and gates, so the episode carries the
status attr 'observed' only (declared). Nothing here is recalled or imagined.

Flag LookingEpisodeParams.enabled, OFF by default (sec 9). Looks also need the
segmentation (FieldLook) and persistence (SurfaceLook) flags. Manifest
latency_class hard_realtime. Depends on surface_persistence.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "looking_episode.json")


# --------------------------------------------------------------- AST helpers
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Ne(a, b): return Not(Eq(a, b))
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
def Nbrs(n, e):
    node = V(n) if isinstance(n, str) else n
    return {"type": "Neighbours", "node": node, "edge_type": e, "any_type": False}
def InNbrs(n, e): return {"type": "InNeighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Count(src): return {"type": "Count", "source": src}
def Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var, "value": val}
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
PARAMS = "LookingEpisodeParams"
LSTATE = "LookingState"
OBSERVER = "Observer"
EPISODE = "LookingEpisode"
SLOOK = "SurfaceLook"
FLOOK = "FieldLook"
HALF = L(0.5)
PERCEPT_KEYS = (("rg", "red_green"), ("by", "blue_yellow"), ("intensity", "intensity"))


def flag(node_type, key, var):
    return Gt(MaxOver(NodesOfType(node_type), var, A(var, key), L(0.0)), HALF)


LE_ON = flag(PARAMS, "enabled", "lep_")
SEG_ON = flag("SurfaceSegmentationParams", "enabled", "sp_")
PS_ON = flag("SurfacePersistenceParams", "enabled", "pp_")


def percept(cell):
    return PickUnique(Nbrs(cell, "has_retinal_percept"))


def percepts_at(cells, var, epoch):
    return Not(Exists(cells, var, Ne(A(percept(var), "input_epoch"), epoch)))


def mean_percept(cells, var, key, n):
    return Div(Sum(cells, var, A(percept(var), key)), n)


RULES = [
    {
        "name": "le_mint",
        "comment": "One durable LookingEpisode per exposure: when the Retina's "
                   "input_epoch passes LookingState.last_epoch. Bound once per "
                   "retina through its first column (cell_index 0, a position, not "
                   "a tuned value). Epoch 0 is the eye's pre-exposure clock.",
        "match": [["lep", "has_looking_state", "ls"],
                  ["agent", "has_observer", "ob"],
                  ["retina", "has_column", "c0"]],
        "where": And(LE_ON, Eq(A("c0", "cell_index"), L(0)),
                     Gt(A("retina", "input_epoch"), L(0)),
                     Gt(A("retina", "input_epoch"), A("ls", "last_epoch"))),
        "effects": [
            ["add_node", "E", EPISODE, {
                "epoch": T(A("retina", "input_epoch")),
                "status": T(L("observed")),
            }],
            ["add_edge", "retina", "had_episode", "E"],
            ["add_edge", "E", "observed_by", "ob"],
            ["add_edge", "ls", "current_episode", "E"],
            seta("ls", "last_epoch", T(A("retina", "input_epoch"))),
        ],
    },
    {
        "name": "le_retire",
        "comment": "Drop the live current_episode pointer to an older episode "
                   "(the episode itself is durable).",
        "match": [["ls", "current_episode", "E"]],
        "where": And(LE_ON, Lt(A("E", "epoch"), A("ls", "last_epoch"))),
        "effects": [["del_edge", "ls", "current_episode", "E"]],
    },
    {
        "name": "le_surface_look",
        "comment": "Per (current episode, PersistentSurface matched this epoch "
                   "through an applied segment S): a SurfaceLook holding the mean "
                   "RetinalPercept red_green / blue_yellow / intensity over S's "
                   "member cells, once every member percept carries the epoch. "
                   "episode -includes_look-> look -look_of-> P.",
        "match": [["ls", "current_episode", "E"],
                  ["st", "has_segment", "S"],
                  ["S", "segment_of", "P"]],
        "where": And(
            LE_ON, SEG_ON, PS_ON,
            Eq(A("S", "epoch"), A("E", "epoch")),
            Gt(A("S", "current"), HALF),
            Eq(A("S", "applied"), L(1.0)),
            Ne(A("P", "look_epoch"), A("E", "epoch")),
            percepts_at(InNbrs("S", "in_segment"), "m_", A("E", "epoch"))),
        "effects": [
            ["add_node", "K", SLOOK, {
                "epoch": T(A("E", "epoch")),
                "sid": T(A("P", "sid")),
                "n_cells": T(A("S", "n_cells")),
                **{k: T(mean_percept(InNbrs("S", "in_segment"), "m" + k, key,
                                     A("S", "n_cells")))
                   for k, key in PERCEPT_KEYS},
            }],
            ["add_edge", "E", "includes_look", "K"],
            ["add_edge", "K", "look_of", "P"],
            seta("P", "look_epoch", T(A("E", "epoch"))),
        ],
    },
    {
        "name": "le_field_look",
        "comment": "Ganzfeld / eyelid: segmentation finalised this epoch with NO "
                   "boundary segment, so there is no surface to look at -- the "
                   "episode gets ONE FieldLook, the whole-field mean percept.",
        "match": [["ls", "current_episode", "E"],
                  ["retina", "had_episode", "E"],
                  ["sp", "has_segmentation_state", "st"]],
        "where": And(
            LE_ON, SEG_ON,
            Eq(A("st", "final_epoch"), A("E", "epoch")),
            Eq(A("E", "field_done"), L(None)),
            Not(Exists(Nbrs("st", "has_segment"), "s_", And(
                Eq(A("s_", "epoch"), A("E", "epoch")),
                Gt(A("s_", "has_boundary"), HALF)))),
            percepts_at(Nbrs("retina", "has_column"), "m_", A("E", "epoch"))),
        "effects": [
            ["add_node", "K", FLOOK, {
                "epoch": T(A("E", "epoch")),
                "n_cells": T(Count(Nbrs("retina", "has_column"))),
                **{k: T(mean_percept(Nbrs("retina", "has_column"), "f" + k, key,
                                     Count(Nbrs("retina", "has_column"))))
                   for k, key in PERCEPT_KEYS},
            }],
            ["add_edge", "E", "has_field_look", "K"],
            seta("E", "field_done", 1.0),
        ],
    },
]

DESCRIPTION = (
    "Mary's Room stage 4.5 (seed 4): LOOKING EPISODES, kept apart from colour "
    "properties. Per exposure (Retina.input_epoch advance) ONE durable "
    "LookingEpisode{epoch, status 'observed'}: Retina -had_episode-> episode "
    "-observed_by-> Observer (a seed-declared node, agent_root -has_observer->). "
    "Per PersistentSurface matched that epoch, a SurfaceLook{epoch, sid, rg, by, "
    "intensity, n_cells} = mean over member cells of the RetinalPercept "
    "red_green / blue_yellow / intensity (opponent ACTIVATIONS: adaptation "
    "changes the look), episode -includes_look-> look -look_of-> surface. An "
    "exposure with no boundary segment (ganzfeld, eyelid) gets ONE FieldLook "
    "(whole-field mean) and no SurfaceLook. Provenance: status attr only "
    "(episodic_working_memory_core not reused: it brings its own policies and "
    "gates). Flag LookingEpisodeParams.enabled, OFF by default (sec 9). See "
    "tools/build_looking_episode_seed.py."
)

MANIFEST = {
    "id": "looking_episode",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["surface_persistence"],
    "latency_class": "hard_realtime",
    "description": DESCRIPTION,
    "microtheory": {
        "name": "looking_episode",
        "description": "exposures -> looking episodes with per-surface looks",
    },
    "nodes": [
        {"local_id": 0, "type": PARAMS, "attrs": {"enabled": 0.0}},
        {"local_id": 1, "type": LSTATE, "attrs": {"last_epoch": -1}},
        {"local_id": 2, "type": OBSERVER, "attrs": {"role": "observer"}},
    ],
    "edges": [
        {"src": {"role": "agent_root"}, "type": "has_looking_episode_params",
         "tgt": {"local": 0}, "attrs": {}},
        {"src": {"local": 0}, "type": "has_looking_state",
         "tgt": {"local": 1}, "attrs": {}},
        {"src": {"role": "agent_root"}, "type": "has_observer",
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
