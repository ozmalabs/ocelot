#!/usr/bin/env python3
"""Exact semantic and queue-work analysis for the join-multiplicity sweep."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/all_queue_multiplicity_work_trace_v1_workers_20261001.json"
OUT=ROOT/"evaluation/reports/all_queue_multiplicity_work_trace_v1_analysis_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/all_queue_multiplicity_work_trace_v1_lock_20261001.json"
FAMILIES=("rule_edits","rule_patches","fb_samples","track_identity","net_collapses")
FAMILY_CODES={"rule_edits":1,"rule_patches":2,"fb_samples":3,"track_identity":4,"net_collapses":5}
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
  expected_by_family={f:(r if f=="rule_patches" else items) for f in FAMILIES}
  checks[pre+"_global_queue_conservation"]=all(c.get(f"deferred_queue:{f}:enqueued_items")==expected_by_family[f] and c.get(f"deferred_queue:{f}:drained_items")==expected_by_family[f] and c.get(f"deferred_queue:{f}:drain_batches")==1 for f in FAMILIES)
  trace=a.get("runtime_work_trace") or {};work_rows=trace.get("rows",[]);work_counts={};ops={};work_valid=int(trace.get("dropped",-1))==0
  for wr in work_rows:
   scope=int(wr["scope"]);op=int(wr["operation_id"]);units=int(wr["units"]);uid=int(wr["producer_rule_uid"])
   work_valid &= scope>0 and op>0 and units>0 and uid>=0
   ops.setdefault((scope,op),[]).append(wr)
   work_counts[(str(wr["kind"]),wr.get("subject"))]=work_counts.get((str(wr["kind"]),wr.get("subject")),0)+units
  marker_valid=bool(ops) and all(len([z for z in group if z["kind"]=="operation_kind"])==1 and
   int([z for z in group if z["kind"]=="operation_kind"][0]["units"])==1 and
   int([z for z in group if z["kind"]=="operation_kind"][0]["subject"]) in (1,2,3) for group in ops.values())
  queue_trace_match=True
  for family in FAMILIES:
   code=FAMILY_CODES[family]
   for kind,suffix in (("deferred_queue_enqueue_items","enqueued_items"),("deferred_queue_drained_items","drained_items"),("deferred_queue_drain_batches","drain_batches")):
    queue_trace_match &= work_counts.get((kind,code),0)==int(c.get(f"deferred_queue:{family}:{suffix}",0))
  checks[pre+"_runtime_work_trace_zero_drops_values_and_markers"]=work_valid and marker_valid
  checks[pre+"_runtime_work_trace_queue_family_reconciliation"]=queue_trace_match
  writer_ids={int(z["rule_index"]) for z in a["writers"]}
  for f in FAMILIES:
   metric=f"deferred_queue_enqueued:{f}";attributed={int(i):int(count) for i,name,count in a["per_rule"] if name==metric and int(i) in writer_ids}
   expected_per_writer=1 if f=="rule_patches" else m
   checks[pre+f"_{f}_per_writer_enqueues"]=attributed=={i:expected_per_writer for i in writer_ids}
  checks[pre+"_trigger_deletions_exact"]=c.get("rule_effect_edge_deletes")==r
  work_by_kind={}
  for (kind,_subject),units in work_counts.items():work_by_kind[kind]=work_by_kind.get(kind,0)+units
  queue_trace={f:{kind:work_counts.get((kind,FAMILY_CODES[f]),0) for kind in ("deferred_queue_enqueue_items","deferred_queue_drained_items","deferred_queue_drain_batches")} for f in FAMILIES}
  rows.append({"rules":r,"multiplicity":m,"replicate":rep,"queue_items_expected_by_family":expected_by_family,"queue_items_observed":{f:c.get(f"deferred_queue:{f}:enqueued_items",0) for f in FAMILIES},"operation_count":len(ops),"work_units_by_kind":dict(sorted(work_by_kind.items())),"queue_work_trace_by_family":queue_trace,"candidate_pairs":c.get("cand_enum",0),"candidate_tests":c.get("cand_tested",0),"bindings_cloned":c.get("bindings_cloned",0),"scheduler_passes":c.get("scheduler_passes",0),"scheduler_plan_ns":c.get("scheduler_plan_ns",0)})
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"claim_boundary":"One authored positive two-edge join workload simultaneously queues all five deferred families and mutates/deletes its trigger. Operation-work units reconcile to independent family counters. The RulePatch family deduplicates a shared pending patch; four other families queue per successful binding. This is not natural-task frequency, scoped/fallback completeness, or a generalized complexity guarantee."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
