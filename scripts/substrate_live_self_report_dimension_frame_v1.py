#!/usr/bin/env python3
"""Live self-report capability and work across task-dimension sizes."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,statistics,subprocess,sys,time
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_DIMENSION_FRAME_V1_PREREG_20260927.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_DIMENSION_FRAME_V1_1_AMENDMENT_20260927.md"
LOCK=ROOT/"evaluation/substrate_capability/live_self_report_dimension_frame_v1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/live_self_report_dimension_frame_v1_20260927.json"
RAW=ROOT/"evaluation/reports/live_self_report_dimension_frame_v1_workers_raw_20260927.json"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py",
 "reflective_faculty":ROOT/"domains/reflective_faculty.py","self_organisation_reader":ROOT/"domains/self_organisation_reader.py","arc_self_report":ROOT/"scripts/arc_self_report.py",
 "discourse_seed":ROOT/"seeds/conversation_discourse_state.json","self_model":ROOT/"domains/self_model.py","native_py":ROOT/"runners/dsl/src/py.rs",
 "native_access_trace":ROOT/"runners/dsl/src/access_trace.rs","native_scale_audit":ROOT/"runners/dsl/src/scale_audit.rs",
 "native_rewrite":ROOT/"runners/dsl/src/rewrite.rs","analyzer":ROOT/"scripts/analyze_substrate_live_self_report_dimension_frame_v1.py","amendment":AMENDMENT}
SIZES=(4,8,12,16,24)
PROMPT="report your organisation"
PERCEPTS=[{"kind":"static","colour":"grey"},{"kind":"meter","colour":"yellow"},{"kind":"mover","colour":"blue","responds_to_my_action":False}]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,"value") else x)
def semantic_digest(graph):
 nodes=[]
 for node in graph.get("nodes",[]):
  attrs=dict(node.get("attrs",{}))
  if node.get("type")=="SystemModel":attrs.pop("ts",None);attrs.pop("runtime_s",None)
  nodes.append({"id":node["id"],"type":node["type"],"attrs":attrs})
 return hashlib.sha256(json.dumps({"nodes":nodes,"edges":graph.get("edges",[])},sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def source_closure():
 paths=set()
 for folder in (ROOT/"domains",ROOT/"substrate",ROOT/"runners/dsl/python"):
  paths.update(p for p in folder.rglob("*.py") if "__pycache__" not in p.parts)
 paths.update((ROOT/"seeds").glob("*.json"));paths.update((ROOT/"seeds/generated").glob("*.json"))
 return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},
  "source_closure_sha256":source_closure(),"native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def add_dimensions(a,count):
 agents=[x for x in a.s.nodes("Agent") if a.s.node(x)["attrs"].get("microtheory_inventory_schema")=="seed_microtheory_inventory.v1"]
 if len(agents)!=1:raise RuntimeError("unique seeded self-organisation inventory required")
 agent=agents[0];names=[];frame_nodes=[];roles={}
 for i in range(count):
  name=f"frame_probe_area_{i+1:02d}";names.append(name)
  mt=a.s.add_node("Microtheory",{"name":name,"description":f"Controlled self-report dimension {i+1}","kind":"frame_probe_area"})
  con=a.s.add_node("Concept",{"name":f"frame_probe_concept_{i+1:02d}","kind":"frame_probe"})
  a.inner.add_edge_unchecked(agent,"holds_area",mt);a.inner.add_edge_unchecked(mt,"has_concept",con)
  frame_nodes.extend([nid(mt),nid(con)])
  roles[nid(mt)]={"area":name,"role":"Microtheory"};roles[nid(con)]={"area":name,"role":"Concept"}
 a.inner.set_attr(agent,"microtheory_inventory_areas_json",json.dumps([{"name":n,"concept_count":1} for n in names],separators=(",",":")))
 a.inner.set_attr(agent,"microtheory_inventory_area_count",count)
 return names,frame_nodes,nid(agent),roles
def worker(rep,size,arm):
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());t0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-t0
 expected_areas,frame_nodes,frame_root,frame_roles=add_dimensions(a,size)
 before=a.s.graph_to_dict();base_memberships=sum(e.get("type")=="has_concept" for e in before.get("edges",[]))
 base_concepts=sum(n.get("type")=="Concept" for n in before.get("nodes",[]))
 audited=arm=="audited"
 if audited:
  a.inner.scale_audit_reset();a.inner.scale_audit_per_rule_reset();a.inner.runtime_access_trace_reset()
  a.inner.scale_audit_set_enabled(True);a.inner.scale_audit_set_per_rule_enabled(True);a.inner.runtime_access_trace_set_enabled(True)
 import domains.reflective_faculty as rf
 original_reflect=rf.reflect;reflections=[]
 def capture_reflect(target,*args,**kwargs):
  result=original_reflect(target,*args,**kwargs)
  if target=="self_organisation":reflections.append(result)
  return result
 rf.reflect=capture_reflect
 t0=time.perf_counter_ns();cpu0=time.process_time_ns()
 try:reply=str(a.converse(PROMPT,speech_act="instruction",speaker="alice"))
 finally:
  rf.reflect=original_reflect
  if audited:
   a.inner.runtime_access_trace_set_enabled(False);a.inner.scale_audit_set_per_rule_enabled(False);a.inner.scale_audit_set_enabled(False)
 wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-cpu0
 if audited:
  scale={str(k):int(v) for k,v in dict(a.inner.scale_audit_snapshot()).items()}
  per_rule=[[int(i),str(m),int(v)] for i,m,v in a.inner.scale_audit_per_rule_snapshot()]
  per_clause=[[int(i),int(p),int(v)] for i,p,v in a.inner.scale_audit_match_clause_snapshot()]
  metadata=[[int(i),int(sym),str(name),int(arity),bool(amb)] for i,sym,name,arity,amb in a.inner.scale_audit_rule_metadata_snapshot()]
  trace_rows,dropped=a.inner.runtime_access_trace_snapshot();trace_counts=Counter()
  frame_touch_count=0;root_touch_count=0;frame_touches=[]
  for uid,kind,node,res,peer,n in trace_rows:
   trace_counts[(int(uid),str(kind),"<none>" if res is None else str(res))]+=int(n)
   node=None if node is None else int(node);peer=None if peer is None else int(peer);count=int(n)
   touched=sorted({x for x in (node,peer) if x is not None and x in frame_roles})
   root_touched=frame_root in (node,peer)
   if touched:frame_touch_count+=count
   if root_touched:root_touch_count+=count
   if touched or root_touched:
    frame_touches.append({"rule_uid":int(uid),"kind":str(kind),"node":node,"resource":None if res is None else str(res),"peer":peer,"count":count,"frame_node_ids":touched,"frame_roles":[frame_roles[x] for x in touched],"touches_agent_root":root_touched})
  trace=[{"rule_uid":k[0],"kind":k[1],"resource":k[2],"count":v} for k,v in sorted(trace_counts.items())]
 else:scale={};per_rule=[];per_clause=[];metadata=[];trace=[];dropped=0;frame_touch_count=0;root_touch_count=0;frame_touches=[]
 message=getattr(a,"_last_turn_inbound",None);attrs=dict(a.s.node(message)["attrs"]) if message is not None else {}
 goals=[g for g in a.s.nodes("Goal") if message is not None and message in a.inner.neighbours(g,"comprehends")]
 goal=None
 if len(goals)==1:
  g=goals[0];ga=dict(a.s.node(g)["attrs"]);evs=list(a.inner.neighbours(g,"transitioned_by"));evs.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
  goal={"id":nid(g),"status":ga.get("lifecycle_status"),"transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in evs],"transition_event_ids":[nid(e) for e in evs],"closed":any(g in a.inner.neighbours(s,"has_closed_goal") for s in a.s.nodes("DiscourseState")),"active":any(g in a.inner.neighbours(s,"has_active_goal") for s in a.s.nodes("DiscourseState"))}
 noise_classified=sum(len(list(a.inner.neighbours(n,"is_a"))) for n in a.s.nodes("Concept") if str(a.s.node(n)["attrs"].get("name","")).startswith("frame_probe_concept_"))
 outbound=[]
 for m in a.s.nodes("Message"):
  ma=dict(a.s.node(m)["attrs"])
  if ma.get("from") in ("agent","adapter") and message is not None and message in a.inner.neighbours(m,"responds_to"):
   outbound.append({"text":ma.get("text"),"suppressed":bool(ma.get("turn_reply_suppressed"))})
 outbound_match=any(str(m.get("text") or "").strip()==reply.strip() for m in outbound if not m["suppressed"])
 graph=a.s.graph_to_dict();trace_count=sum(x["count"] for x in trace)
 graph_nodes=set(frame_nodes);edge_rows=[(int(e["src"]),str(e["type"]),int(e["tgt"])) for e in graph.get("edges",[])];frame_internal=[e for e in edge_rows if e[0] in graph_nodes and e[2] in graph_nodes];frame_cut=[e for e in edge_rows if (e[0] in graph_nodes)!=(e[2] in graph_nodes)]
 reflect_state=reflections[-1] if reflections else None
 return {"replicate":rep,"size":size,"arm":arm,"pid":os.getpid(),"boot_ns":boot_ns,"request_wall_ns":wall,"request_process_cpu_ns":cpu,
  "peak_rss_bytes":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024,"reply":reply,"reply_nonempty":bool(reply),"reply_mentions_organisation":"organis" in reply.lower(),
  "route":attrs.get("communication_route"),"goal_count":len(goals),"goal":goal,"frame_root_id":frame_root,"frame_node_ids":sorted(frame_nodes),"expected_areas":expected_areas,"reflection_area_count":len(reflect_state.get("areas",[])) if isinstance(reflect_state,dict) else None,"reflection_areas":reflect_state.get("areas",[]) if isinstance(reflect_state,dict) else None,"surface_areas":getattr(a,"_last_self_organisation_delivery",None),
  "base_concepts_before_frame":base_concepts-size,"base_memberships_before_frame":base_memberships-size,
  "frame_area_count":size,"frame_membership_count":size,"frame_classified_edges":noise_classified,"frame_internal_edge_count":len(frame_internal),"frame_boundary_incidence_count":len(frame_cut),"frame_boundary_external_nodes":sorted({e[2] if e[0] in graph_nodes else e[0] for e in frame_cut}),
  "graph_node_count":len(graph.get("nodes",[])),"graph_edge_count":len(graph.get("edges",[])),"semantic_graph_sha256":semantic_digest(graph),
  "scale":scale,"per_rule":per_rule,"per_clause":per_clause,"metadata":metadata,"trace_rows":trace,"trace_dropped":int(dropped),"trace_event_count":trace_count,"frame_direct_access_event_count":frame_touch_count,"agent_root_access_event_count":root_touch_count,"frame_access_trace_rows":frame_touches,
  "outbound_message_count":len(outbound),"outbound_message_alignment":outbound_match,"worker_started_inputs":started,"worker_finished_inputs":lock_inputs()}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==5 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale source lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[(s,r,a) for s in SIZES for r in range(2) for a in ("untraced","audited")];random.Random(20260927).shuffle(jobs);runs=[]
 for size,rep,arm in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep),str(size),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  row=json.loads(p.stdout);runs.append(row);print(f"completed size={size} replicate={rep} arm={arm}",flush=True)
 post=lock_inputs();raw={"schema_version":1,"run_id":"live-self-report-live-scale-v1-20260927","locked_inputs":locked,"post_run_inputs":post,"schedule":jobs,"runs":runs}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 OUT.write_text(json.dumps({"raw_report":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"schedule":jobs,"worker_count":len(runs)},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"raw":str(RAW),"workers":len(runs),"source_stable":post==locked},indent=2))
 if post!=locked or len({r["pid"] for r in runs})!=20:raise SystemExit("worker/source gate failed")
if __name__=="__main__":main()
