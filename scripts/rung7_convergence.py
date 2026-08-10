"""rung7_convergence — PROTOCOL §2, THE GATE THAT MUST BE RUN FIRST.

*"Before any experience/ablation arm is run, measure: does the rule settle?
This single check explains nine failed attempts. Run it FIRST."*

Formative input ONLY (the agent's own waves). Reports, at checkpoints out to
6400 steps:

  * `g1`, `g2`      — the learned surround gains (the structure)
  * `drift`         — ||g(t) - g(t-dt)|| / ||g(t)||, the settling measure
  * `CS = g1+g2`    — the centre-surround index
  * `SD`            — the shape-departure gate, over the SAME window
  * NaN count

CONVERGENT + USEFUL := SD/CS plateau at non-zero structure AND drift -> 0.
Both of rung 6's stop conditions (never converges; converges to death) are
checked here BEFORE any arm is defined.
"""
from __future__ import annotations

import sys

import numpy as np

from scripts.rung7_lib import (
    build, corr_by_distance, gains, record_channels, run_waves, shape_departure,
    space_constant,
)

from domains.engine_provenance import provenance_line

CKPTS = [400, 800, 1600, 3200, 6400]


def measure(w, anat, *, seed):
    """Read SD off a frozen 300-step window, then restore learning."""
    from domains.lateral_world import freeze_lateral, thaw_lateral
    freeze_lateral(w)
    on, off = record_channels(w, anat, 300)
    thaw_lateral(w)
    ds, Cnn = corr_by_distance(on, on)
    _, Cnf = corr_by_distance(on, off)
    return {"SD": shape_departure(Cnn, Cnf),
            "s_nn": space_constant(ds, Cnn), "s_nf": space_constant(ds, Cnf),
            "on_mean": float(on.mean()), "off_mean": float(off.mean())}


def main(eta):
    print("=" * 76)
    print(f"RUNG 7 CONVERGENCE  (PROTOCOL 2)   eta={eta:g}   seed 3000")
    print(provenance_line())
    print("=" * 76)
    w, anat = build(seed=3000, lateral=1.0, eta=eta)
    prev = gains(w, anat["hcells"]).copy()
    done = 0
    rows = []
    for ck in CKPTS:
        run_waves(w, ck - done)
        done = ck
        g = gains(w, anat["hcells"])
        num = float(np.linalg.norm(g - prev))
        den = float(np.linalg.norm(g)) or 1.0
        drift = num / den
        prev = g.copy()
        m = measure(w, anat, seed=3000)
        nan = int(np.isnan(g).sum())
        rows.append((ck, g[:, 0].mean(), g[:, 1].mean(), drift, m["SD"],
                     m["s_nn"], m["s_nf"], m["on_mean"], m["off_mean"], nan))
        print(f"  step {ck:5d}  g1={g[:,0].mean():.4f}  g2={g[:,1].mean():.4f}  "
              f"CS={g.sum(axis=1).mean():.4f}  drift={drift:.4f}  "
              f"SD={m['SD']:.4f}  sigma_nn={m['s_nn']:.3f} sigma_nf={m['s_nf']:.3f}  "
              f"ON={m['on_mean']:.3f} OFF={m['off_mean']:.3f}  NaN={nan}")
    return rows


if __name__ == "__main__":
    for eta in [float(x) for x in (sys.argv[1:] or ["2e-3", "5e-4"])]:
        main(eta)
        print()
