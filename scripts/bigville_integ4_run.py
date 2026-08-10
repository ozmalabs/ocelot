"""bigville_integ4_run -- boot the R10d town with REAL CIRCULATION (block 275000): the
shopping loop wired (know -> seek -> walk -> buy), run it LONG, MEASURE circulation +
the buy count/day + Sigma(coin) invariance + a few movers' is_at traces reaching the
market, and RE-CLASSIFY the macro regime with R10's UNCHANGED classifier. Mechanical:
seed knowledge -> arm -> walk -> buy -> read. The verdict is whatever the REAL data says.

Usage:  python scripts/bigville_integ4_run.py [ticks] [cast] [seed]
Writes:
    results/bigville_integ4/macro.json     -- macro series + verdict + evidence + circulation
    results/bigville_integ4/townstate.json -- the UI data contract (+ social state)
    results/bigville_integ4/shopping.json  -- per-day buys + is_at traces + conservation
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

from worlds.bigville_integ4_world import BigvilleInteg4World          # noqa: E402
from worlds.bigville_integ3_state import write_snapshot3             # noqa: E402
from scripts.bigville_integ_measure import classify_regime           # noqa: E402

OUTDIR = os.path.join(_ROOT, "results", "bigville_integ4")


def main(argv):
    ticks = int(argv[1]) if len(argv) > 1 else 1800
    cast = int(argv[2]) if len(argv) > 2 else 16
    seed = int(argv[3]) if len(argv) > 3 else 275000
    os.makedirs(OUTDIR, exist_ok=True)

    t0 = time.time()
    w = BigvilleInteg4World(cast=cast, seed=seed)
    sys_coin_start = w.system_coin()
    circ_start = w.circulation()
    w.run_town(T=ticks)
    dt = time.time() - t0
    sys_coin_end = w.system_coin()

    verdict, ev = classify_regime(w.macro, exploded=w.exploded)
    kinds = Counter(e["kind"] for e in w.events)

    conservation = {
        "system_coin_start": round(sys_coin_start, 3),
        "system_coin_end": round(sys_coin_end, 3),
        "delta": round(sys_coin_end - sys_coin_start, 6),
        "invariant": abs(sys_coin_end - sys_coin_start) < 1e-6,
    }

    days = [d for d in w.buys_per_day]
    total_buys = sum(d["buys"] for d in days)
    total_credit = sum(d["credit"] for d in days)
    active_days = [d for d in days if d["buys"] > 0]
    buys_per_day_mean = (total_buys / len(days)) if days else 0.0
    circulation = {
        "circulation_before": circ_start,
        "circulation_after": w.circulation(),
        "total_buys": total_buys,
        "total_credit_extended": total_credit,
        "shopping_days": len(days),
        "days_with_a_buy": len(active_days),
        "buys_per_day_mean": round(buys_per_day_mean, 2),
        "keeper_takings": w.keeper_takings(),
        "trip_report": w.trip_report,
    }

    macro_doc = {
        "block": 275000, "ticks": len(w.macro), "cast": cast, "seed": seed,
        "elapsed_s": round(dt, 1), "exploded": w.exploded,
        "verdict": verdict, "evidence": ev,
        "conservation": conservation,
        "circulation": circulation,
        "event_kinds": dict(kinds),
        "macro": w.macro, "events": w.events,
    }
    with open(os.path.join(OUTDIR, "macro.json"), "w") as f:
        json.dump(macro_doc, f, indent=2)
    write_snapshot3(w, os.path.join(OUTDIR, "townstate.json"))
    with open(os.path.join(OUTDIR, "shopping.json"), "w") as f:
        json.dump({"circulation": circulation, "conservation": conservation,
                   "buys_per_day": w.buys_per_day,
                   "is_at_traces": w.shopping_traces}, f, indent=2)

    print("\n=== R10d REAL-CIRCULATION TOWN (block 275000) ===")
    print("ticks=%d cast=%d seed=%d elapsed=%.1fs (%.2fs/tick) days=%d living=%d/%d"
          % (len(w.macro), cast, seed, dt, dt / max(1, len(w.macro)),
             w.world_epoch // 36, w.living_count(), len(w.people)))
    print("CONSERVATION:", conservation)
    print("\n--- CIRCULATION ---")
    for k in ("circulation_before", "circulation_after", "total_buys",
              "total_credit_extended", "shopping_days", "days_with_a_buy",
              "buys_per_day_mean", "keeper_takings"):
        print("  %-24s %s" % (k, circulation[k]))
    print("  trip_report:", w.trip_report)
    print("\n--- SAMPLE is_at TRACES (movers reaching a stall) ---")
    for tr in w.shopping_traces[:8]:
        print("  d%-2d %-16s home=%s -> shop=%s good=%d hops=%d arrived=%s bought=%s"
              % (tr["day"], tr["name"], tr["home"], tr["shop"], tr["good"],
                 tr["hops"], tr["arrived"], tr["bought"]))
        print("       is_at path:", tr["is_at_path"])
    print("\n--- BUYS PER DAY (head/tail) ---")
    for d in (w.buys_per_day[:6] + [None] + w.buys_per_day[-6:]):
        print("   ...") if d is None else print(
            "   day %-3d shoppers=%-2d arrivals=%-2d buys=%-2d credit=%d"
            % (d["day"], d["shoppers"], d["arrivals"], d["buys"], d["credit"]))
    print("\nMACRO REGIME VERDICT:", verdict)
    for k, v in ev.items():
        print("  %-28s %s" % (k, v))
    print("wrote:", os.path.join(OUTDIR, "macro.json"))
    print("wrote:", os.path.join(OUTDIR, "townstate.json"))
    print("wrote:", os.path.join(OUTDIR, "shopping.json"))
    return verdict


if __name__ == "__main__":
    main(sys.argv)
