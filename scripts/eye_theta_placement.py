"""eye_theta_placement — theta OUTSIDE the learning rule (GCAL) vs theta INSIDE
it (BCM), on ONE architecture where the ONLY difference is the placement.

THE CLAIM UNDER TEST (VISION_PRIOR_ART.md §2.3). BCM's theta sits inside the
learning rule and gates the SIGN of dw; if it outruns activity, everything
depresses and the weights annihilate — this tree measured exactly that (0.004).
GCAL's theta sits on the ACTIVATION FUNCTION, outside the rule, and never
touches dw's sign; it is therefore structurally unable to annihilate. The
sharpest version of the point is that these are the SAME VARIABLE in two places,
so a comparison that changes nothing else isolates the placement itself.

`theta_mode` selects the arm as DATA on EyeParams (PROTOCOL §0) — not a Python
code path, not two models.

WHAT THE STATISTIC IS. Structure = the L2 norm of the unit's weight vector,
normalised by its initial norm. Annihilation is norm -> 0. This is deliberately
NOT a selectivity measure: rung 5 established that reading structure OUT of a
response needs an instrument of its own, and the question here is only whether
the weights SURVIVE.

Seeds 0-13 are already burned (the ledger); this is calibration, not a
confirmatory run.
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
CHECKS = (0, 100, 200, 400, 800, 1600, 3200, 6400)


def run(*, theta_mode, seed=0, steps=6400, eta=5e-4):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_eye"])
    w = EyeWorld(s, h=H, w=W, gaze_l=11, seed=seed)
    set_params(w, eye=1.0, logr=1.0, saw=0.0, theta_mode=theta_mode, eta=eta)
    us = w.add_units(4, rf=RF, seed=seed)
    rng = np.random.default_rng(1000 + seed)
    w0 = np.array([np.linalg.norm(w.weights(u)) for u in us])
    out = []
    last = 0
    for c in CHECKS:
        for _ in range(c - last):
            # A fresh natural-ish scene each step: the input ensemble, not a
            # single frozen stimulus.
            w.step(frame=(rng.random((H, W)) + 0.1))
        last = c
        nrm = np.array([np.linalg.norm(w.weights(u)) for u in us])
        out.append((c, float(np.mean(nrm / w0)), float(np.mean(nrm))))
    return out


def main():
    print(provenance_line())
    print(f"commit {os.popen('git rev-parse HEAD').read().strip()[:12]}")
    print()
    for tm, name in ((0.0, "theta OUTSIDE (GCAL)"), (1.0, "theta INSIDE (BCM)")):
        print(f"=== {name}")
        print(f"{'step':>6} {'||w||/||w0||':>14} {'||w||':>10}")
        for c, rel, nrm in run(theta_mode=tm):
            print(f"{c:>6} {rel:>14.4f} {nrm:>10.4f}")
        print()


if __name__ == "__main__":
    main()
