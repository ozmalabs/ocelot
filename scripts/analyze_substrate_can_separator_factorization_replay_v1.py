#!/usr/bin/env python3
"""Independent current-source analysis of the separator-factorization replay."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/can_separator_factorization_replay_v1_20260926.json"
OUT=ROOT/"evaluation/reports/can_separator_factorization_replay_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/can_separator_factorization_replay_v1_lock_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def expected_factor_evaluations(r):
 f,m,k,d=(r[x] for x in ("frames","interior_nodes_per_frame","separator_dimensions","domain_size"))
 return d**k*(math.comb(k,2)+f*d**m*(m+k*m+math.comb(m,2)))
def main():
 p=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());workers=p["workers"]
 all_runs=[(w["replicate"],r) for w in workers for r in w["base_capture"]["runs"]]
 cfg=lambda r:(r["frames"],r["interior_nodes_per_frame"],r["separator_dimensions"],r["domain_size"],r["replicate"])
 unique={cfg(r) for _,r in all_runs}
 design=lambda r:(r["frames"],r["interior_nodes_per_frame"],r["separator_dimensions"],r["domain_size"])
 checks={"schema_and_288_runs":p.get("schema_version")==1 and len(all_runs)==288,"source_lock_and_capture_hash":p["locked_inputs"]==lock["locked_inputs"] and p["lock_sha256"]==sha(LOCK) and p["post_run_inputs"]==p["locked_inputs"],"three_fresh_stable_workers":len(workers)==3 and len({w["pid"] for w in workers})==3 and all(w["started_inputs"]==p["locked_inputs"]==w["finished_inputs"] for w in workers),"complete_96_case_design_replayed":len(unique)==96 and all(len(w["base_capture"]["runs"])==96 for w in workers),"current_python_sources_match_lock":all(w["base_capture"]["source_sha256"]["domains/can_junction_tree.py"]==p["locked_inputs"]["source_sha256"]["jt"] and w["base_capture"]["source_sha256"]["domains/graph_treewidth.py"]==p["locked_inputs"]["source_sha256"]["width"] and w["base_capture"]["source_sha256"]["scripts/can_separator_factorization_envelope.py"]==p["locked_inputs"]["base_runner_sha256"] for w in workers),"model_extraction_width_and_map_all_valid":all(r["input_model_extraction_exact"] and abs(r["exact_energy_gap"])<=1e-7 and r["treewidth_upper_bound"]==r["separator_dimensions"]+r["interior_nodes_per_frame"]-1 for _,r in all_runs),"boundary_and_local_assignment_formulas":all(r["separator_assignments"]==r["domain_size"]**r["separator_dimensions"] and r["frame_local_assignments_checked"]==r["frames"]*r["domain_size"]**(r["separator_dimensions"]+r["interior_nodes_per_frame"]) for _,r in all_runs),"factor_touch_count_formula":all(r["factor_evaluations"]==expected_factor_evaluations(r) for _,r in all_runs),"three_samples_per_fixed_seed_model":all(sum(cfg(r)==key for _,r in all_runs)==3 for key in unique),"six_samples_per_structural_configuration":all(sum(design(r)==key for _,r in all_runs)==6 for key in {design(r) for _,r in all_runs})}
 selected=[]
 for F in (2,4,8):
  for k in (1,3):
   rs=[r for _,r in all_runs if r["frames"]==F and r["interior_nodes_per_frame"]==4 and r["separator_dimensions"]==k and r["domain_size"]==3]
   selected.append({"frames":F,"interior_size":4,"boundary_dimensions":k,"domain_size":3,"nodes":rs[0]["nodes"],"treewidth":rs[0]["treewidth_upper_bound"],"local_assignments_per_run":rs[0]["frame_local_assignments_checked"],"median_conditional_map_ms":statistics.median(r["cost_ns"]["conditional_frame_exact"] for r in rs)/1e6,"median_global_junction_tree_ms":statistics.median(r["cost_ns"]["global_junction_tree"] for r in rs)/1e6,"median_factor_touches":int(statistics.median(r["factor_evaluations"] for r in rs))})
 out={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"passed":all(checks.values()),"runs":len(all_runs),"unique_generated_models":96,"timing_samples_per_generated_model":6,"selected_scaling_rows":selected,"claim_boundary":"Validates the explicit single-separator cost formula and exact results on this generated family; bounded separator alone is insufficient unless frame interior/factor work is also bounded, and the substrate does not discover or schedule these cuts automatically."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
 if not out["passed"]:raise SystemExit("independent analysis failed")
if __name__=="__main__":main()
