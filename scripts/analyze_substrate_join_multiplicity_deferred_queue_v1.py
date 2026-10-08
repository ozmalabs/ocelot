#!/usr/bin/env python3
"""Exact semantic and queue-work analysis for the join-multiplicity sweep."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_join_multiplicity_deferred_queue_v1_workers_raw_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_join_multiplicity_deferred_queue_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/join_multiplicity_deferred_queue_v1_lock_20260926.json"
FAMILIES=("rule_edits","fb_samples")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(r,m,rep) for r in (1,8,32) for m in (1,4,16) for rep in range(3)}
 checks={"27_worker_factorial":len(runs)==27 and {(x["rules"],x["multiplicity"],x["replicate"]) for x in runs}==expected,"fresh_processes":len({x["pid"] for x in runs})==27,"stable_source_native_inputs":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["before"]==lock==x["after"] for x in runs)}
 rows=[]
 for x in runs:
  r,m,rep=x["rules"],x["multiplicity"],x["replicate"];p=x["plain"];a=x["audit"];c=a["counters"];pre=f"r{r}_m{m}_rep{rep}";items=r*m
  checks[pre+"_plain_audit_graph_report_parity"]=p["graph"]==a["graph"] and p["report"]==a["report"]
  checks[pre+"_positive_join_and_mutation_oracle"]=a["report"]["status"]=="fixed_point" and a["report"]["budget_overshoot"]==0 and a["seen_edges"]==r and a["grid_cells"]==4*r and a["trigger_edges"]==0
  checks[pre+"_global_queue_conservation"]=all(c.get(f"deferred_queue:{f}:enqueued_items")==items and c.get(f"deferred_queue:{f}:drained_items")==items and c.get(f"deferred_queue:{f}:drain_batches")==1 for f in FAMILIES)
  writer_ids={int(z["rule_index"]) for z in a["writers"]}
  for f in FAMILIES:
   metric=f"deferred_queue_enqueued:{f}";attributed={int(i):int(count) for i,name,count in a["per_rule"] if name==metric and int(i) in writer_ids}
   checks[pre+f"_{f}_per_writer_match_multiplicity"]=attributed=={i:m for i in writer_ids}
  checks[pre+"_trigger_deletions_exact"]=c.get("rule_effect_edge_deletes")==r
  rows.append({"rules":r,"multiplicity":m,"replicate":rep,"queue_items_expected":items,"queue_items_observed":{f:c.get(f"deferred_queue:{f}:enqueued_items",0) for f in FAMILIES},"candidate_pairs":c.get("cand_enum",0),"candidate_tests":c.get("cand_tested",0),"bindings_cloned":c.get("bindings_cloned",0),"scheduler_passes":c.get("scheduler_passes",0),"scheduler_plan_ns":c.get("scheduler_plan_ns",0)})
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"claim_boundary":"Two-edge positive joins with multiplicity M, queue work and trigger deletion/requeue suppression in one authored full-closure workload. No natural workload, scoped execution, or generalized complexity guarantee."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
