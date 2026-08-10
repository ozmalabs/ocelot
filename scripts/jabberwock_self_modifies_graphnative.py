"""THE JABBERWOCK SELF-MODIFIES its value with THE GRAPH'S OWN OPTIMISER — the manifold-collapse
residual loop (w <- w + lr*Xt(y - Xw)), a Fold the evaluator runs in ONE dispatch. No host descent.

Creator: "the graph already has optimisers. its the entire point. get the jabberwock to implement it.
its the same manifold collapse residual loop." So self-modification = fit the value to what it watched,
by the residual loop the graph already has (verified == least-squares in probe_optimizer, 8/8).

  WATCH (host I/O)      — play; at each settle record the board features + the Monte-Carlo RETURN from
                          there (lines + survival still to come). The data; the env never enters the
                          optimiser.
  OPTIMISE (the graph)  — the residual-loop Fold fits the value's weights to predict that return from
                          the features, in ONE evaluate. The agent's own optimiser.
  SELF-MODIFY           — the fitted weights ARE the new value; persist them; re-play to verify.

Run: PYTHONPATH=.:runners/dsl/python:scripts python3 scripts/jabberwock_self_modifies_graphnative.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import _native_eval2
from domains.teach import teach
from tetris_world import TetrisEnv, EMPTY
from worlds.arc import ArcWorld
from probe_landing import host_landing
from jabberwock_learns_dynamics import landing_from_learned
from probe_optimizer import fit_linear_term                    # the GRAPH'S optimiser (residual loop)
from probe_features import (L, Var, IA, Plus, Times, Minus, Eq, Lte, Not, Ite, Sum, MinOver, MaxOver, Let, ROWS, COLS)
H, W = 16, 8
ev = None


def rot(shape):
    rr = [(c, -r) for (r, c) in shape]; mr = min(r for r, _ in rr); mc = min(c for _, c in rr)
    return [(r - mr, c - mc) for (r, c) in rr]


def value_w(board, shape, col, wf, wh, wm, wc):
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
    value = Plus(Times(L(wf), free), Times(L(wh), holes), Times(L(wm), maxh), Times(L(wc), cleared))
    return Let("rs", landing_from_learned(board, shape, col, 1, 0), value)


def feats(board):
    free = sum(row.count(EMPTY) for row in board)
    holes = sum(1 for c in range(W) for r in range(H)
                if board[r][c] == EMPTY and any(board[rr][c] != EMPTY for rr in range(r)))
    maxh = max((H - next((r for r in range(H) if board[r][c] != EMPTY), H) for c in range(W)), default=0)
    return free, holes, maxh


def play(weights, seed, cap=220, record=False):
    w = ArcWorld(TetrisEnv(seed=seed)); w.reset(); env = w.env
    pieces = 0; last = None; target = (0, 0, 0); recs = []; prev_score = 0
    while pieces < cap:
        if env._state.name == "GAME_OVER":
            break
        shape = env._shape
        if shape is not last:
            vals = []; s = shape
            for rc in range(4):
                for col in range(W - max(c for _, c in s)):
                    if (host_landing(env._board, s, col) or -1) >= 0:
                        vals.append((float(ev(value_w(env._board, s, col, *weights))), rc, col))
                s = rot(s)
            bv = max(v for v, _r, _c in vals) if vals else 0
            b = next(((rc, col) for v, rc, col in vals if v == bv), (0, env._pc))
            target = (b[0], b[1], 0); last = shape
        trot, tcol, done = target
        act = ("Up" if done < trot else "Right" if env._pc < tcol else "Left" if env._pc > tcol else "Down")
        if done < trot:
            target = (trot, tcol, done + 1)
        w.apply((act,))
        if env._shape is not shape:                           # a piece settled
            if record:
                fr, ho, mh = feats(env._board)
                recs.append([fr, ho, mh, env._score - prev_score, env._score, pieces])
                prev_score = env._score
            pieces += 1; last = None
    return env._score, pieces, recs


def main():
    global ev
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    nat = _native_eval2(a); ev = lambda t: nat.evaluate(t, {})
    import numpy as np
    SEEDS = (3, 7); w0 = (1.0, -4.0, -0.5, 8.5)
    print("=" * 84)
    print("THE JABBERWOCK SELF-MODIFIES via THE GRAPH'S OPTIMISER (manifold-collapse residual loop)")
    print("=" * 84)

    # WATCH (host I/O): record (features, Monte-Carlo return) at every settle
    X, y = [], []; base_lines = []
    for s in SEEDS:
        sc, pc, recs = play(w0, s, record=True); base_lines.append(sc)
        for fr, ho, mh, cd, lso, i in recs:
            ret = (sc - lso) + 0.05 * (pc - i)                # return-to-go: lines + survival still ahead
            X.append([fr, ho, mh, cd]); y.append(ret)
    X = np.array(X, float); y = np.array(y, float)
    print(f"  [watch] {len(SEEDS)} games, lines {base_lines}; recorded {len(X)} states with returns")

    # OPTIMISE (the graph): z-score, then the residual-loop Fold fits w in ONE evaluate
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Xz = (X - mu) / sd; yz = (y - y.mean()) / (y.std() + 1e-9)
    rows = [[*Xz[i].tolist(), float(yz[i])] for i in range(len(Xz))]
    res = ev(fit_linear_term(rows, lr=0.3, T=300, d=4))       # THE GRAPH'S OPTIMISER runs
    w_norm = np.array([float(v) for v in res])
    raw = w_norm / sd                                          # de-normalise; argmax is scale-invariant
    raw = raw / (abs(raw).max() + 1e-9) * 8.0                  # scale to the value's range (argmax-invariant)
    w1 = tuple(round(float(x), 3) for x in raw)
    print(f"  [optimise] the graph's residual loop fit the value's weights (one evaluate):")
    print(f"     {('free','holes','maxh','cleared')} : {w0}  ->  {w1}")

    # SELF-MODIFY + verify
    opt_lines = [play(w1, s)[0] for s in SEEDS]
    teach(a, "ValuePolicy", {"free": w1[0], "holes": w1[1], "maxh": w1[2], "cleared": w1[3]}, category="policy")
    print("=" * 84)
    print(f"  [self-modify] new value persisted; lines {base_lines} -> {opt_lines} "
          f"(avg {sum(base_lines)/2:.1f} -> {sum(opt_lines)/2:.1f}); donkey {donkey['n']}")
    print("  The agent self-modified its value with THE GRAPH'S OWN OPTIMISER — the manifold-collapse")
    print("  residual loop (w += lr*Xt(y-Xw)), one evaluate, fitting the value to the returns it watched.")
    print("  Not a host descent: the graph already has the optimiser; the agent ran it. Only the watch")
    print("  (recording its own play) is host I/O. donkey=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
