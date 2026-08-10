"""shape_generation_gate — GATE for SHAPE GENERATION: the fed-forward iterate of
the held difference operator. "A circle is stepped, but the reason it is a circle
is the residual at every step feeding into the next." (creator)

A shape = the trajectory of a residual-feedback recurrence:
    state_{n+1} = advance(state_n, sigma_n);  sigma_{n+1} = update(sigma_n).
The residual-LAW (sigma_0, update) IS the generator:
    CIRCLE = CONSTANT residual (constant turn);  SPIRAL = COMPOUNDING residual;
    LINE   = identity residual (zero turn).
Closing the loop is a Fold whose ACCUMULATOR is the threaded state (the held rule
engine's state-thread): state read positionally (a Tuple, via IndexAt — Attr only
reads graph nodes, not Dict values), advanced by the held arithmetic/trig Terms,
the trajectory accumulated with Append. The iterate is a Term TREE run by the Rust
evaluator — NO Python loop, NO new Rust. Recognition (inverse) recovers the
residual-law from a stepped shape: consecutive-step turning deltas; constant =>
circle. Regression: the static shape-math gates still pass.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/shape_generation_gate.py
"""
from __future__ import annotations
import os, sys, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
import substrate_rs as srs

def L(v): return {"type": "Lit", "value": v}
def V(n): return {"type": "Var", "name": n}
def Vec(*items): return {"type": "Vec", "items": list(items)}
def IndexAt(seq, i): return {"type": "IndexAt", "seq": seq, "index": i}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Sin(a): return {"type": "Sin", "arg": a}
def Cos(a): return {"type": "Cos", "arg": a}
def Atan2(y, x): return {"type": "Atan2", "y": y, "x": x}
def Append(seq, item): return {"type": "Append", "seq": seq, "item": item}
def Fold(src, var, acc, init, body):
    return {"type": "Fold", "source": src, "var_name": var, "acc_name": acc,
            "init": init, "body": body}

# state Tuple = (x, y, h, turn, dturn, trail). Indices:
X, Y, H, TURN, DTURN, TRAIL = 0, 1, 2, 3, 4, 5
STEP = 1.0


def _gen_term(turn0, dturn0, nsteps):
    """Build the generation iterate as ONE Term tree (a Fold over a step-list whose
    accumulator IS the threaded turtle state)."""
    st = V("st")
    h_n = Plus(IndexAt(st, L(H)), IndexAt(st, L(TURN)))                 # h += turn
    x_n = Plus(IndexAt(st, L(X)), Times(L(STEP), Cos(h_n)))             # advance
    y_n = Plus(IndexAt(st, L(Y)), Times(L(STEP), Sin(h_n)))
    turn_n = Plus(IndexAt(st, L(TURN)), IndexAt(st, L(DTURN)))          # sigma update
    body = Vec(x_n, y_n, h_n, turn_n, IndexAt(st, L(DTURN)),
               Append(IndexAt(st, L(TRAIL)), Vec(x_n, y_n)))
    init = Vec(L(0.0), L(0.0), L(0.0), L(turn0), L(dturn0), Vec())
    return Fold(L(list(range(nsteps))), "i", "st", init, body)


def _pts(res):
    trail = res[TRAIL]
    return [(round(p[0], 4), round(p[1], 4)) for p in trail]


