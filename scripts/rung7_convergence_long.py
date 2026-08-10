"""rung7_convergence_long — PROTOCOL §2, the settled version.

The first pass (`rung7_convergence.py`) checkpointed at DOUBLING intervals, so
its `drift` was measured over a window that doubled each row — a moving target.
This one uses a FIXED drift window (`STRIDE`), so `drift` is comparable row to
row and "drift -> 0" means what it says.

It also runs far past 6400, because the first pass showed `SD` still FALLING at
6400 (0.93 -> 0.38) while `CS` was still RISING (-> 1.07). PROTOCOL §2's
distinction is between a plateau at non-zero structure and a decay to nothing,
and 6400 steps cannot tell those apart here. The question this script exists to
answer: **does SD plateau above its analytic floor of 0, or decay into it?**
"""
from __future__ import annotations

import sys

import numpy as np

from domains.engine_provenance import provenance_line
from domains.lateral_world import freeze_lateral, thaw_lateral
from scripts.rung7_lib import (
    build, corr_by_distance, gains, record_channels, run_waves, shape_departure,
    space_constant,
)

STRIDE = 1600


def main(eta, total=25600, seed=3000):
    print("=" * 92)
    print(f"RUNG 7 CONVERGENCE (LONG, FIXED drift window={STRIDE})  eta={eta:g}  seed {seed}")
    print(provenance_line())
    print("=" * 92)
    print(f"{'step':>7}{'g1':>8}{'g2':>8}{'CS':>8}{'drift':>9}{'SD':>8}"
          f"{'sig_nn':>8}{'sig_nf':>8}{'ratio':>8}{'ON':>7}{'OFF':>7}{'NaN':>5}")
    w, anat = build(seed=seed, lateral=1.0, eta=eta)
    prev = gains(w, anat["hcells"]).copy()
    for step in range(STRIDE, total + 1, STRIDE):
        run_waves(w, STRIDE)
        g = gains(w, anat["hcells"])
        drift = float(np.linalg.norm(g - prev)) / (float(np.linalg.norm(g)) or 1.0)
        prev = g.copy()
        freeze_lateral(w)
        on, off = record_channels(w, anat, 300)
        thaw_lateral(w)
        ds, Cnn = corr_by_distance(on, on)
        _, Cnf = corr_by_distance(on, off)
        sd = shape_departure(Cnn, Cnf)
        snn, snf = space_constant(ds, Cnn), space_constant(ds, Cnf)
        ratio = snf / snn if snn else float("nan")
        print(f"{step:>7}{g[:,0].mean():>8.4f}{g[:,1].mean():>8.4f}"
              f"{g.sum(axis=1).mean():>8.4f}{drift:>9.4f}{sd:>8.4f}"
              f"{snn:>8.3f}{snf:>8.3f}{ratio:>8.3f}"
              f"{on.mean():>7.3f}{off.mean():>7.3f}{int(np.isnan(g).sum()):>5d}")


if __name__ == "__main__":
    eta = float(sys.argv[1]) if len(sys.argv) > 1 else 2e-3
    total = int(sys.argv[2]) if len(sys.argv) > 2 else 25600
    main(eta, total)
