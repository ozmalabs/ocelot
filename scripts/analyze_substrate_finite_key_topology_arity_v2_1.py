#!/usr/bin/env python3
"""Independent oracle and cost analysis for finite-key topology/arity sweep."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/mint_termination_topology_arity_v2_20260926.json"
OUT=ROOT/"evaluation/reports/mint_termination_topology_arity_v2_1_analysis_20260926.json"
TOPOLOGIES={"path":(16,32,64,128,256),"cycle":(16,32,64,128,256),"out_star":(16,32,64,128,256),"complete":(8,12,16,20)}
ARITIES=(1,2,3);REPEATS=3
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def edges_for(top,n):
 if top=="path":return [(i,i+1) for i in range(n-1)]
 if top=="cycle":return [(i,(i+1)%n) for i in range(n)]
 if top=="out_star":return [(0,j) for j in range(1,n)]
 return [(i,j) for i in range(n) for j in range(n) if i!=j]
def oracle(top,n,arity):
 initial=edges_for(top,n);targets=set()
 for start in range(n):
  def extend(path):
   if len(path)==arity+1:targets.add(path[-1]);return
   for a,b in initial:
    if a==path[-1] and b not in path:extend(path+[b])
  extend([start])
 nodes=[["Seed",json.dumps({"idx":i},sort_keys=True,separators=(",",":"))] for i in range(n)]
 if targets:nodes.append(["Witness",json.dumps({"tag":"shared"},sort_keys=True,separators=(",",":"))])
 labels={i:("Seed",json.dumps({"idx":i},sort_keys=True,separators=(",",":"))) for i in range(n)}
 if targets:labels[n]=("Witness",json.dumps({"tag":"shared"},sort_keys=True,separators=(",",":")))
 ed=sorted([[list(labels[i]),"link",list(labels[j]),"{}"] for i,j in initial]+[[list(labels[t]),"derived",list(labels[n]),"{}"] for t in targets])
 proj={"nodes":sorted(nodes),"edges":ed}
 return proj,len(targets)
def main():
 r=json.loads(RAW.read_text());cells=r["cells"];keys={(c["topology"],c["n"],c["arity"],c["replicate"]) for c in cells}
 expected={(t,n,a,rep) for t,ns in TOPOLOGIES.items() for n in ns for a in ARITIES for rep in range(1,REPEATS+1)}
 rowmap={(c["topology"],c["n"],c["arity"],c["replicate"]):c for c in cells};log=r["run_manifest"]["stdout_stderr_capture"];lp=ROOT/log["path"]
 exact=[];cost_rows=[]
 for key,c in rowmap.items():
  oracle_graph,target_count=oracle(*key[:3]);pair_ok=True
  for arm in ("plain","audit"):
   x=c[arm]
   pair_ok &= x["projection"]==oracle_graph and x["status"]=="fixed_point" and x["budget_overshoot"]==0 and x["progress_steps"]<=x["bound"]
  exact.append(pair_ok)
  counters={x["metric"]:x["count"] for x in c["audit"]["per_rule_counters"]}
  cost_rows.append({"topology":key[0],"n":key[1],"arity":key[2],"replicate":key[3],"target_count":target_count,"plain_wall_ns":c["plain"]["closure_wall_ns"],"audit_wall_ns":c["audit"]["closure_wall_ns"],"audit_cpu_ns":c["audit"]["closure_cpu_ns"],"candidate_tests":counters.get("candidate_tests",0),"candidate_pairs":counters.get("candidate_pairs",0),"term_evaluations":sum(v for k,v in counters.items() if "term" in k)})
 groups=[]
 for top,ns in TOPOLOGIES.items():
  for n in ns:
   for arity in ARITIES:
    rows=[x for x in cost_rows if x["topology"]==top and x["n"]==n and x["arity"]==arity]
    groups.append({"topology":top,"n":n,"arity":arity,"replicates":len(rows),"plain_wall_median_ns":statistics.median(x["plain_wall_ns"] for x in rows),"audit_wall_median_ns":statistics.median(x["audit_wall_ns"] for x in rows),"audit_candidate_tests_median":statistics.median(x["candidate_tests"] for x in rows),"audit_term_evaluations_median":statistics.median(x["term_evaluations"] for x in rows)})
 checks={"balanced_factorial":keys==expected and len(cells)==171 and r["passed_cells"]==171,"all_matched_arms_exact_oracle_fixedpoint_and_bounded":all(exact),"audit_counters_recorded_for_workloads":all(x["candidate_tests"]>0 for x in cost_rows),"finite_nonnegative_costs":all(x["plain_wall_ns"]>=0 and x["audit_wall_ns"]>=0 and x["audit_cpu_ns"]>=0 for x in cost_rows),"randomized_arm_order_valid":all(set(c["arm_order"])=={"plain","audit"} for c in cells),"source_lock_stable":r["locked_inputs"]==r["post_run_inputs"] and bool(r["lock_sha256"]),"manifest_success_and_engine_fresh":r["run_manifest"]["manifest_schema"]=="substrate-run-manifest-v1" and r["run_manifest"]["exit_status"]==0 and not r["run_manifest"]["engine"]["build_is_stale"],"parent_log_hash_matches":lp.is_file() and sha(lp)==log["sha256"] and lp.stat().st_size==log["bytes"] and lp.stat().st_size>0,"native_hash_matches":sha(Path(r["run_manifest"]["engine"]["native_extension_path"]))==r["run_manifest"]["engine"]["native_extension_sha256"]}
 out={"schema_version":1,"source":str(RAW.relative_to(ROOT)),"analysis_source_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"cell_summaries":groups,"claim_boundary":"Four authored directed graph topologies, three positive match arities, and one fixed finite-key effect family only. Uninstrumented and audit-on cost are separated; work counters describe this matcher path and do not establish a universal cost exponent or natural workload prevalence."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":out["all_checks_pass"],"checks":checks},indent=2,sort_keys=True))
 if not out["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
