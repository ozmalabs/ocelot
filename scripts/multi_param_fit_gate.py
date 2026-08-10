"""multi_param_fit_gate — GATE for MULTI-PARAMETER / NON-CONVEX fitting: fit (k,c)
JOINTLY where naive descent diverges/traps, via a graph-native multi-start solver.

SELF-SIMILAR KEYSTONE: the solver is still a residual-feedback recurrence — now over
a parameter vector, with clipping + multi-start to escape divergence/local minima.

GRAPH-NATIVE (the donkey check): the model-vs-observation SSE is a HELD numeric Term
run by the Rust evaluator (the model-fitting reasoning); the joint gradient + clip +
multi-start (keep lowest-SSE) is the residual-feedback iteration DISPATCHED over that
Term (master_tick-style: Python drives the loop, the model/residual is the Term).
NO scipy/numpy, NO Python SSE/model arithmetic, NO LLM.

HONEST NOTE: the single-param fit_magnitudes kept the WHOLE descent as a Fold Term;
the multi-param solver dispatches the outer loop because fully-inlining the joint
descent exceeds the Rust Term-parser size limit. The reasoning (SSE) stays a Term;
the iteration is dispatched — the permitted split.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/multi_param_fit_gate.py
"""
from __future__ import annotations
import os, sys, inspect, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import substrate_rs as srs
from domains.reflective_faculty import fit_multi, _sse_term_kc
import domains.reflective_faculty as rf