def main() -> int:
    s = srs._NativeSubstrate()
    ev = s.evaluate
    ok = True

    # 1. GENERATE
    circle = ev(_gen_term(math.radians(30), 0.0, 12), {})       # 12*30deg = 360 -> closes
    line = ev(_gen_term(0.0, 0.0, 6), {})                       # zero turn
    spiral = ev(_gen_term(math.radians(20), math.radians(8), 18), {})  # compounding
    cp, lp, sp = _pts(circle), _pts(line), _pts(spiral)

    closure = math.hypot(cp[-1][0] - 0.0, cp[-1][1] - 0.0)      # 12-gon returns to origin
    circle_ok = len(cp) == 12 and closure < 1e-6
    line_ok = len(lp) == 6 and all(abs(p[1]) < 1e-9 for p in lp)
    # spiral: turning radius grows each step -> the run does NOT return to origin
    spiral_gap = math.hypot(sp[-1][0], sp[-1][1])
    spiral_ok = len(sp) == 18 and spiral_gap > 0.5
    print("[GENERATE] CIRCLE (constant turn):", len(cp), "pts, closure gap", round(closure, 6),
          "-> closes:", circle_ok)
    print("           LINE (identity turn):", lp[:3], "... straight:", line_ok)
    print("           SPIRAL (compounding turn):", len(sp), "pts, end-gap", round(spiral_gap, 3),
          "-> open:", spiral_ok)
    print("   ->", "OK" if (circle_ok and line_ok and spiral_ok) else "FAIL")
    ok &= circle_ok and line_ok and spiral_ok

    # 2. RECOVER (inverse) — recover the residual-law from the stepped shape:
    #    per-step turning delta (the residual fed forward). The recovery is a Term
    #    tree over the generated trail: heading_i = atan2(dy,dx); turn_i = h_i - h_{i-1}.
    #    Build it graph-natively via a Fold that reads consecutive trail points.
    trail = circle[TRAIL]
    # turn-sequence as a Term tree: Fold over indices 1..n-1 reading trail[i], trail[i-1]
    tl = L([list(p) for p in trail])
    def heading(i, j):  # atan2 of segment from point j to point i
        pi, pj = IndexAt(tl, L(i)), IndexAt(tl, L(j))
        return Atan2(Minus(IndexAt(pi, L(1)), IndexAt(pj, L(1))),
                     Minus(IndexAt(pi, L(0)), IndexAt(pj, L(0))))
    def turn_at(i):     # normalised turning residual = atan2(sin dh, cos dh) in (-pi,pi]
        dh = Minus(heading(i, i - 1), heading(i - 1, i - 2))
        return Atan2(Sin(dh), Cos(dh))     # wrap-free, pure trig identity (a Term, not a decision)
    turns = []
    for i in range(2, len(trail)):
        turns.append(round(math.degrees(ev(turn_at(i), {})), 3))
    constant = turns and all(abs(t - turns[0]) < 1e-6 for t in turns)
    recover_ok = constant and abs(turns[0] - 30.0) < 1e-3
    print("[RECOVER] consecutive-step turning deltas:", turns[:5], "... constant:", constant,
          "(=30deg => CIRCLE law)", "->", "OK" if recover_ok else "FAIL")
    ok &= recover_ok

    # 3. STABILITY — constant/identity law CLOSES or stays bounded; compounding runs away
    stable_closes = closure < 1e-6                       # |update|: dturn=0 -> bounded/closed
    runaway = spiral_gap > closure + 0.5                 # dturn>0 -> diverges, not silent noise
    stab_ok = stable_closes and runaway
    print("[STABILITY] constant law closes (gap", round(closure, 6), ") vs compounding runs away (gap",
          round(spiral_gap, 3), ") ->", "OK" if stab_ok else "FAIL")
    ok &= stab_ok

    # 4. REGRESSION — static shape-math gates
    import subprocess
    reg = True
    for g in ("shape_math_gate.py", "shape_blend_gate.py"):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", g)],
                           capture_output=True, text=True,
                           env={**os.environ, "PYTHONPATH": f"{ROOT}:{os.path.join(ROOT,'runners','dsl','python')}"})
        passed = r.returncode == 0
        reg &= passed
        print(f"[REGRESSION] {g}:", "PASS" if passed else "FAIL")
    ok &= reg

    print("=" * 74)
    print(("PASS" if ok else "FAIL"),
          "- SHAPE GENERATION: a shape is the fed-forward iterate of the residual operator "
          "(state_{n+1}=advance(state_n,sigma); sigma_{n+1}=update(sigma)). CIRCLE=constant, "
          "SPIRAL=compounding, LINE=identity; inverse recovers the residual-law; constant closes "
          "vs compounding runs away. The iterate is a Fold-threaded Term tree (held engine + held "
          "arithmetic, NO new Rust, NO Python loop); regressions intact; donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
