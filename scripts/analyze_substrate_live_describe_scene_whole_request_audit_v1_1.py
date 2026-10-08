#!/usr/bin/env python3
"""Independent analysis for the whole-request audit with explicit Term residue."""
from __future__ import annotations
from collections import Counter
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/live_describe_scene_whole_request_audit_v1_1_workers_raw_20260927.json"
DRIVER=ROOT/"evaluation/reports/live_describe_scene_whole_request_audit_v1_1_20260927.json"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_whole_request_audit_v1_1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/live_describe_scene_whole_request_audit_v1_1_analysis_20260927.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());driver=json.loads(DRIVER.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 pairs={i:{r["arm"]:r for r in runs if r["replicate"]==i} for i in range(3)}
 checks={"six_unique_workers":len(runs)==6 and len({r["pid"] for r in runs})==6,
  "three_complete_pairs":all(set(p)=={"audited","untraced"} for p in pairs.values()),
  "source_lock_stable":raw["locked_inputs"]==locked and driver["locked_inputs"]==locked and driver["post_run_inputs"]==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
  "all_replies_and_goal_lifecycles_valid":all(r["reply_matches_expected"] and r["route"]=="describe_scene" and r["goal_count"]==1 and r["goal"] is not None and r["goal"]["status"]=="resolved" and r["goal"]["transition_kinds"]==["selection","execution","action_result"] and r["goal"]["closed"] and not r["goal"]["active"] for r in runs),
  "paired_semantic_and_whole_graph_parity":all(p["audited"]["reply"]==p["untraced"]["reply"] and p["audited"]["goal"]==p["untraced"]["goal"] and p["audited"]["semantic_graph_sha256"]==p["untraced"]["semantic_graph_sha256"] and p["audited"]["graph_node_count"]==p["untraced"]["graph_node_count"] and p["audited"]["graph_edge_count"]==p["untraced"]["graph_edge_count"] for p in pairs.values()),
  "untraced_arm_has_zero_instrumentation":all(not r["scale"] and not r["per_rule"] and not r["trace_rows"] and r["trace_event_count"]==0 for r in runs if r["arm"]=="untraced"),
  "audited_trace_is_complete":all(r["trace_dropped"]==0 and r["trace_event_count"]==sum(x["count"] for x in r["trace_rows"]) and r["trace_event_count"]>0 for r in runs if r["arm"]=="audited")}
 profiles=[];intervals=[]
 for r in runs:
  if r["arm"]!="audited":continue
  c=r["scale"];global_n=int(c.get("cand_tested",0));unattr=int(c.get("cand_tested_unattributed",0));meta={int(i):{"name":n,"arity":int(a),"ambiguous":bool(b)} for i,s,n,a,b in r["metadata"]}
  per=Counter();clauses=Counter();term_per=0;missing=set();bad=[];amb_clause=[]
  for i,m,v in r["per_rule"]:
   i=int(i);v=int(v)
   if i not in meta:missing.add(i)
   if m=="candidate_tests":per[i]+=v
   if m=="term_evaluations":term_per+=v
  for i,pos,v in r["per_clause"]:
   i=int(i);pos=int(pos);v=int(v);info=meta.get(i)
   if info is None:missing.add(i)
   elif info["ambiguous"]:amb_clause.append((i,pos,v))
   elif pos>=info["arity"]:bad.append((i,pos,v))
   else:clauses[i]+=v
  ambiguous={i for i,v in meta.items() if v["ambiguous"]}
  ambiguous_rows=[row for row in r["per_rule"] if int(row[0]) in ambiguous]
  attributed=global_n-unattr;per_n=sum(per.values());clause_n=sum(clauses.values());term_total=int(c.get("term_evals_total",0));term_kinds=sum(int(v) for k,v in c.items() if k.startswith("term_eval:"));term_unattr=int(c.get("term_evals_unattributed",0))
  profile={"replicate":r["replicate"],"candidate_tests":global_n,"attributed_candidates":attributed,"unattributed_candidates":unattr,"per_rule_candidates":per_n,"per_clause_candidates":clause_n,"term_evaluations":term_total,"per_rule_term_evaluations":term_per,"term_evaluations_unattributed":term_unattr,"term_kind_evaluations":term_kinds,"ambiguous_rule_ids":sorted(ambiguous),"per_rule_rows_for_ambiguous_ids":len(ambiguous_rows),"trace_events":r["trace_event_count"],"trace_dropped":r["trace_dropped"],"candidate_rule_count":len(per),"trace_row_count":len(r["trace_rows"]),"semantic_digest":r["semantic_graph_sha256"],"graph_nodes":r["graph_node_count"],"graph_edges":r["graph_edge_count"],"wall_ns":r["request_wall_ns"],"process_cpu_ns":r["request_process_cpu_ns"],"public_reply_has_matching_outbound_message":r["outbound_matches_public_reply"],"metadata_missing_ids":sorted(missing),"bad_clauses":bad,"ambiguous_clause_rows":amb_clause}
  intervals.append(profile);profiles.append((global_n,attributed,unattr,per_n,clause_n,term_total,term_per,term_unattr,term_kinds,r["trace_event_count"]))
 checks.update({"candidate_conservation":all(x[0]==x[1]+x[2] and x[1]==x[3]==x[4] for x in profiles),
  "term_conservation_with_explicit_unattributed":all(x[5]==x[6]+x[7]==x[8] for x in profiles),
  "ambiguous_rule_rows_withdrawn":all(x["per_rule_rows_for_ambiguous_ids"]==0 and not x["ambiguous_clause_rows"] for x in intervals),
  "metadata_and_clause_validation":all(not x["metadata_missing_ids"] and not x["bad_clauses"] for x in intervals),
  "audited_work_repeats_exactly":len({json.dumps(x) for x in profiles})==1})
 by_arm={}
 for arm in ("audited","untraced"):
  rows=[r for r in runs if r["arm"]==arm]
  by_arm[arm]={"request_wall_ns_median":statistics.median(r["request_wall_ns"] for r in rows),"request_process_cpu_ns_median":statistics.median(r["request_process_cpu_ns"] for r in rows),"reply":rows[0]["reply"],"graph_nodes":rows[0]["graph_node_count"],"graph_edges":rows[0]["graph_edge_count"],"semantic_graph_digests":[r["semantic_graph_sha256"] for r in rows]}
 sample=next(r for r in runs if r["arm"]=="audited");cand=Counter();terms=Counter()
 for i,m,v in sample["per_rule"]:
  if m=="candidate_tests":cand[int(i)]+=int(v)
  elif m=="term_evaluations":terms[int(i)]+=int(v)
 by_rule=[{"audit_id":i,"name":next((x[2] for x in sample["metadata"] if int(x[0])==i),None),"candidate_tests":cand[i],"term_evaluations":terms[i]} for i in sorted(set(cand)|set(terms))]
 trace_kind=Counter();trace_resource=Counter()
 for row in sample["trace_rows"]:trace_kind[row["kind"]]+=row["count"];trace_resource[row["resource"] or "<none>"]+=row["count"]
 payload={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"all_checks_pass":all(checks.values()),"behavioral_observations":{"public_graph_output_alignment_passes":all(r["outbound_matches_public_reply"] for r in runs),"public_graph_output_alignment_failure_count":sum(not r["outbound_matches_public_reply"] for r in runs)},"by_arm":by_arm,"audited_replicates":intervals,"whole_request_work":{k:v for k,v in intervals[0].items() if k in ("candidate_tests","attributed_candidates","unattributed_candidates","per_rule_candidates","per_clause_candidates","term_evaluations","per_rule_term_evaluations","term_evaluations_unattributed","term_kind_evaluations","trace_events","trace_row_count","candidate_rule_count")},"per_rule_work":by_rule,"trace_event_counts_by_kind":dict(trace_kind),"trace_event_counts_by_resource":dict(trace_resource),"claim_boundary":"Complete native matcher and selected access audit for one serial full-seed describe_scene request on the rebuilt engine. Candidate and Term totals reconcile with explicit ambiguity/no-rule attribution. Exact paired parity is fixture-specific; access events are not candidate tests; this does not establish frame locality, natural-task prevalence, asymptotic scaling, or general capability."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"checks":checks,"all_checks_pass":payload["all_checks_pass"],"whole_request_work":payload["whole_request_work"],"by_arm":by_arm,"behavioral_observations":payload["behavioral_observations"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("whole-request audit v1.1 analysis failed")
if __name__=="__main__":main()
