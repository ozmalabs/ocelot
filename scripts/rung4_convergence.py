"""RUNG 4 — CONVERGENCE CHECK (PROTOCOL 2). Run BEFORE any arm.

Does the scaffold still SETTLE once `vm_burst_lateral` is switched on? The
lateral rule makes several units learn per step instead of one, which is a real
change to the learning dynamics — Oja's stability argument (eta*y^2 < 1) is
per-unit and survives, but the POPULATION dynamics are new, so the fixed point
must be re-measured rather than assumed. Nine prior attempts failed by running
arms on a transient.

Checkpoints anisotropy AND drift out to 3200 steps on waves alone, for
lateral=1 (the new mechanism) and lateral=0 (the committed reference).

  anisotropy = mean over units of |Sum p*exp(2i*theta)| / Sum p   (structure)
  drift      = mean over units of ||w(t) - w(t-D)|| / ||w(t)||    (settling)

with D = 100 steps, a fixed window ending at each checkpoint.

CONVERGENT + USEFUL = anisotropy plateaus at NON-ZERO structure AND drift -> 0.

Seeds 4100-4107 (burned here; recorded in VISION_PROTOCOL.md's ledger).
"""
from __future__ import annotations

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.cortex_sheet import add_cortex, orientation_selectivity

H = W = 16
RF = 7
GH = GW = 6
ETA = 5e-4
DELTA = 100
CKPTS = [0, 50, 100, 200, 400, 800, 1600, 3200]


def _weights(world, units):
    return [world.receptive_field(u).flatten().astype(float) for u in units]


def run(lateral: float, seed: int):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_maps"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", ETA)
    s.set_attr(s.nodes("MapParams")[0], "lateral", float(lateral))
    w = WaveWorld(s, h=H, w=W, seed=seed)
    us = add_cortex(w, GH, GW, rf=RF)

    hist: dict[int, list] = {}
    out = {}
    for t in range(max(CKPTS) + 1):
        if t in CKPTS:
            ws = _weights(w, us)
            anis = float(np.mean([orientation_selectivity(x) for x in ws]))
            prev = hist.get(t - DELTA)
            if prev is None:
                drift = float("nan")
            else:
                drift = float(np.mean([
                    np.linalg.norm(a - b) / max(np.linalg.norm(a), 1e-9)
                    for a, b in zip(ws, prev)]))
            nan = int(sum(1 for x in ws if not np.all(np.isfinite(x))))
            out[t] = (anis, drift, nan)
        if (t + DELTA) in CKPTS:
            hist[t] = _weights(w, us)
        w.step(ignite_k=1 if t % 5 == 0 else 0)
    return out


def main():
    seeds = list(range(4100, 4108))
    for lateral in (1.0, 0.0):
        rows = [run(lateral, sd) for sd in seeds]
        print(f"\n=== lateral={lateral:.0f}  (waves only, oja eta={ETA}, "
              f"{GH}x{GW} sheet, n={len(seeds)} seeds 4100-4107)")
        print(f"{'steps':>6} {'anisotropy':>11} {'drift':>8} {'NaN units':>10}")
        for t in CKPTS:
            a = float(np.mean([r[t][0] for r in rows]))
            d = float(np.mean([r[t][1] for r in rows]))
            n = int(sum(r[t][2] for r in rows))
            ds = "  —" if np.isnan(d) else f"{d:8.3f}"
            print(f"{t:6d} {a:11.3f} {ds} {n:10d}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
