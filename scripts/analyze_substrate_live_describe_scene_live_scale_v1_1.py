#!/usr/bin/env python3
"""Independent analysis of live full-rule Concept-membership scaling."""
from __future__ import annotations
from collections import Counter
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/live_describe_scene_live_scale_v1_workers_raw_20260927.json"
DRIVER=ROOT/"evaluation/reports/live_describe_scene_live_scale_v1_20260927.json"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_live_scale_v1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/live_describe_scene_live_scale_v1_1_analysis_20260927.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());driver=json.loads(DRIVER.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 groups={(size,rep):{r["arm"]:r for r in runs if r["size"]==size and r["replicate"]==rep} for size in (0,1024,4096) for rep in range(2)}
 checks={"twelve_unique_workers":len(runs)==12 and len({r["pid"] for r in runs})==12,
  "complete_factorial":all(set(g)=={"audited","untraced"} for g in groups.values()),
  "source_stable":raw["locked_inputs"]==locked and driver["locked_inputs"]==locked and driver["post_run_inputs"]==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
  "expected_reply_and_lifecycle_all_cells":all(r["reply_matches_expected"] and r["route"]=="describe_scene" and r["goal_count"]==1 and r["goal"] is not None and r["goal"]["status"]=="resolved" and r["goal"]["transition_kinds"]==["selection","execution","action_result"] and r["goal"]["closed"] and not r["goal"]["active"] for r in runs),
  "audited_control_pair_parity":all(g["audited"]["reply"]==g["untraced"]["reply"] and g["audited"]["goal"]==g["untraced"]["goal"] and g["audited"]["semantic_graph_sha256"]==g["untraced"]["semantic_graph_sha256"] and (g["audited"]["graph_node_count"],g["audited"]["graph_edge_count"])==(g["untraced"]["graph_node_count"],g["untraced"]["graph_edge_count"]) for g in groups.values()),
  "three_percepts_and_noise_semantics":all(r["scene_percepts"]==3 and r["noise_concept_count"]==r["noise_membership_count"]==r["size"] and r["noise_classified_edges"]==0 and r["reply_matches_expected"] for r in runs),
  "base_graph_constant_and_size_deltas":len({(r["base_concepts_before_noise"],r["base_memberships_before_noise"]) for r in runs})==1 and all(r["graph_node_count"]-r["size"]==next(x["graph_node_count"] for x in runs if x["size"]==0 and x["arm"]==r["arm"] and x["replicate"]==r["replicate"]) for r in runs),
  "untraced_arms_have_zero_audit":all(not r["scale"] and not r["per_rule"] and not r["per_clause"] and not r["metadata"] and not r["trace_rows"] and r["trace_event_count"]==0 for r in runs if r["arm"]=="untraced"),
  "audited_trace_conserves_with_zero_drops":all(r["trace_dropped"]==0 and r["trace_event_count"]==sum(x["count"] for x in r["trace_rows"]) and r["trace_event_count"]>0 for r in runs if r["arm"]=="audited")}
 audited=[];work_profiles=[]
 for r in runs:
  if r["arm"]!="audited":continue
  c=r["scale"];cand=int(c.get("cand_tested",0));cand_un=int(c.get("cand_tested_unattributed",0));terms=int(c.get("term_evals_total",0));terms_un=int(c.get("term_evals_unattributed",0))
  meta={int(i):{"name":name,"arity":int(arity),"ambiguous":bool(amb)} for i,sym,name,arity,amb in r["metadata"]}
  per=Counter();per_term=0;clauses=Counter();missing=set();bad=[]
  for i,m,v in r["per_rule"]:
   i=int(i);v=int(v)
   if i not in meta:missing.add(i)
   if m=="candidate_tests":per[i]+=v
   elif m=="term_evaluations":per_term+=v
  for i,pos,v in r["per_clause"]:
   i=int(i);pos=int(pos);v=int(v)
   if i not in meta:missing.add(i)
   elif pos>=meta[i]["arity"]:bad.append((i,pos,v))
   else:clauses[i]+=v
  amb={i for i,m in meta.items() if m["ambiguous"]};amb_rows=[x for x in r["per_rule"] if int(x[0]) in amb]
  term_kinds=sum(int(v) for k,v in c.items() if k.startswith("term_eval:"))
  record={"size":r["size"],"replicate":r["replicate"],"candidate_tests":cand,"candidate_unattributed":cand_un,"candidate_attributed":sum(per.values()),"per_clause_candidates":sum(clauses.values()),"term_evaluations":terms,"per_rule_term_evaluations":per_term,"term_evaluations_unattributed":terms_un,"term_kind_evaluations":term_kinds,"ambiguous_rule_ids":sorted(amb),"ambiguous_rule_rows":len(amb_rows),"metadata_missing_ids":sorted(missing),"bad_clauses":bad,"trace_events":r["trace_event_count"],"trace_rows":len(r["trace_rows"]),"trace_dropped":r["trace_dropped"],"candidate_rule_count":len(per),"wall_ns":r["request_wall_ns"],"cpu_ns":r["request_process_cpu_ns"],"peak_rss_bytes":r["peak_rss_bytes"],"graph_nodes":r["graph_node_count"],"graph_edges":r["graph_edge_count"],"base_concepts":r["base_concepts_before_noise"],"base_memberships":r["base_memberships_before_noise"],"noise_classified_edges":r["noise_classified_edges"],"reply":r["reply"],"graph_digest":r["semantic_graph_sha256"],"outbound_message_alignment":r["outbound_message_alignment"]}
  audited.append(record)
  work_profiles.append((r["size"],cand,cand_un,sum(per.values()),sum(clauses.values()),terms,per_term,terms_un,term_kinds,r["trace_event_count"],len(per)))
 checks.update({"candidate_and_term_conservation":all(x[1]==x[2]+x[3] and x[3]==x[4] and x[5]==x[6]+x[7]==x[8] for x in work_profiles),
  "ambiguous_ids_have_no_attribution":all(x["ambiguous_rule_rows"]==0 and not x["bad_clauses"] and not x["metadata_missing_ids"] for x in audited),
  "audited_work_repeats_within_cell":all(len({json.dumps(x[1:],sort_keys=True) for x in work_profiles if x[0]==size})==1 for size in (0,1024,4096)),
  "exact_graph_repeats_within_cell":all(len({(x["graph_digest"],x["graph_nodes"],x["graph_edges"]) for x in audited if x["size"]==size})==1 for size in (0,1024,4096))})
 cells=[]
 for size in (0,1024,4096):
  xs=[x for x in audited if x["size"]==size]
  by_arm={arm:[r for r in runs if r["size"]==size and r["arm"]==arm] for arm in ("audited","untraced")}
  cells.append({"noise_concepts":size,"base_concepts":xs[0]["base_concepts"],"base_memberships":xs[0]["base_memberships"],"total_memberships":xs[0]["base_memberships"]+size,
   "candidate_tests":xs[0]["candidate_tests"],"candidate_attributed":xs[0]["candidate_attributed"],"candidate_unattributed":xs[0]["candidate_unattributed"],"term_evaluations":xs[0]["term_evaluations"],"term_attributed":xs[0]["per_rule_term_evaluations"],"term_unattributed":xs[0]["term_evaluations_unattributed"],"term_kinds":xs[0]["term_kind_evaluations"],"trace_events":xs[0]["trace_events"],"trace_rows":xs[0]["trace_rows"],"candidate_rule_count":xs[0]["candidate_rule_count"],"request_wall_ns_median_by_arm":{arm:statistics.median(r["request_wall_ns"] for r in rows) for arm,rows in by_arm.items()},"request_cpu_ns_median_by_arm":{arm:statistics.median(r["request_process_cpu_ns"] for r in rows) for arm,rows in by_arm.items()},"peak_rss_bytes_median_by_arm":{arm:statistics.median(r["peak_rss_bytes"] for r in rows) for arm,rows in by_arm.items()},"graph_nodes":xs[0]["graph_nodes"],"graph_edges":xs[0]["graph_edges"],"graph_digest":xs[0]["graph_digest"],"outbound_message_alignment":all(x["outbound_message_alignment"] for x in xs)})
 profile_by_size=[]
 for size in (0,1024,4096):
  x=next(r for r in runs if r["size"]==size and r["arm"]=="audited")
  cv=Counter();tv=Counter()
  for i,m,v in x["per_rule"]:
   if m=="candidate_tests":cv[int(i)]+=int(v)
   elif m=="term_evaluations":tv[int(i)]+=int(v)
  names={int(i):name for i,sym,name,arity,amb in x["metadata"]}
  profile_by_size.append({"size":size,"rules":[{"audit_id":i,"name":names.get(i),"candidate_tests":cv[i],"term_evaluations":tv[i]} for i in sorted(set(cv)|set(tv))]})
 payload={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"all_checks_pass":all(checks.values()),"summary_by_size":cells,"audited_worker_profiles":audited,"per_rule_work_by_size":profile_by_size,"claim_boundary":"Source-locked full-seed live describe_scene route, with all rules active, one fixed 3-Percept Scene, and synthetic noise Concepts in a dedicated Microtheory. This measures one graph-membership axis; it does not establish natural workload prevalence, learned frame locality, scaling in other dimensions, or general task capability."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"checks":checks,"all_checks_pass":payload["all_checks_pass"],"summary_by_size":cells},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("live full-rule scale analysis failed")
if __name__=="__main__":main()
