"""RUNG 3 — THE CONFIRMATORY RUN. Executes VISION_RUNG3_PREREG.md exactly.

Seeds 4000-4099. Exactly three hypothesis tests. No sweeps. No re-runs.
"""
import sys
import time
import numpy as np
sys.path.insert(0, 'scratchpad3')
from r3lib import ARMS, VIDEO32, ETA, P1, P2, run, signflip, event_rates

N = 100
S0 = 4000
ALPHA = 0.05 / 3          # Bonferroni, fixed in the pre-registration
SESOI = 0.049             # 10% of the calibrated dynamic range (0.111 -> 0.600)

vid = np.load(VIDEO32)
rows = []
t0 = time.time()
for i in range(N):
    sd = S0 + i
    rows.append([run(a, sd, vid) for a in ARMS])
    if (i + 1) % 10 == 0:
        print("  %d/%d  %.0fs" % (i + 1, N, time.time() - t0), flush=True)
R = np.array(rows)
np.save("scratchpad3/confirm_R.npy", R)

d_normal = R[:, 2] - R[:, 1]      # normal - dark
d_dark = R[:, 1] - R[:, 0]        # dark   - untrained
d_strobe = R[:, 2] - R[:, 3]      # normal - strobe

rng = np.random.default_rng(20260717)
print("\n" + "=" * 78)
print("RUNG 3 CONFIRMATORY — direction selectivity (n=%d seeds %d-%d)" % (N, S0, S0 + N - 1))
print("eta=%.0e  P1=%d  P2=%d   Bonferroni alpha=%.4f   SESOI=%.3f"
      % (ETA, P1, P2, ALPHA, SESOI))
print("=" * 78)

res = {}
for nm, d, pred in (("H1a d_normal  (normal - dark)", d_normal, "> 0"),
                    ("H1b d_dark    (dark - untrained)", d_dark, "~ 0"),
                    ("H1c d_strobe  (normal - strobe)", d_strobe, "> 0")):
    obs, p, lo, hi = signflip(d, rng)
    res[nm.split()[0]] = (obs, p, lo, hi)
    print("%-34s %+.4f  95%% CI [%+.4f, %+.4f]  p=%.4f   (predicted %s)"
          % (nm, obs, lo, hi, p, pred))

a_obs, a_p, a_lo, a_hi = res["H1a"]
b_obs, b_p, b_lo, b_hi = res["H1b"]
c_obs, c_p, c_lo, c_hi = res["H1c"]

h1a = (a_obs > 0) and (a_p < ALPHA)
h1b = (b_lo > -SESOI) and (b_hi < SESOI)        # equivalence to the floor
h1c = (c_obs > 0) and (c_p < ALPHA)
print("\n  H1a (experience produces direction) : %s" % ("PASS" if h1a else "FAIL"))
print("  H1b (waves do NOT, equiv +-%.3f)    : %s" % (SESOI, "PASS" if h1b else "FAIL"))
print("  H1c (motion, not spatial structure) : %s" % ("PASS" if h1c else "FAIL"))
print("\nDECISION: %s" % ("*** RUNG 3 BUILT ***" if (h1a and h1b and h1c)
                          else "NOT BUILT — reported exactly as observed"))

print("\n--- descriptive (NOT tests) ---")
print("  arm means: " + " | ".join("%s %.4f" % (a, m) for a, m in zip(ARMS, R.mean(0))))
print("  floor (untrained) %.4f ; ideal (calibration) 0.600 ; range %.3f"
      % (R[:, 0].mean(), 0.600 - R[:, 0].mean()))
for nm, (obs, p, lo, hi) in res.items():
    print("  %s = %+.4f = %+.1f%% of the dynamic range" % (nm, obs, 100 * obs / 0.489))
print("  strobe - untrained = %+.4f  (negative => strobe DISSOLVES the innate bias)"
      % (R[:, 3] - R[:, 0]).mean())
print("  per-seed SD: d_normal %.4f  d_dark %.4f  d_strobe %.4f"
      % (d_normal.std(ddof=1), d_dark.std(ddof=1), d_strobe.std(ddof=1)))
print("\n  event rates, seed %d:" % S0)
for a, (tr, bu) in event_rates(S0, vid).items():
    print("    %-9s onset %.4f   burst duty %.4f" % (a, tr, bu))
