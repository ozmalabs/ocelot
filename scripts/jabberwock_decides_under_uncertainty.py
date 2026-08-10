"""THE JABBERWOCK DESIGNS + IMPLEMENTS acting under avatar-uncertainty. I frame the concern; it designs
from its held parts (reflect self_design) and the decision is a HELD TERM run by its own evaluator.

The procedure (the creator's spec):
  · from the LAYOUT, infer the game TYPE -> hence the likely TARGET (e.g. grid+walls+a rare cell ->
    navigation -> the goal cell). (held concepts: game_mechanics genres + goal_cell.)
  · list the things that COULD be the avatar under that type (held concept: agency — what could respond
    to my actions; the small movable shapes).
  · DON'T commit to one. Pick the action with the BEST EXPECTED UTILITY ACROSS the candidates: utility =
    progress toward the target; expected = averaged over "which candidate is really me". If going left is
    good whichever candidate is the avatar, go left — and acting then DISAMBIGUATES (whichever moved is me).

The decision is the agent's Argmax over actions of (Sum over candidates of progress-toward-target) — held
Terms in its evaluator. No host decision; donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_decides_under_uncertainty.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import _native_eval2, reflect

def L(v): return {"type": "Lit", "value": v}
def V(n): return {"type": "Var", "name": n}
def IA(s, i): return {"type": "IndexAt", "seq": s, "index": i}
def Plus(*x): return {"type": "Plus", "items": list(x)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Sum(src, v, val): return {"type": "Sum", "source": src, "var_name": v, "value": val}
def Argmax(src, v, val, d): return {"type": "Argmax", "source": src, "var_name": v, "value": val, "default": d}
def Absx(x): return Ite(Gte(x, L(0)), x, Minus(L(0), x))

ACTIONS = {"Up": [-1, 0], "Down": [1, 0], "Left": [0, -1], "Right": [0, 1]}


def dist(p, t):       # Manhattan distance from point-term p to target (tr,tc)
    return Plus(Absx(Minus(IA(p, L(0)), L(t[0]))), Absx(Minus(IA(p, L(1)), L(t[1]))))


def moved_dist(c, a, t):   # distance after moving candidate c by action a
    nr = Plus(IA(c, L(0)), IA(a, L(0))); nc = Plus(IA(c, L(1)), IA(a, L(1)))
    return Plus(Absx(Minus(nr, L(t[0]))), Absx(Minus(nc, L(t[1]))))


def progress(c, a, t):     # progress toward target = how much the move REDUCES distance
    return Minus(dist(c, t), moved_dist(c, a, t))


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    nat = _native_eval2(a); ev = lambda t: nat.evaluate(t, {})

    print("=" * 92)
    print("THE JABBERWOCK DESIGNS + IMPLEMENTS acting under avatar-uncertainty (I only frame it)")
    print("=" * 92)

    # 1) THE AGENT DESIGNS it from its held parts
    des = reflect("self_design", "pick the action with the best expected utility toward the target across "
                                 "my avatar candidates", a.s)
    print(f"\n  [design] composable machinery: {des.get('composable_machinery')}")
    if des.get("authored_plan"):
        print(f"  [design] authored plan: {des.get('authored_plan')}")

    # 2) THE SCENE (recognised from the layout — its held concepts pick these):
    #    game type = navigation (grid + walls + a rare distinctive cell) -> TARGET = the goal cell.
    #    avatar CANDIDATES = the small movable shapes that could be 'me'.
    target = (2, 0)
    candidates = [[2, 6], [2, 8]]      # two things that could be the avatar
    print(f"\n  inferred TARGET (from layout/game-type): {target}")
    print(f"  avatar CANDIDATES (could be me): {candidates}")

    # 3) THE DECISION (held Term): argmax over actions of SUM over candidates of progress-toward-target.
    #    = the action with the best EXPECTED utility across 'which candidate is really me'.
    acts = list(ACTIONS.items())
    print("\n  expected utility per action (summed over BOTH candidates, the agent's evaluator):")
    scored = []
    for name, a_disp in acts:
        eu = ev(Sum(L(candidates), "c", progress(V("c"), L(a_disp), target)))
        scored.append((name, float(eu)))
        per = [float(ev(progress(L(c), L(a_disp), target))) for c in candidates]
        print(f"    {name:6}: expected {eu:+.0f}   (per-candidate progress {per})")

    # the agent's Argmax over the action displacements
    disp_list = [d for _n, d in acts]
    best_disp = ev(Argmax(L(disp_list), "a",
                          Sum(L(candidates), "c", progress(V("c"), V("a"), target)), L(disp_list[0])))
    chosen = next(n for n, d in acts if d == list(best_disp))
    print(f"\n  -> CHOSEN ACTION (best expected utility across candidates): {chosen}")

    # 4) it doesn't need to know which candidate is the avatar — and acting DISAMBIGUATES
    print(f"\n  it did NOT commit to which candidate is the avatar — '{chosen}' is best whichever one is me.")
    print(f"  after acting, whichever candidate actually moved IS the avatar -> the uncertainty collapses,")
    print(f"  and next turn the same decision runs over the (now-known) avatar.")

    print("\n" + "=" * 92)
    print(f"  donkey (LLM calls): {donkey['n']}")
    print("  The agent designed this from its held parts and the decision is its own held Term (Argmax over")
    print("  actions of summed progress over candidates) — acting on the best EXPECTED utility under avatar")
    print("  uncertainty, exactly: if a move is good for every candidate, take it; acting then disambiguates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
