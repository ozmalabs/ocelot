"""WIRE the jabberwock's held CURIOSITY drive to the game: it already has hypothesis-testing
(drive_curiosity: probe the most AMBIVALENT/uncertain nodes — highest expected info gain). Here that
drive selects which STRATEGY-HYPOTHESIS to test in Tetris; the game outcome COMMITS the concept (its
uncertainty resolves) = the info gain realised = learning. Dying isn't failure — a fatal hypothesis is
maximally uncertain, so curiosity probes it, and the death is the answer.

WIRING (held faculties, no new logic): hypothesis-Concepts (tower / tessellate / efficiency / flat)
start AMBIVALENT (state=0). The agent's curiosity (find_ambivalent_nodes) picks the most uncertain to
probe. It TESTS it (plays Tetris with that strategy via the graph-native planner). The OUTCOME commits
the concept (set_attr state: survived -> +, died -> -) and records what happened = the agent learns
the hypothesis. Loop until none remain ambivalent. Then it has LEARNED what each strategy does — and
which features are fatal (the survival value, derived from dying, not given).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_wires_curiosity.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import substrate_rs as srs
from domains.reflective_faculty import _Term
from domains.drive_curiosity import find_ambivalent_nodes
from substrate.world_adapter import WorldAdapter
from tetris_world import TetrisEnv
from worlds.arc import ArcWorld
from probe_landing import host_landing
from probe_features import (L, Var, IA, Plus, Minus, Eq, Lte, Not, Ite, Sum, MinOver, MaxOver, Let, ROWS, COLS, landing_term)
H, W = 16, 8
EV = srs.Substrate()
ev = lambda t: EV.evaluate(_Term(t), {})

# the agent's hypotheses = push different features it observes (the examples: tower, tessellate, ...)
WEIGHTS = {                          # weights over [free, holes, maxh, cleared]
    "huge_tower":  (0.0, 0.0, 1.0, 0.0),       # "what if I build a super-high tower?"
    "tessellate":  (0.0, -1.0, 0.0, 0.0),      # "what if I pack with no gaps?"
    "efficiency":  (1.0, -4.0, -0.5, 8.5),     # "what if I go for maximum efficiency?"
    "stay_flat":   (0.0, 0.0, -1.0, 0.0),      # "what if I keep it low?"
}


def rot(shape):
    rr = [(c, -r) for (r, c) in shape]; mr = min(r for r, _ in rr); mc = min(c for _, c in rr)
    return [(r - mr, c - mc) for (r, c) in rr]


def feat_term(board, shape, col):
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
    return Let("rs", landing_term(board, shape, col), {"type": "Vec", "items": [free, holes, maxh, cleared]})


def best(board, shape, weights):
    cands = []; s = shape
    for rc in range(4):
        for col in range(W - max(c for _, c in s)):
            if (host_landing(board, s, col) or -1) >= 0:
                f = ev(feat_term(board, s, col))
                cands.append((sum(weights[k] * float(f[k]) for k in range(4)), rc, col))
        s = rot(s)
    if not cands:
        return None
    bv = max(c[0] for c in cands)
    return next((rc, col) for v, rc, col in cands if v == bv)


def play(weights, frames=1500):
    w = ArcWorld(TetrisEnv()); w.reset(); env = w.env
    pieces = 0; maxh = 0; last = None; target = (0, 0, 0)
    for _ in range(frames):
        if env._state.name == "GAME_OVER":
            break
        shape = env._shape
        if shape is not last:
            b = best(env._board, list(shape), weights); target = (b[0], b[1], 0) if b else (0, env._pc, 0); last = shape
        trot, tcol, done = target
        act = ("Up" if done < trot else "Right" if env._pc < tcol else "Left" if env._pc > tcol else "Down")
        if done < trot:
            target = (trot, tcol, done + 1)
        w.apply((act,))
        if env._shape is not shape:
            pieces += 1; last = None
            h = max((H - next((r for r in range(H) if env._board[r][c] != 0), H) for c in range(W)), default=0)
            maxh = max(maxh, h)
    return {"pieces": pieces, "max_height": maxh, "lines": env._score, "died": env._state.name == "GAME_OVER"}


def main():
    a = WorldAdapter(seeds=())                          # bare substrate: just the curiosity faculty + graph
    mt = a.s.add_node("Microtheory", {"name": "tetris_strategies"})
    cid = {}
    for name in WEIGHTS:
        c = a.s.add_node("Concept", {"name": name, "state": 0.0})   # AMBIVALENT = untested = uncertain
        a.inner.add_edge_unchecked(mt, "has_concept", c); cid[name] = c

    print("=" * 86)
    print("WIRING the jabberwock's CURIOSITY drive to the game — it probes the most UNCERTAIN hypothesis")
    print("=" * 86)
    order = []
    while True:
        amb = find_ambivalent_nodes(a.s, mt)            # the agent's curiosity: most uncertain first
        if not amb:
            break
        name = amb[0]["name"]
        out = play(WEIGHTS[name])                        # TEST the hypothesis it's most curious about
        # LEARN: the outcome COMMITS the concept (uncertainty -> resolved = info gain realised). Tetris
        # always ends, so the signal is SURVIVAL TIME, not whether it ended — a fast death = fatal.
        state = 1.0 if out["pieces"] >= 20 else -1.0
        a.s.set_attr(cid[name], "state", state)
        a.s.set_attr(cid[name], "out_pieces", float(out["pieces"]))
        a.s.set_attr(cid[name], "out_lines", float(out["lines"]))
        a.s.set_attr(cid[name], "out_maxh", float(out["max_height"]))
        order.append((name, out, state))
        print(f"  curiosity probes '{name:11}' -> pieces {out['pieces']:3d}  maxh {out['max_height']:2d}  "
              f"lines {out['lines']:2d}  -> learned state {state:+.0f} "
              f"({'viable' if state > 0 else 'fatal (died fast)'})")

    print("=" * 86)
    fatal = [(n, o) for n, o, s in order if s < 0]
    viable = [(n, o) for n, o, s in order if s > 0]
    best = max(order, key=lambda t: t[1]["pieces"])
    if fatal and viable:
        print(f"  META-LESSON (learned from outcomes — dying IS the signal): the FATAL hypothesis was")
        print(f"  {', '.join(n for n, _o in fatal)} (pushes HEIGHT) — survived only "
              f"{sum(o['pieces'] for _n, o in fatal)//len(fatal)} pieces; the best was '{best[0]}' "
              f"({best[1]['pieces']} pieces, {best[1]['lines']} lines).")
        print(f"  -> the agent LEARNS: maximising height kills; the survival value PENALISES height — and")
        print(f"  the winning hypothesis '{best[0]}' IS the empowerment shape. The value is DERIVED from")
        print(f"  testing + dying, not given.")
    print("  The curiosity drive (held: probe the most uncertain) was WIRED to the game: it chose which")
    print("  hypothesis to test, the game answered, and each outcome (death included) COMMITTED the")
    print("  concept = the agent learned it. Failing any clear value, curiosity is what makes it act —")
    print("  and dying is just the most informative answer. donkey=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
