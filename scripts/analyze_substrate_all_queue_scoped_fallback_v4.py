#!/usr/bin/env python3
"""Validate unified five-family scoped/fallback semantics and work accounting."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/all_queue_scoped_fallback_v4_workers_20261001.json"
OUT=ROOT/"evaluation/reports/all_queue_scoped_fallback_v4_analysis_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/all_queue_scoped_fallback_v4_lock_20261001.json"
FAMILIES=("rule_edits","rule_patches","fb_samples","track_identity","net_collapses")
CODES={"rule_edits":1,"rule_patches":2,"fb_samples":3,"track_identity":4,"net_collapses":5}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def counts(phase):return phase["audit"]["counters"]
def trace_counts(phase):
 out={}
 for row in phase["audit"]["runtime_work_trace"]["rows"]:
  key=(row["kind"],row["subject"]);out[key]=out.get(key,0)+row["units"]
 return out
def selected_follows_last_handled_edge(arm):
 handled=[e for e in arm["graph"]["edges"] if e["type"]=="handled_mid"]
 selected=arm.get("selected_mid")
 return bool(handled) and isinstance(selected,dict) and int(selected.get("__nid__",-1))==int(handled[-1]["tgt"])
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(r,m,p) for r in (1,8,32) for m in (1,4,16) for p in range(3)}
 checks={"27_worker_factorial":len(runs)==27 and {(x["rules"],x["multiplicity"],x["replicate"]) for x in runs}==expected,"fresh_processes":len({x["pid"] for x in runs})==27,"stable_source_native_inputs":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["before"]==lock==x["after"] for x in runs)}
 rows=[]
 for x in runs:
  r,m,p=x["rules"],x["multiplicity"],x["replicate"];arms=x["arms"];full=arms["full"];scoped=arms["scoped_only"];fallback=arms["scoped_fallback"];key=f"r{r}_m{m}_rep{p}";items=r*m
  checks[key+"_full_and_fallback_graph_parity"]=full["graph"]==fallback["graph"]
  checks[key+"_full_selection_tracks_handled_insertion_order"]=selected_follows_last_handled_edge(full)
  checks[key+"_fallback_selection_tracks_handled_insertion_order"]=selected_follows_last_handled_edge(fallback)
  checks[key+"_full_fixed_point_and_expected_mutations"]=full["phases"]["full"]["report"]["status"]=="fixed_point" and full["seen_edges"]==r and full["handled_mid_edges"]==items and full["verified_edges"]==items and full["grid_cells"]==4*r and full["trigger_edges"]==0
  sr=scoped["phases"]["scoped"]["report"]
  checks[key+"_scoped_only_reports_pending_and_not_settled"]=sr["deferred_effects_pending"] and scoped["seen_edges"]==0 and scoped["handled_mid_edges"]==items and scoped["verified_edges"]==items and scoped["trigger_edges"]==0
  sp=fallback["phases"]["scoped"];fp=fallback["phases"]["fallback"]
  checks[key+"_fallback_fixed_point_and_expected_mutations"]=fp["report"]["status"]=="fixed_point" and fallback["seen_edges"]==r and fallback["handled_mid_edges"]==items and fallback["verified_edges"]==items and fallback["grid_cells"]==4*r and fallback["trigger_edges"]==0
  # At scoped closure the effects are queued but not drained. The fallback phase drains those exact pending items.
  fullc=counts(full["phases"]["full"]);sc=counts(scoped["phases"]["scoped"]);sfc=counts(sp);fc=counts(fp)
  enq={f:(r if f=="rule_patches" else items) for f in FAMILIES}
  checks[key+"_scoped_enqueues_all_five_families_without_drain"]=all(sc.get(f"deferred_queue:{f}:enqueued_items")==enq[f] and sc.get(f"deferred_queue:{f}:drained_items",0)==0 for f in FAMILIES)
  checks[key+"_fallback_phase_drains_pending_families"]=all(fc.get(f"deferred_queue:{f}:drained_items")==enq[f] for f in FAMILIES)
  checks[key+"_cumulative_queue_totals_match_direct_closure"]=all(sfc.get(f"deferred_queue:{f}:enqueued_items",0)+fc.get(f"deferred_queue:{f}:enqueued_items",0)==fullc.get(f"deferred_queue:{f}:enqueued_items",0) and sfc.get(f"deferred_queue:{f}:drained_items",0)+fc.get(f"deferred_queue:{f}:drained_items",0)==fullc.get(f"deferred_queue:{f}:drained_items",0) for f in FAMILIES)
  phase_work={}
  for name,obj in (("full",full["phases"]["full"]),("scoped_only",scoped["phases"]["scoped"]),("scoped_fallback_scoped",sp),("scoped_fallback_global",fp)):
   tc=trace_counts(obj);ctr=counts(obj);trace=obj["audit"]["runtime_work_trace"]
   valid=trace["dropped"]==0
   for fam,code in CODES.items():
    for kind,suffix in (("deferred_queue_enqueue_items","enqueued_items"),("deferred_queue_drained_items","drained_items"),("deferred_queue_drain_batches","drain_batches")):
     valid &= tc.get((kind,code),0)==int(ctr.get(f"deferred_queue:{fam}:{suffix}",0))
   checks[key+"_"+name+"_trace_reconciles"]=bool(valid)
   phase_work[name]={"candidate_tests":ctr.get("cand_tested",0),"queue_items_enqueued":{f:int(ctr.get(f"deferred_queue:{f}:enqueued_items",0)) for f in FAMILIES},"queue_items_drained":{f:int(ctr.get(f"deferred_queue:{f}:drained_items",0)) for f in FAMILIES},"queue_trace_rows":len(trace["rows"])}
  rows.append({"rules":r,"multiplicity":m,"replicate":p,"selected_mid_full":full.get("selected_mid"),"selected_mid_scoped_fallback":fallback.get("selected_mid"),"selected_mid_equal":full.get("selected_mid")==fallback.get("selected_mid"),"selected_tracks_each_arm_order":selected_follows_last_handled_edge(full) and selected_follows_last_handled_edge(fallback),"queue_items_expected":enq,"phase_work":phase_work})
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"claim_boundary":"Tests whether direct matcher enumeration of the first handled_mid clause makes insertion order observably affect a one-shot shared-sink last-match continuation. Exact graph-wire parity remains a separate gate. Scoped-only is explicitly pending. No general scope-completeness, natural-task, or asymptotic claim."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
