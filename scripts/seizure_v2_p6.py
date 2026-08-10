"""V2-P6 (EXPLORATORY) — one escalation term, two pathologies.

The escalation ingredient (alpha: over-threshold residual regenerates more
residual) is the SAME in both regimes. What differs is whether it is allowed to
COUPLE laterally:

  SEIZURE       : alpha + recruitment coupling (g_rec>0)  -> SPREADING traveling wave
  HALLUCINATION : alpha with NO lateral spread (g=0, g_rec=0) -> a persistent,
                  spatially STATIONARY confabulated pattern locked to the onset
                  footprint (a percept self-sustained after the input is removed).

Prereg signature (SEIZURE_MODEL_V2_PREREG.md V2-P6): source-escalation persists
with LOW propagation (max_front ~ onset radius, onset_prop ~ 0, high stable
post-onset rank-1) vs the recruitment seizure's large front + propagation.
Writes results/seizure_v2_p6.json. Clearly EXPLORATORY; a null is reported.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.seizure_engine_lattice as M

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "results", "seizure_v2_p6.json")


def post_onset_rank1(res, arch):
    """rank-1 fraction of the spatial pattern AFTER the drive is removed
    (stationary self-sustained pattern => high & stable)."""
    idx = [k for k, tt in enumerate(res["snap_t"]) if tt >= arch.t_onset]
    if len(idx) < 3:
        return float("nan")
    M2 = np.stack([res["snaps"][k].ravel() for k in idx], axis=0)
    M2 = M2 - M2.mean()
    if not np.any(M2):
        return float("nan")
    s = np.linalg.svd(M2, compute_uv=False)
    return float(s[0] ** 2 / (s ** 2).sum())


def signature(res, arch):
    c = M.classify(res, arch)
    return {
        "persists": c["persists"], "final_active": c["final_active"],
        "max_front": c["max_front"], "onset_prop_areas": c["onset_prop_areas"],
        "peak_active": c["peak_active"], "speed_mm_s": c["speed_mm_s"],
        "post_onset_rank1": post_onset_rank1(res, arch),
    }


def run_p6():
    a = M.Arch()
    arms = {}
    # SEIZURE: recruitment coupling on, moderate alpha, low give
    r = M.run_one(a, D=3.0, give=0.5, alpha=0.5, seed=5, g_rec=0.2)
    arms["seizure_recruitment"] = {"params": {"g": a.g, "g_rec": 0.2, "alpha": 0.5, "give": 0.5},
                                   "sig": signature(r, a)}
    # HALLUCINATION: no lateral spread (override g=0), high alpha, low give
    a0 = M.Arch(g=0.0)  # kill diffusion channel too
    for al in (0.5, 1.0, 2.0, 3.0):
        r = M.run_one(a0, D=3.0, give=0.5, alpha=al, seed=5, g_rec=0.0)
        arms[f"halluc_alpha{al}"] = {"params": {"g": 0.0, "g_rec": 0.0, "alpha": al, "give": 0.5},
                                     "sig": signature(r, a0)}
    # CONTROLS on the hallucination config: full give should NOT persist; alpha=0 should not
    r = M.run_one(a0, D=3.0, give=1.0, alpha=2.0, seed=5, g_rec=0.0)
    arms["halluc_ctrl_fullgive"] = {"params": {"g": 0.0, "g_rec": 0.0, "alpha": 2.0, "give": 1.0},
                                    "sig": signature(r, a0)}
    r = M.run_one(a0, D=3.0, give=0.5, alpha=0.0, seed=5, g_rec=0.0)
    arms["halluc_ctrl_alpha0"] = {"params": {"g": 0.0, "g_rec": 0.0, "alpha": 0.0, "give": 0.5},
                                  "sig": signature(r, a0)}
    return {"arms": arms}


if __name__ == "__main__":
    out = run_p6()
    for k, v in out["arms"].items():
        s = v["sig"]
        print(f"{k:<24} persist={str(s['persists']):<5} final={s['final_active']:>8.1f} "
              f"front={s['max_front']:>6.2f} prop={s['onset_prop_areas']:>6.2f} "
              f"postR1={s['post_onset_rank1']:.3f}")
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)
