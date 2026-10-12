#!/usr/bin/env python3
"""Capture native runtime dependencies and boundary schemas for held-topic turns."""
from __future__ import annotations
import argparse, gzip, hashlib, importlib.util, json, os, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
if os.environ.get("SUBSTRATE_NATIVE_PACKAGE"):
 sys.path.insert(0,str(Path(os.environ["SUBSTRATE_NATIVE_PACKAGE"]).resolve().parent))
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_RUNTIME_INTERFACE_TRACE_V1_8_PREREG_20261001.md"
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/"scripts/analyze_substrate_held_topic_runtime_interface_trace_v2_0.py"
BASE_PATH=ROOT/"scripts/substrate_live_held_topic_evidence_v1_6.py"
LOCK=ROOT/"evaluation/substrate_capability/held_topic_runtime_interface_trace_v1_8_20261001_lock.json"
OUTDIR=ROOT/"evaluation/reports/held_topic_runtime_interface_trace_v1_8_20261001"
CAPTURE=OUTDIR/"capture.json.gz"
def sha(p):return "sha256:"+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location("held_topic_base_v1_6",BASE_PATH);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def lock_payload():
 base=load_base()
 from substrate_rs import _native
 return {"schema_version":1,"base_inputs":base.fingerprint(),"protocol_sha256":sha(PROTOCOL),
  "runner_sha256":sha(RUNNER),"analyzer_sha256":sha(ANALYZER),"base_runner_sha256":sha(BASE_PATH),
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "design":{"workers":3,"turn_count":7,"runtime_trace":"whole-worker all-scope work trace is re-enabled immediately after each access-trace toggle; concrete access rows are differenced around each converse",
   "ownership":"unchanged operational task projections from held-topic v1.6","capture":"gzip JSON"}}
def nid(x):return int(x.value if hasattr(x,"value") else x)
def value_shape(value):
 if value is None:kind="null";card=0
 elif isinstance(value,bool):kind="bool";card=2
 elif isinstance(value,int):kind="int";card=None
 elif isinstance(value,float):kind="float";card=None
 elif isinstance(value,str):kind="str";card=None
 elif isinstance(value,list):kind="list";card=len(value)
 elif isinstance(value,dict):kind="dict";card=len(value)
 else:kind=type(value).__name__;card=None
 return {"type":kind,"container_length":card}
def enrich_frame(base,agent,frame):
 from substrate_rs import NodeID
 owned=set(int(x) for x in frame["node_ids"])
 external={int(edge[2]) if int(edge[0]) in owned else int(edge[0]) for edge in frame["boundary_edges"]}
 records={}
 for node_id in sorted(owned|external):
  node=agent.s.node(NodeID(node_id))
  attrs=dict(node.get("attrs",{}))
  records[str(node_id)]={"type":str(node["type"]),"role":"owned" if node_id in owned else "boundary_external",
    "attribute_schema":{str(k):value_shape(v) for k,v in sorted(attrs.items())},
    "attribute_value_hashes":{str(k):hashlib.sha256(json.dumps(v,sort_keys=True,default=str,separators=(",",":")).encode()).hexdigest() for k,v in sorted(attrs.items())}}
 frame["interface_nodes"]=records
 frame["attribute_names_by_role"]={role:dict(sorted(Counter(k for row in records.values() if row["role"]==role for k in row["attribute_schema"]).items())) for role in ("owned","boundary_external")}
 return frame
