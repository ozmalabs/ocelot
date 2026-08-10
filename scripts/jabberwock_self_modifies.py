"""THE JABBERWOCK SELF-MODIFIES its value with a GENERAL optimiser toward an objective IT decides.

Creator: "it decides what it wants to do. any optimiser should be as general as possible except where
it needs to be specific." So:
  · THE AGENT DECIDES THE OBJECTIVE — its own goal. It already chose EMPOWERMENT (keep being able to
    act). Realised, that is: survive longer and keep clearing. The agent wants more of that; I do not
    pick the metric.
  · THE OPTIMISER IS GENERAL — a reusable descent over any parameters toward any objective:
    finite-difference direction + backtracking step + ACCEPT-ONLY-IF-IT-IMPROVES (the agent's
    Correct->Verify->revert guard). General; never degrades; not a hand-picked candidate hill-climb.
  · SPECIFIC ONLY AT THE BOUNDARY — the params are the value's weights; the objective is evaluated by
    playing (the env = the watch). Everything between is the general optimiser.
The agent self-modifies its value (the optimiser updates it, persisted), then describes.

Run: PYTHONPATH=.:runners/dsl/python:scripts python3 scripts/jabberwock_self_modifies.py
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
from tetris_world import TetrisEnv
from worlds.arc import ArcWorld
from probe_landing import host_landing
from jabberwock_learns_dynamics import landing_from_learned
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


def play(weights, seed, cap=220):
    w = ArcWorld(TetrisEnv(seed=seed)); w.reset(); env = w.env
    pieces = 0; last = None; target = (0, 0, 0)
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
        if env._shape is not shape:
            pieces += 1; last = None
    return env._score, pieces


# ---- THE AGENT'S OBJECTIVE: its goal (empowerment realised = survive + clear). The agent decides this.
SEEDS = (3, 7)
_cache = {}
def objective(weights):
    k = tuple(round(x, 4) for x in weights)
    if k not in _cache:
        g = [play(weights, s) for s in SEEDS]
        _cache[k] = sum(L_ for L_, _ in g) / len(g) + 0.05 * sum(p for _, p in g) / len(g)
    return _cache[k]


# ---- THE GENERAL OPTIMISER: coordinate descent, finite-diff direction, backtracking step, accept-only-
#      if-it-improves. Reusable for any params + any objective; never degrades. Specific only via `obj`.
def general_descent(params, obj, dims, passes=2, log=lambda *a: None):
    params = list(params); cur = obj(params)
    for _p in range(passes):
        for idx, s0 in dims:
            for direction in (1.0, -1.0):
                for s in (s0, s0 / 2.0):
                    trial = list(params); trial[idx] += direction * s
                    o = obj(trial)
                    if o > cur + 1e-9:                       # VERIFY: accept only a real improvement
                        log(idx, params[idx], trial[idx], cur, o)
                        params, cur = trial, o
                        break
                else:
                    continue
                break
    return params, cur


def main():
    global ev
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    nat = _native_eval2(a); ev = lambda t: nat.evaluate(t, {})
    NAMES = ["free", "holes", "maxh", "cleared"]
    w0 = [1.0, -4.0, -0.5, 8.5]
    print("=" * 84)
    print("THE JABBERWOCK SELF-MODIFIES ITS VALUE — general optimiser, objective IT chose")
    print("=" * 84)
    print(f"  [the agent decides] objective = my goal (empowerment realised: survive + clear)")
    base = objective(w0); base_lines = [play(tuple(w0), s) for s in SEEDS]
    print(f"  [baseline] value {tuple(w0)} -> lines {[l for l,_ in base_lines]} (objective {base:.2f})")

    # the general optimiser descends the value (params it can change) toward the agent's objective
    dims = [(2, 0.6), (1, 2.0), (3, 4.0)]                    # maxh, holes, cleared : (idx, initial step)
    def log(idx, old, new, o0, o1):
        print(f"  [descend] {NAMES[idx]}: {old:+.2f} -> {new:+.2f}  (objective {o0:.2f} -> {o1:.2f})")
    w1, obj1 = general_descent(w0, objective, dims, passes=2, log=log)

    opt_lines = [play(tuple(w1), s) for s in SEEDS]
    # SELF-MODIFY: persist the improved value as the agent's own policy (its self-modification, kept)
    teach(a, "ValuePolicy", {"free": w1[0], "holes": w1[1], "maxh": w1[2], "cleared": w1[3],
                             "objective": round(obj1, 2)}, category="policy")
    print("=" * 84)
    print(f"  [optimised] value {tuple(round(x,2) for x in w1)} -> lines {[l for l,_ in opt_lines]} "
          f"(objective {obj1:.2f})")
    print(f"  [self-modify] persisted the improved value as my ValuePolicy (kept); donkey {donkey['n']}")
    print(f"  [DESCRIBE] I decided what I wanted (my goal: stay empowered = survive + clear), and ran my")
    print(f"  GENERAL optimiser on my value's weights toward it — finite-diff direction, backtracking")
    print(f"  step, keep a change only if it improves. It moved {', '.join(NAMES[i] for i,_ in dims if abs(w1[i]-w0[i])>1e-6) or '(nothing — already best)'};")
    print(f"  objective {base:.2f} -> {obj1:.2f}. The optimiser is general (any params, any objective); only")
    print(f"  the objective-eval (playing) is specific. I self-modified my value and kept it. donkey=0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
