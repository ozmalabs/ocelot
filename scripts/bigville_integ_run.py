"""bigville_integ_run -- boot the ASSEMBLED town, run it LONG, dump the macro series
+ the town-state contract JSON, and print the pre-registered regime verdict
(BIGVILLE_INTEG_PREREG.md, block 258000).

Usage:
    python scripts/bigville_integ_run.py [ticks] [cast] [seed]

Writes:
    results/bigville_integ/macro.json      -- the per-tick macro series + verdict
    results/bigville_integ/townstate.json  -- the UI data contract (a snapshot)

This script is mechanical: it INGESTS (constructs the town), TICKS, and READS. No
agent decision lives here. The verdict is whatever the REAL data says.
"""
from __future__ import annotations

import json
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.bigville_integ_world import BigvilleIntegWorld            # noqa: E402
from worlds.bigville_integ_state import write_snapshot                # noqa: E402
from scripts.bigville_integ_measure import classify_regime            # noqa: E402

OUTDIR = os.path.join(_ROOT, "results", "bigville_integ")


def main(argv):
    ticks = int(argv[1]) if len(argv) > 1 else 400
    cast = int(argv[2]) if len(argv) > 2 else 16
    seed = int(argv[3]) if len(argv) > 3 else 258000
    os.makedirs(OUTDIR, exist_ok=True)

    t0 = time.time()
    w = BigvilleIntegWorld(cast=cast, seed=seed)
    print("ASSEMBLED: %d sibling seeds clean, %d conflicts; %d core rungs on the MRO"
          % (len(w.assembled), len(w.conflicts), len(w.core_rungs)))
    if w.conflicts:
        for sid, err in w.conflicts:
            print("  CONFLICT:", sid, "->", err[:160])
    w.run_town(T=ticks)
    dt = time.time() - t0

    verdict, ev = classify_regime(w.macro, exploded=w.exploded)
    from collections import Counter
    kinds = Counter(e["kind"] for e in w.events)

    macro_doc = {
        "block": 258000, "ticks": len(w.macro), "cast": cast, "seed": seed,
        "elapsed_s": round(dt, 1), "exploded": w.exploded,
        "assembled_siblings": w.assembled, "conflicts": w.conflicts,
        "core_rungs": w.core_rungs,
        "verdict": verdict, "evidence": ev,
        "event_kinds": dict(kinds),
        "macro": w.macro,
        "events": w.events,
    }
    with open(os.path.join(OUTDIR, "macro.json"), "w") as f:
        json.dump(macro_doc, f, indent=2)
    write_snapshot(w, os.path.join(OUTDIR, "townstate.json"))

    print("\n=== R10 ASSEMBLED-TOWN MACRO MEASUREMENT (block 258000) ===")
    print("ticks=%d cast=%d seed=%d elapsed=%.1fs living=%d/%d"
          % (len(w.macro), cast, seed, dt, w.living_count(), len(w.people)))
    print("event kinds:", dict(kinds))
    print("MACRO REGIME VERDICT:", verdict)
    for k, v in ev.items():
        print("  %-28s %s" % (k, v))
    print("\nwrote:", os.path.join(OUTDIR, "macro.json"))
    print("wrote:", os.path.join(OUTDIR, "townstate.json"))
    return verdict


if __name__ == "__main__":
    main(sys.argv)
