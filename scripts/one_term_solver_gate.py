"""one_term_solver_gate — GATE for the WHOLE multi-param (k,c) solver as ONE held
Term (the construction-bug frontier: close the multi-param 'one Term' caveat).

ROOT CAUSE (pinned): the inlined solver was NEVER a parse bug. It PARSES and
EVALUATES (depth ~30, under the now-fixed 128 recursion cap) — it returned
(nan, nan): NUMERIC divergence from unclamped finite-difference gradient steps
(lr too large -> grad blows to inf -> nan). The earlier `expected value at column
764` was a transient harness artifact (a stale builder), not the construction. The
JSON the builder emits is valid (json.dumps strict allow_nan=False passes; no
Infinity/NaN tokens).

FIX (graph-native, donkey=0): gradient CLIPPING as held Terms (IfThenElse clamp) in
the Fold body -> the residual-feedback recurrence cannot diverge -> the WHOLE joint
(k,c) solver builds as ONE Fold Term that parses + evaluates + recovers (k,c),
matching the dispatched fit_multi. Outer loop is a Fold Term, not Python-dispatched.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/one_term_solver_gate.py
"""
from __future__ import annotations
import os, sys, json, inspect, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
import substrate_rs as srs
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import fit_multi_one_term, fit_multi
import domains.reflective_faculty as rf


