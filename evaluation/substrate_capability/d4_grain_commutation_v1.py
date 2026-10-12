#!/usr/bin/env python3
"""Tranche 2 gate 4: does dyadic coarse-graining make HELD D4/scale generators
discriminate jittered handwriting? Pure analysis (no engine); decides whether
a DimInfer grain field is worth building.

For 20 Omniglot drawings at 16x16 and each held map M (rot90, rot180, rot270,
reflect r, reflect c, transpose, anti-transpose, scale2), grain g in 0..3,
with q_g(X) = set of floor((x - min)/2^g):
  commute : q_g(M.A) == M.q_g(A) up to translation
  jitter  : q_g(M.A') == M.q_g(A)   (A' = same drawing re-rendered with +-0.35 cell jitter)
  cross   : q_g(M.B)  == M.q_g(A)   (B = another character; false-explain control)
A useful grain needs jitter >> cross.
"""
import json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from geninfer_grain_ladder_omniglot_v1 import drawings, strokes, raster  # noqa: E402
OUT = ROOT / "evaluation/reports/d4_grain_commutation_v1_20261007.json"

def norm(cs):
    mr = min(r for r, _ in cs); mc = min(c for _, c in cs)
    return frozenset((r - mr, c - mc) for r, c in cs)

MAPS = {"rot90": lambda r, c: (c, -r), "rot180": lambda r, c: (-r, -c), "rot270": lambda r, c: (-c, r),
        "refl_r": lambda r, c: (-r, c), "refl_c": lambda r, c: (r, -c), "transpose": lambda r, c: (c, r),
        "antitranspose": lambda r, c: (-c, -r), "scale2": lambda r, c: (2 * r, 2 * c)}

def M(f, cs): return norm([f(r, c) for r, c in cs])
def q(cs, g): return norm([(r >> g, c >> g) for r, c in norm(cs)])

def main():
    rng = random.Random(20261007)
    ds = drawings()
    As = [raster(strokes(p)) for _, p in ds]
    Js = [raster(strokes(p), 0.35, rng) for _, p in ds]
    res = {}
    for name, f in MAPS.items():
        for g in range(4):
            com = jit = cro = 0
            for i, A in enumerate(As):
                target = M(f, q(A, g))
                com += q(M(f, A), g) == target
                jit += q(M(f, Js[i]), g) == target
                cro += q(M(f, As[(i + 7) % len(As)]), g) == target
            res[f"{name}:g{g}"] = {"commute": com, "jitter": jit, "cross": cro, "n": len(As)}
    agg = {g: {k: sum(v[k] for kk, v in res.items() if kk.endswith(f"g{g}")) for k in ("commute", "jitter", "cross")} for g in range(4)}
    OUT.write_text(json.dumps({"schema": "D4GrainCommutationV1", "per_map": res, "by_grain": agg}, indent=1) + "\n")
    for g, v in agg.items(): print("grain", g, v, "of", 8 * len(As))
    for k, v in res.items():
        if k.startswith(("rot90", "refl_r", "scale2")): print(k, v)

main()
