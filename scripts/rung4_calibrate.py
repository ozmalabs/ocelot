"""RUNG 4 — CALIBRATE THE MAP MEASURE (PROTOCOL 1). Run BEFORE measuring the agent.

"A gate whose measure passes noise is not a gate." Stage 1's sign classifiers
passed random noise AND failed an ideal Gabor; anisotropy passed two checks and
failed the duration check for nine attempts. So this calibrates on all three,
plus the two readouts the map statistic is built out of.

  A. PREFERRED-ORIENTATION READOUT — an ideal Gabor at a KNOWN orientation must
     read back that orientation (up to the constant 90-degree spectral offset
     named in `preferred_orientation`'s docstring). If the per-unit readout is
     wrong, every map statistic built on it is meaningless.
  B. IDEAL MAP — a hand-built smooth map (orientation a linear ramp across the
     sheet) must score STRONGLY NEGATIVE (smoother than its shuffled null).
  C. RANDOM TUNING — uniformly random orientations must score AT the shuffled
     null (d ~ 0). This is the "does it pass noise?" check that Stage 1 failed.
  D. DURATION CONFOUND — the statistic must not drift with how long the SAME
     input is learned on. Run on the ACTUAL agent, waves only, lateral=0
     (the no-mechanism arm) at increasing durations: if d moves systematically
     with duration under the no-mechanism condition, the measure is
     duration-confounded and every arm comparison is meaningless.
  E. HAND-BUILT PINWHEEL — reported as a descriptive reference point only.

Seeds 4200-4215 (burned here; recorded in VISION_PROTOCOL.md's ledger).
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.cortex_sheet import (add_cortex, map_stats, map_smoothness,
                                  preferred_orientation, sheet_pairs,
                                  shuffled_null)

H = W = 16
RF = 7
GH = GW = 6
ETA = 5e-4


def gabor(theta_deg: float, n: int = 7, lam: float = 4.0, sigma: float = 2.0):
    """An ideal Gabor at `theta_deg`: a grating whose BARS run at theta_deg."""
    t = np.radians(theta_deg)
    c = np.arange(n) - (n - 1) / 2.0
    yy, xx = np.meshgrid(c, c, indexing="ij")
    # Perpendicular to the bars is the direction the grating varies along.
    xp = xx * np.cos(t) + yy * np.sin(t)
    yp = -xx * np.sin(t) + yy * np.cos(t)
    return np.exp(-(xp ** 2 + yp ** 2) / (2 * sigma ** 2)) * np.cos(2 * np.pi * yp / lam)


def check_a():
    print("\n=== A. PREFERRED-ORIENTATION READOUT vs an IDEAL GABOR")
    print(f"{'true bars':>10} {'read':>8} {'read-90 (mod180)':>18} {'err':>7}")
    errs = []
    for th in (0, 15, 30, 45, 60, 75, 90, 120, 150):
        r = preferred_orientation(gabor(th))
        corr = (r - 90.0) % 180.0
        e = min(abs(corr - th) % 180.0, 180.0 - abs(corr - th) % 180.0)
        errs.append(e)
        print(f"{th:10d} {r:8.1f} {corr:18.1f} {e:7.2f}")
    ok = max(errs) < 5.0
    print(f"  max error {max(errs):.2f} deg  ->  {'PASS' if ok else 'FAIL'}"
          "  (constant -90 offset = spectral energy is perpendicular to bars)")
    return ok


def _ideal_map_thetas(gh, gw, cycles=1.0):
    return [(180.0 * cycles * j / gw) % 180.0 for i in range(gh) for j in range(gw)]


def check_b():
    print("\n=== B. IDEAL (hand-built smooth) MAP — orientation ramps across the sheet")
    ps = sheet_pairs(GH, GW)
    th = _ideal_map_thetas(GH, GW)
    obs = map_smoothness(th, ps)
    null = shuffled_null(th, ps, n_perm=2000, seed=1)
    d = obs - null
    print(f"  smoothness {obs:.2f}   null {null:.2f}   d {d:+.2f}")
    ok = d < -15.0
    print(f"  -> {'PASS' if ok else 'FAIL'} (an ideal map must score strongly negative)")
    return ok


def check_c():
    print("\n=== C. RANDOM TUNING — must score AT the shuffled null (the noise check)")
    ps = sheet_pairs(GH, GW)
    ds = []
    for sd in range(4200, 4216):
        rng = np.random.default_rng(sd)
        th = list(rng.uniform(0, 180, GH * GW))
        ds.append(map_smoothness(th, ps) - shuffled_null(th, ps, n_perm=500, seed=sd))
    m, se = float(np.mean(ds)), float(np.std(ds, ddof=1) / np.sqrt(len(ds)))
    print(f"  d = {m:+.3f} +/- {se:.3f} (SEM, n={len(ds)} random draws)")
    ok = abs(m) < 3.0 * max(se, 1e-9) or abs(m) < 1.0
    print(f"  -> {'PASS' if ok else 'FAIL'} (random tuning must sit at the null)")
    return ok


def _run_agent(lateral, seed, steps):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_maps"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", ETA)
    s.set_attr(s.nodes("MapParams")[0], "lateral", float(lateral))
    w = WaveWorld(s, h=H, w=W, seed=seed)
    us = add_cortex(w, GH, GW, rf=RF)
    for i in range(steps):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    return map_stats(w, us, GH, GW, n_perm=200, seed=seed)


def check_d():
    print("\n=== D. DURATION CONFOUND — the no-mechanism arm (lateral=0) vs duration")
    print("    (if d moves systematically with duration here, the measure is confounded)")
    seeds = list(range(4200, 4208))
    print(f"{'steps':>6} {'d (deg)':>10} {'SEM':>7} {'anisotropy':>11}")
    rows = []
    for steps in (200, 400, 800, 1600, 3200):
        st = [_run_agent(0.0, sd, steps) for sd in seeds]
        ds = [x["d"] for x in st]
        m = float(np.mean(ds))
        se = float(np.std(ds, ddof=1) / np.sqrt(len(ds)))
        a = float(np.mean([x["selectivity"] for x in st]))
        rows.append((steps, m, se))
        print(f"{steps:6d} {m:+10.2f} {se:7.2f} {a:11.3f}")
    return rows


def check_e():
    print("\n=== E. HAND-BUILT PINWHEEL (descriptive reference point only)")
    ps = sheet_pairs(GH, GW)
    cy, cx = (GH - 1) / 2.0, (GW - 1) / 2.0
    th = [(np.degrees(np.arctan2(i - cy, j - cx))) % 180.0
          for i in range(GH) for j in range(GW)]
    obs = map_smoothness(th, ps)
    null = shuffled_null(th, ps, n_perm=2000, seed=3)
    print(f"  smoothness {obs:.2f}   null {null:.2f}   d {obs - null:+.2f}")
    print("  (NOT a claim about the agent — a reference for what a pinwheel scores)")


def main():
    a, b, c = check_a(), check_b(), check_c()
    rows = check_d()
    check_e()
    print("\n=== CALIBRATION SUMMARY")
    print(f"  A ideal-Gabor orientation readout : {'PASS' if a else 'FAIL'}")
    print(f"  B ideal map scores smooth         : {'PASS' if b else 'FAIL'}")
    print(f"  C random tuning sits at null      : {'PASS' if c else 'FAIL'}")
    print("  D duration confound               : see table above")
    print(f"    d across 200..3200 steps: "
          f"{', '.join(f'{s}:{m:+.2f}' for s, m, _ in rows)}")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
