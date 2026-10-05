"""Emit seeds/look_property_link.json (Mary's Room stage 4.5, seed 5).

THE LINK between a look (looking_episode) and a property (colour_property).
Every decision is a graph rule; this script only writes JSON. Run:

    PYTHONPATH=. python tools/build_look_property_link_seed.py

A SurfaceLook of PersistentSurface P at epoch e is linked to P's
ColourProperty CP by the RUNG-1 PropertyCheck of (CP, e):
  lk_presents      check status 'minted' (the minting epoch) or 'holds'
                   -> look -presents_property-> CP, look.link = 'property'.
  lk_unrecognised  check status 'refused'
                   -> look -presents_unrecognised-> CP, look.link = 'unrecognised'.
No check for (CP, e) -> no link (the look stays unlinked until the check
exists; a look of a surface with no property is never linked). The edge name
presents_as is NOT used (deformation_beneficiary owns it). Only rung 1 links;
rung 2's pooled_status stays on the PropertyCheck (it is computed after the
whole frame is checked, so it is read from the check, not copied).

No flag of its own: gated on BOTH ColourPropertyParams.enabled and
LookingEpisodeParams.enabled (each OFF by default, sec 9). Manifest
latency_class hard_realtime. Depends on colour_property and looking_episode.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "look_property_link.json")


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Ne(a, b): return Not(Eq(a, b))
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def NodesOfType(t): return {"type": "NodesOfType", "node_type": t}
def InNbrs(n, e): return {"type": "InNeighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def MaxOver(src, var, val, default=None):
    t = {"type": "MaxOver", "source": src, "var_name": var, "value": val}
    if default is not None:
        t["default"] = default
    return t
def PickUnique(src): return {"type": "PickUnique", "source": src}
def T(term): return {"__term__": term}


HALF = L(0.5)


def flag(node_type, key, var):
    return Gt(MaxOver(NodesOfType(node_type), var, A(var, key), L(0.0)), HALF)


GATE = And(flag("ColourPropertyParams", "enabled", "cpp_"),
           flag("LookingEpisodeParams", "enabled", "lep_"))


def check_of_epoch(var):
    return Filter(InNbrs("CP", "check_of"), var, Eq(A(var, "epoch"), A("K", "epoch")))


def has_check(statuses, var):
    return Exists(check_of_epoch(var), var + "x",
                  Or(*[Eq(A(var + "x", "status"), L(s)) for s in statuses]))


MATCH = [["K", "look_of", "P"], ["P", "has_colour_property", "CP"]]

RULES = [
    {
        "name": "lk_presents",
        "comment": "The look presents the surface's held property when that "
                   "epoch's rung-1 PropertyCheck holds, or at the minting epoch.",
        "match": MATCH,
        "where": And(GATE, Eq(A("K", "link"), L(None)),
                     has_check(("minted", "holds"), "kh_")),
        "effects": [["add_edge", "K", "presents_property", "CP"],
                    ["set_attr", "K", "link", "property"]],
    },
    {
        "name": "lk_unrecognised",
        "comment": "The look presents the surface but NOT its held property: that "
                   "epoch's rung-1 PropertyCheck refused (the property is "
                   "unchanged; the look is linked as unrecognised).",
        "match": MATCH,
        "where": And(GATE, Eq(A("K", "link"), L(None)),
                     has_check(("refused",), "kr_")),
        "effects": [["add_edge", "K", "presents_unrecognised", "CP"],
                    ["set_attr", "K", "link", "unrecognised"]],
    },
]

DESCRIPTION = (
    "Mary's Room stage 4.5 (seed 5): links a SurfaceLook (looking_episode) to "
    "its surface's ColourProperty (colour_property) through that epoch's "
    "rung-1 PropertyCheck: status minted|holds -> look -presents_property-> "
    "property; refused -> look -presents_unrecognised-> property; no check -> "
    "no link. presents_as is not used (deformation_beneficiary). Only rung 1 "
    "links; rung 2 stays on the PropertyCheck. Gated on "
    "ColourPropertyParams.enabled and LookingEpisodeParams.enabled, both OFF by "
    "default (sec 9). See tools/build_look_property_link_seed.py."
)

MANIFEST = {
    "id": "look_property_link",
    "version": "1.0.0",
    "self_load_only": True,
    "depends_on": ["colour_property", "looking_episode"],
    "latency_class": "hard_realtime",
    "description": DESCRIPTION,
    "microtheory": {
        "name": "look_property_link",
        "description": "looks -> the colour property they present (or fail to)",
    },
    "nodes": [],
    "edges": [],
    "productions": [],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
        f.write("\n")
    print(f"wrote {OUT} with {len(RULES)} rules")
