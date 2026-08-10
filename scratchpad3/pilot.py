"""RUNG 3 PILOT — BURNED SEEDS 0-13 ONLY. Variance + event rates for the
pre-registration's power analysis. NO hypothesis test is run here."""
import time, numpy as np, sys
sys.path.insert(0, 'scratchpad3')
from r3lib import *

vid = np.load(VIDEO32)
print("event rates (descriptive), seed 0:")
for a,(tr,bu) in event_rates(0, vid).items():
    print("   %-9s transient/onset rate %.4f   burst duty %.4f" % (a, tr, bu))

N = 10
rows = []
t0 = time.time()
for i in range(N):
    sd = i                     # BURNED block 0-13
    rows.append([run(a, sd, vid) for a in ARMS])
    print("  seed %d  %s  (%.0fs)" % (sd, np.round(rows[-1],3), time.time()-t0), flush=True)
R = np.array(rows)
print("\narm means:", dict(zip(ARMS, np.round(R.mean(0),4))))
d_normal = R[:,2]-R[:,1]      # normal - dark
d_dark   = R[:,1]-R[:,0]      # dark - untrained
d_strobe = R[:,2]-R[:,3]      # normal - strobe
for nm, d in (("d_normal (normal-dark)",d_normal), ("d_dark (dark-untrained)",d_dark),
              ("d_strobe (normal-strobe)",d_strobe)):
    print("%-26s mean %+.4f   per-seed SD %.4f" % (nm, d.mean(), d.std(ddof=1)))
