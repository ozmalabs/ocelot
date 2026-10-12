#!/usr/bin/env python3
"""Independent integrity and outcome analysis for the self-report frame sweep."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/live_self_report_dimension_frame_v1_workers_raw_20260927.json"
DRIVER=ROOT/"evaluation/reports/live_self_report_dimension_frame_v1_20260927.json"
LOCK=ROOT/"evaluation/substrate_capability/live_self_report_dimension_frame_v1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/live_self_report_dimension_frame_v1_analysis_20260927.json"
SIZES=(4,8,12,16,24)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def oxford(xs):
 if len(xs)==1:return xs[0]
 if len(xs)==2:return " and ".join(xs)
 return ", ".join(xs[:-1])+", and "+xs[-1]
def main():
 raw=json.loads(RAW.read_text());driver=json.loads(DRIVER.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 cells={(n,r):{x["arm"]:x for x in runs if x["size"]==n and x["replicate"]==r} for n in SIZES for r in range(2)}
 checks={"twenty_unique_workers":len(runs)==20 and len({x["pid"] for x in runs})==20,
  "complete_size_replicate_arm_factorial":all(set(c)=={"audited","untraced"} for c in cells.values()),
  "locked_sources_stable":raw["locked_inputs"]==locked and driver["locked_inputs"]==locked and driver["post_run_inputs"]==locked and all(x["worker_started_inputs"]==locked and x["worker_finished_inputs"]==locked for x in runs),
  "route_and_goal_lifecycle":all(x["route"]=="self_report" and x["goal_count"]==1 and x["goal"] and x["goal"]["status"]=="resolved" and x["goal"]["transition_kinds"]==["selection","execution","action_result"] and x["goal"]["closed"] and not x["goal"]["active"] for x in runs),
  "reflection_reads_full_frame":all(x["reflection_area_count"]==x["size"] and x["reflection_areas"]==x["expected_areas"] for x in runs),
  "surface_reports_first_twelve_only":all(x["surface_areas"] and x["surface_areas"]["source_areas"]==x["expected_areas"][:12] and x["surface_areas"]["delivered_areas"]==x["expected_areas"][:12] and x["reply"]=="I am organised into "+oxford(x["expected_areas"][:12]) for x in runs),
  "coverage_contract_exposed":all(len(x["surface_areas"]["delivered_areas"])==min(x["size"],12) for x in runs),
  "frame_nodes_edges_and_boundary_conserve":all(len(x["frame_node_ids"])==2*x["size"] and x["frame_area_count"]==x["frame_membership_count"]==x["size"] and x["frame_internal_edge_count"]==x["size"] and x["frame_boundary_incidence_count"]==x["size"] and x["frame_boundary_external_nodes"]==[x["frame_root_id"]] and x["frame_classified_edges"]==0 for x in runs),
  "audit_control_pair_parity":all(c["audited"]["reply"]==c["untraced"]["reply"] and c["audited"]["goal"]==c["untraced"]["goal"] and c["audited"]["semantic_graph_sha256"]==c["untraced"]["semantic_graph_sha256"] and (c["audited"]["graph_node_count"],c["audited"]["graph_edge_count"])==(c["untraced"]["graph_node_count"],c["untraced"]["graph_edge_count"]) for c in cells.values()),
  "base_graph_and_size_deltas_reconcile":len({(x["graph_node_count"]-2*x["size"],x["graph_edge_count"]-2*x["size"]) for x in runs})==1,
  "untraced_arms_have_no_audit":all(not x["scale"] and not x["per_rule"] and not x["per_clause"] and not x["metadata"] and not x["trace_rows"] and x["trace_event_count"]==0 for x in runs if x["arm"]=="untraced"),
  "audited_trace_has_no_drops":all(x["trace_dropped"]==0 and x["trace_event_count"]==sum(q["count"] for q in x["trace_rows"]) and x["trace_event_count"]>0 for x in runs if x["arm"]=="audited")}
 checks["concrete_frame_access_rows_reconcile"]=all(x["frame_direct_access_event_count"]==sum(q["count"] for q in x["frame_access_trace_rows"] if q["frame_node_ids"]) and x["agent_root_access_event_count"]==sum(q["count"] for q in x["frame_access_trace_rows"] if q["touches_agent_root"]) and all(q["frame_node_ids"]==sorted({i for i in (q["node"],q["peer"]) if i in x["frame_node_ids"]}) and bool(q["frame_roles"])==bool(q["frame_node_ids"]) and q["touches_agent_root"]==(x["frame_root_id"] in (q["node"],q["peer"])) for q in x["frame_access_trace_rows"]) for x in runs if x["arm"]=="audited")
 work=[];summaries=[]
 for x in runs:
  if x["arm"]!="audited":continue
  c=x["scale"];cand=int(c.get("cand_tested",0));cu=int(c.get("cand_tested_unattributed",0));terms=int(c.get("term_evals_total",0));tu=int(c.get("term_evals_unattributed",0))
  per={};clauses={};pt=0;missing=set();bad=[];meta={int(i):{"arity":int(a),"ambiguous":bool(b)} for i,s,n,a,b in x["metadata"]}
  for i,m,v in x["per_rule"]:
   i=int(i);v=int(v)
   if i not in meta:missing.add(i)
   if m=="candidate_tests":per[i]=per.get(i,0)+v
   if m=="term_evaluations":pt+=v
  for i,pos,v in x["per_clause"]:
   i=int(i);pos=int(pos)
   if i not in meta:missing.add(i)
   elif pos>=meta[i]["arity"]:bad.append([i,pos])
   else:clauses[i]=clauses.get(i,0)+int(v)
  ambiguous={i for i,m in meta.items() if m["ambiguous"]};amb_rows=[r for r in x["per_rule"] if int(r[0]) in ambiguous]
  term_kinds=sum(int(v) for k,v in c.items() if k.startswith("term_eval:"))
  work.append({"size":x["size"],"candidate":cand,"candidate_unattributed":cu,"candidate_rule_sum":sum(per.values()),"candidate_clause_sum":sum(clauses.values()),"terms":terms,"term_rule_sum":pt,"term_unattributed":tu,"term_kind_sum":term_kinds,"missing_ids":sorted(missing),"bad_clause_positions":bad,"ambiguous_rows":len(amb_rows),"trace_events":x["trace_event_count"],"nodes":x["graph_node_count"],"edges":x["graph_edge_count"],"wall_ns":x["request_wall_ns"],"cpu_ns":x["request_process_cpu_ns"],"rss":x["peak_rss_bytes"],"digest":x["semantic_graph_sha256"]})
 checks["counter_conservation"]=all(w["candidate"]==w["candidate_unattributed"]+w["candidate_rule_sum"]==w["candidate_unattributed"]+w["candidate_clause_sum"] and w["terms"]==w["term_rule_sum"]+w["term_unattributed"]==w["term_kind_sum"] for w in work)
 checks["metadata_attribution_valid"]=all(not w["missing_ids"] and not w["bad_clause_positions"] and w["ambiguous_rows"]==0 for w in work)
 checks["audited_work_and_graph_repeat"]=all(len({tuple(w[k] for k in ("candidate","candidate_unattributed","candidate_rule_sum","candidate_clause_sum","terms","term_rule_sum","term_unattributed","term_kind_sum","trace_events","nodes","edges","digest")) for w in work if w["size"]==n})==1 for n in SIZES)
 for n in SIZES:
  ws=[w for w in work if w["size"]==n];rs=[x for x in runs if x["size"]==n]
  audited_rows=[y for y in rs if y["arm"]=="audited"]
  summaries.append({"dimensions":n,"reported_dimensions":min(n,12),"coverage_fraction":min(n,12)/n,"candidate_tests":ws[0]["candidate"],"term_evaluations":ws[0]["terms"],"access_events":ws[0]["trace_events"],"frame_nodes":2*n,"frame_internal_edges":n,"frame_boundary_incidences":n,"frame_direct_access_events":audited_rows[0]["frame_direct_access_event_count"],"agent_root_access_events":audited_rows[0]["agent_root_access_event_count"],"frame_access_trace_rows":len(audited_rows[0]["frame_access_trace_rows"]),"wall_median_ms_by_arm":{a:statistics.median(y["request_wall_ns"] for y in rs if y["arm"]==a)/1e6 for a in ("untraced","audited")},"cpu_median_ms_by_arm":{a:statistics.median(y["request_process_cpu_ns"] for y in rs if y["arm"]==a)/1e6 for a in ("untraced","audited")},"rss_median_gib_by_arm":{a:statistics.median(y["peak_rss_bytes"] for y in rs if y["arm"]==a)/1073741824 for a in ("untraced","audited")},"graph_nodes":ws[0]["nodes"],"graph_edges":ws[0]["edges"],"reply":rs[0]["reply"]})
 payload={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"all_checks_pass":all(checks.values()),"summary_by_size":summaries,"audited_work_profiles":work,"claim_boundary":"This controlled live self-report experiment expands the Agent's cached organization inventory and adds explicit has-area/has-concept frame-probe structure. The task-relevant output is checked exactly, including the observed 12-area surface cap. The frame boundary is injected by the harness, not learned by the substrate. Results do not establish naturally learned cheap cuts, natural-task frequency, asymptotic complexity, or general self-model correctness."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"all_checks_pass":payload["all_checks_pass"],"summary_by_size":summaries},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("dimension-frame analysis failed")
if __name__=="__main__":main()
