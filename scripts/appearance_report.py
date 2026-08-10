#!/usr/bin/env python3
"""Regenerate every table in `VISION_APPEARANCE_RESULTS.md` from the committed
artifact `results/appearance.json`.  No measurement happens here -- this file
only READS.  Run:

    python3 scripts/appearance_report.py
"""
from __future__ import annotations
import json
import math
import sys


def wilson(k, n):
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main(path="results/appearance.json"):
    D = json.load(open(path))
    R = D["rows"]
    print(f"engine {D['engine']}  n={D['n_conditions']}  wall {D['wall_s']:.0f}s  "
          f"loadavg_end {D['loadavg_end']}")
    print("VERDICTS")
    for k, v in D["verdicts"].items():
        print(f"  {k:32s} {v}")
    print(f"fa_silent {D['fa_silent']}   n_disagree {D['n_disagree']}")
    print(f"analytic_rect {D['analytic_rect']}")

    # SEED PROVENANCE, PROVEN AT RUNTIME FROM THE ARTIFACT rather than
    # statically: `seed_audit` reports 5 unresolved sinks for this runner
    # (a loop variable over a parameter), so the block claim is checked HERE,
    # against the seeds actually consumed.
    seeds = sorted({r["seed"] for r in R if r["arm"] not in ("A3", "A4")})
    print(f"SEEDS consumed: n={len(seeds)} min={min(seeds)} max={max(seeds)} "
          f"in_block={all(109000 <= s <= 109999 for s in seeds)}")

    print("\nARM TABLE (tol = the shipped SupportInfer Term)")
    print(f"{'arm':11s} {'n':>2s} {'cond':>5s} {'tol':>5s} {'rate':>6s} "
          f"{'95% CI':>16s} {'strict':>6s}")
    for arm in ("A1", "A2-SWAP", "A2-NOISE", "A2-RECT", "A2-RAGGED", "A3", "A4"):
        for n in (2, 3, None):
            rows = [r for r in R if r["arm"] == arm and (n is None or r["n"] == n)]
            if not rows or (n is None and any(x["n"] in (2, 3) for x in rows)
                            and arm != "A3" and arm != "A4"):
                continue
            k = sum(1 for r in rows if r["term_explained"])
            ks = sum(1 for r in rows if r["strict_explained"])
            lo, hi = wilson(k, len(rows))
            print(f"{arm:11s} {str(n):>2s} {len(rows):5d} {k:5d} "
                  f"{k/len(rows):6.4f} [{lo:6.4f},{hi:6.4f}] {ks:6d}")

    live = [r for r in R if r["arm"] == "A1" and r["live"]]
    print(f"\nA1 LIVE {len(live)}  tol {sum(1 for r in live if r['term_explained'])}"
          f"  strict {sum(1 for r in live if r['strict_explained'])}")
    print("A1 live-by-q (live / tol / strict):")
    for q in (2, 4, 8, 16, 32, 64, 128, 256):
        rows = [r for r in R if r["arm"] == "A1" and r["q"] == q]
        lv = [r for r in rows if r["live"]]
        print(f"  q={q:3d} n={len(rows):4d} live={len(lv):4d} "
              f"tol={sum(1 for r in lv if r['term_explained']):4d} "
              f"strict={sum(1 for r in lv if r['strict_explained']):4d}")

    print("\nA3 RASTER reasons:",
          {r["term_reason"] for r in R if r["arm"] == "A3"})
    print("A3 compared>0:", sum(1 for r in R if r["arm"] == "A3"
                                and (r["term_compared"] or 0) > 0), "/",
          sum(1 for r in R if r["arm"] == "A3"))

    print("\nTHE PARTITION (tol accepts that strict refused):")
    gained = [r for r in R if r["term_explained"] and not r["strict_explained"]]
    print(f"  n={len(gained)}  residual==0: "
          f"{sum(1 for r in gained if r['term_residual'] == 0)}  "
          f"residual>0: {sum(1 for r in gained if r['term_residual'] > 0)}")
    print(f"  residual distinct values across the run: "
          f"{len({r['term_residual'] for r in R})}")

    print("\nA4:", [(r["sub"], r["term_explained"], r["term_reason"])
                    for r in R if r["arm"] == "A4"])
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
