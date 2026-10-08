#!/usr/bin/env python3
"""Independent semantic and isolation checks for the solver snapshot consumer."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/cow_solver_alternatives_snapshot_v1_1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/cow_solver_alternatives_snapshot_v1_1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/cow_solver_alternatives_snapshot_v1_1_analysis_20261001.json"
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(r,v) for r in range(5) for v in (-1.0,-0.25,0.5,1.25)}
 checks={"complete_20_cell_panel":len(runs)==20 and {(x["replicate"],x["perturbation"]) for x in runs}==expected,"20_fresh_processes":len({x["pid"] for x in runs})==20,"stable_locked_inputs":raw["locked_inputs"]==lock==raw["post_run_inputs"],"valid_reusable_snapshot_identity":all(x["snapshot"]["backend"]=="shared_graph_pages" and x["snapshot"]["source_revision"]==x["revision"] for x in runs),"read_only_snapshot_matches_eager_base":all(x["read_only_probe_digest"]==x["eager_initial_digest"]==x["cow_initial_digest"] for x in runs),"primary_unchanged":all(x["primary_digest_before"]==x["primary_digest_after"] for x in runs),"sibling_starts_from_unmodified_base":all(x["sibling_digest_after"]==x["primary_digest_before"] and x["sibling_fields_after"]==x["baseline_fields"] for x in runs)}
 parity=[]
 for x in runs:
  a,b=x["cow"],x["eager"]
  row=(a["pre_perturbation_field"]==b["pre_perturbation_field"]==x["baseline_fields"][next(iter(x["baseline_fields"]))] and a["input_field"]==b["input_field"]==x["perturbation"] and a["steps"]==b["steps"] and a["energy"]==b["energy"] and a["frustration"]==b["frustration"] and a["coverage"]==b["coverage"] and a["states"]==b["states"] and a["fields"]==b["fields"] and a["graph_digest"]==b["graph_digest"])
  parity.append(row)
 checks["solver_results_exactly_match_eager_control"]=all(parity)
 payload={"protocol":"COW_SOLVER_ALTERNATIVES_SNAPSHOT_V1_1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"median_cow_fork_ms":sorted(x["cow_fork_ns"] for x in runs)[len(runs)//2]/1e6,"median_eager_fork_ms":sorted(x["eager_fork_ns"] for x in runs)[len(runs)//2]/1e6,"median_cow_solve_ms":sorted(x["cow"]["solve_ns"] for x in runs)[len(runs)//2]/1e6,"median_eager_solve_ms":sorted(x["eager"]["solve_ns"] for x in runs)[len(runs)//2]/1e6,"exact_solver_parity_cells":sum(parity),"claim_boundary":"Reusable CoW snapshots support one actual native CAN solver-alternative consumer with exact eager-copy parity and isolation on one four-concept topology; not solver optimality, general planning, concurrent lifecycle, broad performance, natural-task, or serving evidence.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analysis_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"parity_cells":payload["exact_solver_parity_cells"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
