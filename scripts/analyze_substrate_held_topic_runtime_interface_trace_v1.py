#!/usr/bin/env python3
"""Check access-trace and interface capture invariants independently."""
from __future__ import annotations
import collections,gzip,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
STEM="held_topic_runtime_interface_trace_v1_20261001"
CAP=ROOT/f"evaluation/reports/{STEM}/capture.json.gz";LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json";OUT=ROOT/f"evaluation/reports/{STEM}/analysis.json"
def sha(p):return "sha256:"+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location("held_interface_trace_runner",ROOT/"scripts/substrate_held_topic_runtime_interface_trace_v1.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def expected_roles(event,owned,external):
 roles=set()
 for n in (event["node"],event["peer"]):
  if n in owned:roles.add("owned")
  elif n in external:roles.add("boundary_external")
  elif n is not None:roles.add("outside_cut")
 return sorted(roles or {"global_or_node_free"})
def check_turn(turn):
 frame=turn["task_frame"];owned=set(map(int,frame["node_ids"]));boundary=[tuple(map(int,e[:1]))+(str(e[1]),)+tuple(map(int,e[2:])) for e in frame["boundary_edges"]]
 internal=[(int(e[0]),str(e[1]),int(e[2])) for e in frame["internal_edges"]]
 external={t if s in owned else s for s,_,t in boundary}
 node_records=frame["interface_nodes"]
 node_gate=all(str(n) in node_records for n in owned|external) and all((node_records[str(n)]["role"]==("owned" if n in owned else "boundary_external")) for n in owned|external)
 schema=collections.Counter(k for row in node_records.values() if row["role"]=="owned" for k in row["attribute_schema"])
 schema_ext=collections.Counter(k for row in node_records.values() if row["role"]=="boundary_external" for k in row["attribute_schema"])
 schema_gate=dict(sorted(schema.items()))==frame["attribute_names_by_role"]["owned"] and dict(sorted(schema_ext.items()))==frame["attribute_names_by_role"]["boundary_external"]
 tr=turn["runtime_dependency_trace"];events=tr["events"];dropped=tr["dropped"]==0
 roles_ok=all(e["scope_roles"]==expected_roles(e,owned,external) for e in events)
 by_kind=collections.Counter();by_scope=collections.defaultdict(collections.Counter);by_resource=collections.defaultdict(collections.Counter);touched=collections.defaultdict(set)
 for e in events:
  by_kind[e["kind"]]+=e["count"]
  for role in e["scope_roles"]:
   by_scope[role][e["kind"]]+=e["count"]
   if e["resource"] is not None:by_resource[role][e["resource"]]+=e["count"]
   for n in (e["node"],e["peer"]):
    if n is not None:touched[role].add(n)
 aggregate=(dict(sorted(by_kind.items()))==tr["access_counts_by_kind"] and
  {r:dict(sorted(v.items())) for r,v in sorted(by_scope.items())}==tr["access_counts_by_scope_and_kind"] and
  {r:dict(sorted(v.items())) for r,v in sorted(by_resource.items())}==tr["resource_counts_by_scope"] and
  {r:len(v) for r,v in sorted(touched.items())}==tr["touched_node_count_by_scope"] and sum(by_kind.values())==tr["event_count"])
 static=all(str(e["rule_uid"]) in tr["static_access_by_observed_rule"] and e["rule_name"]!="<unmapped_rule_uid>" for e in events)
 return {"valid":node_gate and schema_gate and dropped and roles_ok and aggregate and static,
  "interface_nodes_resolve":node_gate,"attribute_schema_reconciles":schema_gate,"trace_has_no_drops":dropped,
  "event_scope_classification_reconciles":roles_ok,"trace_aggregates_reconcile":aggregate,"observed_uids_have_static_declarations":static,
  "owned_nodes":len(owned),"external_boundary_nodes":len(external),"boundary_incidences":len(boundary),
  "trace_events":tr["event_count"],"trace_rows":len(events),"trace_dropped":tr["dropped"],
  "accesses_inside_or_on_boundary":sum(v for role,counts in tr["access_counts_by_scope_and_kind"].items() if role in ("owned","boundary_external") for v in counts.values()),
  "accesses_outside_direct_cut":sum(tr["access_counts_by_scope_and_kind"].get("outside_cut",{}).values())}
def main():
 runner=load_runner();lock=json.loads(LOCK.read_text());source=runner.lock_payload()==lock
 capture=json.loads(gzip.decompress(CAP.read_bytes()));workers=capture["workers"]
 pids={w["payload"]["pid"] for w in workers};workers_gate=len(workers)==3 and len(pids)==3
 rows=[]
 for w in workers:
  r=w["payload"]
  for turn in r["turns"]:rows.append({"replicate":r["replicate"],"prompt":turn["prompt"],**check_turn(turn)})
 turn_coverage=len(rows)==21 and all(sum(row["replicate"]==rep for row in rows)==7 for rep in range(3))
 stable=len({w["payload"]["whole_graph_semantic_sha256"] for w in workers})==1 and len({json.dumps([
  {"prompt":t["prompt"],"reply":t["reply"],"message":t["message"],"goals":t["goals"],
   "task_frame":t["task_frame"],"trace":t["runtime_dependency_trace"]} for t in w["payload"]["turns"]],sort_keys=True) for w in workers})==1
 turn_valid=all(r["valid"] for r in rows)
 result={"all_checks_pass":source and workers_gate and turn_coverage and stable and turn_valid,
  "gates":{"sources_current":source,"three_fresh_workers":workers_gate,"seven_turns_per_worker":turn_coverage,
   "runtime_graph_interface_and_trace_repeat":stable,"all_turn_interface_trace_invariants":turn_valid},
  "turns":rows,"capture_sha256":sha(CAP),"compressed_capture_bytes":CAP.stat().st_size}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"analysis":str(OUT.relative_to(ROOT)),"all_checks_pass":result["all_checks_pass"],"gates":result["gates"]},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
