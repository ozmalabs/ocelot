"""RUNG 8D — STEP 1: WHY IS THE FLOOR 8.33/12 ALIVE, AND WHY IS 0.2304 < 0.3105?

**§1 CALIBRATION / INSTRUMENT DIAGNOSIS on already-burned seeds (0 / 3000). NO
confirmatory seed is touched. NO hypothesis is tested here.** This script only
DECOMPOSES numbers rung 8C already reported. It cannot produce a positive
result — there is no arm to win.

WHAT RUNG 8C LEFT OPEN (its §4.1 / §7.2, in its own words)
-----------------------------------------------------------
    "The floor arm sits at **8.33 of 12** and the ideal at **11.00 of 12**: some
     cells are silenced at some orientations. Not dead ... but not the clean
     12/12 I expected, and partial silencing is exactly the direction that
     INFLATES an OSI. The floor's 0.2304 sitting *below* rung 6's 0.3105 is
     consistent with that and is **not yet explained**."

**Those two facts point in OPPOSITE directions and 8C noticed but did not
resolve it.** Partial silencing INFLATES OSI (silence at the orthogonal
orientation ⇒ `b = 0` ⇒ `osi = (a-0)/(a+0) = 1.0`). So if the floor is partially
silenced, its OSI should be HIGHER than rung 6's, not LOWER. It is LOWER. **Both
cannot be explained by the same mechanism, so at least one cell is doing
something else.**

MY PREDICTION, IN ADVANCE, BEFORE RUNNING THIS (§3.7)
------------------------------------------------------
The mechanism is `oo_sunit_rate` + `oo_sunit_adapt_theta`, read off the seed:

    rate = max(act - theta, 0)            (THE ICEBERG)
    theta <- theta + theta_rate * (act - theta)      (a per-cell EMA of act)

so theta converges to **E[act] over the ensemble it is settled on**, per cell.
`grating_ensemble` interleaves all 12 orientations and all phases, therefore:

    theta_cell -> mean_over_ensemble(act_cell)

and `tuning[i, j] = mean_over_16_phases( max(act - theta, 0) )`. **A cell is
"alive" at orientation j iff its act exceeds its OWN ensemble-mean act at at
least one phase of j.** By construction roughly HALF of a cell's orientations
sit below its own mean. So:

**I PREDICT THE 8.33/12 IS NOT A DEFECT — IT IS WHAT AN EMA THRESHOLD MUST DO**,
and it is NOT the same thing at all as rung 8B's windup death.

**AND I PREDICT THE RESOLUTION OF THE CONTRADICTION IS A MIXTURE**: `osi()`
returns `0.0` BOTH for a cell silenced *everywhere* (`a + b = 0`, the §1.1
divide-guard) AND scores `1.0` for a cell silenced only at its orthogonal. 8C
reported `alive` as a **MEAN OVER CELLS** (`(tc > 1e-9).sum(axis=1).mean()`),
which cannot tell 6 cells at 8.33/12 apart from 4 cells at 12/12 plus 2 cells at
**0/12**. **§1.1 demands the per-CELL number and 8C reported the mean.** If the
floor arm contains any 0/12 cell, its 0.2304 is an average of §1.1 zeros and
inflated ones — and G0 "FLOOR arm ALIVE — PASS, 8.33 of 12" passed a gate that
§1.1 exists to fail.

**If instead every floor cell is alive at >= 1 orientation, my prediction is
WRONG, the mixture story dies, and the 0.2304 needs a different explanation.**

THE DECISIVE COLUMN is `n_dead` (cells with `alive == 0`), which no rung has
reported. Everything else here is context.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PROTOCOL §10.1 rule 3: the preamble MUST run before any `domains.*` import —
# the first `substrate_rs` import binds the engine for the whole process.
from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.complex_cells import THETAS, cell_stats  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from scripts.rung8_lib import PERIOD  # noqa: E402
from scripts.rung8c_ensemble_transfer import N_UNITS, prepare  # noqa: E402
from scripts.rung8b_lib import theta_of  # noqa: E402


def audit(w, us):
    """Per-CELL aliveness + per-CELL OSI. §1.1: report the CELL, not the mean."""
    st = cell_stats(w, us, key="rate", period=PERIOD)
    tc = st["tuning"]
    alive = (tc > 1e-9).sum(axis=1)          # per cell, out of 12
    o = st["osi"]
    return {"alive": alive, "osi": o, "tuning": tc,
            "n_dead": int((alive == 0).sum()),
            "n_full": int((alive == len(THETAS)).sum())}


def main() -> int:
    print("=" * 78)
    print("RUNG 8D STEP 1 — THE PER-CELL AUDIT OF RUNG 8C's FLOOR")
    print(provenance_line())
    print("  Seeds 0/3000 (already burned). NO confirmatory seed. NO hypothesis.")
    print("=" * 78)

    for chan in ("lateral", "degenerate"):
        for adapt in ("waves", "probe"):
            print(f"\n{'='*78}\n  PATHWAY {chan}   THETA SETTLED ON {adapt}\n{'='*78}")
            for armname, ideal in (("IDEAL", True), ("FLOOR", False)):
                w, us, dw = prepare(chan, ideal=ideal, adapt=adapt)
                a = audit(w, us)
                th = theta_of(w)
                print(f"\n  --- {armname} arm  (max|dw| = {dw:.3e}) ---")
                print(f"  {'cell':>4s} {'alive/12':>9s} {'osi':>8s} {'theta':>8s} "
                      f"{'tc_max':>8s} {'tc_orth':>8s}")
                for i in range(len(us)):
                    tci = a["tuning"][i]
                    j = int(np.argmax(tci))
                    jo = (j + len(tci) // 2) % len(tci)
                    print(f"  {i:>4d} {a['alive'][i]:>9d} {a['osi'][i]:>8.4f} "
                          f"{th[i]:>8.3f} {tci[j]:>8.4f} {tci[jo]:>8.4f}")
                print(f"  MEAN alive = {a['alive'].mean():.2f} of 12   "
                      f"MEAN osi = {a['osi'].mean():.4f}")
                print(f"  >>> n_dead (alive==0)  = {a['n_dead']} of {len(us)}"
                      f"   <<< THE DECISIVE COLUMN")
                print(f"  >>> n_full (alive==12) = {a['n_full']} of {len(us)}")
                # The §1.1 decomposition: which cells' OSI is a divide-guard 0?
                guard = [i for i in range(len(us)) if a["alive"][i] == 0]
                infl = [i for i in range(len(us))
                        if a["alive"][i] > 0 and a["osi"][i] > 0.999]
                print(f"  cells scoring osi=0.0000 by the §1.1 DIVIDE-GUARD "
                      f"(dead): {guard}")
                print(f"  cells scoring osi~1.0000 by ORTHOGONAL SILENCE: {infl}")
                if guard:
                    live = a["osi"][a["alive"] > 0]
                    print(f"  MEAN osi over ALIVE cells only = "
                          f"{live.mean():.4f}  (vs {a['osi'].mean():.4f} reported)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
