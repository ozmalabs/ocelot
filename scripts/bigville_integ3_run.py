"""bigville_integ3_run -- boot the R10c town with the SOCIAL RUNGS ACTIVE (block 274000),
run it LONG, MEASURE the macro regime with R10's SAME classifier, verify Sigma(coin)
invariance still holds, and dump the town-state contract + the per-rung fired/dormant
table + the social feed. Mechanical: populate -> arm -> tick -> read. The verdict is
whatever the REAL data says (moved / unmoved / exploded are all valid, reported honestly).

Usage:  python scripts/bigville_integ3_run.py [ticks] [cast] [seed]
Writes:
    results/bigville_integ3/macro.json      -- per-tick macro series + verdict + evidence
    results/bigville_integ3/townstate.json  -- the UI data contract (+ social state)
    results/bigville_integ3/social.json     -- the social feed + rung table + collective action
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

from worlds.bigville_integ3_world import BigvilleInteg3World, CHENOWETH_FRAC  # noqa: E402
from worlds.bigville_integ3_state import write_snapshot3, export_townstate3   # noqa: E402
from scripts.bigville_integ_measure import classify_regime                   # noqa: E402

OUTDIR = os.path.join(_ROOT, "results", "bigville_integ3")


def main(argv):
    ticks = int(argv[1]) if len(argv) > 1 else 1800
    cast = int(argv[2]) if len(argv) > 2 else 16
    seed = int(argv[3]) if len(argv) > 3 else 274000
    os.makedirs(OUTDIR, exist_ok=True)

    t0 = time.time()
    w = BigvilleInteg3World(cast=cast, seed=seed)
    sys_coin_start = w.system_coin()
    w.run_town(T=ticks)
    dt = time.time() - t0
    sys_coin_end = w.system_coin()

    verdict, ev = classify_regime(w.macro, exploded=w.exploded)
    kinds = Counter(e["kind"] for e in w.events)
    social_kinds = Counter(e["kind"] for e in w.social_log)

    conservation = {
        "system_coin_start": round(sys_coin_start, 3),
        "system_coin_end": round(sys_coin_end, 3),
        "delta": round(sys_coin_end - sys_coin_start, 6),
        "invariant": abs(sys_coin_end - sys_coin_start) < 1e-6,
    }

    # collective-action / 3.5% read-off
    iss = w.informed_share_series
    coll = {
        "chenoweth_threshold": CHENOWETH_FRAC,
        "printings": len(iss),
        "coalitions_formed": sum(1 for (_t, _i, _n, _s, fm) in iss if fm),
        "informed_share_max": (round(max(s for (_t, _i, _n, s, _f) in iss), 3)
                               if iss else 0.0),
        "informed_share_mean": (round(sum(s for (_t, _i, _n, s, _f) in iss) / len(iss), 3)
                                if iss else 0.0),
    }

    rung = w.rung_report()

    macro_doc = {
        "block": 274000, "ticks": len(w.macro), "cast": cast, "seed": seed,
        "elapsed_s": round(dt, 1), "exploded": w.exploded,
        "verdict": verdict, "evidence": ev,
        "conservation": conservation,
        "rung_report": rung,
        "event_kinds": dict(kinds), "social_kinds": dict(social_kinds),
        "collective_action": coll,
        "papers": w.papers, "council_log": w.council_log,
        "macro": w.macro, "events": w.events,
    }
    with open(os.path.join(OUTDIR, "macro.json"), "w") as f:
        json.dump(macro_doc, f, indent=2)
    write_snapshot3(w, os.path.join(OUTDIR, "townstate.json"))

    # a compact social-only dump (feed + journals + rung table)
    sample_journals = []
    for nm in w.people:
        j = w.latest_journal(nm)
        if j is not None:
            from worlds.bigville_integ3_state import _render_journal
            sample_journals.append({"resident": w.display.get(nm, nm),
                                    "entry": _render_journal(j)})
    with open(os.path.join(OUTDIR, "social.json"), "w") as f:
        json.dump({"rung_report": rung, "collective_action": coll,
                   "feed": w.social_log, "journals": sample_journals,
                   "papers": w.papers, "council_log": w.council_log}, f, indent=2)

    print("\n=== R10c SOCIAL-ACTIVATED TOWN (block 274000) ===")
    print("ticks=%d cast=%d seed=%d elapsed=%.1fs (%.2fs/tick) days=%d living=%d/%d"
          % (len(w.macro), cast, seed, dt, dt / max(1, len(w.macro)),
             w.world_epoch // 36, w.living_count(), len(w.people)))
    print("CONSERVATION:", conservation)
    print("\n--- PER-RUNG FIRED/DORMANT ---")
    for k, v in rung.items():
        print("  %-34s %s" % (k, v))
    print("\n--- COLLECTIVE ACTION (3.5%% ref) ---", coll)
    print("\n--- SAMPLE MACRO FEED (social + structural) ---")
    for e in w.events[:24]:
        print("  t%-5d [%-9s] %s" % (e["tick"], e["kind"], e.get("text", "")))
    print("\n--- SAMPLE JOURNALS (real graph reads) ---")
    for sj in sample_journals[:3]:
        print("  %s: %s" % (sj["resident"], sj["entry"]))
    print("\nMACRO REGIME VERDICT:", verdict)
    for k, v in ev.items():
        print("  %-28s %s" % (k, v))
    print("wrote:", os.path.join(OUTDIR, "macro.json"))
    print("wrote:", os.path.join(OUTDIR, "townstate.json"))
    print("wrote:", os.path.join(OUTDIR, "social.json"))
    return verdict


if __name__ == "__main__":
    main(sys.argv)
