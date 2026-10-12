#!/usr/bin/env python3
"""Independent integrity analysis for the authored CAN Stage A envelope."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_can_stage_a_fallback_envelope_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_can_stage_a_fallback_envelope_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/can_stage_a_fallback_envelope_v1_lock_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());cells=p["cells"]
 workers=p["worker_processes"]
 checks={"schema_and_cell_count":p.get("schema_version")==1 and len(cells)==18,"lock_and_capture_hashes":p["locked_inputs"]==lock["locked_inputs"] and p["lock_sha256"]==sha(LOCK),"three_distinct_fresh_workers":len(workers)==3 and len({r["pid"] for r in workers})==3,"stable_source_inputs":p["post_run_inputs"]==p["locked_inputs"] and all(r["started_inputs"]==p["locked_inputs"]==r["finished_inputs"] for r in workers) and all(a["inputs_start"]==p["locked_inputs"]==a["inputs_end"] for c in cells for a in (c["ordinary"],c["compare_only"],c["stage_a_enabled"])),"full_design_replication":all(sum(c["n"]==n and c["topology"]==t for c in cells)==3 for n in (16,32) for t in ("path","banded2","complete")),"all_arms_independently_fixed_points":all(a["budget_complete"] and a["terminal_probe"]==0 and a["independent_fixed_point_residuals"]==0 for c in cells for a in (c["ordinary"],c["compare_only"],c["stage_a_enabled"])),"exact_stage_a_vs_ordinary_parity":all(c["exact_graph_parity"] and c["progress_parity"] for c in cells),"rates_and_counts_consistent":all(c["eligible_drain_count"]==c["compare_only"]["stage_a_compare_stats"]["compared_drains"] and c["excluded_drain_count"]==c["stage_a_enabled"]["stage_a_stats"]["excluded_drains"] and ((c["fallback_rate_per_derivable_drain"] is None and c["eligible_drain_count"]==0 and c["stage_a_enabled"]["stage_a_stats"]["conflict_fallbacks"]==0) or c["fallback_rate_per_derivable_drain"]==c["stage_a_enabled"]["stage_a_stats"]["conflict_fallbacks"]/c["eligible_drain_count"]) for c in cells),"diagnostic_divergence_zero":all(c["compare_only"]["stage_a_compare_stats"]["diverged_drains"]==0 and c["compare_only"]["stage_a_compare_stats"]["unsound_drains"]==0 for c in cells)}
 grouped=[]
 for n in (16,32):
  for topology in ("path","banded2","complete"):
   cs=[c for c in cells if c["n"]==n and c["topology"]==topology]
   grouped.append({"n":n,"topology":topology,"replicates":len(cs),"eligible_drains":sum(c["eligible_drain_count"] for c in cs),"excluded_drains":sum(c["excluded_drain_count"] for c in cs),"fallbacks":sum(c["stage_a_enabled"]["stage_a_stats"]["conflict_fallbacks"] for c in cs),"fallback_rate":None if sum(c["eligible_drain_count"] for c in cs)==0 else sum(c["stage_a_enabled"]["stage_a_stats"]["conflict_fallbacks"] for c in cs)/sum(c["eligible_drain_count"] for c in cs),"median_ordinary_wall_ns":int(statistics.median(c["ordinary"]["wall_time_ns"] for c in cs)),"median_stage_a_wall_ns":int(statistics.median(c["stage_a_enabled"]["wall_time_ns"] for c in cs)),"median_time_ratio":statistics.median(c["stage_a_enabled"]["wall_time_ns"]/c["ordinary"]["wall_time_ns"] for c in cs)})
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"passed":all(checks.values()),"cell_count":len(cells),"all_eligible_drain_count":sum(c["eligible_drain_count"] for c in cells),"all_excluded_drain_count":sum(c["excluded_drain_count"] for c in cells),"all_fallback_count":sum(c["stage_a_enabled"]["stage_a_stats"]["conflict_fallbacks"] for c in cells),"by_size_topology":grouped,"claim_boundary":p["claim_boundary"]}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
 if not out["passed"]:raise SystemExit("independent analysis failed")
if __name__=="__main__":main()
