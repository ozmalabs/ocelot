#!/usr/bin/env python3
"""Corrected independent analysis for held-topic interface/access capture."""
from __future__ import annotations
import collections,gzip,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
import os
if os.environ.get("SUBSTRATE_NATIVE_PACKAGE"):sys.path.insert(0,str(Path(os.environ["SUBSTRATE_NATIVE_PACKAGE"]).resolve().parent))
STEM="held_topic_runtime_interface_trace_v1_8_20261001"
CAP=ROOT/f"evaluation/reports/{STEM}/capture.json.gz";LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json";OUT=ROOT/f"evaluation/reports/{STEM}/analysis_v2_0.json"
def sha(p):return "sha256:"+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location("held_interface_trace_runner_v1_8",ROOT/"scripts/substrate_held_topic_runtime_interface_trace_v1_8.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def load_base():
 spec=importlib.util.spec_from_file_location("held_topic_task_base_v1_1",ROOT/"scripts/substrate_live_held_topic_evidence_v1_6.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def expected_roles(event,owned,external):
 roles=set()
 for n in (event["node"],event["peer"]):
  if n in owned:roles.add("owned")
  elif n in external:roles.add("boundary_external")
  elif n is not None:roles.add("outside_cut")
 return sorted(roles or {"global_or_node_free"})
def summarize_operation_work(turn):
 trace=turn["runtime_operation_work_trace"];rows=trace["rows"]
 by_kind=collections.Counter();by_scope=collections.defaultdict(collections.Counter);ops=collections.defaultdict(list);queues=collections.Counter();valid=True
 for row in rows:
  scope=int(row["scope"]);op=int(row["operation_id"]);kind=str(row["kind"]);units=int(row["units"])
  valid &= scope>0 and op>0 and units>0
  by_kind[kind]+=units;by_scope[scope][kind]+=units;ops[(scope,op)].append(row)
  if kind in {"deferred_queue_enqueue_items","deferred_queue_drain_batches","deferred_queue_drained_items"} and row["subject"] is not None:
   queues[(kind,int(row["subject"]))]+=units
 operation_kinds={1:"run_rules",2:"apply_rule_once",3:"apply_rule_batch"};markers_ok=True;by_op_kind=collections.Counter()
 for key,group in ops.items():
  markers=[r for r in group if r["kind"]=="operation_kind"]
  markers_ok &= len(markers)==1 and int(markers[0]["units"])==1 and int(markers[0]["subject"]) in operation_kinds
  if markers:by_op_kind[operation_kinds.get(int(markers[0]["subject"]),"unknown")]+=1
 gate=int(trace["dropped"])==0 and bool(rows) and valid and markers_ok
 return {"integrity_pass":gate,"dropped_zero":int(trace["dropped"])==0,"rows_nonempty":bool(rows),"row_values_valid":bool(valid),
  "one_supported_operation_marker_per_operation":bool(markers_ok),"row_count":len(rows),"operation_count":len(ops),
  "scope_count":len(by_scope),"operation_count_by_kind":dict(sorted(by_op_kind.items())),
  "work_units_by_kind":dict(sorted(by_kind.items())),
  "deferred_work_by_kind_and_family_code":[{"kind":k[0],"family_code":k[1],"units":v} for k,v in sorted(queues.items())],
  "work_units_by_scope_and_kind":{str(s):dict(sorted(c.items())) for s,c in sorted(by_scope.items())}}
def check_turn(turn):
 frame=turn["task_frame"];owned=set(map(int,frame["node_ids"]))
 boundary=[(int(e[0]),str(e[1]),int(e[2])) for e in frame["boundary_edges"]]
 external={t if s in owned else s for s,_,t in boundary}
 internal=[(int(e[0]),str(e[1]),int(e[2])) for e in frame["internal_edges"]]
 records=frame["interface_nodes"]
 node_ok=all(str(n) in records for n in owned|external) and all(records[str(n)]["role"]==("owned" if n in owned else "boundary_external") for n in owned|external)
 schema=collections.Counter(k for row in records.values() if row["role"]=="owned" for k in row["attribute_schema"])
 schema_x=collections.Counter(k for row in records.values() if row["role"]=="boundary_external" for k in row["attribute_schema"])
 schema_ok=dict(sorted(schema.items()))==frame["attribute_names_by_role"]["owned"] and dict(sorted(schema_x.items()))==frame["attribute_names_by_role"]["boundary_external"]
 edge_ok=all(s in owned and t in owned for s,_,t in internal) and all((s in owned)!=(t in owned) for s,_,t in boundary)
 tr=turn["runtime_dependency_trace"];events=tr["events"]
 roles_ok=all(e["scope_roles"]==expected_roles(e,owned,external) for e in events)
 by_kind=collections.Counter();by_scope=collections.defaultdict(collections.Counter);by_resource=collections.defaultdict(collections.Counter);touched=collections.defaultdict(set)
 for e in events:
  by_kind[e["kind"]]+=e["count"]
  for role in e["scope_roles"]:
   by_scope[role][e["kind"]]+=e["count"]
   if e["resource"] is not None:by_resource[role][e["resource"]]+=e["count"]
   for n in (e["node"],e["peer"]):
    if n is not None:touched[role].add(n)
 agg=(dict(sorted(by_kind.items()))==tr["access_counts_by_kind"] and
  {r:dict(sorted(v.items())) for r,v in sorted(by_scope.items())}==tr["access_counts_by_scope_and_kind"] and
  {r:dict(sorted(v.items())) for r,v in sorted(by_resource.items())}==tr["resource_counts_by_scope"] and
  {r:len(v) for r,v in sorted(touched.items())}==tr["touched_node_count_by_scope"] and sum(by_kind.values())==tr["event_count"])
 mapped=not tr["unmapped_rule_uids"] and all(str(e["rule_uid"]) in tr["static_access_by_observed_rule"] for e in events)
 trace_ok=tr["dropped"]==0 and roles_ok and agg and mapped
 work=summarize_operation_work(turn)
 return {"integrity_pass":node_ok and schema_ok and edge_ok and trace_ok and work["integrity_pass"],
  "interface_nodes_resolve":node_ok,"attribute_schema_reconciles":schema_ok,"edge_partition_valid":edge_ok,
  "trace_dropped_zero":tr["dropped"]==0,"event_roles_reconcile":roles_ok,"trace_aggregates_reconcile":agg,
  "observed_rules_mapped_to_static_access":mapped,"owned_nodes":len(owned),"external_boundary_nodes":len(external),
  "boundary_incidences":len(boundary),"trace_event_count":tr["event_count"],"trace_row_count":len(events),
  "inside_or_boundary_accesses":sum(v for role,c in tr["access_counts_by_scope_and_kind"].items() if role in ("owned","boundary_external") for v in c.values()),
  "outside_direct_cut_accesses":sum(tr["access_counts_by_scope_and_kind"].get("outside_cut",{}).values()),
  "access_counts_by_kind":tr["access_counts_by_kind"],"access_counts_by_scope_and_kind":tr["access_counts_by_scope_and_kind"],
  "operation_work_trace_integrity_pass":work["integrity_pass"],"operation_work_trace":work}
def task_quality(turn,base):
 topic=turn["expected_topic"];dispatch=(turn["comprehension"] or {}).get("dispatch",{});goals=turn["goals"]
 if topic not in {"unobtainium","localhitium"}:
  held=turn["held_answers"];goal_ok=len(turn["answer_topic_goal_ids"])==1 and len(goals)==1 and goals[0]["attrs"].get("concept")==topic
  receipt=any(r["attrs"].get("status")=="released" and r["attrs"].get("surface")==turn["reply"] and any(i in r["released_ids"] for i in turn["answer_topic_goal_ids"]+turn["held_answer_ids"]) for r in turn["receipts"])
  ok=(turn["reply"]==base.FACTS[topic] and len(held)==1 and held[0]["attrs"].get("text")==base.FACTS[topic] and held[0]["attrs"].get("grounding_status")=="supported" and len(turn["evidence"])>=1 and goal_ok and receipt and dispatch.get("path")==turn["expected_path"])
 elif topic=="unobtainium":
  ok=len(turn["answer_topic_goal_ids"])==1 and bool(turn["grounder_calls"]) and turn["grounder_calls"][0]["phrase"].lower()=="unobtainium" and goals[0]["attrs"].get("outcome")=="unresolved" and "unobtainium" in turn["reply"].lower() and dispatch.get("path")==turn["expected_path"]
 else:
  ok=turn["reply"]==base.LOCAL_HIT_ANSWER and len(turn["held_answers"])==1 and turn["held_answers"][0]["attrs"].get("grounding_status")=="supported" and goals[0]["attrs"].get("outcome")=="resolved" and dispatch.get("path")==turn["expected_path"]
 return bool(ok)
def repeat_signature(worker):
 r=worker["payload"]
 turns=[]
 for t in r["turns"]:
  frame=json.loads(json.dumps(t["task_frame"]))
  for node in frame.get("interface_nodes",{}).values():node.pop("attribute_value_hashes",None)
  work_rows=collections.Counter((int(row["operation_id"]),int(row["producer_rule_uid"]),str(row["kind"]),row["subject"],int(row["units"])) for row in t["runtime_operation_work_trace"]["rows"])
  turns.append({"prompt":t["prompt"],"reply":t["reply"],"message":t["message"],"comprehension":t["comprehension"],
   "goals":t["goals"],"evidence":t["evidence"],"receipts":t["receipts"],"task_frame":frame,
   "trace":t["runtime_dependency_trace"],"operation_work_trace":{"dropped":t["runtime_operation_work_trace"]["dropped"],
    "operation_rows":[[*key,count] for key,count in sorted(work_rows.items(),key=lambda x:str(x[0]))]}})
 return json.dumps({"final_graph":r["final_graph"],"turns":turns},sort_keys=True)

def whole_worker_work(worker):
 r=worker["payload"];trace=r.get("worker_operation_work_trace",{});rows=trace.get("rows",[])
 def key(row,with_scope=True):
  core=(int(row["operation_id"]),int(row["producer_rule_uid"]),str(row["kind"]),row.get("subject"))
  return ((int(row["scope"]),)+core) if with_scope else core
 total=collections.Counter({key(row):int(row["units"]) for row in rows})
 segments=collections.Counter()
 for segment in trace.get("segments",[]):
  for field in ("pre_turn_rows","during_turn_rows"):
   for row in segment[field]:segments[key(row)]+=int(row["units"])
 for row in trace.get("post_worker_rows",[]):segments[key(row)]+=int(row["units"])
 by_family=collections.Counter();work=collections.Counter();signature=collections.Counter()
 for row in rows:
  kind=str(row["kind"]);units=int(row["units"]);work[kind]+=units
  signature[key(row,False)]+=units
  if kind in {"deferred_queue_enqueue_items","deferred_queue_drained_items"} and row.get("subject") is not None:
   by_family[(kind,int(row["subject"]))]+=units
 families=sorted({family for _,family in by_family})
 reconcile=[{"family_code":family,"enqueued":by_family[("deferred_queue_enqueue_items",family)],
  "drained":by_family[("deferred_queue_drained_items",family)],
  "balanced":by_family[("deferred_queue_enqueue_items",family)]==by_family[("deferred_queue_drained_items",family)]} for family in families]
 return {"integrity_pass":int(trace.get("dropped",-1))==0 and total==segments,
  "dropped_zero":int(trace.get("dropped",-1))==0,"worker_rows_equal_segment_sum":total==segments,
  "worker_row_count":len(rows),"work_units_by_kind":dict(sorted(work.items())),
  "deferred_queue_items_by_family":reconcile,
  "all_observed_queue_families_balanced":all(row["balanced"] for row in reconcile),
  "operation_signature_ignoring_scope":[[*k,int(v)] for k,v in sorted(signature.items(),key=lambda x:str(x[0]))]}
def attribute_hash_differences(workers):
 out=[]
 for turn_index in range(7):
  reference=workers[0]["payload"]["turns"][turn_index]["task_frame"]["interface_nodes"]
  changed=[]
  for other in workers[1:]:
   nodes=other["payload"]["turns"][turn_index]["task_frame"]["interface_nodes"]
   for node_id,row in reference.items():
    for key,value in row["attribute_value_hashes"].items():
     if value!=nodes.get(node_id,{}).get("attribute_value_hashes",{}).get(key):
      changed.append({"replicate":other["payload"]["replicate"],"node_id":node_id,"node_type":row["type"],"attribute":key})
  out.append({"prompt":workers[0]["payload"]["turns"][turn_index]["prompt"],"changed_value_hashes":changed})
 return out
def access_coverage(workers):
 mapping={"term_attr_read":("read","attr:"),"effect_attr_compare_read":("read","attr:"),
  "term_type_read":("read","type:"),"effect_type_candidate_read":("read","type:"),"effect_type_query":("read","type:"),
  "term_edge_read":("term_edge_read","edge:"),"pattern_edge":("read","edge:"),"effect_edge_compare_read":("read","edge:"),
  "term_edge_attr_read":("read","attr:"),"jit_attr_read":("read","attr:"),"jit_type_read":("read","type:"),
  "term_index_scan_candidate":("read","type:"),"term_index_result_candidate":("read","type:"),
  "term_index_query_indexed":("read","attr:"),"term_index_query_fallback":("read","attr:"),
  "term_typed_population_query":("read_wildcard","type:"),"term_typed_population_candidate":("read_wildcard","type:"),
  "effect_attr_write":("write","attr:"),"effect_edge_upsert":("write","edge:"),"effect_edge_delete":("write","edge:"),"effect_node_mint":("write","type:")}
 mapping["effect_node_delete"]=("write",None);mapping["effect_replace_edge"]=("write",None)
 counts=collections.Counter();by_kind=collections.defaultdict(collections.Counter);unmapped=collections.Counter();missing_static=0
 for w in workers:
  for turn in w["payload"]["turns"]:
   trace=turn["runtime_dependency_trace"]
   for e in trace["events"]:
    kind=e["kind"]
    if kind not in mapping:
     unmapped[kind]+=e["count"];continue
    mode,prefix=mapping[kind];resource=e["resource"]
    row=trace["static_access_by_observed_rule"].get(str(e["rule_uid"]))
    if row is None:missing_static+=e["count"];counts["uncovered"]+=e["count"];by_kind[kind]["uncovered"]+=e["count"];continue
    key=(prefix+resource) if prefix is not None and resource is not None else None
    if mode=="write":explicit=key in row["writes"] if key else False;wildcard=row["writes_any"]
    elif mode=="term_edge_read":explicit=key in row["reads"] or key in row["term_edge_reads"] if key else False;wildcard=row["reads_any"]
    elif mode=="read_wildcard":explicit=False;wildcard=row["reads_any"]
    else:explicit=key in row["reads"] if key else False;wildcard=row["reads_any"]
    category="explicit" if explicit else ("wildcard" if wildcard else "uncovered")
    counts[category]+=e["count"];by_kind[kind][category]+=e["count"]
 return {"counts":dict(sorted(counts.items())),"by_event_kind":{k:dict(sorted(v.items())) for k,v in sorted(by_kind.items())},
  "unmapped_event_kind_counts":dict(sorted(unmapped.items())),"missing_static_rows_or_resources":missing_static,
  "mapped_events_total":sum(counts.values()),"scope":"observed runtime events only; wildcard coverage is conservative and does not establish frame locality"}
def index_query_analysis(workers):
 tally=collections.Counter();by_query=collections.Counter();scan_units=collections.Counter();result_units=collections.Counter()
 typed_queries=collections.Counter();typed_candidates=collections.Counter()
 for w in workers:
  for turn in w["payload"]["turns"]:
   tr=turn["runtime_dependency_trace"]
   for e in tr["events"]:
    if e["kind"] in {"term_index_query_indexed","term_index_query_fallback"}:
     row=tr["static_access_by_observed_rule"].get(str(e["rule_uid"]),{})
     attr="attr:"+(e["resource"] or "")
     typ="type:"+(e.get("peer_resource") or "")
     explicit_attr=attr in row.get("reads",[]);explicit_type=typ in row.get("reads",[])
     coverage="explicit" if explicit_attr and explicit_type else ("wildcard" if row.get("reads_any",False) else "uncovered")
     mode="indexed" if e["kind"]=="term_index_query_indexed" else "fallback_scan"
     tally[coverage]+=e["count"];by_query[(e.get("peer_resource"),e["resource"],mode,coverage)]+=e["count"]
    elif e["kind"]=="term_index_scan_candidate":scan_units[e.get("resource")]+=e["count"]
    elif e["kind"]=="term_index_result_candidate":result_units[e.get("resource")]+=e["count"]
    elif e["kind"]=="term_typed_population_query":typed_queries[(e["rule_name"],e.get("resource"))]+=e["count"]
    elif e["kind"]=="term_typed_population_candidate":typed_candidates[e.get("resource")]+=e["count"]
 return {"query_count_by_coverage":dict(sorted(tally.items())),"queries_by_type_attribute_mode_and_coverage":[
   {"node_type":k[0],"attribute":k[1],"mode":k[2],"coverage":k[3],"query_count":v} for k,v in sorted(by_query.items(),key=lambda x:str(x[0]))],
  "fallback_candidate_scan_units_by_type":dict(sorted(scan_units.items())),"result_candidates_by_type":dict(sorted(result_units.items())),
  "typed_population_fingerprint_queries_by_rule_and_type":[{"rule_name":k[0],"node_type":k[1],"query_count":v} for k,v in sorted(typed_queries.items())],
  "typed_population_fingerprint_candidate_visits_by_type":dict(sorted(typed_candidates.items())),
  "indexed_lookup_internal_work":"not instrumented; result-candidate counts measure output enumeration only",
  "scope":"each query requires both attr and type keys explicitly, or is conservative only when reads_any is declared"}
def main():
 runner=load_runner();base=load_base();lock=json.loads(LOCK.read_text());capture=json.loads(gzip.decompress(CAP.read_bytes()));workers=capture["workers"]
 source=runner.lock_payload()==lock
 pids={w["payload"]["pid"] for w in workers};fresh=len(workers)==3 and len(pids)==3
 turn_rows=[]
 for w in workers:
  r=w["payload"]
  for t in r["turns"]:
   turn_rows.append({"replicate":r["replicate"],"prompt":t["prompt"],**check_turn(t),"task_quality_pass":task_quality(t,base)})
 coverage=len(turn_rows)==21 and all(sum(x["replicate"]==i for x in turn_rows)==7 for i in range(3))
 worker_sources=all(w["payload"]["worker_started_inputs"]==lock["base_inputs"]==w["payload"]["worker_finished_inputs"] for w in workers)
 signatures=[repeat_signature(w) for w in workers]
 stable=len(set(signatures))==1
 whole=[whole_worker_work(w) for w in workers]
 whole_stable=len({json.dumps(x["operation_signature_ignoring_scope"],sort_keys=True) for x in whole})==1
 whole_integrity=all(x["integrity_pass"] for x in whole)
 queues_balanced=all(x["all_observed_queue_families_balanced"] for x in whole)
 scope_counts_by_turn=[{"prompt":workers[0]["payload"]["turns"][i]["prompt"],"counts_by_replicate":[
  len({r["scope"] for r in w["payload"]["turns"][i]["runtime_operation_work_trace"]["rows"]}) for w in workers]} for i in range(7)]
 interfaces=all(x["integrity_pass"] for x in turn_rows)
 operation_work_integrity=all(x["operation_work_trace_integrity_pass"] for x in turn_rows)
 quality=all(x["task_quality_pass"] for x in turn_rows)
 coverage_report=access_coverage(workers);index_report=index_query_analysis(workers)
 aggregate_work=collections.Counter()
 for x in turn_rows:aggregate_work.update(x["operation_work_trace"]["work_units_by_kind"])
 result={"schema":"HeldTopicRuntimeInterfaceTraceAnalysisV2_0","source_capture_lock_sha256":sha(LOCK),
  "analysis_amendment_sha256":sha(ROOT/"docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_RUNTIME_INTERFACE_TRACE_V1_6_ANALYSIS_AMENDMENT_20261001.md"),
  "capture_sha256":sha(CAP),"capture_integrity_pass":source and fresh and coverage and worker_sources and stable and interfaces and operation_work_integrity and whole_stable and whole_integrity,
  "task_quality_pass":quality,"all_claim_gates_pass":source and fresh and coverage and worker_sources and stable and interfaces and operation_work_integrity and whole_stable and whole_integrity and queues_balanced and quality,
  "gates":{"locked_runtime_sources_current":source,"three_fresh_workers":fresh,"seven_turns_per_worker":coverage,
   "worker_source_stability":worker_sources,"runtime_graph_interface_and_trace_repeat":stable,"interface_and_trace_invariants":interfaces,
   "all_scope_operation_work_trace_invariants":operation_work_integrity,"whole_worker_trace_segments_reconcile":whole_integrity,
   "whole_worker_operation_work_repeats":whole_stable,"deferred_queue_items_balance_by_family":queues_balanced,
   "frozen_task_quality_oracles":quality},"turns":turn_rows,
  "attribute_value_repeat_differences":attribute_hash_differences(workers),"observed_static_dynamic_access_coverage":coverage_report,
  "type_index_query_analysis":index_report,"operation_work_units_by_kind_all_workers_turns":dict(sorted(aggregate_work.items())),
  "whole_worker_operation_work":whole,
  "raw_scope_pointer_counts_by_turn":scope_counts_by_turn}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(OUT.relative_to(ROOT)),"capture_integrity_pass":result["capture_integrity_pass"],
  "task_quality_pass":quality,"gates":result["gates"]},indent=2))
 if not result["capture_integrity_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
