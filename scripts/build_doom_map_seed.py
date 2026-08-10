"""Authoring script for seeds/doom_ingraph_map.json — the graph-native, persistent
IN-GRAPH SPATIAL MAP the agent accumulates while it explores (block 161000-161999).

Same Term-JSON authoring style as scripts/build_quanta_nav_seed.py (V/A/L/... helpers);
this is a one-off seed EMITTER (CLAUDE.md tools/* class), not runtime agent code.

    PYTHONPATH=runners/dsl/python:. python3 scripts/build_doom_map_seed.py

WHAT THIS SEED IS
-----------------
The world adapter (domains/doom_map_ingest.py) turns the agent's OWN senses into
per-frame observation tokens — mechanical I/O only, NO decision:

  * POSE / self-motion (efference copy): the cell the agent stands in this frame
    -> ObsCell{pose, src:"walk"}   (first-hand: a cell you occupy is FREE).
  * DEPTH range-vision (the marine's LIDAR): each azimuth ray -> the cells in front
    of the wall are ObsCell{pose, src:"depth_free"}; the hit cell (depth < range) is
    ObsCell{pose, src:"depth_wall"}.  game -observed-> ObsCell.

Then master_tick / run_rules does the ACCUMULATION — and every merge DECISION is a
rule here, never Python:

  * dm_free_new / dm_wall_new  GROW the persistent belief: an ObsCell whose pose is
    not yet a known has_cell Cell mints one (value 0=free / 1=wall).  The frontier is
    unknown = ABSENCE, first-class: a pose with no Cell node is simply not in the map.
  * dm_walk_frees_wall  is the merge POLICY: first-hand walking is authoritative, so
    a cell you actually stood in is set FREE even if depth had guessed a wall there.
    (You cannot walk through a real wall in Doom, so this only ever corrects a depth
    mis-hit — which is exactly why the map never registers a wall on a walked cell.)

The persistent has_cell belief is then decoded by the EXISTING Rust `space_quantize`
primitive into SpaceQuantum boxes ("passable" explored areas) + "frontier" boxes (the
unknown border).  A SpaceQuantum IS an area; its human KIND falls out of its geometry
relative to the agent's own body width (config-space) — no magic number (§13):

  * dm_kind_room      both extents exceed the body width -> open in both directions.
  * dm_kind_corridor  exactly one extent equals the body width, the other is longer
                      -> a passage exactly wide enough for the body.
  * dm_kind_area      both extents equal the body width -> a single-body junction/pocket.
  * dm_kind_frontier  a "frontier" quantum -> the still-UNKNOWN border (M3).

(lava / outside are NAMED RESIDUALS: they need a hazard sense (health-damage-on-contact
-> value 2) resp. a sky sense (a wide depth no-hit arc), not box geometry; the
value-keyed `dm_kind_lava` rule is shipped so the mechanism is present and gated, and
fires on a constructed hazard cell, but the short real route does not exercise it.)

INERT BY DEFAULT (§9): every rule guards on game.map_mode=="doom".  A game without that
flag (every existing world) matches nothing here, so the coarse path is byte-identical
and all committed results reproduce.
"""
import json, os

# derive from this file's location so the seed lands in the tree we are RUN from
# (this rung is authored in a worktree, not the canonical tree).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seeds", "doom_ingraph_map.json")

DIMS = 2  # Doom map is planar (x, y); z is a separate coarse bin, not decoded here.


