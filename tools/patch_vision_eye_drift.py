#!/usr/bin/env python
"""AUTHORING SCRIPT (one-off, not runtime): wire the drift into the image.

Emits the JOB-1 additions to `seeds/vision_eye.json`:

  * Gamma productions for the Gaze<->Eye coupling and the world sheet. FM-0
    measured that NO production admits a Gaze<->Eye edge -- verified again here
    before the patch: `Gamma rejects: type 'has_gaze' not in vocabulary`. The
    coupling is INADMISSIBLE, so Gamma must gain the production; that is graph
    data, not Python.
  * `ey_sample_at_gaze` -- THE SAMPLING DECISION, as a seed rule. The adapter
    states the photon count at each WORLD location (physics: photons exist at
    places). WHICH world cell a receptor sees is the GRAPH's decision, and it is
    the gaze position that decides it.
  * `world_sample` on EyeParams, default **0.0** (PROTOCOL 9: off by default, so
    every committed result reproduces byte-identically).

Run:  python tools/patch_vision_eye_drift.py
"""
import json
import os

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "seeds", "vision_eye.json")


def attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def var(n):
    return {"type": "Var", "name": n}


def lit(v):
    return {"type": "Lit", "value": v}


def param(key):
    """A config read on the EyeParams SINGLETON.

    `PickUnique`, never `Pick` (main's 185-read rebind, `PickUnique` in
    `runners/dsl/src/term.rs`): `Pick` returns `iter().next()` -- ONE of N
    candidates, silently, so a second params node would be ignored without a
    word. `PickUnique` is identical for 0 or 1 and PANICS on >1, so an ambiguous
    config read SCREAMS instead of quietly reading someone else's default. Same
    disease as `.get('Name','')` and a guarded division returning 0.0 (§1.1,
    §12) -- a silent wrong answer where there should be an error.
    """
    return attr({"type": "PickUnique", "source": {"type": "NodesOfType",
                                                  "node_type": "EyeParams"}}, key)


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def term(t):
    return {"__term__": t}


# ---------------------------------------------------------------- productions
PRODUCTIONS = [
    # THE COUPLING. This is the edge Gamma refused; FM-0's "one is INADMISSIBLE"
    # is exactly this vocabulary entry being absent. Adding it is what makes a
    # rule able to read a GazeCell and an EyeCell in the same match.
    {"src": {"type": "Eye", "var": "a"}, "edge_type": "has_gaze",
     "tgt": {"type": "Gaze", "var": "b"},
     "provenance": "seed:vision_eye"},
    # The world sheet: the stationary scene the eye moves OVER.
    {"src": {"type": "World", "var": "a"}, "edge_type": "has_worldcell",
     "tgt": {"type": "WorldCell", "var": "b"},
     "provenance": "seed:vision_eye"},
]

# ---------------------------------------------------------------- the rule
SAMPLE_RULE = {
    "name": "ey_sample_at_gaze",
    "comment": (
        "THE DRIFT MOVES THE IMAGE. Each receptor's `lum` is the luminance of "
        "the WorldCell it currently overlies, and the gaze position is what "
        "decides which one that is: world(row,col) = gaze(row,col) + "
        "receptor(row,col). So the gaze is the top-left corner of the retinal "
        "window in world coordinates -- no centring constant is needed or "
        "used. THIS IS THE SAMPLING DECISION AND IT IS THE GRAPH'S: the "
        "adapter states the photon count at each world location (photons exist "
        "at places -- physics, legitimately given, exactly as the retina's "
        "adjacency is in PreVisualWorld's docstring), and never says which "
        "receptor sees which photon. FM-0 measured the previous arrangement "
        "VACUOUS: `present()` wrote frame[r,c] and never called gaze_pos(), so "
        "D == 0.0 EXACTLY on lum/x/theta/resp -- the walk's only consumer was "
        "the ruler that measured it. Gated `world_sample`, default 0 "
        "(PROTOCOL 9). NOT gated by `saw`: freezing the walk must leave the "
        "sampling intact and simply stop moving it, or the ablation would "
        "confound 'no drift' with 'no image' -- which is the Troxler arm's "
        "whole point."
    ),
    "match_type": "EyeCell",
    "match": [["e", "has_eyecell", "c"],
              ["e", "has_gaze", "g"],
              ["g", "gaze_at", "gc"]],
    "where": {"type": "And", "items": [
        gt(param("eye"), lit(0.5)),
        gt(param("world_sample"), lit(0.5)),
        lt(attr(var("c"), "lum_step"), attr(var("e"), "step")),
    ]},
    "effects": [
        # `PickUnique`, not `Pick`: this filter must match EXACTLY ONE WorldCell
        # -- world coordinates are unique by construction. 0 matches (a gaze that
        # ran off the sheet) behaves identically to `Pick` (None); >1 means
        # DUPLICATE WORLD CELLS, which is a real defect and must SCREAM rather
        # than silently sample whichever one `iter().next()` happened to yield.
        # Same principle as the config reads (main's 185-read rebind).
        ["set_attr", "c", "lum", term(attr(
            {"type": "PickUnique", "source": {
                "type": "Filter",
                "source": {"type": "NodesOfType", "node_type": "WorldCell"},
                "var_name": "w",
                "predicate": {"type": "And", "items": [
                    eq(attr(var("w"), "row"),
                       plus(attr(var("gc"), "row"), attr(var("c"), "row"))),
                    eq(attr(var("w"), "col"),
                       plus(attr(var("gc"), "col"), attr(var("c"), "col"))),
                ]},
            }}, "lum"))],
        ["set_attr", "c", "lum_step", term(attr(var("e"), "step"))],
    ],
}


def main():
    with open(SEED) as f:
        d = json.load(f)

    # --- param: off by default (PROTOCOL 9) ---
    p = d["nodes"][0]
    assert p["type"] == "EyeParams", p["type"]
    p["attrs"]["world_sample"] = 0.0

    # --- productions ---
    have = {(pr["src"]["type"], pr["edge_type"], pr["tgt"]["type"])
            for pr in d["productions"]}
    for pr in PRODUCTIONS:
        key = (pr["src"]["type"], pr["edge_type"], pr["tgt"]["type"])
        if key not in have:
            d["productions"].append(pr)

    # --- rule (insert before the saw rules so `lum` is fresh when the
    #     receptor reads it; the step-gates make order irrelevant, but the
    #     reading order should match the causal order) ---
    names = [r["name"] for r in d["rules"]]
    if "ey_sample_at_gaze" not in names:
        i = names.index("ey_receptor_log")
        d["rules"].insert(i, SAMPLE_RULE)

    d["version"] = "1.1.0"

    with open(SEED, "w") as f:
        json.dump(d, f, indent=1)
        f.write("\n")
    print(f"patched {SEED}")
    print(f"  productions: {len(d['productions'])}")
    print(f"  rules:       {len(d['rules'])}")


if __name__ == "__main__":
    main()
