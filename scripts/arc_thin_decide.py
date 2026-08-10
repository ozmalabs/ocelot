"""THIN ADAPTER + the assembled graph-native DECISION TERM drives ls20. The adapter is mechanical only:
perceive the frame, tell the agent what it `sees` (one edge per perceived feature), declare affordances
(with their displacement vectors), tick, read chosen_action. EVERYTHING else is graph rules:
  MARK_POS  : a seen feature gets pos = [cy, cx]                       (perception -> N-d position)
  MARK_CAND : a seen MOVER is an avatar candidate                     (could be me; the agent decides under
              uncertainty across candidates)
  MARK_GOAL : a seen METER is the goal landmark to route toward       (one goal)
  DECIDE    : chosen_action = the ASSEMBLED decision Term (EvalSubgraph) = Argmax over affordances of
              Sum over candidates of (dist - dist_moved), N-dimensional.
No nav logic in the adapter; the agent decides in its own graph + evaluator. donkey=0.

Honest: ls20's true win-goal is unknown, so the routed goal is a perceived landmark (a meter); the point
is that the graph-native decision Term DRIVES the action under avatar-uncertainty, thin-adapter, no logic.

  ulimit -v 12000000
  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_thin_decide.py [--actions 14]
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
_HERE = Path(__file__).resolve().parent; _ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from _arc3_load_key import load_arc_api_key
from arc3_live_env import Arc3LiveEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import jabberwock_assembles_decision as D   # CHOSEN (the assembled decision Term), ACTIONS

def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*x): return {"type": "And", "items": list(x)}
def Not(a): return {"type": "Not", "arg": a}
def Vec(*x): return {"type": "Vec", "items": list(x)}
def Nb(n, et): return {"type": "Neighbours", "node": V(n), "edge_type": et}
def Pick(src): return {"type": "Pick", "source": src}
def Eval(node): return {"type": "EvalSubgraph", "node": node}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}

MARK_POS = {"id": "mark_pos", "name": "mark_pos", "match": [["game", "sees", "f"]],
            "effects": [["set_attr", "f", "pos", {"__term__": Vec(A("f", "cy"), A("f", "cx"))}]]}
MARK_CAND = {"id": "mark_cand", "name": "mark_cand", "match": [["game", "sees", "f"]],
             "where": Eq(A("f", "kind"), L("mover")),
             "effects": [["add_edge", "game", "avatar_candidate", "f"]]}
MARK_GOAL = {"id": "mark_goal", "name": "mark_goal", "match": [["game", "sees", "f"]],
             "where": And(Eq(A("f", "kind"), L("meter")),
                          Not(Exists(Nb("game", "has_goal"), "_g", L(True)))),
             "effects": [["add_edge", "game", "has_goal", "f"]]}
DECIDE = {"id": "decide", "name": "decide", "match": [["game", "has_goal", "g"]],
          "where": Exists(Nb("game", "avatar_candidate"), "_c", L(True)),
          "effects": [["set_attr", "game", "chosen_action",
                       {"__term__": Eval(Pick(Nb("game", "decision_term")))}]]}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--game", default="ls20-9607627b"); ap.add_argument("--actions", type=int, default=14)
    args = ap.parse_args()
    if not load_arc_api_key():
        print("no key"); return 1
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner

    root = I.add_term_subgraph(D.CHOSEN)                       # the assembled decision Term as graph data
    affs = {nm: s.add_node("Affordance", {"name": nm, "delta": [float(x) for x in d]}) for nm, d in D.ACTIONS.items()}
    for r in (MARK_POS, MARK_CAND, MARK_GOAL, DECIDE):
        I.add_rule(r)
    print("decision Term wired into the thin adapter; native eye:", hasattr(I, "segment"), flush=True)

    env = Arc3LiveEnv(args.game); world = ArcWorld(env)
    sub, ctx = world.reset(); a.perceive_frame(sub)
    drove = 0
    for i in range(args.actions):
        feats = [s.node(f)["attrs"] for f in s.nodes("Feature")]
        kinds = {}
        for fa in feats:
            kinds[fa.get("kind")] = kinds.get(fa.get("kind"), 0) + 1
        # adapter (mechanical): fresh game, tell it what it sees, declare affordances + dims + decision Term
        game = s.add_node("WorldInstance", {"world_type": "Game", "dims": [0.0, 1.0], "chosen_action": ""})
        I.add_edge_unchecked(game, "decision_term", root)
        for aff in affs.values():
            I.add_edge_unchecked(game, "affordance", aff)
        for f in s.nodes("Feature"):
            if s.node(f)["attrs"].get("cy") is not None:
                I.add_edge_unchecked(game, "sees", f)
        t = time.time()
        I.run_rules()                                          # the agent marks + decides, graph-native
        action = s.node(game)["attrs"].get("chosen_action") or ""
        ncand = len(list(I.neighbours(game, "avatar_candidate")))
        bootstrap = not action
        if bootstrap:
            action = ["Up", "Right", "Down", "Left"][i % 4]
        else:
            drove += 1
        sub, ctx = world.apply((action,), reasoning=f"graph-native decision Term: {ncand} avatar-candidates, "
                                                     f"routing under uncertainty -> {action}")
        a.perceive_frame(sub)
        print(f"  {i+1:3} {action:6} ({(time.time()-t)*1000:4.0f}ms) "
              f"{'DECISION-TERM' if not bootstrap else 'bootstrap   '} | candidates {ncand} kinds {kinds}", flush=True)
        if ctx.get("over") or ctx.get("won"):
            print("  game", "WON" if ctx.get("won") else "OVER"); break

    print(f"\ntotal: the graph-native decision Term chose the action on {drove}/{args.actions} turns "
          f"(rest = host bootstrap before movers/goal were perceived). donkey={donkey['n']}. No nav logic in "
          f"the adapter — the agent marked candidates/goal and DECIDED in its own graph + evaluator.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
