"""seeds/maze_capability.json — the maze world's capability map so the jabberwock running IN the maze does its
OWN independent design, WITHOUT a teacher. It is GIVEN only weak baseline strategies; but it already
UNDERSTANDS routing/navigation (it holds the routing primitives below — its flood IS a distance field, its hop
IS gradient descent, its learned-walls IS map memory), so when the baselines fall short it COMPOSES a better
strategy from those primitives itself. No LLM, no teacher — the agent assembles what it already knows.

  GIVEN baselines (both sub-optimal, so the agent is driven to do better):
    greedy_amnesia — routing (distance_field + gradient_descent) but FORGETTING the map each attempt.
    wall_follower  — the reactive left-hand rule (no map, no routing): a long path.

  UNDERSTOOD routing primitives (RoutingPrimitive nodes — what the agent already knows about navigation):
    map_memory       — remember obstacles you discover, so you don't re-explore (a learned map).
    distance_field   — compute distance-to-goal over the known map (a flood).
    gradient_descent — step to the neighbour with the lowest distance-to-goal.

The agent's insight, from its own understanding: its amnesiac routing fails because it lacks `map_memory`; it
HAS that primitive; so it composes distance_field + gradient_descent + map_memory into a new strategy.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

nodes = [
    {"local_id": 0, "type": "Microtheory", "attrs": {"name": "maze_world", "domain": "maze"}},
    {"local_id": 1, "type": "Operator", "attrs": {
        "name": "greedy_amnesia", "runner": "flood_amnesia", "metric": "maze_efficiency", "target": 0.9,
        "comment": "routing (distance_field + gradient_descent) but FORGETS the map each attempt -> re-explores."}},
    {"local_id": 2, "type": "Operator", "attrs": {
        "name": "wall_follower", "runner": "wall_follower", "metric": "maze_efficiency", "target": 0.9,
        "comment": "reactive left-hand rule: no map, no routing -> a long path."}},
    {"local_id": 3, "type": "CapabilityAxis", "attrs": {
        "is_axis": 1.0, "capability_keys": ["solve", "maze", "amnesia"], "saturation": 0.0,
        "shortfall": 0.5, "min_order": 1.0, "investigated_count": 0, "mf_stall": 0}},
    {"local_id": 4, "type": "CapabilityAxis", "attrs": {
        "is_axis": 1.0, "capability_keys": ["solve", "maze", "reactive"], "saturation": 0.0,
        "shortfall": 0.5, "min_order": 1.0, "investigated_count": 0, "mf_stall": 0}},
    # The routing the agent ALREADY UNDERSTANDS — the primitives it will compose from. (Not axes: knowledge.)
    {"local_id": 5, "type": "RoutingPrimitive", "attrs": {
        "name": "map_memory", "does": "remember obstacles you discover so you don't re-explore — a learned map"}},
    {"local_id": 6, "type": "RoutingPrimitive", "attrs": {
        "name": "distance_field", "does": "compute distance-to-goal over the known map (a flood)"}},
    {"local_id": 7, "type": "RoutingPrimitive", "attrs": {
        "name": "gradient_descent", "does": "step to the neighbour with the lowest distance-to-goal"}},
]
edges = [
    {"src": {"local": 3}, "type": "investigated_by", "tgt": {"local": 1}},
    {"src": {"local": 4}, "type": "investigated_by", "tgt": {"local": 2}},
    {"src": {"local": 1}, "type": "applies_in", "tgt": {"local": 0}},
    {"src": {"local": 2}, "type": "applies_in", "tgt": {"local": 0}},
    # the agent's routing understanding is anchored in the maze world.
    {"src": {"local": 5}, "type": "understood_in", "tgt": {"local": 0}},
    {"src": {"local": 6}, "type": "understood_in", "tgt": {"local": 0}},
    {"src": {"local": 7}, "type": "understood_in", "tgt": {"local": 0}},
]

# ---- THE COMPOSE RULE: the agent's design act, now graph-native (fires in tick(), no host Python) ----
def V(n): return {"type": "Var", "name": n}
def A(nd, k): return {"type": "Attr", "node": nd, "key": k}
def L(v): return {"type": "Lit", "value": v}
def P0(nd, k): return {"type": "Plus", "items": [A(nd, k), L(0)]}
def EQ(a, b): return {"type": "Eq", "a": a, "b": b}
def NEQ(a, b): return {"type": "Not", "arg": EQ(a, b)}
def NOT(x): return {"type": "Not", "arg": x}
def LT(a, b): return {"type": "Lt", "a": a, "b": b}
def GT(a, b): return {"type": "Gt", "a": a, "b": b}
def AND(*xs): return {"type": "And", "items": list(xs)}
def NODESOF(t): return {"type": "NodesOfType", "node_type": t}
def EXISTS(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}

# a GIVEN baseline maze strategy that was investigated but fell short of its target (0 < saturation < 1).
baseline_short = EXISTS(NODESOF("CapabilityAxis"), "x",
    AND(GT(P0(V("x"), "saturation"), L(0.0)), LT(P0(V("x"), "saturation"), L(1.0)),
        NEQ(P0(V("x"), "composed"), L(1.0))))
# guard: a composed strategy does not already exist (compose ONCE).
composed_exists = EXISTS(NODESOF("CapabilityAxis"), "y", EQ(P0(V("y"), "composed"), L(1.0)))

compose_routing_on_shortfall = {
    "name": "compose_routing_on_shortfall",
    # bind the agent + the maze microtheory it operates in (scopes the rule to the maze world only).
    "match": [["ag", "operates_in", "mt"]],
    "where": AND(EQ(A(V("mt"), "name"), L("maze_world")), baseline_short, NOT(composed_exists)),
    "effects": [
        ["add_node", "cop", "Operator", {
            "name": "composed_routing", "runner": "composed_routing", "metric": "maze_efficiency",
            "target": 0.9, "composed": 1.0,
            "comment": ("COMPOSED by the agent from the routing primitives it understands "
                        "(map_memory + distance_field + gradient_descent), because its baseline routing fell "
                        "short of target. No teacher.")}],
        ["add_node", "cax", "CapabilityAxis", {
            "is_axis": 1.0, "capability_keys": ["solve", "maze", "composed"], "saturation": 0.0,
            "shortfall": 0.7, "min_order": 1.0, "investigated_count": 0, "mf_stall": 0, "composed": 1.0}],
        ["add_edge", "cax", "investigated_by", "cop"],
        ["add_edge", "cop", "applies_in", "mt"]]}

seed = {"id": "maze_capability", "version": "1.0.0", "depends_on": ["enact", "autonomy"],
        "description": ("The maze world's capability map: 2 weak baseline strategies (greedy_amnesia, "
            "wall_follower) the agent is GIVEN, plus the routing PRIMITIVES it already UNDERSTANDS "
            "(map_memory, distance_field, gradient_descent). When the baselines fall short the "
            "compose_routing_on_shortfall RULE composes a better strategy from those primitives itself — a "
            "graph-native design act, no teacher and no host Python."),
        "nodes": nodes, "edges": edges, "productions": [], "concepts": [],
        "rules": [compose_routing_on_shortfall]}
path = os.path.join(ROOT, "seeds", "maze_capability.json")
json.dump(seed, open(path, "w"), indent=1); json.load(open(path))
print("wrote seeds/maze_capability.json:",
      [n["attrs"].get("name") or n["attrs"].get("capability_keys") for n in nodes])
