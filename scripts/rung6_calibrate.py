"""RUNG 6 — CALIBRATE THE MEASURE (PROTOCOL 1), on burned seeds only (0-2).

Three checks, all mandatory before any gate:
  1. an IDEAL exemplar must score high  -> the TARGET
  2. random/untrained must score at the floor -> the FLOOR
  3. the score must not move with learning DURATION on the same input
Plus the freeze audit: `oja=0` is NOT a freeze; the real one must be exact.
"""
from __future__ import annotations

import numpy as np

from scripts.rung6_lib import (build, run_waves, osi_of, ideal_split_gabor,
                               adapt_theta, RF, PERIOD, H, W)
from domains.onoff_world import (freeze, set_params, signed_rf, weights,
                                 segregation, install_signed_rf)
from domains.complex_cells import cell_stats, gabor


def line(k, v):
    print(f"  {k:<46s} {v}")


print("=" * 78)
print("RUNG 6 CALIBRATION — the SIGNED simple layer (seeds 0-2, already burned)")
print("=" * 78)

# --------------------------------------------------------------------------- #
# 1. THE IDEAL EXEMPLAR — what a PERFECT signed simple cell scores here
# --------------------------------------------------------------------------- #
print("\n[1] IDEAL EXEMPLAR (the TARGET) — a Gabor split across two nonneg channels")
w, us, bip = build(seed=0, n_units=4)
for i, th in enumerate((0.0, 45.0, 90.0, 135.0)):
    ideal_split_gabor(w, us[i], theta=th)
adapt_theta(w, 400)          # the SAME threshold adaptation every arm gets
o, st = osi_of(w, us)
for i, th in enumerate((0.0, 45.0, 90.0, 135.0)):
    line(f"ideal SPLIT-Gabor {th:5.1f} deg  OSI", f"{o[i]:.4f}   "
         f"F1/F0 {st['f1f0'][i]:.3f}  base/act {st['baseline'][i]/max(st['tuning'][i].max(),1e-9):.3f}")
TARGET = float(np.mean(o))
line("TARGET = mean ideal split-Gabor OSI", f"{TARGET:.4f}")

wnt, unt, _ = build(seed=0, n_units=4)
for i, th in enumerate((0.0, 45.0, 90.0, 135.0)):
    ideal_split_gabor(wnt, unt[i], theta=th)
ont, _ = osi_of(wnt, unt)    # homeo never ran => theta pinned at 0
line("ideal split-Gabor, NO threshold (theta=0)", f"{ont.mean():.4f}   "
     "<- the measured reason the threshold is in the model")

# the same Gabor with NO split (single nonneg channel) — rung 5's condition,
# reproduced here as a sanity check that the CONTROL really is the old failure
w2, us2, _ = build(seed=0, n_units=1, split=0.0)
ideal_split_gabor(w2, us2[0], theta=0.0)
adapt_theta(w2, 400)
o2, st2 = osi_of(w2, us2)
line("ideal Gabor, split ABLATED (split=0)  OSI", f"{o2[0]:.4f}")

# --------------------------------------------------------------------------- #
# 2. THE FLOOR — untrained
# --------------------------------------------------------------------------- #
print("\n[2] THE FLOOR — untrained SUnits (uniform weights + tie-break jitter)")
floors = []
for sd in (0, 1, 2):
    wf, uf, _ = build(seed=sd, n_units=6)
    adapt_theta(wf, 400)     # matched: theta adapts, NO weight moves
    of, _ = osi_of(wf, uf)
    floors.append(of)
    line(f"seed {sd}: mean OSI", f"{of.mean():.4f}   max {of.max():.4f}")
FLOOR = float(np.mean([f.mean() for f in floors]))
line("FLOOR = mean untrained OSI", f"{FLOOR:.4f}")

SESOI = 0.10 * (TARGET - FLOOR)
line("SESOI = 10% of dynamic range", f"{SESOI:.4f}")

# --------------------------------------------------------------------------- #
# 3. DURATION CHECK — does the MEASURE move with training length?
# --------------------------------------------------------------------------- #
print("\n[3] DURATION CHECK (PROTOCOL 1's third test)")
for steps in (0, 400, 1600, 3200):
    wd, ud, _ = build(seed=0, n_units=6)
    run_waves(wd, steps)
    od, _ = osi_of(wd, ud)
    line(f"waves {steps:5d} steps: mean OSI", f"{od.mean():.4f}  max {od.max():.4f}")

# --------------------------------------------------------------------------- #
# 4. THE FREEZE AUDIT — oja=0 is NOT a freeze
# --------------------------------------------------------------------------- #
print("\n[4] FREEZE AUDIT — a probe must never train what it measures")
wA, uA, _ = build(seed=0, n_units=6)
run_waves(wA, 200)
before = weights(wA, uA).copy()
freeze(wA)
cell_stats(wA, uA, key="act", period=PERIOD)
after = weights(wA, uA)
line("REAL freeze  max |dw| across a full probe", f"{np.abs(after-before).max():.3e}")

wB, uB, _ = build(seed=0, n_units=6)
run_waves(wB, 200)
before = weights(wB, uB).copy()
set_params(wB, frozen=0.0)                    # the DEFECTIVE 'freeze'
for p in wB.s.nodes("WaveParams"):
    wB.s.set_attr(p, "oja", 0.0)              # <- the trap
cell_stats(wB, uB, key="act", period=PERIOD)
after = weights(wB, uB)
line("DEFECTIVE freeze (oja=0) max |dw|", f"{np.abs(after-before).max():.3e}")

print("\n" + "=" * 78)
print(f"FLOOR {FLOOR:.4f}   TARGET {TARGET:.4f}   SESOI {SESOI:.4f}")
print("=" * 78)
