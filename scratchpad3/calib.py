"""RUNG 3 — DSI CALIBRATION (PROTOCOL section 1). Burned seeds only."""
import sys
import numpy as np
import domains.seed_registry
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.dorsal_world import (add_dunits, probe_dsi, set_dunit_ideal,
                                  dunit_weights, DIRECTIONS)

H = W = 16
RF = 7
MAXD = 3
NU = 10


def mk(seed, *, dorsal=1.0, propagate=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_dorsal"])
    dp = s.nodes("DorsalParams")[0]
    wp = s.nodes("WaveParams")[0]
    s.set_attr(dp, "dorsal", float(dorsal))
    s.set_attr(dp, "oja_eta", 5e-4)
    s.set_attr(wp, "propagate", float(propagate))
    w = WaveWorld(s, h=H, w=W, seed=seed, track_prev_burst=True)
    us = add_dunits(w, NU, rf=RF, max_delay=MAXD, rng=np.random.default_rng(seed))
    return s, w, us


print("=" * 74)
print("DSI CALIBRATION — burned seeds only (0-13 exploration block)")
print("=" * 74)

# ---- 1. FLOOR: untrained/random units --------------------------------------
print("\n[1] RANDOM / UNTRAINED units (no learning at all) — must be at FLOOR 0")
fl = []
for sd in range(8):
    s, w, us = mk(sd)
    d = probe_dsi(w, us, seed=sd)
    fl.append(d.mean())
    print("    seed %2d   mean DSI %+.4f   per-unit sd %.4f" % (sd, d.mean(), d.std()))
fl = np.array(fl)
print("    FLOOR = %+.4f   (SD across seeds %.4f, |t|=%.2f)"
      % (fl.mean(), fl.std(ddof=1), abs(fl.mean() / (fl.std(ddof=1) / np.sqrt(len(fl))))))

# ---- 2. IDEAL direction-selective unit -------------------------------------
print("\n[2] IDEAL hand-built direction-selective units — must score HIGH")
for th_i, th in enumerate([0.0, np.pi / 2]):
    ideals = []
    for sd in range(4):
        s, w, us = mk(sd)
        for u in us:
            set_dunit_ideal(w, u, th)
        d = probe_dsi(w, us, seed=sd)
        ideals.append(d.mean())
    print("    ideal theta=%3d deg   mean DSI %+.4f  (per-seed %s)"
          % (th * 180 / np.pi, np.mean(ideals), np.round(ideals, 3)))

# ---- 3. DURATION CONFOUND --------------------------------------------------
print("\n[3] DURATION CHECK — DSI vs training length on the SAME input (waves)")
print("    a score that moves with duration on ONE input is duration-confounded")
for steps in (0, 200, 800, 1600, 3200):
    vals = []
    for sd in range(6):
        s, w, us = mk(sd)
        for i in range(steps):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
        vals.append(probe_dsi(w, us, seed=sd).mean())
    v = np.array(vals)
    print("    waves x %4d steps   DSI %+.4f  (SD %.4f)" % (steps, v.mean(), v.std(ddof=1)))
