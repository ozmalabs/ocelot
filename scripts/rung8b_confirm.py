"""RUNG 8B — THE CONFIRMATORY RUN (rung 8's H1/H2, now readable).

**RUNS ONLY IF THE §1 GATE PASSED** (`scripts/rung8b_calibrate.py`). Rungs 5, 6,
8 and phase 0 all correctly burned nothing when their gates failed.

Pre-registered in `VISION_RUNG8B_PREREG.md` §8, BEFORE this ran:

  H1 — SUnits on rung 7's decorrelated channels become orientation-selective:
       OSI >> the LATERAL untrained floor measured IN THIS RUN, under THIS
       theta rule.
  H2 — on the DEGENERATE split, OSI stays at ITS OWN floor (rung 6's negative,
       reproduced as the control).

Two-sided: an OSI BELOW the floor is as reportable as above (rung 3's `strobe`
dissolved an innate bias below the floor, and only an `untrained` arm caught it).

THE STATISTIC (PROTOCOL §4): mean OSI per SEED — never per unit. Units in a run
share input and compete under WTA, so they are not independent; counting units
inflated every early p-value in this arc.

Because the two arms have DIFFERENT floors and the degenerate control is
emphatically NON-NULL, the pre-registered test is the INTERACTION:

    D_arm       = OSI(trained, arm) - OSI(untrained, arm)     [paired, per seed]
    INTERACTION = D_lateral - D_degenerate

SESOI 0.0595 (rung 6's, adopted unchanged — same layer, same probe).
CONFIRMATORY SEEDS: 13000+, never used for anything.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.complex_cells import present  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from domains.lateral_world import set_lat_params  # noqa: E402
from domains.onoff_world import set_params  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    develop_retina, freeze_all, osi_of, run_waves,
)
from scripts.rung8b_lib import (  # noqa: E402
    build8b, grating_ensemble, set_theta_params, theta_of,
)

SESOI = 0.0595
ADAPT = 5000
TRAIN = 6400
N_UNITS = 6


def one(chan, seed, *, trained, adapt=ADAPT, train=TRAIN):
    """develop the retina -> (TRAIN the cortex on WAVES) -> adapt theta on the
    ensemble being responded to -> PIN theta -> measure. Mechanical."""
    w, us, _a, _b = build8b(seed=seed, n_units=N_UNITS, channels=chan,
                            theta_mode=1.0)
    develop_retina(w, 3000)
    if trained:
        # THE FORMATIVE INPUT: the agent's OWN spontaneous waves.
        set_params(w, frozen=0.0)
        if w.s.nodes("LatParams"):
            set_lat_params(w, frozen=1.0)   # rung 7 is already at its fixed point
        run_waves(w, train)
    freeze_all(w)
    set_theta_params(w, theta_adapt=1.0)
    rng = np.random.default_rng(7)
    for _ in range(adapt):
        present(w, grating_ensemble(w, rng))
    set_theta_params(w, theta_adapt=0.0)
    o, _ = osi_of(w, us)
    return float(o.mean()), float(theta_of(w).mean())


def ci(x, n_boot=20000, seed=0):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    bs = rng.choice(x, size=(n_boot, len(x)), replace=True).mean(axis=1)
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def signflip_p(x, n_perm=20000, seed=0):
    """The sign-flip permutation test — the arc's own, on the paired deltas."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    obs = abs(x.mean())
    s = rng.choice([-1.0, 1.0], size=(n_perm, len(x)))
    null = (s * x).mean(axis=1)
    return float((np.abs(null) >= obs).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--base", type=int, default=13000)
    a = ap.parse_args()

    print("=" * 78)
    print("RUNG 8B CONFIRMATORY — H1/H2 through GCAL's setpoint theta")
    print(provenance_line())
    print(f"  seeds {a.base}..{a.base + a.n - 1}   SESOI {SESOI}   "
          f"adapt {ADAPT}  train {TRAIN}")
    print("=" * 78)

    rows = {}
    for chan in ("lateral", "degenerate"):
        for trained in (False, True):
            vals = []
            for i in range(a.n):
                sd = a.base + i
                o, th = one(chan, sd, trained=trained)
                vals.append(o)
                print(f"  [{chan:<10s}] seed {sd}  "
                      f"{'trained' if trained else 'untrained'}: "
                      f"OSI {o:.4f}  theta {th:.3f}", flush=True)
            rows[(chan, trained)] = np.array(vals)

    print("\n--- ARMS (mean OSI per SEED) ---")
    for chan in ("lateral", "degenerate"):
        u, t = rows[(chan, False)], rows[(chan, True)]
        print(f"  [{chan:<10s}] untrained {u.mean():.4f} +/- {u.std(ddof=1):.4f}"
              f"   trained {t.mean():.4f} +/- {t.std(ddof=1):.4f}")

    d_lat = rows[("lateral", True)] - rows[("lateral", False)]
    d_deg = rows[("degenerate", True)] - rows[("degenerate", False)]
    inter = d_lat - d_deg

    print("\n--- THE PRE-REGISTERED TESTS ---")
    for name, d in (("D_lateral", d_lat), ("D_degenerate", d_deg),
                    ("INTERACTION", inter)):
        lo, hi = ci(d)
        p = signflip_p(d)
        print(f"  {name:<14s} {d.mean():+.4f}  CI [{lo:+.4f}, {hi:+.4f}]  "
              f"p={p:.4g}")

    lo, hi = ci(d_lat)
    ilo, ihi = ci(inter)
    h1 = (d_lat.mean() > SESOI) and (lo > 0 or hi < 0) and not (ilo <= 0 <= ihi)
    print(f"\n  H1: {'CONFIRMED' if h1 else 'NULL'}  "
          f"(needs D_lateral > {SESOI} AND its CI to exclude 0 AND the "
          f"interaction CI to exclude 0)")


if __name__ == "__main__":
    sys.exit(main())
