#!/usr/bin/env python3
"""Analyze edge-matched graph width sweep."""
from __future__ import annotations
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/"evaluation/reports/can_edge_matched_width_topology_v1_20260929.json"
LOCK=ROOT/"evaluation/substrate_capability/can_edge_matched_width_topology_v1_lock_20260929.json"
RUNNER=ROOT/"evaluation/substrate_capability/can_edge_matched_width_topology_v1.py"
OUT=ROOT/"evaluation/reports/can_edge_matched_width_topology_v1_20260929_analysis.json"
def main():
 cap=json.loads(CAP.read_text()); lock=json.loads(LOCK.read_text())
 spec=importlib.util.spec_from_file_location("edge_match_runner",RUNNER); r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
 assert cap["input_lock"]==cap["post_run_input_lock"]==lock==r.input_lock()
 rows=cap["runs"]; assert len(rows)==72 and all(cap["checks"].values())
 cells=[]
 for q in r.WIDTHS:
  for f in r.FAMILIES:
   group=[x for x in rows if x["width"]==q and x["family"]==f]
   cells.append({"width":q,"family":f,"replicates":len(group),
    "minfill_width_counts":{str(k):sum(x["minfill_width"]==k for x in group) for k in sorted({x["minfill_width"] for x in group})},
    "false_refusals_at_bound_q":sum(not x["gate_accept_bound_q"] for x in group),
    "chordal_count":sum(x["chordal_by_mcs"] for x in group),
    "median_order_ms":statistics.median(x["ordering_ns"] for x in group)/1e6,
    "median_gate_ms":statistics.median(x["gate_ns"] for x in group)/1e6,
    "edge_counts":sorted({x["edges"] for x in group})})
 out={"schema_version":1,"capture_sha256":hashlib.sha256(CAP.read_bytes()).hexdigest(),
  "lock_matches_live_inputs":True,"worker_count":len(rows),"integrity_gates_pass":all(cap["checks"].values()),"cells":cells,
  "false_refusals_at_known_width_bound":sum(c["false_refusals_at_bound_q"] for c in cells),"claim_boundary":cap["claim_boundary"]}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":OUT.relative_to(ROOT).as_posix(),"workers":len(rows),"false_refusals":out["false_refusals_at_known_width_bound"]},indent=2))
if __name__=="__main__": main()
