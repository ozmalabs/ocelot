"""MOVE-SPACE PLANNER (reusable) — the general configuration-space planner, graph-native, that arc_run
uses instead of the blind pocket_escape cycle.

It learns a move-space graph FROM OBSERVED transitions (Config = an N-dim REST pose; Move = an affordance
that takes one config to another at a LEARNED scale), and CHOOSES the next action by graph rules:

  CHOOSE_EXPAND : the current config still has an UNTRIED affordance -> press the lowest-order untried one
                  (systematic expansion of the move-space, NOT a blind U/R/D/L cycle).
  CHOOSE_ROUTE  : the current config is fully tried but an OPEN config is reachable -> press the move that
                  descends dist-to-the-nearest-open (an M-waypoint route, one step at a time).
  CLOSED        : no open config is reachable -> movement is EXHAUSTED -> mint a Hypothesis that the way
                  forward is a NON-MOVEMENT affordance (interaction), and emit "" so the host switches.

Two-phase run (flood the dist fields to steady state, then choose) avoids the fixpoint race. The construction
from observation is mechanical ingest (cached dedup); every CHOICE is a graph rule. donkey=0.

Self-test (slider sim): PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/move_space_planner.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Anode(node, k): return {"type": "Attr", "node": node, "key": k}
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
def Pick(src): return {"type": "Pick", "source": src}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}

def _td2(mvvar):  # dist-to-open of a move's TARGET config: Pick(Neighbours(move,"to")).dist2
    return Anode(Pick({"type": "Neighbours", "node": V(mvvar), "edge_type": "to"}), "dist2")

# ---- floods (phase 0): build the dist fields over the move graph ---------------------------------
FLOOD = {"id": "msp_flood", "name": "msp_flood",                 # dist FROM the current config (reachability)
    "match": [["c1", "has_move", "mv"], ["mv", "to", "c2"]],
    "where": And(Gte(A("c1", "dist"), L(0.0)),
                 Or(Lt(A("c2", "dist"), L(0.0)), Gt(A("c2", "dist"), Plus(A("c1", "dist"), L(1.0))))),
    "effects": [["set_attr", "c2", "dist", {"__term__": Plus(A("c1", "dist"), L(1.0))}]]}
OPEN_INIT = {"id": "msp_open_init", "name": "msp_open_init",     # OPEN configs are the dist2 sources (dist2=0)
    "match": [["p", "knows", "c"]],
    "where": And(Lt(A("c", "ntried"), A("c", "naff")), Lt(A("c", "dist2"), L(0.0))),
    "effects": [["set_attr", "c", "dist2", 0.0]]}
FLOOD2 = {"id": "msp_flood2", "name": "msp_flood2",              # dist TO the nearest open config (route field)
    "match": [["c", "has_move", "mv"], ["mv", "to", "c2"]],
    "where": And(Gte(A("c2", "dist2"), L(0.0)),
                 Or(Lt(A("c", "dist2"), L(0.0)), Gt(A("c", "dist2"), Plus(A("c2", "dist2"), L(1.0))))),
    "effects": [["set_attr", "c", "dist2", {"__term__": Plus(A("c2", "dist2"), L(1.0))}]]}

# ---- choices (phase 1): the next action, by graph rule ------------------------------------------
CHOOSE_EXPAND = {"id": "msp_expand", "name": "msp_expand",
    "match": [["p", "at_config", "c"], ["p", "affordance", "aff"]],
    "where": And(Eq(A("p", "phase"), L(1.0)), Eq(A("p", "closed"), L(0.0)),
                 Not(Exists(Nb("c", "tried"), "t", Eq(V("t"), V("aff")))),     # aff untried at current
                 Not(Exists(Nb("p", "affordance"), "aff2",                     # ...and lowest-order such
                     And(Not(Exists(Nb("c", "tried"), "t2", Eq(V("t2"), V("aff2")))),
                         Lt(A("aff2", "order"), A("aff", "order")))))),
    "effects": [["set_attr", "p", "ms_action", {"__term__": A("aff", "name")}],
                ["set_attr", "p", "ms_mode", "expand"]]}
CHOOSE_ROUTE = {"id": "msp_route", "name": "msp_route",
    "match": [["p", "at_config", "c"], ["c", "has_move", "mv"], ["mv", "to", "c2"]],
    "where": And(Eq(A("p", "phase"), L(1.0)), Eq(A("p", "closed"), L(0.0)),
                 Gte(A("c", "ntried"), A("c", "naff")),                        # current fully tried
                 Gte(A("c2", "dist2"), L(0.0)),
                 Not(Exists(Nb("c", "has_move"), "mv2",                        # ...descend dist-to-open
                     And(Gte(_td2("mv2"), L(0.0)), Lt(_td2("mv2"), A("c2", "dist2")))))),
    "effects": [["set_attr", "p", "ms_action", {"__term__": A("mv", "action")}],
                ["set_attr", "p", "ms_mode", "route"]]}
CLOSED = {"id": "msp_closed", "name": "msp_closed",
    "match": [["p", "knows", "c0"]],
    "where": And(Eq(A("p", "phase"), L(1.0)), Eq(A("p", "closed"), L(0.0)),
                 Not(Exists(Nb("p", "knows"), "c2",
                     And(Gte(A("c2", "dist"), L(0.0)), Lt(A("c2", "ntried"), A("c2", "naff")))))),
    "effects": [["set_attr", "p", "closed", 1.0], ["set_attr", "p", "ms_mode", "closed"],
                ["set_attr", "p", "ms_action", ""]]}
MINT_HYP = {"id": "msp_mint_hyp", "name": "msp_mint_hyp",        # closed -> the way forward is INTERACTION
    "match": [["p", "knows", "c0"]],
    "where": And(Eq(A("p", "closed"), L(1.0)),
                 Not(Exists(Nb("p", "minted"), "h", L(True)))),
    "effects": [["add_node", "hyp", "Hypothesis", {"kind": "need_non_movement_affordance", "open": 1.0}],
                ["add_edge", "p", "minted", "hyp"]]}

RULES = [FLOOD, OPEN_INIT, FLOOD2, CHOOSE_EXPAND, CHOOSE_ROUTE, CLOSED, MINT_HYP]


class MoveSpacePlanner:
    """Graph-native move-space planner. The host calls observe()/set_current()/plan(); the choice is a rule."""
    def __init__(self, agent, affordances):
        self.a, self.s, self.I = agent, agent.s, agent.inner
        self.p = self.s.add_node("MSPlanner", {"closed": 0.0, "phase": 0.0, "ms_action": "", "ms_mode": ""})
        self.naff = float(len(affordances))
        self.aff_by_name = {}
        for k, name in enumerate(affordances):
            an = self.s.add_node("MSAff", {"name": name, "order": float(k)})
            self.I.add_edge_unchecked(self.p, "affordance", an); self.aff_by_name[name] = an
        self.by_key, self.tried, self.cur_key = {}, {}, None
        for r in RULES:
            self.I.add_rule(r)

    def _cfg(self, pose):
        key = tuple(round(float(x), 3) for x in pose)
        if key not in self.by_key:
            nid = self.s.add_node("Config", {"pose": list(key), "key": str(key), "dist": -1.0,
                                             "dist2": -1.0, "ntried": 0.0, "naff": self.naff})
            self.I.add_edge_unchecked(self.p, "knows", nid)
            self.by_key[key] = nid; self.tried[key] = set()
        return self.by_key[key], key

    def observe(self, prev_pose, action, new_pose):
        pc, pk = self._cfg(prev_pose); nc, nk = self._cfg(new_pose)
        if action not in self.tried[pk]:                       # a newly-tried affordance from this config
            self.tried[pk].add(action)
            self.I.set_attr(pc, "ntried", float(len(self.tried[pk])))
            self.I.add_edge_unchecked(pc, "tried", self.aff_by_name[action])
        if nk != pk:                                           # a real move (not a slide-into-wall no-op)
            mv = self.s.add_node("Move", {"action": action})
            self.I.add_edge_unchecked(pc, "has_move", mv); self.I.add_edge_unchecked(mv, "to", nc)

    def set_current(self, pose):
        for old in list(self.I.neighbours(self.p, "at_config")):
            self.I.remove_edge_unchecked(self.p, "at_config", old)
        cur, key = self._cfg(pose); self.cur_key = key
        self.I.add_edge_unchecked(self.p, "at_config", cur)

    def plan(self):
        """Two-phase: flood the fields, then choose. Returns (action_str, mode) — mode in expand/route/closed."""
        for nid in self.by_key.values():
            self.I.set_attr(nid, "dist", -1.0); self.I.set_attr(nid, "dist2", -1.0)
        cur = self.by_key[self.cur_key]; self.I.set_attr(cur, "dist", 0.0)
        self.I.set_attr(self.p, "closed", 0.0); self.I.set_attr(self.p, "ms_action", "")
        self.I.set_attr(self.p, "ms_mode", "")
        self.I.set_attr(self.p, "phase", 0.0); self.I.run_rules()   # flood dist + dist2
        self.I.set_attr(self.p, "phase", 1.0); self.I.run_rules()   # choose / closed
        at = self.s.node(self.p)["attrs"]
        res = (at.get("ms_action") or "", at.get("ms_mode") or "")
        self.I.set_attr(self.p, "phase", -1.0)                      # neutral: the choice rules don't fire
        return res                                                  # on the host's own run_rules() between plans


# ============================ self-test (slider sim, donkey=0) ====================================
def _slide(walls, pose, dvec, lo, hi):
    r, c = pose; dr, dc = dvec
    while True:
        nr, nc = r + dr, c + dc
        if not (lo <= nr <= hi and lo <= nc <= hi) or (nr, nc) in walls:
            return (r, c)
        r, c = nr, nc


def main():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    DIRS = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}
    AFFS = list(DIRS.keys())
    print("=" * 92)
    print("MOVE-SPACE PLANNER self-test — systematic exploration -> CLOSED (no blind cycle); + routing")
    print("=" * 92)
    donkey = {"n": 0}

    # (1) ls20-like CLOSED slider chamber: a 2x2 open room (walls around). Slider stops at the 4 corners.
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    walls = set()  # open 2x2 room cells (1,1),(1,2),(2,1),(2,2); bounds lo=1 hi=2 -> walls are the bounds
    pl = MoveSpacePlanner(a, AFFS)
    cur = (1, 1); pl.set_current(cur)
    actions, modes, seen = [], [], set()
    for step in range(60):
        act, mode = pl.plan()
        modes.append(mode)
        if mode == "closed":
            break
        new = _slide(walls, cur, DIRS[act], 1, 2)
        pl.observe(cur, act, new); seen.add(new)
        actions.append(act); cur = new; pl.set_current(cur)
    closed = pl.s.node(pl.p)["attrs"].get("closed") == 1.0
    hyp = next(iter(pl.I.neighbours(pl.p, "minted")), None)
    print(f"\n[CLOSED chamber 2x2]  steps to recognise closure: {len(actions)}  configs: {len(pl.by_key)}  "
          f"stops visited: {sorted(seen)}")
    print(f"  actions taken (systematic, not a blind cycle): {actions}")
    print(f"  -> mode={modes[-1]}, closed={closed}, hypothesis={pl.s.node(hyp)['attrs'].get('kind') if hyp else None}")
    # must TERMINATE (recognise closure, not bounce to the cap) having visited every reachable stop. ~16
    # (config,affordance) pairs + a few travel presses; the point is it converges, vs the blind cycle never does.
    d1 = closed and len(actions) < 30 and len(seen) == 4

    # (2) ROUTING: current fully tried, a DISTANT config still open -> CHOOSE_ROUTE steps toward it.
    a2 = WorldAdapter(seeds=()); load_all_seeds(a2)
    a2.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    pl2 = MoveSpacePlanner(a2, AFFS)
    A_, B_, C_, D_ = (0, 0), (0, 5), (0, 10), (0, 15)
    line = [(A_, "Right", B_), (A_, "Left", A_), (A_, "Up", A_), (A_, "Down", A_),
            (B_, "Left", A_), (B_, "Right", C_), (B_, "Up", B_), (B_, "Down", B_),
            (C_, "Left", B_), (C_, "Right", D_), (C_, "Up", C_), (C_, "Down", C_),
            (D_, "Left", C_)]                       # D_ open (only Left tried); A_,B_,C_ fully tried
    for pr, ac, nw in line:
        pl2.observe(pr, ac, nw)
    pl2.set_current(A_)
    act, mode = pl2.plan()
    print(f"\n[ROUTING]  at {A_} (fully tried); only open config is {D_} (3 moves away)")
    print(f"  chosen: action={act!r} mode={mode!r}  (expect 'Right' toward {D_})")
    d2 = (mode == "route" and act == "Right")

    print("\n" + "=" * 92)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = d1 and d2
    print(f"  {'PASS' if ok else 'FAIL'} — the planner EXPLORES systematically (each affordance from each")
    print("  config once) and RECOGNISES the closed chamber -> interaction hypothesis (replacing the blind")
    print("  pocket_escape cycle), and ROUTES one step toward a distant open config. Ready to wire into arc_run.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
