#!/usr/bin/env python3
"""Corrected independent analysis for held-topic interface/access capture."""
from __future__ import annotations
import collections,gzip,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
STEM="held_topic_runtime_interface_trace_v1_1_20261001"
CAP=ROOT/f"evaluation/reports/{STEM}/capture.json.gz";LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json";OUT=ROOT/f"evaluation/reports/{STEM}/analysis_v1_2.json"
def sha(p):return "sha256:"+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location("held_interface_trace_runner_v1_1",ROOT/"scripts/substrate_held_topic_runtime_interface_trace_v1_1.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def load_base():
 spec=importlib.util.spec_from_file_location("held_topic_task_base_v1_1",ROOT/"scripts/substrate_live_held_topic_evidence_v1_6.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def expected_roles(event,owned,external):
 roles=set()
 for n in (event["node"],event["peer"]):
  if n in owned:roles.add("owned")
  elif n in external:roles.add("boundary_external")
  elif n is not None:roles.add("outside_cut")
 return sorted(roles or {"global_or_node_free"})
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
 return {"integrity_pass":node_ok and schema_ok and edge_ok and trace_ok,
  "interface_nodes_resolve":node_ok,"attribute_schema_reconciles":schema_ok,"edge_partition_valid":edge_ok,
  "trace_dropped_zero":tr["dropped"]==0,"event_roles_reconcile":roles_ok,"trace_aggregates_reconcile":agg,
  "observed_rules_mapped_to_static_access":mapped,"owned_nodes":len(owned),"external_boundary_nodes":len(external),
  "boundary_incidences":len(boundary),"trace_event_count":tr["event_count"],"trace_row_count":len(events),
  "inside_or_boundary_accesses":sum(v for role,c in tr["access_counts_by_scope_and_kind"].items() if role in ("owned","boundary_external") for v in c.values()),
  "outside_direct_cut_accesses":sum(tr["access_counts_by_scope_and_kind"].get("outside_cut",{}).values()),
  "access_counts_by_kind":tr["access_counts_by_kind"],"access_counts_by_scope_and_kind":tr["access_counts_by_scope_and_kind"]}
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
  turns.append({"prompt":t["prompt"],"reply":t["reply"],"message":t["message"],"comprehension":t["comprehension"],
   "goals":t["goals"],"evidence":t["evidence"],"receipts":t["receipts"],"task_frame":frame,
   "trace":t["runtime_dependency_trace"]})
 return json.dumps({"final_graph":r["final_graph"],"turns":turns},sort_keys=True)
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
  "term_edge_read":("term_edge_read","edge:"),"pattern_edge":("read","edge:"),
  "effect_attr_write":("write","attr:"),"effect_edge_upsert":("write","edge:"),"effect_edge_delete":("write","edge:"),"effect_node_mint":("write","type:")}
 counts=collections.Counter();by_kind=collections.defaultdict(collections.Counter);unmapped=collections.Counter();missing_static=0
 for w in workers:
  for turn in w["payload"]["turns"]:
   trace=turn["runtime_dependency_trace"]
   for e in trace["events"]:
    kind=e["kind"]
    if kind not in mapping:
     unmapped[kind]+=e["count"];continue
    mode,prefix=mapping[kind];resource=e["resource"]
    if resource is None:missing_static+=e["count"];counts["uncovered"]+=e["count"];by_kind[kind]["uncovered"]+=e["count"];continue
    key=prefix+resource;row=trace["static_access_by_observed_rule"].get(str(e["rule_uid"]))
    if row is None:missing_static+=e["count"];counts["uncovered"]+=e["count"];by_kind[kind]["uncovered"]+=e["count"];continue
    if mode=="write":explicit=key in row["writes"];wildcard=row["writes_any"]
    elif mode=="term_edge_read":explicit=key in row["reads"] or key in row["term_edge_reads"];wildcard=row["reads_any"]
    else:explicit=key in row["reads"];wildcard=row["reads_any"]
    category="explicit" if explicit else ("wildcard" if wildcard else "uncovered")
    counts[category]+=e["count"];by_kind[kind][category]+=e["count"]
 return {"counts":dict(sorted(counts.items())),"by_event_kind":{k:dict(sorted(v.items())) for k,v in sorted(by_kind.items())},
  "unmapped_event_kind_counts":dict(sorted(unmapped.items())),"missing_static_rows_or_resources":missing_static,
  "mapped_events_total":sum(counts.values()),"scope":"observed runtime events only; wildcard coverage is conservative and does not establish frame locality"}
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
 interfaces=all(x["integrity_pass"] for x in turn_rows)
 quality=all(x["task_quality_pass"] for x in turn_rows)
 coverage_report=access_coverage(workers)
 result={"schema":"HeldTopicRuntimeInterfaceTraceAnalysisV1_2","source_capture_lock_sha256":sha(LOCK),
  "analysis_amendment_sha256":sha(ROOT/"docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_RUNTIME_INTERFACE_TRACE_V1_ANALYSIS_AMENDMENT_20261001.md"),
  "capture_sha256":sha(CAP),"capture_integrity_pass":source and fresh and coverage and worker_sources and stable and interfaces,
  "task_quality_pass":quality,"all_claim_gates_pass":source and fresh and coverage and worker_sources and stable and interfaces and quality,
  "gates":{"locked_runtime_sources_current":source,"three_fresh_workers":fresh,"seven_turns_per_worker":coverage,
   "worker_source_stability":worker_sources,"runtime_graph_interface_and_trace_repeat":stable,"interface_and_trace_invariants":interfaces,
   "frozen_task_quality_oracles":quality},"turns":turn_rows,
  "attribute_value_repeat_differences":attribute_hash_differences(workers),"observed_static_dynamic_access_coverage":coverage_report}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(OUT.relative_to(ROOT)),"capture_integrity_pass":result["capture_integrity_pass"],
  "task_quality_pass":quality,"gates":result["gates"]},indent=2))
 if not result["capture_integrity_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