def run_worker(rep,output_path):
 base=load_base()
 from substrate.world_adapter import WorldAdapter
 from substrate_rs import _native
 traced_calls=[];static_by_uid={}
 _native.Substrate.runtime_access_trace_reset()
 _native.Substrate.runtime_work_trace_set_all_scopes_enabled(True)
 def work_snapshot():
  rows,dropped=_native.Substrate.runtime_work_trace_all_scopes_snapshot()
  return Counter({(int(s),int(op),int(uid),str(k),None if sub is None else int(sub)):int(units) for s,op,uid,k,sub,units in rows}),int(dropped)
 def work_rows(counter):
  return [{"scope":k[0],"operation_id":k[1],"producer_rule_uid":k[2],"kind":k[3],"subject":k[4],"units":int(v)} for k,v in sorted(counter.items()) if v]
 def access_snapshot(inner):
  rows,dropped=inner.runtime_access_trace_snapshot_detailed()
  return Counter({(int(u),str(k),None if n is None else int(n),None if r is None else str(r),None if p is None else int(p),None if pr is None else str(pr)):int(count) for u,k,n,r,p,pr,count in rows}),int(dropped)
 def access_rows(counter):
  return [{"rule_uid":k[0],"kind":k[1],"node":k[2],"resource":k[3],"peer":k[4],"peer_resource":k[5],"count":int(v)} for k,v in sorted(counter.items()) if v]
 previous_work,previous_work_dropped=work_snapshot()
 worker_segments=[]
 original_converse=WorldAdapter.converse
 original_projection=base.frame_projection
 def traced_converse(agent,*args,**kwargs):
  nonlocal previous_work,previous_work_dropped
  inner=agent.inner
  pre_work,pre_work_dropped=work_snapshot()
  pre_rows=pre_work-previous_work
  pre_dropped=max(0,pre_work_dropped-previous_work_dropped)
  access_before,access_before_dropped=access_snapshot(inner)
  inner.runtime_access_trace_set_enabled(True)
  _native.Substrate.runtime_work_trace_set_all_scopes_enabled(True)
  try:return original_converse(agent,*args,**kwargs)
  finally:
   inner.runtime_access_trace_set_enabled(False)
   _native.Substrate.runtime_work_trace_set_all_scopes_enabled(True)
   access_after,access_after_dropped=access_snapshot(inner)
   now_work,now_work_dropped=work_snapshot()
   in_call=now_work-pre_work
   in_call_dropped=max(0,now_work_dropped-pre_work_dropped)
   traced_calls.append({"access_rows":access_rows(access_after-access_before),"dropped":max(0,access_after_dropped-access_before_dropped),
    "operation_work_rows":work_rows(in_call),"operation_work_dropped":in_call_dropped,
    "pre_turn_work_rows":work_rows(pre_rows),"pre_turn_work_dropped":pre_dropped})
   worker_segments.append({"pre_turn_rows":work_rows(pre_rows),"during_turn_rows":work_rows(in_call)})
   previous_work,previous_work_dropped=now_work,now_work_dropped
   for row in inner.rule_access_sets():
    slot=int(row[0]);meta=inner.rule_metadata(slot);uid=int(meta["rule_uid"])
    static_by_uid[uid]={"rule_name":str(row[1]),"active":bool(row[2]),"reads":list(row[3]),"term_edge_reads":list(row[4]),"writes":list(row[5]),"reads_any":bool(row[6]),"writes_any":bool(row[7])}
 def projection(agent,*args,**kwargs):
  frame=original_projection(agent,*args,**kwargs)
  return enrich_frame(base,agent,frame)
 WorldAdapter.converse=traced_converse;base.frame_projection=projection
 try:result=base.worker(rep)
 finally:
  _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
  WorldAdapter.converse=original_converse;base.frame_projection=original_projection
 final_work,final_work_dropped=work_snapshot()
 result["worker_operation_work_trace"]={"rows":work_rows(final_work),"dropped":int(final_work_dropped),
  "post_worker_rows":work_rows(final_work-previous_work),"post_worker_dropped":max(0,final_work_dropped-previous_work_dropped),
  "segments":worker_segments}
 turns=result["turns"]
 if len(traced_calls)!=len(turns):raise RuntimeError(f"trace/turn mismatch {len(traced_calls)} vs {len(turns)}")
 for turn,trace in zip(turns,traced_calls):
  frame=turn["task_frame"];owned=set(int(x) for x in frame["node_ids"])
  external={int(e[2]) if int(e[0]) in owned else int(e[0]) for e in frame["boundary_edges"]}
  enriched=[];totals=Counter();resource_by_role=defaultdict(Counter);kind_by_role=defaultdict(Counter);touched_by_role=defaultdict(set)
  for event in trace["access_rows"]:
   uid=event["rule_uid"];event["rule_name"]=static_by_uid.get(uid,{}).get("rule_name","<unmapped_rule_uid>")
   node=event["node"];peer=event["peer"]
   roles=set()
   for n in (node,peer):
    if n in owned:roles.add("owned")
    elif n in external:roles.add("boundary_external")
    elif n is not None:roles.add("outside_cut")
   if not roles:roles={"global_or_node_free"}
   event["scope_roles"]=sorted(roles);enriched.append(event)
   totals[event["kind"]]+=event["count"]
   for role in roles:
    kind_by_role[role][event["kind"]]+=event["count"]
    if event["resource"] is not None:resource_by_role[role][event["resource"]]+=event["count"]
    for n in (node,peer):
     if n is not None:touched_by_role[role].add(n)
  observed_uids=sorted({e["rule_uid"] for e in enriched})
  turn["runtime_dependency_trace"]={"dropped":trace["dropped"],"event_count":sum(e["count"] for e in enriched),
   "distinct_rows":len(enriched),"access_counts_by_kind":dict(sorted(totals.items())),
   "access_counts_by_scope_and_kind":{r:dict(sorted(c.items())) for r,c in sorted(kind_by_role.items())},
   "resource_counts_by_scope":{r:dict(sorted(c.items())) for r,c in sorted(resource_by_role.items())},
   "touched_node_count_by_scope":{r:len(ns) for r,ns in sorted(touched_by_role.items())},
   "unmapped_rule_uids":[u for u in observed_uids if u not in static_by_uid],
   "static_access_by_observed_rule":{str(u):static_by_uid.get(u,{}) for u in observed_uids},
   "events":enriched}
  turn["runtime_operation_work_trace"]={"dropped":trace["operation_work_dropped"],"rows":trace["operation_work_rows"]}
 result["runtime_trace_gate"]=all(t["runtime_dependency_trace"]["dropped"]==0 and not t["runtime_dependency_trace"]["unmapped_rule_uids"] for t in turns)
 raw=json.dumps(result,sort_keys=True,separators=(",",":"),default=str).encode()
 Path(output_path).write_bytes(gzip.compress(raw,compresslevel=6,mtime=0))
 return {"replicate":rep,"sha256":hashlib.sha256(raw).hexdigest(),"compressed_bytes":Path(output_path).stat().st_size}