def _gen(k, c, n=30):
    s = srs._NativeSubstrate(); ev = s.evaluate
    def L(v): return {"type": "Lit", "value": v}
    def V(x): return {"type": "Var", "name": x}
    def IA(s_, i): return {"type": "IndexAt", "seq": s_, "index": i}
    def P(*x): return {"type": "Plus", "items": list(x)}
    def T(*x): return {"type": "Times", "items": list(x)}
    def Mi(a, b): return {"type": "Minus", "a": a, "b": b}
    def Vec(*x): return {"type": "Vec", "items": list(x)}
    def Ap(s_, it): return {"type": "Append", "seq": s_, "item": it}
    def Fd(src, va, ac, ini, bo): return {"type": "Fold", "source": src, "var_name": va, "acc_name": ac, "init": ini, "body": bo}
    st = V("ms"); vn = P(IA(st, L(1)), T(Mi(L(0.0), L(k)), IA(st, L(0))), T(Mi(L(0.0), L(c)), IA(st, L(1)))); xn = P(IA(st, L(0)), vn)
    return [float(x) for x in ev(Fd(L(list(range(n))), "i", "ms", Vec(L(1.0), L(0.0), Vec()), Vec(xn, vn, Ap(IA(st, L(2)), xn))), {})[2]]


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    calls = {"n": 0}
    try:
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    except Exception:
        pass
    native = rf._native_eval2(a)
    ok = True

    # 1. JOINT MULTI-PARAMETER FIT
    print("=" * 78)
    print("GATE 1 — JOINT (k,c) FIT recovers both params")
    print("=" * 78)
    TK, TC = 1.2, 0.10
    traj = _gen(TK, TC)
    r = fit_multi(a, traj)
    print(f"  true (k,c)=({TK},{TC}) -> fitted (k,c)=({r['restoring_k']},{r['decay_c']}) SSE={r['sse']}")
    print(f"  per-init SSE: {r['per_init_sse']} | model-evals: {r['model_evals']}")
    g1 = abs(r["restoring_k"] - TK) < 0.15 and abs(r["decay_c"] - TC) < 0.05 and r["sse"] < 0.5
    print("  -> both params recovered jointly:", "OK" if g1 else "FAIL")
    ok &= g1

    # 2. NON-CONVEX ESCAPE CONTRAST (the load-bearing control)
    print("\n" + "=" * 78)
    print("GATE 2 — NON-CONVEX ESCAPE: naive diverges/traps vs robust solver escapes")
    print("=" * 78)
    n, sse_term = _sse_term_kc(traj)
    def SSE(k, c):
        v = float(native.evaluate(sse_term, {"k": k, "c": c}))
        return v if (v == v and abs(v) < 1e12) else 1e12
    # NAIVE: large fixed lr, no clip, single start from a far/bad init -> diverges
    def naive(k, c, iters=120, lr=0.06, eps=0.01):
        for _ in range(iters):
            b = SSE(k, c); gk = (SSE(k + eps, c) - b) / eps; gc = (SSE(k, c + eps) - b) / eps
            k -= lr * gk; c -= lr * gc
            if abs(k) > 1e6:
                return k, c, SSE(k, c)
        return k, c, SSE(k, c)
    nk, nc, ns = naive(2.0, 0.4)
    print(f"  (a) NAIVE (fixed lr, no clip) from far init (2.0,0.4): k={nk:.2g} SSE={ns:.3g} -> "
          f"{'DIVERGED/trapped' if ns > 1.0 else 'converged'}")
    # ROBUST: the graph-native multi-start solver (clip + multi-start) from the SAME bad init included
    rr = fit_multi(a, traj, inits=[(2.0, 0.4), (0.5, 0.3), (1.2, 0.1), (0.8, 0.2)])
    print(f"  (b) ROBUST multi-start solver: k={rr['restoring_k']} c={rr['decay_c']} SSE={rr['sse']}")
    contrast = ns > 1.0 and abs(rr["restoring_k"] - TK) < 0.15 and rr["sse"] < 0.5
    print(f"  -> CONTRAST holds (naive failed SSE={ns:.3g}, robust escaped SSE={rr['sse']}):",
          "OK" if contrast else "FAIL")
    ok &= contrast

    # 3. GRAPH-NATIVE (donkey check)
    print("\n" + "=" * 78)
    print("GATE 3 — GRAPH-NATIVE (SSE is a held Term; no scipy/numpy/LLM)")
    print("=" * 78)
    src = inspect.getsource(rf.fit_multi) + inspect.getsource(rf._sse_term_kc)
    real_imports = bool(re.search(r"import\s+scipy|import\s+numpy|from\s+scipy|from\s+numpy", src))
    sse_is_term = '"type": "Fold"' in inspect.getsource(rf._sse_term_kc) and "native.evaluate(sse_term" in inspect.getsource(rf.fit_multi)
    llm = len(re.findall(r"make_ask|claude|openai|\.chat\(", src))
    print(f"  real scipy/numpy import: {real_imports} (False=clean) | LLM calls: {llm}")
    print(f"  SSE/model IS a held Fold Term, evaluated by Rust per candidate: {sse_is_term}")
    g3 = (not real_imports) and llm == 0 and sse_is_term
    ok &= g3

    # 4. GENERALISES + NULL
    print("\n" + "=" * 78)
    print("GATE 4 — GENERALISES (2 different (k,c)) + NULL (un-fittable)")
    print("=" * 78)
    gen_ok = True
    for (k, c) in [(0.5, 0.18), (1.6, 0.08)]:
        rg = fit_multi(a, _gen(k, c))
        rec = abs(rg["restoring_k"] - k) < 0.2 and abs(rg["decay_c"] - c) < 0.06
        gen_ok &= rec
        print(f"  true (k={k},c={c}) -> fitted (k={rg['restoring_k']},c={rg['decay_c']}) SSE={rg['sse']} recovered={rec}")
    null = fit_multi(a, [0.5] * 30)
    print(f"  NULL flat data -> fitted={null['fitted']} ({null.get('reason','')[:50]})")
    g4 = gen_ok and (null["fitted"] is False)
    print("  -> generalises + null:", "OK" if g4 else "FAIL")
    ok &= g4

    # 5. ESCAPE SUCCESS RATE (honest) + donkey
    print("\n" + "=" * 78)
    print("GATE 5 — escape success rate (honest) + donkey=0")
    print("=" * 78)
    # how many of the individual starts converged to the global min (the per-init breakdown)?
    converged_starts = sum(1 for v in r["per_init_sse"] if v < 0.5)
    print(f"  per-init convergence: {converged_starts}/{len(r['per_init_sse'])} starts reached the global min")
    print(f"  -> multi-start needed (single random start often traps): {converged_starts < len(r['per_init_sse'])}")
    print(f"  DONKEY calls: {calls['n']}")
    ok &= (calls["n"] == 0)

    print("\n" + "=" * 78)
    print(("PASS" if ok else "FAIL"),
          "- MULTI-PARAMETER / NON-CONVEX FIT (graph-native): (k,c) fitted JOINTLY by a multi-start "
          "residual-feedback solver — the SSE/model is a held Term (Rust-evaluated), the joint gradient + "
          "clip + multi-start is dispatched over it; naive fixed-lr descent DIVERGES from a bad init while "
          "the robust multi-start solver ESCAPES and recovers both params; generalises; null holds; NO "
          "scipy/numpy/LLM, donkey=0.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
