#!/usr/bin/env python3
"""Independent exact-work and semantic analysis for scheduler dirty-density v1."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_scheduler_dirty_density_v1_workers_raw_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_scheduler_dirty_density_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/scheduler_dirty_density_v1_lock_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(n,k,pos,rep) for n in (8,32,128) for k in {1,n//4,n} for pos in ("prefix","suffix") for rep in range(3)}
 checks={"complete_factorial_54_workers":len(runs)==54 and {(r["rule_count"],r["dirty_count"],r["position"],r["replicate"]) for r in runs}==expected,"fresh_process_per_worker":len({r["pid"] for r in runs})==54,"locked_inputs_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(r["before"]==lock==r["after"] for r in runs)}
 rows=[]
 for r in runs:
  n,k,pos,rep=r["rule_count"],r["dirty_count"],r["position"],r["replicate"];p=r["cells"]["plain"];a=r["cells"]["audit"];c=a["counters"]
  probe_first=1 if pos=="prefix" else n-k+1
  target={"scheduler_passes":2,"scheduler_external_poll_slots":2*n,"scheduler_fixedpoint_probe_slots":n+probe_first,"scheduler_dirty_vector_slots":n,"scheduler_selected_rules":k,"rule_enumerations":k,"rule_effect_edge_insert_attempts":k}
  prefix=f"n{n}_k{k}_{pos}_r{rep}"
  checks[prefix+"_plain_audit_graph_report_parity"]=p["graph"]==a["graph"] and p["report"]==a["report"]
  checks[prefix+"_positive_effect_oracle"]=a["report"]["status"]=="fixed_point" and a["report"]["progress_steps"]==k and a["report"]["passes_completed"]==2 and a["derived_edge_count"]==k and a["trigger_edge_count"]==k
  checks[prefix+"_exact_scheduler_integer_work"]=all(c.get(name)==value for name,value in target.items())
  checks[prefix+"_selected_rules_exact"]=len(a["selected"])==k
  rows.append({"rule_count":n,"dirty_count":k,"position":pos,"replicate":rep,"expected":target,"observed":{key:c.get(key,0) for key in target},"scheduler_plan_ns":c.get("scheduler_plan_ns",0),"progress_steps":a["report"]["progress_steps"]})
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"claim_boundary":"Positive one-edge joins after one controlled mutation; exact monolithic scheduler slot work and graph/report parity only. Authored rule schema, no natural workload, no scoped execution, and timer excludes setup, queue drains and rule execution."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
