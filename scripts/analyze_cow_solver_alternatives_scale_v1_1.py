#!/usr/bin/env python3
"""Independent validation and cost summary for scaled solver alternatives."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/cow_solver_alternatives_scale_v1_1_workers_20261001.json";LOCK=ROOT/"evaluation/substrate_capability/cow_solver_alternatives_scale_v1_1_lock_20261001.json";OUT=ROOT/"evaluation/reports/cow_solver_alternatives_scale_v1_1_analysis_20261001.json"
def median_ms(xs):return statistics.median(xs)/1e6

def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"];expected={(n,t,r) for n in (32,128,256) for t in ("path","banded2") for r in range(3)}
 checks={"complete_18_worker_factorial":len(runs)==18 and {(x["n"],x["topology"],x["replicate"]) for x in runs}==expected,"fresh_worker_processes":len({x["pid"] for x in runs})==18,"stable_locked_inputs":raw["locked_inputs"]==lock==raw["post_run_inputs"],"snapshot_identity_revision":all(x["snapshot"]["backend"]=="shared_graph_pages" and x["snapshot"]["source_revision"]==x["revision"] for x in runs),"primary_and_later_fork_isolation":all(x["base_digest"]==x["primary_digest_after"]==x["later_fork_digest"] and x["base_states"]==x["later_fork_states"] for x in runs),"all_workers_four_alternatives":all(len(x["alternatives"])==4 for x in runs)}
 parity=[];fixed=[]
 for w in runs:
  for alt in w["alternatives"]:
   a,b=alt["cow"],alt["eager"]
   parity.append(a["input"]==b["input"]==alt["value"] and a["steps"]==b["steps"] and a["energy"]==b["energy"] and a["frustration"]==b["frustration"] and a["coverage"]==b["coverage"] and a["states"]==b["states"] and a["graph_digest"]==b["graph_digest"])
   fixed.append(a["terminal_progress"]==b["terminal_progress"]==0)
 checks["exact_solver_and_graph_parity_72_branches"]=len(parity)==72 and all(parity);checks["fixed_point_after_settle"]=len(fixed)==72 and all(fixed)
 groups=[]
 for n in (32,128,256):
  for topo in ("path","banded2"):
   cells=[w for w in runs if w["n"]==n and w["topology"]==topo]
   cowfork=[a["cow_fork_ns"] for w in cells for a in w["alternatives"]];eagerfork=[a["eager_fork_ns"] for w in cells for a in w["alternatives"]]
   cowsolve=[a["cow"]["settle_ns"] for w in cells for a in w["alternatives"]];eagersolve=[a["eager"]["settle_ns"] for w in cells for a in w["alternatives"]]
   groups.append({"n":n,"topology":topo,"snapshot_capture_median_ms":median_ms([w["capture_ns"] for w in cells]),"cow_fork_median_ms":median_ms(cowfork),"eager_fork_median_ms":median_ms(eagerfork),"cow_settle_median_ms":median_ms(cowsolve),"eager_settle_median_ms":median_ms(eagersolve)})
 payload={"protocol":"COW_SOLVER_ALTERNATIVES_SCALE_V1_1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"alternative_branch_pairs":len(parity),"cost_by_size_topology":groups,"claim_boundary":"Measured a reusable CoW solver consumer over 32–256 node path/banded CAN graphs with exact eager parity and fixed-point checks. One host/three replicates; no global-optimum, natural-task, concurrency, general planning, or broad speed claim.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analysis_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"branch_pairs":len(parity)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
