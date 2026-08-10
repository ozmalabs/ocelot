"""RUNG 8D — STEP 5: THE H1 POWER PILOT. Is H1 RUNNABLE AT ALL?

**§3.3 PILOT on ALREADY-BURNED seeds (0-7). NO confirmatory seed (13000-13999
stays CLEAN). NO hypothesis is tested.** This fixes `n` for H1 in advance — and
it may find that no affordable `n` suffices, which is itself the answer.

WHY THIS IS THE DECIDING MEASUREMENT
--------------------------------------
Rung 8's prereg fixes H1's statistic:

    Delta_arm   = OSI(trained, arm) - OSI(untrained, arm)     [paired, per seed]
    INTERACTION = Delta_lateral - Delta_degenerate
    SESOI       = 0.0595   (rung 6's, adopted unchanged)

and says **"n: fixed in advance by a power analysis on a pilot restricted to
already-burned seeds."** No rung has ever run that pilot.

**This rung's calibration has since measured the number that decides it:** the
FLOOR's per-seed **sd = 0.1091** — **1.8x the SESOI** — because `osi()`'s argmax
is a LOTTERY over EXACT ties on a nearly-flat curve (prereg §8).

If Delta's sd were `sqrt(2) * 0.1091 = 0.154` (the unpaired case), detecting
SESOI = 0.0595 at 80% power would need

    n = (2.8 * 0.154 / 0.0595)^2 ~= 52 SEEDS

which no rung in this arc has ever come close to. **But the design is PAIRED**:
the trained and untrained arms of one seed START FROM THE SAME INIT, so they
share the RF that generates the tie structure, and the lottery may largely
CANCEL in the difference. **sd(Delta) is therefore an EMPIRICAL question and I
must measure it, not assume it.** That is the whole point of this pilot.

MY PREDICTION, IN ADVANCE (§3.7)
---------------------------------
**I predict the pairing helps but does NOT rescue it**: sd(Delta) somewhere in
0.05-0.12, so the required n is ~10-30 seeds. I expect H1 to be runnable but
**expensive**, and I expect n=8 (this arc's habitual size) to be **UNDERPOWERED**
for the SESOI.

Provisos:
 1. **If sd(Delta) is small (<0.03)**, the pairing cancels the lottery and H1 is
    cheap. Good news, and it would mean the lottery is an init property that
    subtracts out.
 2. **If sd(Delta) is large (>0.12)**, the pairing does NOT cancel — training
    changes the RF enough to re-roll the lottery — and H1 needs n in the
    hundreds. **Then H1 is NOT RUNNABLE at this rung's budget and must not be
    half-run**, because an underpowered H1 that returns "null" is exactly the
    un-diagnosed negative §7 forbids.
 3. **If Delta_lateral is already >> SESOI at n=8**, H1 may be answerable early
    — but I would NOT read that as a result here (this is a burned-seed pilot;
    §3.4 forbids confirming on burned seeds).

TRAINING: eta = 5e-4, 6400 steps — **rung 8's prereg's own FROZEN choice**
("eta, RF, period, lat_eta, gmax are FROZEN" = rung 6's values), NOT chosen by
me after seeing results. Its §1-clause-5 vacuity is verified per arm
(`max|dw|`): at 5e-4 the lateral RF moves 4.49% (LOAD-BEARING); at 1e-4 it moves
0.86% (near-VACUOUS — H1 would be null because nothing happened), which is why
the frozen 5e-4 is also the only non-vacuous option.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble  # noqa: E402

engine_preamble()

from domains.complex_cells import cell_stats  # noqa: E402
from domains.engine_provenance import provenance_line  # noqa: E402
from domains.lateral_world import set_lat_params  # noqa: E402
from domains.onoff_world import set_params  # noqa: E402
from scripts.rung8_lib import (  # noqa: E402
    PERIOD, build, develop_retina, freeze_all, run_waves,
)
from scripts.rung8b_lib import theta_of, weights_of  # noqa: E402
from scripts.rung8c_ensemble_transfer import adapt_theta_on_probe  # noqa: E402

PILOT_SEEDS = list(range(8))      # 0-7: ALREADY BURNED
ETA = 5e-4                        # rung 8 prereg's FROZEN value (rung 6's)
TRAIN = 6400                      # rung 8's own §2 convergence horizon
SESOI = 0.0595                    # rung 6's, adopted unchanged


def arm(chan, *, trained, seed):
    w, us, _a, _b = build(seed=seed, n_units=6, channels=chan, eta=ETA)
    develop_retina(w, 3000)
    wt0 = weights_of(w, us)
    if trained:
        set_params(w, frozen=0.0, oo_eta=ETA)
        if w.s.nodes("LatParams"):
            set_lat_params(w, frozen=1.0)   # only the cortex learns
        run_waves(w, TRAIN)
    dw_train = float(np.abs(weights_of(w, us) - wt0).max())
    wt1 = weights_of(w, us)
    adapt_theta_on_probe(w, 2000)
    set_params(w, homeo=0.0)
    freeze_all(w)
    dw_probe = float(np.abs(weights_of(w, us) - wt1).max())
    st = cell_stats(w, us, key="rate", period=PERIOD)
    tc = st["tuning"]
    alive = (tc > 1e-9).sum(axis=1)
    return {"osi": float(st["osi"].mean()), "n_dead": int((alive == 0).sum()),
            "alive": alive, "dw_train": dw_train, "dw_probe": dw_probe,
            "theta": float(theta_of(w).mean())}


def main() -> int:
    print("=" * 78)
    print("RUNG 8D STEP 5 — H1 POWER PILOT (burned seeds 0-7). NO hypothesis.")
    print(provenance_line())
    print(f"  eta={ETA:.0e} (rung 8 prereg's FROZEN value), train={TRAIN} steps.")
    print("  13000-13999 NOT TOUCHED.")
    print("=" * 78)

    res = {}
    for chan in ("lateral", "degenerate"):
        d = []
        print(f"\n  --- {chan} ---")
        for sd in PILOT_SEEDS:
            t = arm(chan, trained=True, seed=sd)
            u = arm(chan, trained=False, seed=sd)
            delta = t["osi"] - u["osi"]
            d.append(delta)
            print(f"    seed {sd}: trained {t['osi']:.4f} (dead {t['n_dead']}, "
                  f"train max|dw| {t['dw_train']:.4f}, probe |dw| {t['dw_probe']:.1e})"
                  f"  untrained {u['osi']:.4f} (dead {u['n_dead']})"
                  f"  DELTA {delta:+.4f}")
        res[chan] = np.array(d)

    print("\n" + "=" * 78)
    print("  THE POWER NUMBERS (unit = SEED, §4)")
    print("=" * 78)
    for chan in ("lateral", "degenerate"):
        d = res[chan]
        print(f"  Delta_{chan:<11s} mean {d.mean():+.4f}  sd {d.std(ddof=1):.4f}  "
              f"min {d.min():+.4f}  max {d.max():+.4f}")
    inter = res["lateral"] - res["degenerate"]
    print(f"  INTERACTION      mean {inter.mean():+.4f}  sd {inter.std(ddof=1):.4f}")

    print(f"\n--- n REQUIRED FOR 80 PERCENT POWER AT SESOI = {SESOI:.4f} ---")
    for name, d in (("Delta_lateral", res["lateral"]),
                    ("INTERACTION", inter)):
        s = d.std(ddof=1)
        n_need = int(np.ceil((2.8 * s / SESOI) ** 2)) if s > 0 else 3
        print(f"  {name:<14s} sd {s:.4f}  =>  n >= {n_need:>4d} seeds "
              f"({'AFFORDABLE' if n_need <= 40 else 'NOT AFFORDABLE at ~130s/seed'})")
    print("""
  READING (fixed in advance):
    * n <= ~40  => H1 is runnable; pre-register that n and run on 13000+.
    * n >> 40   => the argmax LOTTERY makes H1 unanswerable with this readout,
                   and the honest report is: H1 NOT RUN, blocker = the measure,
                   13000-13999 still CLEAN. An underpowered H1 returning "null"
                   would be an UN-DIAGNOSED negative (§7 forbids it).""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
