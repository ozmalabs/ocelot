"""PART 0 — reproduce the reviewer's numbers, on the INIT ALONE.

No rule has fired. No clock has advanced. This measures ONLY what
`WaveWorld.add_units` hands the agent.
"""
from __future__ import annotations

import numpy as np

from scripts.w0_ablation_lib import (INITS, build, rf_stats, dc_power_fraction,
                                     dc_ratio, frac_negative)
from domains.engine_provenance import provenance_line


if __name__ == "__main__":
    print(provenance_line())
    print("=" * 78)
    print("PART 0 — THE INITIALISATION ITSELF (no rule has fired, step=0)")
    print("=" * 78)
    print(f"{'arm':7s} {'DC power frac':>14s} {'DC:structure':>14s} "
          f"{'frac(w<0)':>11s} {'||w||':>8s} {'anisotropy':>11s}")
    for arm in INITS:
        # 8 seeds so the numbers are not one draw's luck.
        rows = []
        for seed in range(8):
            w, us = build(seed, arm)
            rows.append(rf_stats(w, us))
        agg = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
        print(f"{arm:7s} {agg['dc_frac']:14.5f} {agg["dc_ratio"]:13.3f}:1 "
              f"{agg['frac_neg']:11.4f} {agg['norm']:8.3f} {agg['anis']:11.4f}")

    print("\nANALYTIC CHECK (no engine, pure arithmetic on the same formula):")
    rng = np.random.default_rng(0)
    for label, f in (("DC    w=max(1.0*(1+0.05*N),1e-3)",
                      lambda g: np.maximum(1.0 * (1 + 0.05 * g), 1e-3)),
                     ("ZERO  w=0.0+0.05*N", lambda g: 0.0 + 0.05 * g),
                     ("ZEROM w=0.0+1.0*N", lambda g: 0.0 + 1.0 * g)):
        vals = [f(rng.normal(size=49)) for _ in range(2000)]
        print(f"  {label:34s} DC frac = {np.mean([dc_power_fraction(v) for v in vals]):.5f}"
              f"   ratio = {np.mean([dc_ratio(v) for v in vals]):8.3f}:1"
              f"   frac(w<0) = {np.mean([frac_negative(v) for v in vals]):.4f}")
