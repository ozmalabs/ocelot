"""Standalone: the GRAPH'S optimiser = the manifold-collapse residual loop as a held Term —
w <- w + lr*Xt(y - Xw), a Fold the evaluator runs in ONE dispatch. Verify it converges to least-squares.
"""
import os, sys, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path: sys.path.insert(0, p)
import numpy as np
from domains.reflective_faculty import run_program_on_fresh

L = lambda v: {"type": "Lit", "value": v}
Var = lambda n: {"type": "Var", "name": n}
IA = lambda s, i: {"type": "IndexAt", "seq": s, "index": i}
Plus = lambda *x: {"type": "Plus", "items": list(x)}
Times = lambda *x: {"type": "Times", "items": list(x)}
Minus = lambda a, b: {"type": "Minus", "a": a, "b": b}
Sum = lambda src, v, val: {"type": "Sum", "source": src, "var_name": v, "value": val}
Vec = lambda *x: {"type": "Vec", "items": list(x)}
Fold = lambda src, var, acc, init, body: {"type": "Fold", "source": src, "var_name": var, "acc_name": acc, "init": init, "body": body}


def fit_linear_term(rows, lr, T, d):
    """rows = [[x0..x_{d-1}, y], ...]. Returns the Fold that residual-feedback-descends w over T steps."""
    w = Var("w"); r = Var("r")
    dot = Sum(L(list(range(d))), "k", Times(IA(w, Var("k")), IA(r, Var("k"))))   # w . x_i
    resid = Minus(IA(r, L(d)), dot)                                              # y_i - w.x_i
    coef = lr / len(rows)
    comp = [Plus(IA(w, L(j)), Times(L(coef), Sum(L(rows), "r", Times(IA(r, L(j)), resid)))) for j in range(d)]
    return Fold(L(list(range(T))), "it", "w", Vec(*[L(0.0)] * d), Vec(*comp))


def main():
    rng = np.random.default_rng(0); ok = 0; tot = 0
    for _ in range(8):
        n, d = 120, 4
        X = rng.standard_normal((n, d)); X = (X - X.mean(0)) / (X.std(0) + 1e-9)
        wt = rng.standard_normal(d); y = X @ wt + 0.05 * rng.standard_normal(n)
        rows = [[*X[i].tolist(), float(y[i])] for i in range(n)]
        res = run_program_on_fresh(fit_linear_term(rows, lr=0.3, T=300, d=d), {})
        if not res.get("ran"):
            print("EVAL FAIL", res.get("reason")); return 1
        wfit = np.array([float(x) for x in res["value"]])
        wls, *_ = np.linalg.lstsq(X, y, rcond=None)
        err = float(np.linalg.norm(wfit - wls))
        tot += 1; ok += err < 0.05
        print(f"  graph-fit {np.round(wfit,2)} vs lstsq {np.round(wls,2)}  ||diff|| {err:.3f}")
    print(f"\n  graph residual-loop == least-squares: {ok}/{tot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
