"""ARM 4 -- the observability fraction.

For each whole-seed ablation of the fixed probe world: did the functional
readout DEGRADE, and if so did the graph RECORD it?

  DEGRADED   the probe's readout (node/edge counts, ON/OFF channels, learned
             gains) differs from baseline.
  SELF-EVIDENT  the marker inventory also differs -- the graph carries some
             node type or attribute saying something went wrong.
  SILENT     degraded, and the marker inventory is IDENTICAL to baseline. The
             system produced a confident, well-formed, WRONG answer and left
             no evidence.

The reported statistic is SELF-EVIDENT / DEGRADED.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS = os.path.join(ROOT, "results", "redundancy_obs")


def main() -> None:
    base = json.load(open(os.path.join(OBS, "BASELINE.json")))
    br, bm = base["readout"], base["markers"]
    rows = []
    print("=" * 96)
    print("ARM 4 -- OBSERVABILITY. Does the graph RECORD that a fallback happened?")
    print("=" * 96)
    print(f"{'seed':24s} {'crash':>6s} {'degraded':>9s} {'markers?':>9s}  {'verdict':<12s} what changed")
    for fn in sorted(os.listdir(OBS)):
        sid = fn[:-5]
        if sid == "BASELINE":
            continue
        d = json.load(open(os.path.join(OBS, fn)))
        if d.get("crashed"):
            print(f"{sid:24s} {'YES':>6s} {'-':>9s} {'-':>9s}  {'CRASH':<12s} {d.get('exc','')[:40]}")
            rows.append({"seed": sid, "crashed": True})
            continue
        r, m = d["readout"], d["markers"]
        degraded = r != br
        marked = m != bm
        what = []
        if r.get("nodes") != br.get("nodes"):
            what.append(f"nodes {br['nodes']}->{r['nodes']}")
        for key in ("channels_on", "channels_off", "gains"):
            a, b = r.get(key), br.get(key)
            if a != b:
                sa = sum(x for x in (a or []) if isinstance(x, float))
                sb = sum(x for x in (b or []) if isinstance(x, float))
                what.append(f"{key} sum {sb:.3f}->{sa:.3f}")
        verdict = ("SELF-EVIDENT" if marked else "SILENT") if degraded else "no-change"
        rows.append({"seed": sid, "crashed": False, "degraded": degraded,
                     "marked": marked, "verdict": verdict, "what": what})
        print(f"{sid:24s} {'no':>6s} {str(degraded):>9s} {str(marked):>9s}  {verdict:<12s} "
              f"{'; '.join(what)[:70]}")

    deg = [r for r in rows if not r.get("crashed") and r.get("degraded")]
    se = [r for r in deg if r["marked"]]
    print()
    print(f"  degraded-and-non-crashing: {len(deg)}")
    print(f"  of those, SELF-EVIDENT from graph state alone: {len(se)}")
    print(f"  OBSERVABILITY FRACTION = {len(se)}/{len(deg)} = "
          f"{(len(se)/len(deg) if deg else float('nan')):.3f}")
    with open(os.path.join(ROOT, "results", "redundancy_observability.json"), "w") as fh:
        json.dump({"rows": rows, "n_degraded": len(deg), "n_self_evident": len(se)},
                  fh, indent=1, sort_keys=True)
    print("\n[written] results/redundancy_observability.json")


if __name__ == "__main__":
    main()
