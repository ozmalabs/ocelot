"""DEFAULTS-OFF BYTE-IDENTITY: the v1.1.0 seed with bistable=0 must reproduce
the committed rung-3 numbers EXACTLY (PROTOCOL section 9)."""
import numpy as np, sys
sys.path.insert(0, ".")
import scratchpad3.r3lib as old, scratchpad3.r3b_lib as new
v = np.load(old.VIDEO32)
mx = 0.0
for seed in (0, 1, 2):
    for arm in ("untrained", "dark", "normal", "strobe"):
        a = old.run(arm, seed, v)
        b = new.run(arm, seed, v, bistable=0.0, bi_eta=0.0)
        mx = max(mx, abs(a - b))
        print(f"  seed {seed} {arm:10s} old={a:+.12f} new={b:+.12f} diff={abs(a-b):.3e}")
print(f"MAX DIFF = {mx:.3e}")
