"""RUNG 3B POWER PILOT — VARIANCE ONLY, on BURNED seeds 0-13 (PROTOCOL section 3.3).
Never used to choose a hypothesis, a direction or a parameter: it fixes n."""
import numpy as np, sys
sys.path.insert(0, ".")
from scratchpad3.r3b_lib import run, VIDEO32
BI_ETA = float(sys.argv[1])
v = np.load(VIDEO32)
S = list(range(14))
R = {a: np.array([run(a, s, v, bistable=1.0, bi_eta=BI_ETA) for s in S]) for a in
     ("untrained", "dark", "normal", "strobe")}
for nm, d in (("d_normal (normal-dark)", R["normal"] - R["dark"]),
              ("d_dark (dark-untrained)", R["dark"] - R["untrained"]),
              ("d_strobe (normal-strobe)", R["normal"] - R["strobe"])):
    print(f"{nm:26s} mean={d.mean():+.4f}  SD={d.std(ddof=1):.4f}", flush=True)
for a in R: print(f"  arm {a:10s} mean DSI {R[a].mean():+.4f}", flush=True)
