"""eye_convergence — VISION_PROTOCOL.md §2, run FIRST and run before anything else.

"Before any experience/ablation arm is run, measure: does the rule settle?"
That single check explains nine failed attempts in this ladder. The stop
conditions are the protocol's, not mine:

  CONVERGENT + USEFUL : the score plateaus at non-zero structure AND drift -> 0
  never converges     : the scaffold is a TRANSIENT; every arm is then measured
                        at an arbitrary point on a decay curve
  converges to death  : drift -> 0 at ~0 structure; equally useless

Both of rung 6's stop conditions fired at once and it correctly STOPPED. If this
one fails, this rung reports the cause and stops too.

Seeds: 0-13 are already burned (the ledger), so calibration/convergence work
reuses them and consumes no clean confirmatory seed.
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
RF = 5
# The protocol's floor is >=3200. It is not enough here and that is a MEASURED
# fact, not a preference: the homeostat's theta rises in proportion to the
# response but falls at only lam*mu = 2.4e-4/step, so a high illumination
# overshoots theta and the recovery is slow. At k=1000 the reference is still
# moving at 6400 and only reaches drift 0 around 14k. Every check runs to 40k.
CHECKS = (0, 100, 400, 1600, 3200, 6400, 12800, 20000, 30000, 40000)


def scene(seed=99):
    rng = np.random.default_rng(seed)
    return (rng.random((H, W)) + 0.1).astype(np.float64)


def trace(*, logr=1.0, k=1.0, steps=6400, seed=0, mu=0.024, lam=0.01):
    """Run the receptor on a STATIC scene at illumination k and checkpoint the
    reference's drift + the population's mean response."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    w = EyeWorld(s, h=H, w=W, gaze_l=11, seed=seed)
    set_params(w, eye=1.0, logr=logr, saw=0.0, mu=mu, lam=lam)
    sc = scene() * k
    rows = []
    prev = w.thetas().copy()
    last = 0
    for c in CHECKS:
        for _ in range(c - last):
            w.step(frame=sc)
        last = c
        th = w.thetas()
        r = w.responses()
        # drift, the protocol's stability statistic: ||theta(t)-theta(t-d)|| / ||theta||
        den = np.linalg.norm(th) or 1.0
        drift = float(np.linalg.norm(th - prev) / den)
        prev = th.copy()
        rows.append((c, float(np.mean(r)), float(np.mean(th)), drift,
                     int(np.sum(~np.isfinite(r)))))
    return rows


def learn_trace(*, theta_mode, seed=0, eta=5e-4):
    """Convergence of the LEARNING layer, and — the part that matters — whether
    the arm is ALIVE while it is stable.

    PROTOCOL §4: "a mechanism could pass by making itself inert". The first
    version of this rung measured the theta-OUTSIDE arm at a rock-steady
    ||w||/||w0|| = 0.6188 and nearly reported a 33x stability win over BCM's
    0.0187 — but the unit was SILENT (meanrate 0.000000, max|dw| 0.000e+00) and
    the weights were frozen, not stable. `meanrate` and `max|dw|` are reported
    at every checkpoint precisely so that failure cannot hide again: an arm
    whose rate is 0 is INERT and its stability means nothing.
    """
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    w = EyeWorld(s, h=H, w=W, gaze_l=5, seed=seed)
    set_params(w, eye=1.0, logr=1.0, saw=0.0, theta_mode=theta_mode, eta=eta)
    us = w.add_units(4, rf=RF, seed=seed)
    rng = np.random.default_rng(1000 + seed)
    w0 = np.array([np.linalg.norm(w.weights(u)) for u in us])
    prev = np.concatenate([w.weights(u) for u in us])
    rows = []
    last = 0
    for c in CHECKS:
        rates = []
        for _ in range(c - last):
            w.step(frame=(rng.random((H, W)) + 0.1))
            rates.append(np.mean([float(w.s.node(u)["attrs"]["rate"]) for u in us]))
        last = c
        cur = np.concatenate([w.weights(u) for u in us])
        dw = float(np.max(np.abs(cur - prev))) if c else 0.0
        prev = cur.copy()
        nrm = np.array([np.linalg.norm(w.weights(u)) for u in us])
        rows.append((c, float(np.mean(nrm / w0)),
                     float(np.mean(rates)) if rates else 0.0, dw))
    return rows


def main():
    print(provenance_line())
    print(f"commit {os.popen('git rev-parse HEAD').read().strip()[:12]}")
    print()
    print("#" * 72)
    print("# PART 1 — the RECEPTOR + the adaptive reference")
    print("#" * 72)
    for logr, name in ((1.0, "LOG"), (0.0, "LINEAR")):
        for k in (1.0, 1000.0):
            print(f"=== {name}  k={k}   (target mean resp mu=0.024)")
            print(f"{'step':>6} {'mean resp':>11} {'mean theta':>11} "
                  f"{'drift':>9} {'nonfinite':>10}")
            for c, mr, mt, dr, nf in trace(logr=logr, k=k):
                print(f"{c:>6} {mr:>11.6f} {mt:>11.4f} {dr:>9.5f} {nf:>10}")
            print()

    print("#" * 72)
    print("# PART 2 — the LEARNING layer, and whether each arm is ALIVE.")
    print("# An arm with meanrate 0 and max|dw| 0 is INERT: its stability is")
    print("# frozen weights, and means nothing (PROTOCOL §4).")
    print("#" * 72)
    for tm, name in ((0.0, "theta OUTSIDE (GCAL)"), (1.0, "theta INSIDE (BCM)")):
        print(f"=== {name}")
        print(f"{'step':>6} {'||w||/||w0||':>13} {'mean rate':>11} "
              f"{'max|dw|':>11}   (mu=0.024)")
        for c, rel, mr, dw in learn_trace(theta_mode=tm):
            print(f"{c:>6} {rel:>13.4f} {mr:>11.6f} {dw:>11.3e}")
        print()


if __name__ == "__main__":
    main()
