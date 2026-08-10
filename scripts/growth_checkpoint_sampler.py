#!/usr/bin/env python3
"""Sample a growth run from its CHECKPOINTS rather than its HTTP endpoint.

Written after growth7-9 (2026-08-07), whose samplers failed twice over: they
polled HTTP and timed out for the last 2-4 hours of every run once the daemon
got slow, and they wrote lines TRUNCATED AT 340 CHARACTERS, so the developmental
state -- the only thing the runs existed to measure -- was never captured at all
and had to be recovered from the checkpoints afterwards.

So read the checkpoint. It is written on a fixed interval by the daemon itself,
it cannot be starved by a busy tick loop, and it is the same artefact the
forensics used. One JSON object per line, never truncated.

Watches specifically for the three things fixed in 855ee0e4c8:
  imagined_conclusions   -- the OOM (960,663 nodes in growth7, 96.1% of graph)
  positive_progress      -- kept apart from success_count, which mastery reads
  suspension             -- released_from_meta_suspension / status
plus the ordering fix's unmeasured_receipt_count, which should stay 0 while the
support-topology channel is live.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys
import time


def sample(checkpoint: pathlib.Path) -> dict:
    graph = json.loads(checkpoint.read_text(encoding="utf-8"))["graph"]
    nodes = graph["nodes"]
    types = collections.Counter(n["type"] for n in nodes)

    caps = []
    for n in nodes:
        if n["type"] != "EmbodiedSituatedDevelopmentalCapability":
            continue
        a = n["attrs"]
        if not (a.get("attempt_count") or a.get("status") not in (None, "available")):
            continue
        caps.append({
            "ordinal": a.get("ordinal"),
            "name": a.get("name"),
            "status": a.get("status"),
            "attempts": a.get("attempt_count"),
            "successes": a.get("success_count"),
            "failures": a.get("failure_count"),
            "retention": a.get("retention_count"),
            "progress": a.get("positive_progress_count"),
            "unmeasured": a.get("unmeasured_receipt_count"),
            "blocked_on": a.get("measurement_blocked_on"),
            "released": a.get("released_from_meta_suspension"),
        })
    caps.sort(key=lambda c: (c["ordinal"] is None, c["ordinal"]))

    imaginations = [n for n in nodes if n["type"] == "Imagination"]
    compacted = sum(1 for n in imaginations if n["attrs"].get("trace_compacted"))

    return {
        "t": int(checkpoint.stat().st_mtime),
        "checkpoint": checkpoint.name,
        "nodes": len(nodes),
        "edges": len(graph["edges"]),
        "imagined_conclusions": types.get("ImaginedConclusion", 0),
        "imaginations": len(imaginations),
        "traces_compacted": compacted,
        "receipts": types.get("EmbodiedLearningTrialReceipt", 0),
        "top_types": types.most_common(5),
        "capabilities": caps,
    }


def main(argv) -> int:
    ckpt_dir = pathlib.Path(argv[1])
    out = pathlib.Path(argv[2])
    every = float(argv[3]) if len(argv) > 3 else 300.0
    seen = set()
    while True:
        saves = sorted(ckpt_dir.glob("*.save"), key=lambda p: p.stat().st_mtime)
        if saves and saves[-1].name not in seen:
            newest = saves[-1]
            seen.add(newest.name)
            try:
                record = sample(newest)
            except Exception as exc:                      # noqa: BLE001
                # A checkpoint caught mid-write is not a reason to lose the run.
                record = {"t": int(time.time()), "error": f"{type(exc).__name__}: {exc}"}
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        time.sleep(every)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
