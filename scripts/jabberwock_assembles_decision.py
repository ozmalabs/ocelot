"""ASSEMBLE THE FULL N-DIMENSIONAL DECISION TERM from the four proven graph-native rungs, materialise it as
graph data, and EXECUTE it in a rule (EvalSubgraph) -> chosen_action. donkey=0.

The decision (acting under avatar-uncertainty, N-dimensional):
  chosen_action = name of  Argmax over affordances act of
                              Sum over avatar-candidates c of
                                 progress(c, act)
  progress(c,act) = dist(c.pos, goal.pos) - dist_moved(c.pos, act.delta, goal.pos)
  dist        = Sum over dims i of  absdiff(c.pos[i],            goal.pos[i])      <- rung: Sum-wrap of body
  dist_moved  = Sum over dims i of  absdiff(c.pos[i]+act.delta[i], goal.pos[i])    <- rung: +delta body
Each piece is exactly what the rungs synthesise: absdiff (GENERATE-composes-subgraphs), Sum-over-dims
(aggregation-body), Minus (binary compose), Sum-over-candidates + Argmax-over-affordances (aggregation
with a different source). Here we ASSEMBLE that known structure and VERIFY the whole computes the right
action graph-natively (EvalSubgraph in run_rules). N-dimensional: dist sums over game.dims (any length).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_assembles_decision.py
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
def Atr(node, k): return {"type": "Attr", "node": node, "key": k}
def L(v): return {"type": "Lit", "value": v}
def IA(seq, idx): return {"type": "IndexAt", "seq": seq, "index": idx}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Ite(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}
def Nb(node, et): return {"type": "Neighbours", "node": node, "edge_type": et}
def Pick(src): return {"type": "Pick", "source": src}
def Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var, "value": val}
def Argmax(src, var, val, d): return {"type": "Argmax", "source": src, "var_name": var, "value": val, "default": d}
def Eval(node): return {"type": "EvalSubgraph", "node": node}

# --- assemble the decision Term from the rungs' pieces ---
def absdiff(a, b):                                   # GENERATE-composes-subgraphs rung (binary macro)
    return Ite(Gte(a, b), Minus(a, b), Minus(b, a))
GOAL = Pick(Nb(V("game"), "has_goal"))               # the recognised target
DIMS = Atr(V("game"), "dims")                        # the coordinate axes (any length -> N-dimensional)
def cpos_i(): return IA(Atr(V("c"), "pos"), V("i"))
def gpos_i(): return IA(Atr(GOAL, "pos"), V("i"))
def moved_i(): return Plus(cpos_i(), IA(Atr(V("act"), "delta"), V("i")))
DIST = Sum(DIMS, "i", absdiff(cpos_i(), gpos_i()))            # aggregation-body rung (Sum over dims)
DIST_MOVED = Sum(DIMS, "i", absdiff(moved_i(), gpos_i()))     # same rung, +delta body
PROGRESS = Minus(DIST, DIST_MOVED)                            # binary compose
EU = Sum(Nb(V("game"), "avatar_candidate"), "c", PROGRESS)   # aggregation over candidates
DECISION = Argmax(Nb(V("game"), "affordance"), "act", EU, L(0))  # aggregation (Argmax) over affordances
CHOSEN = Atr(DECISION, "name")                                # chosen_action = the best affordance's name

ACTIONS = {"Up": [-1, 0], "Down": [1, 0], "Left": [0, -1], "Right": [0, 1]}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner
    print("=" * 94)
    print("ASSEMBLE THE FULL N-DIMENSIONAL DECISION TERM from the rungs, then execute it graph-natively")
    print("=" * 94)

    # materialise the assembled decision Term as graph data (the rungs' add_term_subgraph primitive)
    root = I.add_term_subgraph(CHOSEN)
    print(f"  assembled decision Term materialised as a subgraph (root {root})")

    # the perceived scene (N-dimensional pos/delta vectors)
    game = s.add_node("WorldInstance", {"world_type": "Game", "dims": [0.0, 1.0], "chosen_action": ""})
    I.add_edge_unchecked(game, "decision_term", root)
    goal = s.add_node("Cell", {"pos": [2.0, 0.0]}); I.add_edge_unchecked(game, "has_goal", goal)
    for nm, d in ACTIONS.items():
        aff = s.add_node("Affordance", {"name": nm, "delta": [float(x) for x in d]})
        I.add_edge_unchecked(game, "affordance", aff)
    for pos in ([2.0, 6.0], [2.0, 8.0]):
        cand = s.add_node("Region", {"pos": pos}); I.add_edge_unchecked(game, "avatar_candidate", cand)
    print("  scene: target (2,0); candidates (2,6),(2,8); affordances Up/Down/Left/Right; dims [0,1]")

    # execute the assembled Term in a RULE (EvalSubgraph) -> chosen_action
    DECIDE = {"id": "decide", "name": "decide",
              "match": [["game", "has_goal", "g"]],
              "effects": [["set_attr", "game", "chosen_action",
                           {"__term__": Eval(Pick(Nb(V("game"), "decision_term")))}]]}
    I.add_rule(DECIDE)
    I.run_rules()
    chosen = s.node(game)["attrs"].get("chosen_action")
    print(f"\n  the assembled decision Term (run via EvalSubgraph in run_rules) wrote chosen_action = {chosen!r}")

    print("\n" + "=" * 94)
    print(f"  donkey (LLM calls): {donkey['n']}")
    ok = chosen == "Left"
    print(f"  {'PASS' if ok else 'FAIL'} — the full N-dimensional decision Term, ASSEMBLED from the four graph-")
    print("  native rungs (absdiff compose / Sum-over-dims aggregation / Minus / Sum-over-candidates +")
    print("  Argmax-over-affordances), runs in the agent's evaluator and chooses Left (best expected utility")
    print("  across the avatar candidates). Generate -> wrap -> compose -> aggregate -> decide, all graph-native.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
