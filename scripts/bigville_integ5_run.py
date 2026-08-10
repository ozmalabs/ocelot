"""bigville_integ5_run -- boot the R10e SCALE-TO-50 town (block 276000), run it LONG,
MEASURE the macro regime + circulation + Sigma(coin) invariance, and report COST vs
HEADCOUNT + a cast-16 (R10d) vs cast-50 comparison. Mechanics inherited from R10d; the
only change is cast=50 + the 50-register. The verdict is whatever the real data says.

Usage:  python scripts/bigville_integ5_run.py [ticks] [cast] [seed]
Writes: results/bigville_integ5/{macro,townstate,shopping}.json
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

from worlds.bigville_integ5_world import BigvilleInteg5World          # noqa: E402
from worlds.bigville_integ3_state import write_snapshot3             # noqa: E402
from scripts.bigville_integ_measure import classify_regime           # noqa: E402

OUTDIR = os.path.join(_ROOT, "results", "bigville_integ5")


def main(argv):
    ticks = int(argv[1]) if len(argv) > 1 else 1800
    cast = int(argv[2]) if len(argv) > 2 else 50
    seed = int(argv[3]) if len(argv) > 3 else 276000
    os.makedirs(OUTDIR, exist_ok=True)

    t0 = time.time()
    w = BigvilleInteg5World(cast=cast, seed=seed)
    sys_coin_start = w.system_coin()
    w.run_town(T=ticks)
    dt = time.time() - t0
    sys_coin_end = w.system_coin()

    verdict, ev = classify_regime(w.macro, exploded=w.exploded)
    kinds = Counter(e["kind"] for e in w.events)
    days = list(w.buys_per_day)
    conservation = {
        "system_coin_start": round(sys_coin_start, 3),
        "system_coin_end": round(sys_coin_end, 3),
        "delta": round(sys_coin_end - sys_coin_start, 6),
        "invariant": abs(sys_coin_end - sys_coin_start) < 1e-6,
    }
    ms_per_tick = 1000.0 * dt / max(1, len(w.macro))

    # cast-16 (R10d) comparison, if present
    compare = None
    r10d = os.path.join(_ROOT, "results", "bigville_integ4", "macro.json")
    if os.path.exists(r10d):
        d16 = json.load(open(r10d))
        compare = {
            "cast16_verdict": d16.get("verdict"),
            "cast16_heavy_tail": d16.get("evidence", {}).get("heavy_tail_ratio"),
            "cast16_cascade_max": d16.get("evidence", {}).get("cascade_max"),
            "cast16_ms_per_tick": round(d16.get("elapsed_s", 0) / max(1, d16.get("ticks", 1)) * 1000, 1),
            "cast50_verdict": verdict,
            "cast50_heavy_tail": ev.get("heavy_tail_ratio"),
            "cast50_cascade_max": ev.get("cascade_max"),
            "cast50_ms_per_tick": round(ms_per_tick, 1),
        }

    macro_doc = {
        "block": 276000, "ticks": len(w.macro), "cast": cast, "seed": seed,
        "elapsed_s": round(dt, 1), "ms_per_tick": round(ms_per_tick, 1),
        "exploded": w.exploded, "verdict": verdict, "evidence": ev,
        "conservation": conservation, "event_kinds": dict(kinds),
        "buys_total": sum(x["buys"] for x in days),
        "cast16_vs_cast50": compare,
        "macro": w.macro, "events": w.events,
    }
    with open(os.path.join(OUTDIR, "macro.json"), "w") as f:
        json.dump(macro_doc, f, indent=2)
    write_snapshot3(w, os.path.join(OUTDIR, "townstate.json"))
    with open(os.path.join(OUTDIR, "shopping.json"), "w") as f:
        json.dump({"conservation": conservation, "buys_per_day": w.buys_per_day,
                   "keeper_takings": w.keeper_takings(), "trip_report": w.trip_report}, f, indent=2)

    print("\n=== R10e SCALE-TO-50 (block 276000) ===")
    print("ticks=%d cast=%d elapsed=%.1fs (%.0f ms/tick) living=%d/%d buys=%d"
          % (len(w.macro), cast, dt, ms_per_tick, w.living_count(), len(w.people),
             macro_doc["buys_total"]))
    print("CONSERVATION:", conservation)
    print("MACRO REGIME VERDICT:", verdict)
    for k, v in ev.items():
        print("  %-28s %s" % (k, v))
    print("EVENT KINDS:", dict(kinds))
    if compare:
        print("\n--- CAST-16 (R10d) vs CAST-50 ---")
        for k, v in compare.items():
            print("  %-24s %s" % (k, v))
    print("wrote:", OUTDIR)
    return verdict


if __name__ == "__main__":
    main(sys.argv)
