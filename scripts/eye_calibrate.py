"""eye_calibrate — VISION_PROTOCOL.md §1: gate the MEASURE before the agent.

"A gate whose measure passes noise is not a gate." Stage 1's sign classifiers
passed random noise 50-75% of the time AND failed an ideal Gabor. So before the
invariance measure gates anything, it is run on:

  FLOOR    — input the measure must NOT call invariant (a DIFFERENT scene).
  IDEAL    — input the measure MUST call invariant (the SAME scene, same k).
  DURATION — the same input for different lengths of time. If the score moves
             with duration, the measure is duration-confounded and every arm
             comparison is meaningless (this killed anisotropy nine times).

THE STATISTIC, and why it is not the mean. At its fixed point the homeostat pins
mean(resp) = mu BY CONSTRUCTION, in EVERY arm — so "the mean response is
invariant" is a null instrument that passes for the most trivial possible reason.
The reference pins the MEAN; the question is what happens to the PATTERN. So:

    patdiff(k) = max_i | resp_i(k) - resp_i(1) |

over the receptor sheet, both arms measured AT CONVERGENCE (adaptation is what
an eye DOES; the transient is timed separately in eye_convergence.py).

THE 2x2, which is the real design. Neither mechanism is claimed to suffice:

                  |  homeo=1 (adaptive reference)  |  homeo=0 (none)
    --------------+--------------------------------+------------------
    logr=1 (log)  |  mean AND pattern invariant?   |  drifts by ln k?
    logr=0 (lin)  |  mean invariant, pattern NOT?  |  scales by k?

The prediction is that the REFERENCE is what makes the mean invariant and the
LOG is what makes the PATTERN invariant — log(a)-log(b) = log(a/b), so an
illumination change is an additive constant the reference subtracts away, and
what survives is the ratio. Both are needed; that is the claim.

Seeds 0-13 are burned already (the ledger). No confirmatory seed is spent here.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.eye_world import EyeWorld, set_params  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402

H = W = 8
ADAPT = 20_000   # fixed by eye_convergence.py, NOT tuned per arm


def scene(seed=99):
    rng = np.random.default_rng(seed)
    return (rng.random((H, W)) + 0.1).astype(np.float64)


def adapted(*, logr, homeo, k, sc, steps=ADAPT, seed=0):
    """Let the eye ADAPT to this illumination, then read its response. This is
    what a converged eye does; the transient is a separate measurement."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    w = EyeWorld(s, h=H, w=W, gaze_l=5, seed=seed)
    set_params(w, eye=1.0, logr=logr, homeo=homeo, saw=0.0)
    f = sc * k
    for _ in range(steps):
        w.step(frame=f)
    return w.responses(), w.thetas()


def patdiff(a, b):
    return float(np.max(np.abs(a - b)))


def main():
    print(provenance_line())
    print(f"commit {os.popen('git rev-parse HEAD').read().strip()[:12]}")
    print(f"adaptation steps = {ADAPT} (fixed by eye_convergence.py)")
    print()

    sc = scene(99)
    other = scene(1234)          # a DIFFERENT scene — the floor

    # ---------------- FLOOR: the measure must NOT call this invariant -------
    print("=== FLOOR — a DIFFERENT scene at the same illumination.")
    print("    The measure must score this FAR from 0, or it cannot tell")
    print("    'invariant' from 'anything at all'.")
    for logr, nm in ((1.0, "log"), (0.0, "linear")):
        r1, _ = adapted(logr=logr, homeo=1.0, k=1.0, sc=sc)
        r2, _ = adapted(logr=logr, homeo=1.0, k=1.0, sc=other)
        print(f"    {nm:>6}: patdiff(scene A, scene B) = {patdiff(r1, r2):.6f}")
    print()

    # ---------------- IDEAL: the measure MUST call this invariant -----------
    print("=== IDEAL — the SAME scene at the SAME illumination, adapted twice.")
    print("    Perfect invariance. The measure must score ~0.")
    for logr, nm in ((1.0, "log"), (0.0, "linear")):
        r1, _ = adapted(logr=logr, homeo=1.0, k=1.0, sc=sc)
        r2, _ = adapted(logr=logr, homeo=1.0, k=1.0, sc=sc)
        print(f"    {nm:>6}: patdiff(same, same) = {patdiff(r1, r2):.6e}")
    print()

    # ---------------- DURATION: the confound that killed nine attempts ------
    print("=== DURATION — the same input, different training lengths.")
    print("    If patdiff moves with duration, the measure is duration-")
    print("    confounded and every arm comparison below is meaningless.")
    for logr, nm in ((1.0, "log"), (0.0, "linear")):
        base, _ = adapted(logr=logr, homeo=1.0, k=1.0, sc=sc, steps=ADAPT)
        for d in (10_000, 20_000, 40_000):
            r, _ = adapted(logr=logr, homeo=1.0, k=1.0, sc=sc, steps=d)
            print(f"    {nm:>6} steps={d:>6}: patdiff vs {ADAPT} = "
                  f"{patdiff(r, base):.6e}")
    print()

    # ---------------- THE 2x2 ----------------------------------------------
    print("=== THE 2x2 — patdiff(k) vs the SAME scene at k=1, adapted at each k.")
    for logr, nm in ((1.0, "log"), (0.0, "linear")):
        for homeo, hn in ((1.0, "homeo"), (0.0, "no-homeo")):
            base, th1 = adapted(logr=logr, homeo=homeo, k=1.0, sc=sc)
            row = []
            for k in (10.0, 100.0, 1000.0):
                r, th = adapted(logr=logr, homeo=homeo, k=k, sc=sc)
                row.append(f"k={k:<7.0f} patdiff={patdiff(r, base):>10.4f} "
                           f"meanresp={r.mean():>10.4f} theta={th.mean():>9.3f}")
            print(f"  --- {nm} / {hn}   (k=1: meanresp={base.mean():.4f}, "
                  f"theta={th1.mean():.3f})")
            for x in row:
                print(f"      {x}")
    print()


if __name__ == "__main__":
    main()
