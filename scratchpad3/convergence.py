"""RUNG 3 — CONVERGENCE CHECK (PROTOCOL section 2), run BEFORE any arm.

Does dv_oja_learn settle on its own formative input distribution (waves)?
CONVERGENT + USEFUL = structure plateaus at non-zero AND drift -> 0.
Drift uses a FIXED window (||w(t) - w(t-50)|| / ||w(t)||) so the numbers at
different t are comparable — the whole point is to watch it fall.
This single check explains nine prior failed attempts, so it comes first.
"""
import numpy as np
import domains.seed_registry
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.dorsal_world import add_dunits, probe_dsi, dunit_weights

H = W = 16
RF = 7
MAXD = 3
NU = 10
NSEED = 8
CHECK = [0, 50, 100, 200, 400, 800, 1600, 3200]
DELTA = 50
SNAP = sorted({0} | {c for c in CHECK} | {c - DELTA for c in CHECK if c - DELTA > 0})


def mk(seed):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_dorsal"])
    dp = s.nodes("DorsalParams")[0]
    wp = s.nodes("WaveParams")[0]
    s.set_attr(dp, "dorsal", 1.0)
    s.set_attr(dp, "oja_eta", float(__import__("os").environ.get("ETA","5e-4")))
    s.set_attr(wp, "propagate", 1.0)
    w = WaveWorld(s, h=H, w=W, seed=seed, track_prev_burst=True)
    us = add_dunits(w, NU, rf=RF, max_delay=MAXD, rng=np.random.default_rng(seed))
    return s, w, us


res = {c: {"dsi": [], "drift": [], "wstd": [], "nan": 0} for c in CHECK}
for sd in range(NSEED):
    s, w, us = mk(sd)
    snaps = {}
    done = 0
    for target in SNAP:
        while done < target:
            w.step(ignite_k=1 if done % 5 == 0 else 0)
            done += 1
        snaps[target] = np.concatenate([dunit_weights(w, u) for u in us])
        if target in CHECK:
            res[target]["nan"] += int(np.isnan(snaps[target]).sum())
            res[target]["wstd"].append(float(np.nanstd(snaps[target])))
            res[target]["dsi"].append(float(probe_dsi(w, us, seed=sd).mean()))
    for c in CHECK:
        if c - DELTA < 0:
            continue
        a, b = snaps[c - DELTA], snaps[c]
        den = np.linalg.norm(b)
        res[c]["drift"].append(float(np.linalg.norm(b - a) / den) if den > 0 else np.nan)
    print("  seed %d done" % sd, flush=True)

print("\n" + "=" * 78)
print("RUNG 3 CONVERGENCE — dv_oja_learn on WAVES ONLY (n=%d seeds, eta=%s)" % (NSEED, __import__("os").environ.get("ETA","5e-4")))
print("drift = ||w(t) - w(t-%d)|| / ||w(t)||   (FIXED window)" % DELTA)
print("=" * 78)
print("%8s %13s %13s %13s %6s" % ("steps", "mean DSI", "weight std", "drift", "NaN"))
for c in CHECK:
    r = res[c]
    dr = ("%.4f" % np.nanmean(r["drift"])) if r["drift"] else "-"
    print("%8d %+13.4f %13.4f %13s %6d"
          % (c, np.mean(r["dsi"]), np.mean(r["wstd"]), dr, r["nan"]))
