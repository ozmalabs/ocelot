"""invariant_arch_end_to_end — recognizer (2): the agent's 2-stage recognition
architecture (recognition_arch_accept), RAW units vs INVARIANT units, apples-to-
apples. The ONLY change between the two runs is whether each sign's gammatone
trajectory passes through the agent's now-default invariance chain (CMVN ->
predict-remove k=0.5, REPLACE form) before the both-ears centroid is formed.

It monkeypatches recognition_arch_accept._clip_perception to apply the invariant
transform, then runs the accept's full pipeline (develop -> ground cues -> Stage-1
exemplar kNN -> Stage-2 tie-breaks) once RAW and once INVARIANT, capturing the
Stage-1-only and full-fix accuracies from stdout. No tuning.

Run: python -m scripts.invariant_arch_end_to_end
"""
import io
import os
import re
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.getcwd())

import numpy as np

import scripts.recognition_arch_accept as RA
from domains.invariant_units import cmvn, predict_remove

TRAJ_SAMPLES = 32

_ORIG_CLIP = RA._clip_perception
_APPLY = {"on": False}


def _invariant_traj(traj_flat):
    v = np.asarray(traj_flat, dtype=np.float64)
    if v.size % TRAJ_SAMPLES != 0:
        return v
    n_patch = v.size // TRAJ_SAMPLES
    M = v.reshape(TRAJ_SAMPLES, n_patch)
    M = cmvn(M, do_variance=True)
    M = predict_remove(M, window=2, k=0.5)
    return M.reshape(-1).astype(np.float64)


def _patched_clip(sub, pipe, samples, res):
    """Same as the accept's _clip_perception, but rewrite each sign's stored
    `trajectory` attr through the invariance chain before it gathers gv. We reuse
    the original to gather signs, then recompute gv from the invariant trajectories.
    """
    gv, fv, signs = _ORIG_CLIP(sub, pipe, samples, res)
    if not _APPLY["on"] or not signs:
        return gv, fv, signs
    g = []
    for s in signs:
        a = sub.node(s)["attrs"]
        t = a.get("trajectory")
        if t:
            g.append(_invariant_traj(np.array(t, dtype=float)))
    if not g:
        return gv, fv, signs
    n = float(np.linalg.norm(np.mean(g, axis=0)))
    giv = np.mean(g, axis=0)
    giv = giv / n if n > 0 else giv
    return giv, fv, signs


def _run_once(invariant: bool):
    _APPLY["on"] = invariant
    RA._clip_perception = _patched_clip
    buf = io.StringIO()
    with redirect_stdout(buf):
        RA.main()
    out = buf.getvalue()
    s1 = re.search(r"Stage-1 global only.*?(\d+\.\d+)%", out)
    full = re.search(r"FULL FIX\).*?(\d+\.\d+)%", out)
    s1v = float(s1.group(1)) if s1 else None
    fullv = float(full.group(1)) if full else None
    return s1v, fullv, out


def main():
    print("=== recognizer (2): 2-stage recognition architecture ===\n")
    print("--- RAW units ---", flush=True)
    raw_s1, raw_full, _ = _run_once(False)
    print(f"  Stage-1 only = {raw_s1}%   full fix = {raw_full}%", flush=True)
    print("\n--- INVARIANT units (CMVN+predict-remove) ---", flush=True)
    inv_s1, inv_full, _ = _run_once(True)
    print(f"  Stage-1 only = {inv_s1}%   full fix = {inv_full}%", flush=True)

    print("\n================ SUMMARY (FSDD held-out jackson, 10-way) ===========")
    print(f"  {'features':30s}{'Stage-1 only':>14s}{'full fix':>12s}")
    print(f"  {'RAW units':30s}{str(raw_s1)+'%':>14s}{str(raw_full)+'%':>12s}")
    print(f"  {'INVARIANT units':30s}{str(inv_s1)+'%':>14s}{str(inv_full)+'%':>12s}")
    print(f"  {'baseline (doc)':30s}{'':>14s}{'55.8%':>12s}")
    if raw_full is not None and inv_full is not None:
        d = inv_full - raw_full
        print(f"\n  VERDICT (full fix): raw {raw_full}% -> invariant {inv_full}% "
              f"(Δ {d:+.1f} pts)")
        if d > 0:
            print("  => cleaner perception MOVES the arch recognizer.")
        elif d == 0:
            print("  => arch recognition FLAT — loss is in the recognition stage.")
        else:
            print("  => invariant units HURT the arch recognizer.")


if __name__ == "__main__":
    main()
