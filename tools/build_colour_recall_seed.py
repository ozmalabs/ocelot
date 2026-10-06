"""Emit seeds/colour_recall.json (Mary's Room stage 4 fix: the RECALL arm).

A colour PROPERTY without a LOOK: answering "what colour is surface sid?" from
the held ColourProperty alone, with no new LookingEpisode or SurfaceLook.
Every decision is a graph rule; this script only writes JSON. Run:

    PYTHONPATH=. python tools/build_colour_recall_seed.py

INPUT: a RecallCue{sid, epoch_requested} node, written by the adapter as
EXTERNAL input (like a question) with agent -has_recall_cue-> cue. The adapter
writes the cue blind; it never reads the graph to decide anything.

  cr_recall       an unanswered cue whose sid names a PersistentSurface that HAS
                  a ColourProperty -> ONE Recollection{sid, epoch_requested,
                  status 'recalled', minted_epoch, provenance_kind 'recalled',
                  observation_status 'not_observed'} with
                  recollection -recalls-> ColourProperty,
                  recollection -recollection_of-> PersistentSurface,
                  cue -answered_by-> recollection; cue.status := 'answered'.
  cr_no_property  an unanswered cue with no such property -> ONE Recollection
                  {status 'no_property', reason 'no_surface'|'no_property',
                  provenance_kind 'retrieval_failure', observation_status
                  'not_observed'} with cue -answered_by-> it; nothing is recalled.

NOTHING HERE LOOKS: no rule mints a LookingEpisode, SurfaceLook or FieldLook,
and no rule reads a percept or a catch. The recollection points at the
property minted at first sight; it does not copy or recompute it.

PROVENANCE: the attrs provenance_kind 'recalled' / observation_status
'not_observed' follow seeds/episodic_working_memory_core.json's
observed/recalled split (RecallCandidate), as attrs only: that seed's policies,
gates and retrieval rules are not loaded or reused here.

Flag ColourRecallParams.enabled, OFF by default (sec 9). Manifest
latency_class hard_realtime. Depends on colour_property.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "colour_recall.json")


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def IfThenElse(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
def Nbrs(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def MaxOver(src, var, val, default=None):
    t = {"type": "MaxOver", "source": src, "var_name": var, "value": val}
    if default is not None:
        t["default"] = default
    return t
def T(term): return {"__term__": term}


PARAMS = "ColourRecallParams"
CUE = "RecallCue"
REC = "Recollection"
ENABLED = Gt(MaxOver(NodesOfType(PARAMS), "crp_", A("crp_", "enabled"), L(0.0)), L(0.5))


def surface_with_property(var):
    return Exists(NodesOfType("PersistentSurface"), var, And(
        Eq(A(var, "sid"), A("Q", "sid")),
        Exists(Nbrs(var, "has_colour_property"), var + "c", L(True))))


PROVENANCE = {"provenance_kind": T(L("recalled")),
              "observation_status": T(L("not_observed"))}

RULES = [
    {
        "name": "cr_recall",
        "comment": "An unanswered RecallCue naming a PersistentSurface that holds "
                   "a ColourProperty is answered by ONE Recollection that points at "
                   "that property (recalls) and surface (recollection_of). No look "
                   "is made: no LookingEpisode / SurfaceLook is minted and no "
                   "percept or catch is read.",
        "match": [["agent", "has_recall_cue", "Q"],
                  ["sc", "has_surface", "P"],
                  ["P", "has_colour_property", "CP"]],
        "where": And(ENABLED, Eq(A("Q", "status"), L(None)),
                     Eq(A("P", "sid"), A("Q", "sid"))),
        "effects": [
            ["add_node", "R", REC, {
                "sid": T(A("Q", "sid")),
                "epoch_requested": T(A("Q", "epoch_requested")),
                "status": T(L("recalled")),
                "minted_epoch": T(A("CP", "minted_epoch")),
                **PROVENANCE,
            }],
            ["add_edge", "agent", "has_recollection", "R"],
            ["add_edge", "Q", "answered_by", "R"],
            ["add_edge", "R", "recalls", "CP"],
            ["add_edge", "R", "recollection_of", "P"],
            ["set_attr", "Q", "status", "answered"],
        ],
    },
    {
        "name": "cr_no_property",
        "comment": "An unanswered RecallCue whose sid names no PersistentSurface "
                   "with a ColourProperty is answered by ONE Recollection with "
                   "status 'no_property' (reason 'no_surface' if no surface has "
                   "that sid). Nothing is recalled and nothing is guessed.",
        "match": [["agent", "has_recall_cue", "Q"]],
        "where": And(ENABLED, Eq(A("Q", "status"), L(None)),
                     Not(surface_with_property("np_"))),
        "effects": [
            ["add_node", "R", REC, {
                "sid": T(A("Q", "sid")),
                "epoch_requested": T(A("Q", "epoch_requested")),
                "status": T(L("no_property")),
                "reason": T(IfThenElse(
                    Exists(NodesOfType("PersistentSurface"), "ns_",
                           Eq(A("ns_", "sid"), A("Q", "sid"))),
                    L("no_property"), L("no_surface"))),
                # episodic_working_memory_core's RecallOutcome idiom
                "provenance_kind": T(L("retrieval_failure")),
                "observation_status": T(L("not_observed")),
            }],
            ["add_edge", "agent", "has_recollection", "R"],
            ["add_edge", "Q", "answered_by", "R"],
            ["set_attr", "Q", "status", "answered"],
        ],
    },
]

DESCRIPTION = (
    "Mary's Room stage 4 fix (recall arm): a colour property WITHOUT a look. "
    "Input: a RecallCue{sid, epoch_requested} written by the adapter as external "
    "input (agent -has_recall_cue-> cue). cr_recall: an unanswered cue naming a "
    "PersistentSurface with a ColourProperty -> ONE Recollection{sid, "
    "epoch_requested, status 'recalled', minted_epoch, provenance_kind "
    "'recalled', observation_status 'not_observed'} -recalls-> that "
    "ColourProperty (and -recollection_of-> the surface; cue -answered_by-> "
    "it). cr_no_property: otherwise ONE Recollection{status 'no_property', "
    "reason no_surface|no_property, provenance_kind 'retrieval_failure'}. No rule mints a LookingEpisode, SurfaceLook "
    "or FieldLook or reads a percept or catch. Provenance attrs follow "
    "episodic_working_memory_core's observed/recalled split (attrs only; its "
    "policies are not reused). Flag ColourRecallParams.enabled, OFF by default "
    "(sec 9). See tools/build_colour_recall_seed.py."
)

MANIFEST = {
    "id": "colour_recall",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["colour_property"],
    "latency_class": "hard_realtime",
    "description": DESCRIPTION,
    "microtheory": {
        "name": "colour_recall",
        "description": "recall cue -> the held colour property, with no look",
    },
    "nodes": [
        {"local_id": 0, "type": PARAMS, "attrs": {"enabled": 0.0}},
    ],
    "edges": [
        {"src": {"role": "agent_root"}, "type": "has_colour_recall_params",
         "tgt": {"local": 0}, "attrs": {}},
    ],
    "productions": [],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
        f.write("\n")
    print(f"wrote {OUT} with {len(RULES)} rules")
