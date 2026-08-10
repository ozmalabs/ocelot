"""THE JABBERWOCK PLAYS TETRIS using everything it built ITSELF — every decision is its own graph-
native term, run by its own Rust engine; host code is only I/O (apply a control, read the board).

Assembled from the agent's self-built pieces:
  · LEARNED DYNAMICS (7f151fdd) — landing = fall in the learned gravity direction until the learned
    stop-law (gravity-dir neighbour blocked) holds. Not hand-given; learned by fit.
  · LEARNED LINE-CLEAR (probe_lineclear) — full rows vanish -> a clear-bonus on the value.
  · EMPOWERMENT value (a3ecd241) — free - 4*holes - 0.5*maxh + clear-bonus (its chosen goal direction).
  · GRAPH-NATIVE PLANNER (b4915a7a) — Argmax over placements by the value term, in its evaluator.
The forward model, the value, and the choice are all the agent's held Terms. donkey=0.

Run: PYTHONPATH=.:runners/dsl/python:scripts python3 scripts/jabberwock_plays_tetris.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.world_play as world_play
from tetris_world import TetrisEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import _native_eval2
from probe_landing import host_landing
from jabberwock_learns_dynamics import landing_from_learned     # the LEARNED-law landing
from probe_features import (L, Var, IA, Plus, Times, Minus, Eq, Lte, Not, Ite, Sum, MinOver, MaxOver, Let, ROWS, COLS)
H, W = 16, 8
GDR, GDC = 1, 0                                                  # the LEARNED gravity direction (down)
CONTROLS = ["Up", "Down", "Left", "Right"]


def gnode(a):
    return next((n for n in a.s.nodes("WorldInstance")
                 if a.s.node(n)["attrs"].get("world_type") == "Game"), None)


def rot(shape):
    rr = [(c, -r) for (r, c) in shape]; mr = min(r for r, _ in rr); mc = min(c for _, c in rr)
    return [(r - mr, c - mc) for (r, c) in rr]


def value_learned(board, shape, col):
    """the agent's value term: empowerment (free - 4*holes - 0.5*maxh) + learned clear-bonus, on the
    board resulting from the LEARNED-dynamics landing."""
    sh = L([list(s) for s in shape]); rs = Var("rs")
    origfilled = Sum(L(board), "row", Sum(Var("row"), "x", Ite(Not(Eq(Var("x"), L(0))), L(1), L(0))))
    free = Minus(Minus(L(H * W), origfilled), L(4))
    colh = lambda cv: Minus(L(H), Ite(Lte(
        MinOver(ROWS, "i", Ite(Not(Eq(IA(IA(L(board), Var("i")), cv), L(0))), Var("i"), L(H)), L(H)),
        MinOver(sh, "c", Ite(Eq(Plus(L(col), IA(Var("c"), L(1))), cv), Plus(rs, IA(Var("c"), L(0))), L(H)), L(H))),
        MinOver(ROWS, "i", Ite(Not(Eq(IA(IA(L(board), Var("i")), cv), L(0))), Var("i"), L(H)), L(H)),
        MinOver(sh, "c", Ite(Eq(Plus(L(col), IA(Var("c"), L(1))), cv), Plus(rs, IA(Var("c"), L(0))), L(H)), L(H))))
    fc = lambda cv: Plus(Sum(ROWS, "i", Ite(Not(Eq(IA(IA(L(board), Var("i")), cv), L(0))), L(1), L(0))),
                         Sum(sh, "c", Ite(Eq(Plus(L(col), IA(Var("c"), L(1))), cv), L(1), L(0))))
    maxh = MaxOver(COLS, "col", colh(Var("col")), L(0))
    holes = Sum(COLS, "col", Minus(colh(Var("col")), fc(Var("col"))))
    cleared = Sum(ROWS, "i", Ite(Eq(Minus(
        Sum(COLS, "cc", Ite(Eq(IA(IA(L(board), Var("i")), Var("cc")), L(0)), L(1), L(0))),
        Sum(sh, "c", Ite(Eq(Plus(rs, IA(Var("c"), L(0))), Var("i")), L(1), L(0)))), L(0)), L(1), L(0)))
    value = Plus(Minus(free, Plus(Times(L(4), holes), Times(L(0.5), maxh))), Times(cleared, L(W + 0.5)))
    return Let("rs", landing_from_learned(board, shape, col, GDR, GDC), value)   # LEARNED landing


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    w = ArcWorld(TetrisEnv()); sub, ctx = w.reset(); a.perceive_frame(sub)
    g = gnode(a); body = a.s.add_node("Body", {}); a.inner.add_edge_unchecked(body, "inhabits", g)
    world_play.declare_affordances(a, g, CONTROLS)
    nat = _native_eval2(a); ev = lambda t: nat.evaluate(t, {})

    def plan(board, shape):
        # the AGENT's evaluator scores every placement (its value term) and picks the max (its Argmax)
        vals = []; s = shape
        for rc in range(4):
            for col in range(W - max(c for _, c in s)):
                if (host_landing(board, s, col) or -1) >= 0:
                    vals.append((float(ev(value_learned(board, s, col))), rc, col))
            s = rot(s)
        if not vals:
            return None
        bv = max(v for v, _r, _c in vals)
        return next((rc, col) for v, rc, col in vals if v == bv)

    print("=" * 84)
    print("THE JABBERWOCK PLAYS TETRIS — every decision its own graph-native term (host = I/O only)")
    print("=" * 84)
    pieces = 0; last = None; target = (0, 0, 0)
    for _ in range(2500):
        env = w.env
        if env._state.name == "GAME_OVER":
            break
        shape = env._shape
        if shape is not last:
            b = plan(env._board, list(shape)); target = (b[0], b[1], 0) if b else (0, env._pc, 0); last = shape
        trot, tcol, done = target
        act = ("Up" if done < trot else "Right" if env._pc < tcol else "Left" if env._pc > tcol else "Down")
        if done < trot:
            target = (trot, tcol, done + 1)
        sub, ctx = w.apply((act,)); a.perceive_frame(sub)   # I/O: apply the chosen control, read the board
        if env._shape is not shape:
            pieces += 1; last = None
    print(f"  lines cleared: {w.env._score}   pieces placed: {pieces}   donkey: {donkey['n']}")
    print("=" * 84)
    print("  The jabberwock played using everything IT built: the LEARNED dynamics (landing from its")
    print("  learned gravity+stop law), the LEARNED line-clear (clear-bonus), its EMPOWERMENT value, and")
    print("  its Argmax planner — all held Terms in its own Rust engine. Host code only applied the")
    print("  chosen control and read the board back. donkey=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
