#!/usr/bin/env python3
"""Independent exact-work analysis for monolithic scheduler slot counters."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_monolithic_scheduler_work_v1_workers_raw_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_monolithic_scheduler_work_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/monolithic_scheduler_work_v1_lock_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 checks={"12_workers_complete_factorial":len(runs)==12 and {(r["rule_count"],r["replicate"]) for r in runs}=={(n,k) for n in (1,8,32,128) for k in range(3)},
  "fresh_process_per_worker":len({r["pid"] for r in runs})==12,
  "source_native_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(r["before"]==lock==r["after"] for r in runs)}
 rows=[]
 for r in runs:
  n=r["rule_count"];rep=r["replicate"];plain=r["cells"]["plain"];aud=r["cells"]["audit"]
  for phase,external,fixed,dirty,selected in (("first_call",n,1,n,n),("warm_fixedpoint_call",n,n,0,0)):
   p=plain[phase];a=aud[phase];c=a["counters"];prefix=f"n{n}_r{rep}_{phase}"
   checks[f"{prefix}_plain_audit_semantics_and_projection_equal"]=(p["report"]==a["report"] and p["projection"]==a["projection"])
   checks[f"{prefix}_fixedpoint_no_progress"]=(a["report"]["status"]=="fixed_point" and a["report"]["progress_steps"]==0 and a["report"]["passes_completed"]==1)
   checks[f"{prefix}_scheduler_pass_equals_report"]=(c.get("scheduler_passes")==a["report"]["passes_completed"]==1)
   checks[f"{prefix}_external_poll_slots_exact"]=(c.get("scheduler_external_poll_slots")==external)
   checks[f"{prefix}_fixedpoint_probe_slots_exact"]=(c.get("scheduler_fixedpoint_probe_slots")==fixed)
   checks[f"{prefix}_dirty_vector_scan_exact"]=(c.get("scheduler_dirty_vector_slots")==dirty)
   checks[f"{prefix}_selected_rules_exact"]=(c.get("scheduler_selected_rules")==selected)
   checks[f"{prefix}_plan_time_present"]=(c.get("scheduler_plan_ns",0)>=0)
   if phase=="first_call": checks[f"{prefix}_rule_enumerations_exact"]=(c.get("rule_enumerations")==n)
   else: checks[f"{prefix}_no_rule_enumerations"]=(c.get("rule_enumerations")==0)
   rows.append({"rule_count":n,"replicate":rep,"phase":phase,"counters":{k:c.get(k,0) for k in (
    "scheduler_passes","scheduler_external_poll_slots","scheduler_fixedpoint_probe_slots","scheduler_dirty_vector_slots","scheduler_selected_rules","scheduler_plan_ns","rule_enumerations")}})
 checks["exact_integer_work_rows_repeat_by_size_phase"]=all(len({json.dumps({k:v for k,v in x["counters"].items() if k!="scheduler_plan_ns"},sort_keys=True) for x in rows if x["rule_count"]==n and x["phase"]==phase})==1 for n in (1,8,32,128) for phase in ("first_call","warm_fixedpoint_call"))
 payload={"schema_version":1,"raw_capture_sha256":sha(RAW),"analysis_script_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"rows":rows,
  "claim_boundary":"Exact scheduler slot counts for the monolithic no-match rule family only. The plan timer is audit-on and excludes queue drains and rule execution; it is descriptive. Scoped scheduling, positive matches, external gates and natural workloads remain unmeasured."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":sum(checks.values()),"checks_total":len(checks)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
