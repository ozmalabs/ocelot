#!/usr/bin/env python3
"""Held-out confirmation: SUBSTRATE_DIMINFER_GRAIN_HELDOUT_V1_PREREG_20261007.md"""
import hashlib, json, random, statistics, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(Path(__file__).resolve().parent)]
from geninfer_grain_ladder_omniglot_v1 import strokes, raster  # noqa: E402
from diminfer_grain_omniglot_v1 import MAPS, norm, sig, run  # noqa: E402
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_DIMINFER_GRAIN_HELDOUT_V1_PREREG_20261007.md"
OUT = ROOT / "evaluation/reports/diminfer_grain_heldout_v1_1_degenerate_guard_20261007.json"
EVAL = ROOT / "data/omniglot/strokes_evaluation"

def cp(k, n, a=0.05):
    from scipy.stats import beta  # noqa
    return beta.ppf(a / 2, k, n - k + 1) if k else 0.0, beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0

def cp_exact(k, n, a=0.05):
    # Clopper-Pearson without scipy: bisection on the binomial CDF
    from math import comb
    cdf = lambda x, p: sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(x + 1))
    def bis(f):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if f(mid): hi = mid
            else: lo = mid
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else bis(lambda p: 1 - cdf(k - 1, p) >= a / 2)
    upper = 1.0 if k == n else bis(lambda p: cdf(k, p) <= a / 2)
    return lower, upper

def main():
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    rng = random.Random(20261008)
    chars = []
    for a in sorted(p for p in EVAL.iterdir() if p.is_dir())[:20]:
        c = sorted(p for p in a.iterdir() if p.is_dir())[0]
        d = sorted(c.glob("*.txt"))
        chars.append((f"{a.name}/{c.name}", d[0], d[1]))
    A1 = [raster(strokes(x[1])) for x in chars]; A2 = [raster(strokes(x[2])) for x in chars]
    J = [raster(strokes(x[1]), 0.35, rng) for x in chars]
    rows = []
    for i in range(len(chars)):
        for mn, f in MAPS.items():
            goals = {"exact": norm([f(*p) for p in A1[i]]), "jitter": norm([f(*p) for p in J[i]]),
                     "drawer": norm([f(*p) for p in A2[i]]), "cross": norm([f(*p) for p in A1[(i + 7) % len(chars)]])}
            for cond, g in goals.items():
                rows.append({"char": chars[i][0], "map": mn, "cond": cond,
                             "off": run(sig(A1[i]), sig(g), None), "ladder": run(sig(A1[i]), sig(g), [0, 1, 2])})
        print(i, flush=True)
    k = lambda c, a: sum(r[a]["recognized"] for r in rows if r["cond"] == c)
    n = sum(1 for r in rows if r["cond"] == "exact")
    jl, jo, cl = k("jitter", "ladder"), k("jitter", "off"), k("cross", "ladder")
    ci_j = cp_exact(jl, n); ci_c = cp_exact(cl, n)
    gates = {"H1_jitter_gain": jl - jo >= 25 and ci_j[0] > jo / n,
             "H2_cross_zero": cl == 0,
             "H3_exact_all_grain0": k("exact", "off") == n and k("exact", "ladder") == n and all(
                 r["ladder"]["grain"] == 0 for r in rows if r["cond"] == "exact")}
    summ = {f"{c}:{a}": k(c, a) for c in ("exact", "jitter", "drawer", "cross") for a in ("off", "ladder")}
    grains = {c: sorted(r["ladder"]["grain"] for r in rows if r["cond"] == c and r["ladder"]["recognized"]) for c in ("jitter", "drawer")}
    rep = {"schema": "DimInferGrainHeldoutV1_1", "protocol_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
           "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest(),
           "seed_sha256": hashlib.sha256((ROOT / "seeds/shape_decode_loop.json").read_bytes()).hexdigest(),
           "n": n, "summary": summ, "jitter_ladder_ci": ci_j, "cross_ladder_ci": ci_c,
           "grain_counts": {c: {g: v.count(g) for g in set(v)} for c, v in grains.items()},
           "median_ms": {a: statistics.median(r[a]["seconds"] for r in rows) * 1e3 for a in ("off", "ladder")},
           "gates": gates, "all_pass": all(gates.values()), "chars": [c[0] for c in chars], "rows": rows}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({k2: rep[k2] for k2 in ("summary", "jitter_ladder_ci", "cross_ladder_ci", "grain_counts", "median_ms", "gates")}, indent=1, default=str))

main()
