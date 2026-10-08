#!/usr/bin/env python3
"""Analyze the locked matched-width topology envelope."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/"evaluation/reports/can_matched_width_topology_envelope_v1_1_20260929.json"
LOCK=ROOT/"evaluation/substrate_capability/can_matched_width_topology_envelope_v1_1_lock_20260929.json"
RUNNER=ROOT/"evaluation/substrate_capability/can_matched_width_topology_envelope_v1.py"
OUT=ROOT/"evaluation/reports/can_matched_width_topology_envelope_v1_1_20260929_analysis.json"

def main():
    cap=json.loads(CAP.read_text()); lock=json.loads(LOCK.read_text())
    spec=importlib.util.spec_from_file_location("topology_runner",RUNNER)
    runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    assert cap["input_lock"]==cap["post_run_input_lock"]==lock==runner.input_lock()
    rows=cap["runs"]; assert len(rows)==144 and all(cap["checks"].values())
    cells=[]
    for q in runner.WIDTHS:
        for family in runner.FAMILIES:
            group=[r for r in rows if r["width"]==q and r["family"]==family]
            cells.append({"width":q,"family":family,"replicates":len(group),
                "minfill_width_counts":{str(k):sum(r["minfill_width"]==k for r in group)
                                         for k in sorted({r["minfill_width"] for r in group})},
                "false_refusals_at_bound_q":sum(not r["production_gate_within_bound_q"] for r in group),
                "median_ordering_ms":statistics.median(r["ordering_ns"] for r in group)/1e6,
                "median_gate_ms":statistics.median(r["gate_ns"] for r in group)/1e6,
                "median_bag_histograms":sorted({json.dumps(r["minfill_bag_size_histogram"],sort_keys=True)
                                                 for r in group})})
    analysis={"schema_version":1,"capture_sha256":hashlib.sha256(CAP.read_bytes()).hexdigest(),
        "lock_matches_live_inputs":True,"worker_count":len(rows),"integrity_gates_pass":all(cap["checks"].values()),
        "cells":cells,"claim_boundary":cap["claim_boundary"]}
    OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"analysis":OUT.relative_to(ROOT).as_posix(),"workers":len(rows),
                      "false_refusals":sum(c["false_refusals_at_bound_q"] for c in cells)},indent=2))

if __name__=="__main__": main()