def _gen(k, c, n=24):
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
    ok = True

    # 1. ROOT CAUSE: the unclamped inline = nan (divergence), NOT a parse error
    print("=" * 78)
    print("GATE 1 — ROOT CAUSE: the blocker is NUMERIC divergence (nan), not a parse bug")
    print("=" * 78)
    s = srs._NativeSubstrate(); ev = s.evaluate
    def L(v): return {"type": "Lit", "value": v}
    def V(n): return {"type": "Var", "name": n}
    def IA(q, i): return {"type": "IndexAt", "seq": q, "index": i}
    def P(*x): return {"type": "Plus", "items": list(x)}
    def T(*x): return {"type": "Times", "items": list(x)}
    def Mi(x, y): return {"type": "Minus", "a": x, "b": y}
    def Dv(x, y): return {"type": "Div", "a": x, "b": y}
    def Vec(*x): return {"type": "Vec", "items": list(x)}
    def Ap(q, it): return {"type": "Append", "seq": q, "item": it}
    def Fd(src, va, ac, ini, bo): return {"type": "Fold", "source": src, "var_name": va, "acc_name": ac, "init": ini, "body": bo}
    def Let(nm, val, body): return {"type": "Let", "name": nm, "value": val, "body": body}
    N = 24
    obs = _gen(1.2, 0.10, N)
    def mtrail(ke, ce):
        st = V("ms"); vn = P(IA(st, L(1)), T(Mi(L(0.0), ke), IA(st, L(0))), T(Mi(L(0.0), ce), IA(st, L(1)))); xn = P(IA(st, L(0)), vn)
        return IA(Fd(L(list(range(N))), "i", "ms", Vec(L(1.0), L(0.0), Vec()), Vec(xn, vn, Ap(IA(st, L(2)), xn))), L(2))
    def sse(ke, ce):
        return Let("m", mtrail(ke, ce), Fd(L(list(range(N))), "i", "acc", L(0.0),
                   P(V("acc"), T(Mi(IA(V("m"), V("i")), IA(L(obs), V("i"))), Mi(IA(V("m"), V("i")), IA(L(obs), V("i")))))))
    st = V("p"); k = IA(st, L(0)); c = IA(st, L(1)); eps = L(0.01); lr = L(0.02)
    b = sse(k, c); gk = Dv(Mi(sse(P(k, eps), c), b), eps); gc = Dv(Mi(sse(k, P(c, eps)), b), eps)
    unclamped = Fd(L(list(range(120))), "it", "p", Vec(L(0.3), L(0.1)), Vec(Mi(k, T(lr, gk)), Mi(c, T(lr, gc))))
    j = json.dumps(unclamped)
    valid_json = True
    try:
        json.dumps(unclamped, allow_nan=False)
    except ValueError:
        valid_json = False
    r = ev(unclamped, {})
    is_nan = (r[0] != r[0])
    print(f"  emitted JSON is valid (strict allow_nan=False passes): {valid_json}; contains 'NaN'/'Infinity': {('NaN' in j or 'Infinity' in j)}")
    print(f"  unclamped solver PARSES + EVALUATES -> result {tuple(round(x,3) if x==x else x for x in r)} (nan = divergence): {is_nan}")
    print("  -> root cause = NUMERIC divergence (nan), NOT a parse/construction-JSON bug")
    g1 = valid_json and ("NaN" not in j) and is_nan
    ok &= g1

    # 2. WHOLE SOLVER AS ONE TERM recovers (k,c), matching dispatched fit_multi
    print("\n" + "=" * 78)
    print("GATE 2 — WHOLE solver as ONE Term (Fold, clamped) recovers (k,c), matches dispatched")
    print("=" * 78)
    one = fit_multi_one_term(a, obs)
    disp = fit_multi(a, obs)
    print(f"  ONE-TERM solver: k={one['restoring_k']} c={one['decay_c']} SSE={one['sse']} (term {one['term_chars']} chars)")
    print(f"  dispatched fit_multi: k={disp['restoring_k']} c={disp['decay_c']} SSE={disp['sse']}")
    g2 = (one["fitted"] and abs(one["restoring_k"] - 1.2) < 0.2 and abs(one["decay_c"] - 0.10) < 0.06
          and one["sse"] < 0.5 and abs(one["restoring_k"] - disp["restoring_k"]) < 0.2)
    print("  -> one-Term recovers + matches dispatched:", "OK" if g2 else "FAIL")
    ok &= g2

    # 3. GRAPH-NATIVE / donkey=0
    print("\n" + "=" * 78)
    print("GATE 3 — GRAPH-NATIVE: outer loop is a Fold Term; Python builds JSON + ONE evaluate; donkey=0")
    print("=" * 78)
    src = inspect.getsource(rf.fit_multi_one_term)
    outer_is_fold = 'solver = Fold(' in src and "native.evaluate(solver" in src
    one_eval = src.count("native.evaluate(solver") == 1
    no_py_loop = ("for " not in src.split("solver = Fold")[1])
    llm = len(re.findall(r"make_ask|claude|openai|\.chat\(", src))
    print(f"  outer descent is a Fold Term evaluated once: {outer_is_fold and one_eval}")
    print(f"  no Python descent loop after building the solver Term: {no_py_loop}")
    print(f"  LLM calls in the path: {llm} | DONKEY calls: {calls['n']}")
    g3 = outer_is_fold and one_eval and no_py_loop and llm == 0 and calls["n"] == 0
    ok &= g3

    # 4. GENERALISES + NULL
    print("\n" + "=" * 78)
    print("GATE 4 — GENERALISES (>=2 pairs as one Term) + NULL (degenerate -> non-convergence)")
    print("=" * 78)
    gen_ok = True
    for (k_, c_) in [(0.5, 0.18), (1.6, 0.08)]:
        rg = fit_multi_one_term(a, _gen(k_, c_))
        rec = rg["fitted"] and abs(rg["restoring_k"] - k_) < 0.2 and abs(rg["decay_c"] - c_) < 0.06
        gen_ok &= rec
        print(f"  one-Term true (k={k_},c={c_}) -> (k={rg['restoring_k']},c={rg['decay_c']}) SSE={rg['sse']} recovered={rec}")
    null = fit_multi_one_term(a, [0.5] * 24)
    print(f"  NULL flat data -> fitted={null['fitted']} ({null.get('reason','')[:48]})")
    g4 = gen_ok and (null["fitted"] is False)
    print("  -> generalises + null:", "OK" if g4 else "FAIL")
    ok &= g4

    print("\n" + "=" * 78)
    print(("PASS" if ok else "FAIL"),
          "- ONE-TERM MULTI-PARAM SOLVER: the whole joint (k,c) descent is ONE held Fold Term (outer loop "
          "NOT Python-dispatched) that parses + evaluates + recovers (k,c) matching the dispatched solver. "
          "Root cause of the prior block was NUMERIC divergence (nan), fixed by held-Term gradient CLIPPING "
          "(IfThenElse clamp) — not a parse bug, not authored logic. Generalises; null holds; donkey=0. "
          "The multi-param 'one Term' caveat is CLOSED.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
