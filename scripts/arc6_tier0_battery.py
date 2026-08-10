#!/usr/bin/env python
"""arc6_tier0_battery — the arc-6 tier-0 BEFORE/AFTER measurement.

Driver reused VERBATIM from `scripts/mbpp_arc3_battery.py` (`run_arm`,
`q0_split_tasks`) and the artifact shape from
`scripts/arc5_final_battery.py`.  This script touches NO synthesis,
engine, seed or spec code: it boots agents, feeds the MBPP test split
through the UNCHANGED `domains.prog_synthesis.synthesize_from_request`
pipeline, reads outcomes back and writes ONE snapshot.

`results/arc5_final.json` is a FROZEN artifact and is only ever READ
here (for the 35-id baseline list).  Snapshots are written to
`results/arc6_tier0_<label>.json`.

Run:
  OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python scripts/arc6_tier0_battery.py <label>
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

# Engine provenance FIRST -- before anything imports substrate_rs.
from domains.engine_provenance import engine_preamble, provenance_stamp  # noqa: E402
engine_preamble()

import mbpp_arc3_battery as arc3b  # noqa: E402

FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    test_tasks = arc3b.q0_split_tasks(all_tasks)["test"]
    for t in test_tasks:
        assert "code" not in t, "contamination: code field survived split_tasks"
    test_tasks = sorted(test_tasks, key=lambda t: t["task_id"])

    t0 = time.time()
    arm = arc3b.run_arm("full_r3", test_tasks)
    elapsed = time.time() - t0

    tax = arm["outcome_taxonomy"]
    rec = {
        "_README": ("arc6 tier-0 snapshot -- paired id lists, never a bare "
                    "count.  The aggregate is UNDERPOWERED BY CONSTRUCTION: "
                    "35/257 -> 38/257 sits inside the baseline Wilson CI "
                    "[9.96, 18.35]; the result is the id list plus "
                    "witnesses, not the score."),
        "label": label,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine_provenance": provenance_stamp(),
        "elapsed_seconds": round(elapsed, 2),
        "n_runnable": len(arm["runnable_rows"]),
        "determinism": arm["determinism"],
        "pass_ids": sorted(tax.get("pass", {}).get("task_ids", [])),
        "outcome_taxonomy": {k: {"n": v["n"], "task_ids": sorted(v["task_ids"])}
                             for k, v in sorted(tax.items())},
        "aggregates": arm["aggregates"],
    }
    out = os.path.join(ROOT, "results", "arc6_tier0_%s.json" % label)
    with open(out, "w") as f:
        json.dump(rec, f, indent=2, sort_keys=True, default=arc3b._json_default)
    print("pass n=%d" % len(rec["pass_ids"]))
    print("pass ids:", rec["pass_ids"])
    print("wrote", out, "in %.1fs" % elapsed)


if __name__ == "__main__":
    main()
