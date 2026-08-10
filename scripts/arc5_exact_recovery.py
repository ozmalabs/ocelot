"""Read float asserts as INTERVAL CONSTRAINTS and recover EXACT structure.
Tests: 'no program needs floats; specs are written to imply them.'
Measurement only (reads reference code for classification, never for fitting).
"""
import ast, json, math, itertools, re
from fractions import Fraction

tasks = {t["task_id"]: t for t in json.load(open("tests/fixtures/mbpp/sanitized-mbpp.json"))}
rows  = json.load(open("results/arc5_float_necessity.json"))
FLOATY = [r["task_id"] for r in rows]

def parse_calls(t):
    """(args, expected, tol) from each assert, literals only."""
    out = []
    for a in t.get("test_list", []):
        try: tree = ast.parse(a, mode="exec")
        except SyntaxError: continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
               and n.func.attr == "isclose":
                inner, exp = n.args[0], n.args[1]
                tol = 1e-9
                for kw in n.keywords:
                    if kw.arg in ("rel_tol","abs_tol"):
                        try: tol = ast.literal_eval(kw.value)
                        except Exception: pass
                if isinstance(inner, ast.Call):
                    try:
                        args = [ast.literal_eval(x) for x in inner.args]
                        out.append((args, ast.literal_eval(exp), tol)); break
                    except Exception: pass
            if isinstance(n, ast.Compare) and isinstance(n.left, ast.Call) \
               and len(n.comparators)==1:
                try:
                    args = [ast.literal_eval(x) for x in n.left.args]
                    exp  = ast.literal_eval(n.comparators[0])
                    if isinstance(exp, float):
                        out.append((args, exp, 1e-9)); break
                except Exception: pass
    return out

# exact family: k * C^p * prod(arg_i ** e_i),  k rational, C in {1, pi}, e small ints
KS = [Fraction(a,b) for a in range(1,13) for b in (1,2,3,4,6,8)] 
KS = sorted(set(KS)); CS = [("1",1.0), ("pi",math.pi)]
EX = [0,1,2,3]

def recover(cases, nargs):
    best = None
    for kf in KS:
        for cname, cval in CS:
            for p in (0,1):
                for exps in itertools.product(EX, repeat=min(nargs,3)):
                    ok = True
                    for args, exp, tol in cases:
                        v = float(kf) * (cval**p if cname=="pi" else 1.0)
                        for a,e in zip(args, exps):
                            if not isinstance(a,(int,float)): ok=False; break
                            v *= a**e
                        if not ok: break
                        if not math.isclose(v, exp, rel_tol=max(tol,1e-6)): ok=False; break
                    if ok:
                        cand = (kf, cname if p else "1", exps)
                        if best is None: best = cand
                        return best
    return best

res = {"recovered": [], "not_recovered": [], "no_numeric_cases": []}
for tid in FLOATY:
    t = tasks[tid]
    cases = parse_calls(t)
    cases = [c for c in cases if c[0] and all(isinstance(a,(int,float)) for a in c[0])]
    if not cases:
        res["no_numeric_cases"].append(tid); continue
    nargs = len(cases[0][0])
    got = recover(cases, nargs)
    if got:
        kf, c, exps = got
        res["recovered"].append({"task_id": tid, "k": f"{kf.numerator}/{kf.denominator}",
                                 "const": c, "exps": list(exps),
                                 "prompt": t["prompt"][:58]})
    else:
        res["not_recovered"].append({"task_id": tid, "prompt": t["prompt"][:58]})

print(f"float-involving tasks: {len(FLOATY)}")
print(f"  numeric-literal asserts usable : {len(FLOATY)-len(res['no_numeric_cases'])}")
print(f"  EXACT form recovered           : {len(res['recovered'])}")
print(f"  not recovered by this family   : {len(res['not_recovered'])}")
print(f"  no usable numeric cases        : {len(res['no_numeric_cases'])} {res['no_numeric_cases']}")
print("\nRECOVERED — exact (rational k, cross-frame constant, integer exponents):")
for r in res["recovered"]:
    print(f"  {r['task_id']:>4} k={r['k']:<6} C={r['const']:<3} exps={r['exps']}  {r['prompt']}")
print("\nNOT recovered by the k*C^p*prod(x^e) family (needs a different exact shape):")
for r in res["not_recovered"]:
    print(f"  {r['task_id']:>4} {r['prompt']}")
json.dump(res, open("/tmp/exact_recovery.json","w"), indent=1)
