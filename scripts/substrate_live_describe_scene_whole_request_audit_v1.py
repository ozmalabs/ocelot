#!/usr/bin/env python3
"""Paired full-request native matcher audit for live describe-scene."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_DESCRIBE_SCENE_WHOLE_REQUEST_AUDIT_V1_PREREG_20260927.md"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_whole_request_audit_v1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/live_describe_scene_whole_request_audit_v1_20260927.json"
RAW=ROOT/"evaluation/reports/live_describe_scene_whole_request_audit_v1_workers_raw_20260927.json"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py",
 "reflective_faculty":ROOT/"domains/reflective_faculty.py","arc_self_report":ROOT/"scripts/arc_self_report.py",
 "discourse_seed":ROOT/"seeds/conversation_discourse_state.json","native_py":ROOT/"runners/dsl/src/py.rs",
 "native_access_trace":ROOT/"runners/dsl/src/access_trace.rs","native_scale_audit":ROOT/"runners/dsl/src/scale_audit.rs",
 "native_rewrite":ROOT/"runners/dsl/src/rewrite.rs","analyzer":ROOT/"scripts/analyze_substrate_live_describe_scene_whole_request_audit_v1.py"}
PROMPT="describe what you see"
EXPECTED="I see the grey thing stays, the yellow counter, and the blue thing moves."

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,"value") else x)
def semantic_digest(graph):
 nodes=[]
 for node in graph.get("nodes",[]):
  attrs=dict(node.get("attrs",{}))
  if node.get("type")=="SystemModel":attrs.pop("ts",None);attrs.pop("runtime_s",None)
  nodes.append({"id":node["id"],"type":node["type"],"attrs":attrs})
 payload={"nodes":nodes,"edges":graph.get("edges",[])}
 return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def source_closure():
 paths=set()
 for folder in (ROOT/"domains",ROOT/"substrate",ROOT/"runners/dsl/python"):
  paths.update(p for p in folder.rglob("*.py") if "__pycache__" not in p.parts)
 paths.update((ROOT/"seeds").glob("*.json"));paths.update((ROOT/"seeds/generated").glob("*.json"))
 return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),
  "source_sha256":{k:sha(v) for k,v in SOURCES.items()},"source_closure_sha256":source_closure(),
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def worker(rep,arm):
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains.conversation_action import attach_scene
 a=WorldAdapter(seeds=());t0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-t0
 attach_scene(a,[{"kind":"static","colour":"grey"},{"kind":"meter","colour":"yellow"},{"kind":"mover","colour":"blue","responds_to_my_action":False}])
 audited=arm=="audited"; t0=time.perf_counter_ns();cpu0=time.process_time_ns()
 if audited:
  a.inner.scale_audit_reset();a.inner.scale_audit_per_rule_reset();a.inner.runtime_access_trace_reset()
  a.inner.scale_audit_set_enabled(True);a.inner.scale_audit_set_per_rule_enabled(True);a.inner.runtime_access_trace_set_enabled(True)
 try:reply=str(a.converse(PROMPT,speech_act="instruction",speaker="alice"))
 finally:
  if audited:
   a.inner.runtime_access_trace_set_enabled(False);a.inner.scale_audit_set_per_rule_enabled(False);a.inner.scale_audit_set_enabled(False)
 elapsed=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-cpu0
 if audited:
  scale={str(k):int(v) for k,v in dict(a.inner.scale_audit_snapshot()).items()}
  per_rule=[[int(i),str(m),int(v)] for i,m,v in a.inner.scale_audit_per_rule_snapshot()]
  per_clause=[[int(i),int(pos),int(v)] for i,pos,v in a.inner.scale_audit_match_clause_snapshot()]
  metadata=[[int(i),int(sym),str(name),int(arity),bool(amb)] for i,sym,name,arity,amb in a.inner.scale_audit_rule_metadata_snapshot()]
  trace_rows,dropped=a.inner.runtime_access_trace_snapshot()
  trace=[{"rule_uid":int(uid),"kind":str(kind),"node":None if node is None else int(node),"resource":None if resource is None else str(resource),"peer":None if peer is None else int(peer),"count":int(count)} for uid,kind,node,resource,peer,count in trace_rows]
 else:scale={};per_rule=[];per_clause=[];metadata=[];trace=[];dropped=0
 message=getattr(a,"_last_turn_inbound",None);attrs=dict(a.s.node(message)["attrs"]) if message is not None else {}
 goals=[g for g in a.s.nodes("Goal") if message is not None and message in a.inner.neighbours(g,"comprehends")]
 goal=None
 if len(goals)==1:
  g=goals[0];ga=dict(a.s.node(g)["attrs"]);events=list(a.inner.neighbours(g,"transitioned_by"));events.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
  goal={"id":nid(g),"status":ga.get("lifecycle_status"),"self_target":ga.get("self_target"),"transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in events],"transition_event_ids":[nid(e) for e in events],"closed":any(g in a.inner.neighbours(s,"has_closed_goal") for s in a.s.nodes("DiscourseState")),"active":any(g in a.inner.neighbours(s,"has_active_goal") for s in a.s.nodes("DiscourseState"))}
 outbound=[]
 if message is not None:
  for m in a.s.nodes("Message"):
   ma=dict(a.s.node(m)["attrs"])
   if ma.get("from") in ("agent","adapter") and message in a.inner.neighbours(m,"responds_to"):
    outbound.append({"id":nid(m),"text":ma.get("text"),"suppressed":bool(ma.get("turn_reply_suppressed"))})
 graph=a.s.graph_to_dict();trace_count=sum(x["count"] for x in trace)
 return {"replicate":rep,"arm":arm,"pid":os.getpid(),"boot_ns":boot_ns,"request_wall_ns":elapsed,"request_process_cpu_ns":cpu,
  "reply":reply,"expected_reply":EXPECTED,"reply_matches_expected":reply.strip()==EXPECTED,
  "route":attrs.get("communication_route"),"goal_count":len(goals),"goal":goal,
  "inbound_id":nid(message) if message is not None else None,"outbound_messages":outbound,
  "outbound_matches_public_reply":any(str(m.get("text") or "").strip()==reply.strip() for m in outbound if not m["suppressed"]),
  "graph_node_count":len(graph.get("nodes",[])),"graph_edge_count":len(graph.get("edges",[])),"semantic_graph_sha256":semantic_digest(graph),
  "scale":scale,"per_rule":per_rule,"per_clause":per_clause,"metadata":metadata,
  "trace_rows":trace,"trace_dropped":int(dropped),"trace_event_count":trace_count,
  "worker_started_inputs":started,"worker_finished_inputs":lock_inputs()}
def main():
 if sys.argv[1:]==["--lock"]:
  print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==4 and sys.argv[1]=="--worker":
  print(json.dumps(worker(int(sys.argv[2]),sys.argv[3]),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[(i,arm) for i in range(3) for arm in ("untraced","audited")];random.Random(20260927).shuffle(jobs);runs=[]
 for rep,arm in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  row=json.loads(p.stdout);runs.append(row);print(f"completed replicate={rep} arm={arm}",flush=True)
 post=lock_inputs();payload={"schema_version":1,"run_id":"live-describe-scene-whole-request-audit-v1-20260927","locked_inputs":locked,"post_run_inputs":post,"schedule":jobs,"runs":runs}
 RAW.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 OUT.write_text(json.dumps({"raw_report":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"schedule":jobs,"worker_count":len(runs)},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"raw":str(RAW),"workers":len(runs),"source_stable":post==locked},indent=2))
 if post!=locked or len({r["pid"] for r in runs})!=6:raise SystemExit("worker or source stability gate failed")
if __name__=="__main__":main()