# ---- Term-JSON builders (authoring-time only; mirrors build_quanta_nav_seed.py) ------
def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(node, k):
    node_t = V(node) if isinstance(node, str) else node
    return {"type": "Attr", "node": node_t, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def And(*x): return {"type": "And", "items": list(x)}
def Or(*x): return {"type": "Or", "items": list(x)}
def Not(a): return {"type": "Not", "arg": a}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Neighbours(node, et): return {"type": "Neighbours", "node": node, "edge_type": et, "any_type": False}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def IdxAt(seq, i): return {"type": "IndexAt", "seq": seq, "index": L(i)}

GAME = V("game")


def map_on():
    return Eq(A("game", "map_mode"), L("doom"))


def pose_eq(a_term, b_term):
    """Per-dim pose equality, unrolled over DIMS (None-vs-None-safe idiom from
    build_quanta_nav_seed.contains/pose_eq: IndexAt past a list's real length is None,
    None==None is True, None==number is False — so it degrades safely)."""
    return And(*[Eq(IdxAt(a_term, d), IdxAt(b_term, d)) for d in range(DIMS)])


def set_attr(var, key, term_or_lit, computed=True):
    val = {"__term__": term_or_lit} if computed else term_or_lit
    return ["set_attr", var, key, val]


def set_attr_if_diff(var, key, term_or_lit, computed=True):
    val = {"__term__": term_or_lit} if computed else term_or_lit
    return ["set_attr_if_different", var, key, val]


RULES = []

# ======================================================================================
#  ACCUMULATION — the persistent belief GROWS by rule (unknown = absence, first-class).
# ======================================================================================
_obs_pose = A("O", "pose")
_no_known_cell = Not(Exists(Neighbours(GAME, "has_cell"), "C2", pose_eq(A("C2", "pose"), _obs_pose)))

RULES.append({
    "name": "dm_free_new",
    "comment": ("GROW: an observed FREE cell (src=walk — first-hand occupancy — or "
                "src=depth_free — line-of-sight before a wall) whose pose is not yet a known "
                "has_cell Cell mints one (value 0). Registering an as-yet-unseen pose IS the "
                "explored region growing; a pose with no Cell stays absent = unknown (M3)."),
    "match": [["game", "observed", "O"]],
    "where": And(map_on(),
                 Or(Eq(A("O", "src"), L("walk")), Eq(A("O", "src"), L("depth_free"))),
                 _no_known_cell),
    "effects": [
        ["add_node", "C", "Cell", {"world_type": "Cell", "pose": {"__term__": _obs_pose},
                                    "value": 0.0}],
        ["add_edge", "game", "has_cell", "C", {}],
    ],
})
RULES.append({
    "name": "dm_wall_new",
    "comment": ("GROW: an observed WALL cell (src=depth_wall — the ray's hit, depth<range) "
                "whose pose is not yet known mints a Cell (value 1). Only fills UNKNOWN poses — "
                "never overwrites an already-known free cell (that is dm_walk_frees_wall's job, "
                "and depth-free never overwrites a wall): a first sensed wall persists."),
    "match": [["game", "observed", "O"]],
    "where": And(map_on(), Eq(A("O", "src"), L("depth_wall")), _no_known_cell),
    "effects": [
        ["add_node", "C", "Cell", {"world_type": "Cell", "pose": {"__term__": _obs_pose},
                                    "value": 1.0}],
        ["add_edge", "game", "has_cell", "C", {}],
    ],
})
RULES.append({
    "name": "dm_walk_frees_wall",
    "comment": ("MERGE POLICY: first-hand walking is authoritative. A cell the agent actually "
                "stood in (src=walk) that a depth ray had mis-registered as a wall is corrected "
                "to FREE. This is the rule that GUARANTEES the map never keeps a wall on a walked "
                "cell (M2 trajectory-consistency) — and it can only ever correct a depth mis-hit, "
                "since a real Doom wall is unwalkable."),
    "match": [["game", "observed", "O"], ["game", "has_cell", "C"]],
    "where": And(map_on(), Eq(A("O", "src"), L("walk")),
                 pose_eq(_obs_pose, A("C", "pose")), Eq(A("C", "value"), L(1.0))),
    "effects": [set_attr_if_diff("C", "value", 0.0, computed=False)],
})

# ======================================================================================
#  REGION TYPING — a decoded SpaceQuantum IS an area; its human KIND falls out of its
#  box geometry relative to the agent's own body width (config-space; §13-clean).
# ======================================================================================
# extent along dim d = hi[d] - lo[d] + 1 (inclusive box). body width = game.body_w (the
# agent's own config-space footprint the adapter stamps; default 1 cell at the 64-unit grid).
_ext0 = Plus(Minus(IdxAt(A("Q", "hi"), 0), IdxAt(A("Q", "lo"), 0)), L(1))
_ext1 = Plus(Minus(IdxAt(A("Q", "hi"), 1), IdxAt(A("Q", "lo"), 1)), L(1))
_bw = A("game", "body_w")
_passable = Eq(A("Q", "kind"), L("passable"))

RULES.append({
    "name": "dm_kind_room",
    "comment": "a passable area open in BOTH directions (both extents exceed body width) -> room.",
    "match": [["Q", "in_space", "game"]],
    "where": And(map_on(), _passable, Gt(_ext0, _bw), Gt(_ext1, _bw)),
    "effects": [set_attr_if_diff("Q", "region_kind", "room", computed=False)],
})
RULES.append({
    "name": "dm_kind_corridor",
    "comment": ("a passable area exactly one body wide in one dim and longer in the other -> "
                "corridor (a passage just wide enough for the body — the config-space corridor)."),
    "match": [["Q", "in_space", "game"]],
    "where": And(map_on(), _passable,
                 Or(And(Eq(_ext0, _bw), Gt(_ext1, _bw)),
                    And(Eq(_ext1, _bw), Gt(_ext0, _bw)))),
    "effects": [set_attr_if_diff("Q", "region_kind", "corridor", computed=False)],
})
RULES.append({
    "name": "dm_kind_area",
    "comment": "a passable box exactly one body across in both dims -> a single-body junction/pocket.",
    "match": [["Q", "in_space", "game"]],
    "where": And(map_on(), _passable, Eq(_ext0, _bw), Eq(_ext1, _bw)),
    "effects": [set_attr_if_diff("Q", "region_kind", "area", computed=False)],
})
RULES.append({
    "name": "dm_kind_frontier",
    "comment": ("a frontier quantum -> the still-UNKNOWN border of the explored region (M3: "
                "unknown is first-class, and the frontier is where it becomes known next)."),
    "match": [["Q", "in_space", "game"]],
    "where": And(map_on(), Eq(A("Q", "kind"), L("frontier"))),
    "effects": [set_attr_if_diff("Q", "region_kind", "frontier", computed=False)],
})
RULES.append({
    "name": "dm_kind_lava",
    "comment": ("VALUE-keyed (not geometry): a passable area sitting over HAZARD cells (value 2 — "
                "a damaging floor the adapter marks when standing there costs health) -> lava. "
                "Shipped so the human-area taxonomy is extensible beyond geometry and gated; "
                "exercised by the constructed hazard case. NOTE: sensing lava on a live route "
                "needs the health-damage sense wired — a declared residual, not the short route."),
    "match": [["Q", "in_space", "game"], ["game", "has_cell", "C"]],
    "where": And(map_on(), _passable, Eq(A("C", "value"), L(2.0)),
                 # C inside Q's box (2D containment)
                 And(*[And({"type": "Gte", "a": IdxAt(A("C", "pose"), d), "b": IdxAt(A("Q", "lo"), d)},
                           {"type": "Lte", "a": IdxAt(A("C", "pose"), d), "b": IdxAt(A("Q", "hi"), d)})
                       for d in range(DIMS)])),
    "effects": [set_attr_if_diff("Q", "region_kind", "lava", computed=False)],
})

MANIFEST = {
    "id": "doom_ingraph_map",
    "version": "1.0.0",
    "depends_on": [],
    "description": (
        "The persistent, GRAPH-NATIVE in-graph spatial map the agent accumulates while it "
        "explores (Doom, block 161000-161999). Composes the EXISTING Rust space_quantize "
        "primitive (has_cell belief -> SpaceQuantum passable/frontier boxes) with NEW seed "
        "rules that (1) GROW the persistent occupancy belief from the agent's own senses "
        "(pose/self-motion = walk-free; depth range-vision = depth_free/depth_wall) — "
        "unknown = ABSENCE, first-class; the merge POLICY (walk-free authoritative) is the "
        "dm_walk_frees_wall rule, never Python; and (2) TYPE each decoded area with a human "
        "region_kind (room/corridor/area/frontier) that falls out of the box's geometry "
        "relative to the agent's body width (config-space; no magic number). All rules guard "
        "on game.map_mode==\"doom\" -> INERT for every existing world (coarse path byte-"
        "identical). The ingest (pose/depth -> ObsCell world points) and the PNG display are "
        "mechanical world-adapter I/O (domains/doom_map_ingest.py); every ACCUMULATION and "
        "TYPING decision is a rule here."
    ),
    "microtheory": {
        "name": "doom_ingraph_map",
        "description": "persistent graph-native spatial map: grow occupancy from senses, type areas by geometry",
    },
    "nodes": [],
    "edges": [],
    "productions": [],
    "concepts": [],
    "rules": RULES,
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(MANIFEST, f, indent=1)
    print(f"wrote {OUT} with {len(RULES)} rules")
