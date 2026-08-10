"""bigville_integ2_run -- boot the R10b BALANCE-FIXED town (block 273000), run it LONG
under the TICK/DAY/LIFE hierarchy, MEASURE the macro regime with R10's SAME classifier,
verify Sigma(coin) invariance + the demographic acceptance bar, and dump the town-state
contract. Mechanical: ingest -> tick -> read. The verdict is whatever the REAL data says
(still dead / punctuated / noisy / exploding are all valid, reported honestly).

Usage:  python scripts/bigville_integ2_run.py [ticks] [cast] [seed]
Writes:
    results/bigville_integ2/macro.json      -- per-tick macro series + verdict + evidence
    results/bigville_integ2/townstate.json  -- the UI data contract (named/deep/mapped)
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_integ2_world import (                              # noqa: E402
    BigvilleInteg2World, TICKS_PER_DAY, DAY_AGE_RATE)
from worlds.bigville_integ2_state import write_snapshot2               # noqa: E402
from scripts.bigville_integ_measure import classify_regime            # noqa: E402

OUTDIR = os.path.join(_ROOT, "results", "bigville_integ2")


def main(argv):
    ticks = int(argv[1]) if len(argv) > 1 else 1800
    cast = int(argv[2]) if len(argv) > 2 else 16
    seed = int(argv[3]) if len(argv) > 3 else 273000
    os.makedirs(OUTDIR, exist_ok=True)

    t0 = time.time()
    w = BigvilleInteg2World(cast=cast, seed=seed)
    sys_coin_start = w.system_coin()
    w.run_town(T=ticks)
    dt = time.time() - t0
    sys_coin_end = w.system_coin()

    verdict, ev = classify_regime(w.macro, exploded=w.exploded)
    kinds = Counter(e["kind"] for e in w.events)

    # -- DEFECT 1 acceptance: Sigma(coin) invariant -----------------------------
    conservation = {
        "system_coin_start": round(sys_coin_start, 3),
        "system_coin_end": round(sys_coin_end, 3),
        "delta": round(sys_coin_end - sys_coin_start, 6),
        "invariant": abs(sys_coin_end - sys_coin_start) < 1e-6,
        "pool_coin_end": round(w.pool_coin(), 1),
        "living_subtotal_end": int(sum(w.coin_of(nm) for nm in w.people
                                       if not w.is_dead(nm))),
    }
    # wealth distribution coherence (acceptance check): top holders + banker
    holders = [(w.display.get(nm, nm), int(w.coin_of(nm)), w.classes.get(nm, "?"))
               for nm in w.people]
    bk = getattr(w, "_banker", None)
    if bk:
        holders.append((w.display.get(bk, bk), int(w.coin_of(bk)), "rich(banker)"))
    holders.sort(key=lambda h: -h[1])

    # -- demographic acceptance: lifespans + every death's cause ----------------
    lad = sorted(w.lifespan_after_days.values())
    demographic = {
        "ticks_per_day": TICKS_PER_DAY, "day_age_rate": DAY_AGE_RATE,
        "days_elapsed": int(w.world_epoch // TICKS_PER_DAY),
        "lifespan_days_min": round(lad[0], 1),
        "lifespan_days_median": round(lad[len(lad) // 2], 1),
        "lifespan_days_max": round(lad[-1], 1),
        "genuine_elders": sorted(w.display.get(e, e) for e in w.elders),
        "deaths_total": len(w.death_log),
        "births_total": len(w.births),
        "death_log": w.death_log,
        "healthy_normaladult_deaths": [
            d for d in w.death_log
            if not d["was_genuine_elder"] and d["cause"] in ("aging", "old_age")],
    }

    macro_doc = {
        "block": 273000, "ticks": len(w.macro), "cast": cast, "seed": seed,
        "elapsed_s": round(dt, 1), "exploded": w.exploded,
        "verdict": verdict, "evidence": ev,
        "conservation": conservation,
        "top_holders": holders[:5],
        "demographic": demographic,
        "event_kinds": dict(kinds),
        "macro": w.macro, "events": w.events, "births": w.births,
    }
    with open(os.path.join(OUTDIR, "macro.json"), "w") as f:
        json.dump(macro_doc, f, indent=2)
    write_snapshot2(w, os.path.join(OUTDIR, "townstate.json"))

    print("\n=== R10b BALANCE-FIXED TOWN (block 273000) ===")
    print("ticks=%d cast=%d seed=%d elapsed=%.1fs (%.2fs/tick) days=%d living=%d/%d"
          % (len(w.macro), cast, seed, dt, dt / max(1, len(w.macro)),
             demographic["days_elapsed"], w.living_count(), len(w.people)))
    print("DEFECT1 conservation:", conservation)
    print("top holders:", holders[:5])
    print("DEFECT2 demographic: deaths=%d births=%d healthy-adult-aging-deaths=%d"
          % (demographic["deaths_total"], demographic["births_total"],
             len(demographic["healthy_normaladult_deaths"])))
    for d in w.death_log:
        print("   day%-4d %-20s cause=%-9s age=%.0fy days_lived=%.1f elder=%s"
              % (d["day"], d["name"], d["cause"], d["age_years"],
                 d["days_lived_in_sim"], d["was_genuine_elder"]))
    print("event kinds:", dict(kinds))
    print("MACRO REGIME VERDICT:", verdict)
    for k, v in ev.items():
        print("  %-28s %s" % (k, v))
    print("wrote:", os.path.join(OUTDIR, "macro.json"))
    print("wrote:", os.path.join(OUTDIR, "townstate.json"))
    return verdict


if __name__ == "__main__":
    main(sys.argv)
