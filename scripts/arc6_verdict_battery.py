#!/usr/bin/env python
"""arc6_verdict_battery — the arc-6 NON-SCALAR ROW VERDICT pricing arm.

Same driver as `scripts/arc6_tier0_battery.py` (`mbpp_arc3_battery.run_arm`
verbatim, the UNCHANGED `domains.prog_synthesis.synthesize_from_request`
pipeline), with ONE addition: it keeps the accepted IR and the held-out
verdict for every runnable task, so the pricing report can run constructed
witnesses on the exact program each arm accepted.

This script touches NO synthesis, engine, seed or spec code.  The
intervention under pricing is a SEED edit (`seeds/program_synthesis.json`,
ps_row_pass / ps_row_fail) applied BETWEEN the two invocations of this
script; the script itself is identical in both arms, so the diff is the
seed and nothing else.

Run:
  OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python scripts/arc6_verdict_battery.py <label>
"""
from __future__ import annotations

import hashlib
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
SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
    # Per-task detail the pricing report needs: what was ACCEPTED (status),
    # what IR was accepted, and what the held-out verdict said.  Mechanical
    # read-back of the driver's own row dicts.
    per_task = {}
    for r in arm["runnable_rows"]:
        per_task[str(r["task_id"])] = {
            "outcome": r["outcome"],
            "status": r["status"],
            "construction": r["construction"],
            "gap_reason": r["gap_reason"],
            "enumerate_outcome": r.get("enumerate_outcome"),
            "ir": r.get("ir"),
            "holdout": r.get("holdout"),
            "n_revealed": r["n_revealed"],
            "n_held_out": r["n_held_out"],
        }

    rec = {
        "_README": ("arc6 non-scalar-row-verdict pricing snapshot -- paired "
                    "id lists, never a bare count.  The aggregate is "
                    "UNDERPOWERED BY CONSTRUCTION: any move of a few ids "
                    "sits inside the baseline Wilson CI [9.96, 18.35]; the "
                    "result is the id list plus witnesses, not the score."),
        "label": label,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine_provenance": provenance_stamp(),
        "seed_sha256": _sha256_file(SEED_PATH),
        "elapsed_seconds": round(elapsed, 2),
        "n_runnable": len(arm["runnable_rows"]),
        "determinism": arm["determinism"],
        "pass_ids": sorted(tax.get("pass", {}).get("task_ids", [])),
        "accepted_ids": sorted(int(k) for k, v in per_task.items()
                               if v["status"] == "accepted"),
        "outcome_taxonomy": {k: {"n": v["n"], "task_ids": sorted(v["task_ids"])}
                             for k, v in sorted(tax.items())},
        "aggregates": arm["aggregates"],
        "per_task": per_task,
    }
    out = os.path.join(ROOT, "results", "arc6_verdict_%s.json" % label)
    with open(out, "w") as f:
        json.dump(rec, f, indent=2, sort_keys=True, default=arc3b._json_default)
    print("pass n=%d" % len(rec["pass_ids"]))
    print("pass ids:", rec["pass_ids"])
    print("accepted n=%d" % len(rec["accepted_ids"]))
    print("accepted ids:", rec["accepted_ids"])
    print("wrote", out, "in %.1fs" % elapsed)


if __name__ == "__main__":
    main()
