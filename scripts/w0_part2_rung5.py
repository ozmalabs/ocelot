"""PART 2 — RUNG 5's PRECONDITION, RE-MEASURED BOTH WAYS.

Rung 5's headline: the model's Units are BLIND — response **OSI 0.004** (floor
0.0044) against an ideal Gabor's 1.0000 through the identical frozen probe. Its
root cause, measured: Oja on nonneg binary input yields strictly-POSITIVE weights
(`frac(w<0)=0.0000`) => a DC-dominated response => the oriented structure that IS
in the weights never reaches the RESPONSE.

THE REVIEW'S CHARGE: `frac(w<0)=0.0000` is what `add_units(w0=1.0)` HANDS the
agent, before any rule fires. If OSI lifts under a zero-mean init, "our Units are
blind" is an ADAPTER ARTIFACT and rung 5 was measuring its own initialisation.

THE MEASURE IS RUNG 5'S OWN, UNCHANGED: `complex_cells.cell_stats(key="act",
period=4.0)` through `complex_cells.freeze()` — the same instrument, the same
rectification, the same period-4 anti-aliasing, the same frozen probe. Nothing
about the read-out is touched (PROTOCOL 5: never rescue a gate by changing the
measure — and never rescue an ablation by changing it either).
"""
from __future__ import annotations

import numpy as np

from scripts.w0_ablation_lib import (INITS, build, run_waves, rf_stats, ETA)
from domains.cortex_sheet import orientation_selectivity
from domains.complex_cells import (freeze, cell_stats, gabor, install_weights)
from domains.engine_provenance import provenance_line

PERIOD = 4.0
N_SEEDS = 8               # seeds 0-7: BURNED
CONDS = [("UNTRAINED", 0), ("TRAINED 1600", 1600), ("TRAINED 3200", 3200)]


def arm(seed: int, init: str, steps: int):
    w, us = build(seed, init,
                  seeds_list=("vision_waves", "vision_maps", "vision_complex"))
    run_waves(w, steps)
    freeze(w)
    return w, us


if __name__ == "__main__":
    print(provenance_line())
    print("=" * 78)
    print("PART 2 — RUNG 5 PRECONDITION, BOTH INITS. rung-5's own frozen probe.")
    print(f"eta={ETA:g}  period={PERIOD}  n={N_SEEDS} BURNED seeds (0-7)")
    print("=" * 78)

    # ---- the instrument's own reference points (PROTOCOL 1), unchanged -----
    w, us = arm(0, "DC", 0)
    g = gabor(7, 90.0, 0.0, PERIOD)
    install_weights(w, us[14], g)                    # ideal SIGNED Gabor
    install_weights(w, us[21], g - g.min() + 0.05)   # same Gabor + DC offset
    st = cell_stats(w, [us[14], us[21]], key="act", period=PERIOD)
    print("\nINSTRUMENT REFERENCES (rung 5's, reproduced):")
    for i, nm in ((0, "ideal GABOR (signed)"), (1, "ideal GABOR + DC   ")):
        print(f"  {nm}: OSI={st['osi'][i]:.4f}  F1/F0={st['f1f0'][i]:.3f}")

    print(f"\n{'condition':14s} {'arm':6s} {'OSI':>8s} {'OSI max':>8s} "
          f"{'anis':>7s} {'frac(w<0)':>10s} {'DC frac':>8s} {'base/act':>9s}")
    for label, steps in CONDS:
        for init in INITS:
            osis, rows, bases = [], [], []
            for seed in range(N_SEEDS):
                w, us = arm(seed, init, steps)
                st = cell_stats(w, us, key="act", period=PERIOD)
                osis.append(st["osi"])
                rows.append(rf_stats(w, us))
                bases.append(st["baseline"].mean() /
                             max(st["tuning"].mean(), 1e-9))
            o = np.concatenate(osis)
            a = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
            print(f"{label:14s} {init:6s} {o.mean():8.4f} {o.max():8.4f} "
                  f"{a['anis']:7.4f} {a['frac_neg']:10.4f} {a['dc_frac']:8.4f} "
                  f"{float(np.mean(bases)):9.3f}")
