"""MOVE-SPACE PLANNER (core) — graph-native, donkey=0. The general spatial planner the agent needs:
plan in N dimensions, at ARBITRARY/ADJUSTABLE SCALE (move granularity is a learned variable, not unit
steps), producing M-WAYPOINT ROUTES, re-planned dynamically, and recognising a CLOSED move-space (the ls20
trap) so it switches from MOVEMENT to INTERACTION.

The object is a MOVE-SPACE GRAPH learned from observation:
  Config  node  : a CONFIGURATION — an N-dim pose [x0..x_{n-1}] (the place the avatar comes to REST).
                  (extensible: + orient/scale dims for rotation/squash affordances; + a tuple of Z poses
                   for groups/RTS — same node, wider pose vector.)
  Move    node  : an AFFORDANCE APPLICATION (an action) ; Config --has_move--> Move --to--> Config'.
                  The SCALE is whatever the world did (slide-5, step-1, anything) — learned, not assumed.
  Planner node  : --knows--> every Config ; holds cur config + closed flag + minted hypotheses.

Graph RULES do the planning (run_rules, the agent's evaluator):
  FLOOD     : BFS over Move edges from the current config -> Config.dist (the route field; scale-agnostic,
              N-dim — it counts MOVES, so any move magnitude / any dimensionality works unchanged).
  FRONTIER  : the nearest config still OPEN (not all affordances tried) = the next interesting place.
  CLOSED    : no open config is reachable -> the move-space is EXHAUSTED -> mint a Hypothesis that the way
              forward is a non-movement affordance (interaction), not more motion.
The M-waypoint ROUTE is read off the dist field by descent (mechanical, exactly like the real loop's
hop-follows-the-gradient): waypoints = the configs along the shortest descent to the frontier.

Demos (donkey=0): (1) an ls20-like CLOSED chamber -> recognised closed + hypothesis (the trap, solved
cognitively); (2) an OPEN maze -> a 3-waypoint route; (3) a 3-D space with mixed move SCALES -> an N-dim
route. The construction of the graph FROM OBSERVATION is mechanical adapter ingest (cached dedup); every
DECISION (flood / frontier / closed / route-field) is a graph rule.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_plans_move_space.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*x): return {"type": "And", "items": list(x)}
def Or(*x): return {"type": "Or", "items": list(x)}
def Not(a): return {"type": "Not", "arg": a}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Nb(n, et): return {"type": "Neighbours", "node": V(n), "edge_type": et}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}

# ---- the planning rules (all graph-native) --------------------------------------------------------
# FLOOD: dist over the move graph from the current config (dist=0). Counts MOVES => scale- & dim-agnostic.
FLOOD = {"id": "ms_flood", "name": "ms_flood",
    "match": [["c1", "has_move", "mv"], ["mv", "to", "c2"]],
    "where": And(Gte(A("c1", "dist"), L(0.0)),
                 Or(Lt(A("c2", "dist"), L(0.0)), Gt(A("c2", "dist"), Plus(A("c1", "dist"), L(1.0))))),
    "effects": [["set_attr", "c2", "dist", {"__term__": Plus(A("c1", "dist"), L(1.0))}]]}
# FRONTIER: the nearest OPEN config (ntried < naff) — the next interesting place to expand. Phase 1 only
# (after FLOOD reaches steady state) so the dist field is settled before we judge reachability.
FRONTIER = {"id": "ms_frontier", "name": "ms_frontier",
    "match": [["p", "knows", "c"]],
    "where": And(Eq(A("p", "phase"), L(1.0)),
                 Gte(A("c", "dist"), L(0.0)), Lt(A("c", "ntried"), A("c", "naff")),
                 Not(Exists(Nb("p", "knows"), "c2",
                     And(Gte(A("c2", "dist"), L(0.0)), Lt(A("c2", "ntried"), A("c2", "naff")),
                         Lt(A("c2", "dist"), A("c", "dist")))))),
    "effects": [["set_attr", "c", "is_frontier", 1.0]]}
# CLOSED: no reachable config is open -> movement is EXHAUSTED -> the way forward is interaction. Mint it.
CLOSED = {"id": "ms_closed", "name": "ms_closed",
    "match": [["p", "knows", "c0"]],
    "where": And(Eq(A("p", "phase"), L(1.0)), Eq(A("p", "closed"), L(0.0)),
                 Not(Exists(Nb("p", "knows"), "c2",
                     And(Gte(A("c2", "dist"), L(0.0)), Lt(A("c2", "ntried"), A("c2", "naff")))))),
    "effects": [["set_attr", "p", "closed", 1.0],
                ["add_node", "hyp", "Hypothesis", {"kind": "need_non_movement_affordance", "open": 1.0}],
                ["add_edge", "p", "minted", "hyp"]]}


class MoveSpace:
    """Adapter: learns the move-space graph FROM OBSERVATION (mechanical ingest, cached dedup). The planner
    decisions are graph rules; this only translates observed transitions into Config/Move graph data."""
    def __init__(self, a, naff):
        self.a, self.s, self.I, self.naff = a, a.s, a.inner, float(naff)
        self.p = self.s.add_node("Planner", {"closed": 0.0, "phase": 0.0})
        self.by_key, self.tried = {}, {}

    def cfg(self, pose):
        key = tuple(float(x) for x in pose)
        if key not in self.by_key:
            nid = self.s.add_node("Config", {"pose": list(key), "key": str(key), "dist": -1.0,
                                             "ntried": 0.0, "naff": self.naff, "is_frontier": 0.0})
            self.I.add_edge_unchecked(self.p, "knows", nid)
            self.by_key[key] = nid; self.tried[key] = set()
        return self.by_key[key], key

    def observe(self, prev, action, new):
        pc, pk = self.cfg(prev); nc, nk = self.cfg(new)
        if action not in self.tried[pk]:                       # a new affordance tried from this config
            self.tried[pk].add(action)
            self.I.set_attr(pc, "ntried", float(len(self.tried[pk])))
        if nk != pk:                                           # a real move (not a slide-into-wall no-op)
            mv = self.s.add_node("Move", {"action": action})
            self.I.add_edge_unchecked(pc, "has_move", mv); self.I.add_edge_unchecked(mv, "to", nc)

    def plan_from(self, pose):
        for nid in self.by_key.values():                      # dynamic: reset the field and re-flood
            self.I.set_attr(nid, "dist", -1.0); self.I.set_attr(nid, "is_frontier", 0.0)
        cur, _ = self.cfg(pose); self.I.set_attr(cur, "dist", 0.0)
        self.I.set_attr(self.p, "phase", 0.0); self.I.run_rules()   # phase 0: flood the dist field to steady state
        self.I.set_attr(self.p, "phase", 1.0); self.I.run_rules()   # phase 1: judge frontier / closed on the settled field
        return cur

    def route_to_frontier(self, cur):
        """Read the M-waypoint route off the dist field by descent (mechanical, like hop-follows-gradient)."""
        fr = next((c for c in self.by_key.values()
                   if self.s.node(c)["attrs"].get("is_frontier") == 1.0), None)
        if fr is None:
            return None, []
        path = [fr]; node = fr
        while self.s.node(node)["attrs"].get("dist", 0.0) > 0.0:
            d = self.s.node(node)["attrs"]["dist"]
            pred = None
            for mv in self.I.in_neighbours(node, "to"):
                for c1 in self.I.in_neighbours(mv, "has_move"):
                    if self.s.node(c1)["attrs"].get("dist") == d - 1.0:
                        pred = c1; break
                if pred:
                    break
            if pred is None:
                break
            path.append(pred); node = pred
        path.reverse()
        return fr, [tuple(self.s.node(c)["attrs"]["pose"]) for c in path]


def run_demo(title, naff, transitions, start, donkey):
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    for r in (FLOOD, FRONTIER, CLOSED):
        a.inner.add_rule(r)
    ms = MoveSpace(a, naff)
    for prev, action, new in transitions:
        ms.observe(prev, action, new)
    cur = ms.plan_from(start)
    closed = a.s.node(ms.p)["attrs"].get("closed") == 1.0
    fr, route = ms.route_to_frontier(cur)
    nconf = len(ms.by_key)
    print(f"\n[{title}]  configs learned: {nconf}  dims: {len(start)}  naffordances: {int(naff)}")
    if closed:
        hyp = next(iter(a.inner.neighbours(ms.p, "minted")), None)
        kind = a.s.node(hyp)["attrs"].get("kind") if hyp else "?"
        print(f"  CLOSED move-space — movement exhausted. Minted hypothesis: {kind!r}")
        print("  -> the agent stops bouncing and concludes the way forward is INTERACTION, not motion.")
        return ("closed", None)
    print(f"  frontier: {fr and tuple(a.s.node(fr)['attrs']['pose'])}  "
          f"M-waypoint route ({len(route)-1} moves): {route}")
    return ("route", route)


def main():
    donkey = {"n": 0}
    print("=" * 96)
    print("MOVE-SPACE PLANNER — N-dim, adjustable-scale, M-waypoint routes, closed-detection (graph-native)")
    print("=" * 96)

    # (1) ls20-like CLOSED chamber: a 5-slider stops only at 4 corners; every action from each corner has
    #     been tried (-> all explored) and leads only among the 4. Movement is exhausted.
    A0, B, C, D = (0, 0), (0, 5), (4, 0), (4, 5)
    chamber = [(A0, "Right", B), (A0, "Down", C), (A0, "Up", A0), (A0, "Left", A0),
               (B, "Left", A0), (B, "Down", D), (B, "Up", B), (B, "Right", B),
               (C, "Up", A0), (C, "Right", D), (C, "Down", C), (C, "Left", C),
               (D, "Up", B), (D, "Left", C), (D, "Down", D), (D, "Right", D)]
    r1 = run_demo("ls20-like CLOSED chamber (5-slider, 4 corners)", 4, chamber, A0, donkey)

    # (2) OPEN maze: a corridor of slide-stops; the near configs are fully explored (every action tried,
    #     most are slide-into-wall no-ops), so the only OPEN config is the far end -> a 3-waypoint route.
    P = [(0, 0), (0, 5), (0, 10), (0, 15)]
    maze = [(P[0], "Right", P[1]), (P[0], "Left", P[0]), (P[0], "Up", P[0]), (P[0], "Down", P[0]),
            (P[1], "Left", P[0]), (P[1], "Right", P[2]), (P[1], "Up", P[1]), (P[1], "Down", P[1]),
            (P[2], "Left", P[1]), (P[2], "Right", P[3]), (P[2], "Up", P[2]), (P[2], "Down", P[2]),
            (P[3], "Left", P[2])]                                   # P[3] reached, only Left tried -> OPEN
    r2 = run_demo("OPEN maze (corridor of slide-stops)", 4, maze, P[0], donkey)

    # (3) 3-D space with MIXED move scales (adjustable scale): +x by 5, then +z by 3 -> N-dim route. Near
    #     configs fully explored (6 affordances, untried ones are no-ops); only the far config is OPEN.
    Q0, Q1, Q2 = (0, 0, 0), (5, 0, 0), (5, 0, 3)
    space3d = [(Q0, "+x", Q1), (Q0, "-x", Q0), (Q0, "+y", Q0), (Q0, "-y", Q0), (Q0, "+z", Q0), (Q0, "-z", Q0),
               (Q1, "-x", Q0), (Q1, "+z", Q2), (Q1, "+x", Q1), (Q1, "-z", Q1), (Q1, "+y", Q1), (Q1, "-y", Q1),
               (Q2, "-z", Q1)]                                      # Q2 reached, only -z tried -> OPEN
    r3 = run_demo("3-D space, mixed scales (+x=5, +z=3)", 6, space3d, Q0, donkey)

    print("\n" + "=" * 96)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = (r1[0] == "closed" and r2[0] == "route" and len(r2[1]) == 4 and
          r3[0] == "route" and len(r3[1][0]) == 3)
    print(f"  {'PASS' if ok else 'FAIL'} — one graph-native planner: it RECOGNISED the closed chamber (the")
    print("  ls20 trap, solved by reasoning not bouncing -> mint an interaction hypothesis), planned an")
    print("  M-waypoint route in the open maze, and routed in 3-D under mixed move SCALES. The dist field is")
    print("  the route shape (scale- and dimension-agnostic), re-flooded each plan = dynamic adjustment.")
    print("  EXTENSION HOOKS (same Config/Move representation, next rung): widen the pose vector with")
    print("  orient/scale dims for ROTATION/SQUASH affordances (bounding box transforms), and with a tuple")
    print("  of Z poses for GROUPS/RTS (joint configs) — FLOOD/FRONTIER/CLOSED are unchanged.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
