#!/usr/bin/env python3
"""Independent verification of aggregate Bigville component inference."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_bigville_aggregate_component_inference_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_bigville_aggregate_component_inference_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/bigville_aggregate_component_inference_v1_lock_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=p["runs"];cases=[c for r in runs for c in r["cases"]]
 orders={tuple(c["arm_order"]) for c in cases if c["n_residents"]==10}
 checks={"schema_and_12_cases":p.get("schema_version")==1 and len(cases)==12,"source_lock_and_capture_hash":p["locked_inputs"]==lock["locked_inputs"] and p["lock_sha256"]==sha(LOCK) and p["post_run_inputs"]==p["locked_inputs"],"three_fresh_stable_workers":len(runs)==3 and len({r["pid"] for r in runs})==3 and all(r["started_inputs"]==p["locked_inputs"]==r["finished_inputs"] for r in runs) and all(c["source_inputs_start"]==p["locked_inputs"]==c["source_inputs_end"] for c in cases),"all_resident_counts_replicated":all(sum(c["n_residents"]==n for c in cases)==3 for n in (10,25,50,100)),"all_arm_orders_balanced":orders=={("global","components"),("components","global")},"live_extraction_matches_resident_union":all(c["extraction_union_exact"] for c in cases),"graph_discovery_reconstructs_components":all(c["discovered_component_count"]==c["n_residents"] and c["discovered_component_sizes"]==[5]*c["n_residents"] and c["discovered_component_pair_counts"]==[5]*c["n_residents"] and c["nodes"]==5*c["n_residents"] and c["undirected_pairs"]==5*c["n_residents"] for c in cases),"exact_global_and_local_energy_agreement":all(abs(c["exact_energy_gap"])<=1e-7 and abs(c["global_exact_energy"]-c["independent_global_energy_of_global_state"])<=1e-7 and abs(c["component_exact_energy"]-c["independent_global_energy_of_component_state"])<=1e-7 for c in cases),"width_state_domain_and_oracle_counts":all(c["max_global_width_upper_bound"]==2 and c["max_component_width_upper_bound"]==2 and c["global_state_vocab_valid"] and c["component_state_vocab_valid"] and c["component_exhaustive_states_checked"]==243*c["n_residents"] for c in cases),"positive_timing_records":all(all(v>0 for v in c["timing_ns"].values()) for c in cases)}
 summary=[]
 for n in (10,25,50,100):
  cs=[c for c in cases if c["n_residents"]==n]
  g=statistics.median(c["timing_ns"]["global_width_and_junction_tree"] for c in cs)
  q=statistics.median(c["timing_ns"]["components_discovery_and_exhaustive_map"] for c in cs)
  summary.append({"residents":n,"variables":5*n,"discovered_components":n,"states_checked_by_local_oracle":243*n,"replicates":len(cs),"median_aggregate_extraction_ms":statistics.median(c["timing_ns"]["aggregate_network_extraction"] for c in cs)/1e6,"median_global_width_and_junction_tree_ms":g/1e6,"median_component_discovery_and_exact_local_map_ms":q/1e6,"median_component_over_global_time_ratio":statistics.median(c["timing_ns"]["components_discovery_and_exhaustive_map"]/c["timing_ns"]["global_width_and_junction_tree"] for c in cs)})
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"passed":all(checks.values()),"case_count":len(cases),"summary_by_resident_count":summary,"claim_boundary":p["claim_boundary"]}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
 if not out["passed"]:raise SystemExit("independent analysis failed")
if __name__=="__main__":main()