def main():
 p=argparse.ArgumentParser();p.add_argument("--lock",action="store_true");p.add_argument("--worker",nargs=2);args=p.parse_args()
 if args.lock:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(lock_payload(),indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 if args.worker:
  result=run_worker(int(args.worker[0]),args.worker[1]);print(json.dumps(result));return
 locked=lock_payload()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=locked:raise SystemExit("source lock absent or stale")
 if CAPTURE.exists():raise SystemExit(f"refusing to overwrite {CAPTURE}")
 OUTDIR.mkdir(parents=True,exist_ok=True);workers=[]
 for rep in range(3):
  temp=OUTDIR/f"worker_{rep}.json.gz"
  proc=subprocess.run([sys.executable,str(RUNNER),"--worker",str(rep),str(temp)],cwd=ROOT,text=True,capture_output=True,check=True)
  workers.append({"metadata":json.loads(proc.stdout),"payload":json.loads(gzip.decompress(temp.read_bytes()))})
  temp.unlink()
 capture={"schema":"HeldTopicRuntimeInterfaceTraceV1_8","lock":locked,"workers":workers}
 CAPTURE.write_bytes(gzip.compress(json.dumps(capture,sort_keys=True,separators=(",",":"),default=str).encode(),compresslevel=6,mtime=0))
 print(json.dumps({"capture":str(CAPTURE.relative_to(ROOT)),"workers":len(workers),"compressed_bytes":CAPTURE.stat().st_size},indent=2))
if __name__=="__main__":main()
