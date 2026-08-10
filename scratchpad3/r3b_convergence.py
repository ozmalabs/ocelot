"""RUNG 3B CONVERGENCE (PROTOCOL section 2) — run FIRST, before any arm.
Does the BISTABLE rule SETTLE on its own formative input distribution (waves)?
Checkpoint DSI, weight structure AND drift = ||w(t)-w(t-50)||/||w(t)|| out to
3200 steps. CONVERGENT+USEFUL = plateau at non-zero structure AND drift -> 0.
Nine rung-2 attempts failed because they were measured on a transient; a rule
that never settles, or settles on nothing, is dead and is reported as such.
Burned seeds 0-7 ONLY."""
import numpy as np, sys
sys.path.insert(0, ".")
from scratchpad3.r3b_lib import boot, probe_dsi
from domains.dorsal_world import dunit_weights

SEEDS = tuple(range(8))
CKPT = (0, 50, 200, 800, 1600, 3200)
BI_ETA = float(sys.argv[1]) if len(sys.argv) > 1 else 3e-2


def one(seed):
    s, w, us, dp, wp = boot(seed, bistable=1.0, bi_eta=BI_ETA)
    rows, i, prev = {}, 0, None
    for c in CKPT:
        while i < c:
            if i == c - 50:
                prev = np.concatenate([dunit_weights(w, u) for u in us])
            w.step(ignite_k=1 if i % 5 == 0 else 0, frame=None)
            i += 1
        cur = np.concatenate([dunit_weights(w, u) for u in us])
        drift = (float(np.linalg.norm(cur - prev) / max(np.linalg.norm(cur), 1e-12))
                 if prev is not None else np.nan)
        d = probe_dsi(w, us, seed=seed)
        rows[c] = (float(np.nanmean(d)), float(np.nanstd(cur)), drift,
                   int(np.isnan(cur).sum() + np.isnan(d).sum()))
    return rows


R = [one(s) for s in SEEDS]
print(f"CONVERGENCE, bistable=1, bi_eta={BI_ETA:g}, waves only, n={len(SEEDS)}\n")
print("| steps | mean DSI | weight std | drift | NaN |")
print("|---|---|---|---|---|")
for c in CKPT:
    dsi = np.mean([r[c][0] for r in R]); sd = np.mean([r[c][1] for r in R])
    dr = np.mean([r[c][2] for r in R]); nan = sum(r[c][3] for r in R)
    ds = "—" if np.isnan(dr) else f"{dr:.4f}"
    print(f"| {c} | {dsi:+.4f} | {sd:.4f} | {ds} | {nan} |", flush=True)
