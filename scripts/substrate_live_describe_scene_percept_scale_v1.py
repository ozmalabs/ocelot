#!/usr/bin/env python3
"""Full-request live describe-scene work across Scene/Percept counts."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,statistics,subprocess,sys,time
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_DESCRIBE_SCENE_PERCEPT_SCALE_V1_PREREG_20260929.md"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_percept_scale_v1_lock_20260929.json"
OUT=ROOT/"evaluation/reports/live_describe_scene_percept_scale_v1_20260929.json"
RAW=ROOT/"evaluation/reports/live_describe_scene_percept_scale_v1_workers_raw_20260929.json"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py",
 "reflective_faculty":ROOT/"domains/reflective_faculty.py","arc_self_report":ROOT/"scripts/arc_self_report.py",
 "discourse_seed":ROOT/"seeds/conversation_discourse_state.json","native_py":ROOT/"runners/dsl/src/py.rs",
 "native_access_trace":ROOT/"runners/dsl/src/access_trace.rs","native_scale_audit":ROOT/"runners/dsl/src/scale_audit.rs",
 "native_rewrite":ROOT/"runners/dsl/src/rewrite.rs","analyzer":ROOT/"scripts/analyze_substrate_live_describe_scene_percept_scale_v1.py"}
SIZES=(3,6,12,24)
NOISE_COUNT=4096
PROMPT="describe what you see"
EXPECTED="I see the grey thing stays, the yellow counter, and the blue thing moves."
PERCEPTS=[{"kind":"static","colour":"grey"},{"kind":"meter","colour":"yellow"},{"kind":"mover","colour":"blue","responds_to_my_action":False}]
EXPECTED_CLASS={"static":"a_thing_that_stays_put","meter":"a_counter","mover":"a_thing_that_moves_itself"}
REPLY_PROPOSITIONS=("grey thing stays","yellow counter","blue thing moves")
def make_percepts(count):
 return [dict(PERCEPTS[i % len(PERCEPTS)]) for i in range(count)]
def classify_percepts(a,percepts):
 rows=[]
 for p in percepts:
  attrs=dict(a.s.node(p)["attrs"]);actual=sorted(str(a.s.node(c)["attrs"].get("name")) for c in a.inner.neighbours(p,"is_a"))
  rows.append({"node_id":nid(p),"kind":attrs.get("kind"),"expected":EXPECTED_CLASS.get(attrs.get("kind")),"actual":actual})
 return rows

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
def add_noise(a,count):
 mt=a.s.add_node("Microtheory",{"kind":"tractability_noise","scale_probe":True})
 for i in range(count):
  con=a.s.add_node("Concept",{"name":f"tractability_noise_concept_{i:04d}","kind":"noise"})
  a.inner.add_edge_unchecked(mt,"has_concept",con)
 return nid(mt)
def worker(rep,percept_count,arm):
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains.conversation_action import attach_scene
 a=WorldAdapter(seeds=());t0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-t0
 scene=attach_scene(a,make_percepts(percept_count));noise_mt=add_noise(a,NOISE_COUNT)
 before=a.s.graph_to_dict();base_memberships=sum(e.get("type")=="has_concept" for e in before.get("edges",[]))
 base_concepts=sum(n.get("type")=="Concept" for n in before.get("nodes",[]))
 audited=arm=="audited";t0=time.perf_counter_ns();cpu0=time.process_time_ns()
 if audited:
  a.inner.scale_audit_reset();a.inner.scale_audit_per_rule_reset();a.inner.runtime_access_trace_reset()
  a.inner.scale_audit_set_enabled(True);a.inner.scale_audit_set_per_rule_enabled(True);a.inner.runtime_access_trace_set_enabled(True)
 try:reply=str(a.converse(PROMPT,speech_act="instruction",speaker="alice"))
 finally:
  if audited:
   a.inner.runtime_access_trace_set_enabled(False);a.inner.scale_audit_set_per_rule_enabled(False);a.inner.scale_audit_set_enabled(False)
 wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-cpu0
 if audited:
  work_rows,work_dropped=a.inner.runtime_work_trace_snapshot()
  work_by_kind=Counter();work_by_rule=Counter()
  for op,uid,kind,subject,units in work_rows:work_by_kind[str(kind)]+=int(units);work_by_rule[str(uid)]+=int(units)
  work_trace={"rows":[{"operation_id":int(op),"rule_uid":int(uid),"kind":str(kind),"subject":None if subject is None else int(subject),"work_units":int(units)} for op,uid,kind,subject,units in work_rows],"dropped":int(work_dropped),"units":sum(int(x[4]) for x in work_rows),"by_kind":dict(sorted(work_by_kind.items())),"by_rule_uid":dict(sorted(work_by_rule.items()))}
  scale={str(k):int(v) for k,v in dict(a.inner.scale_audit_snapshot()).items()}
  per_rule=[[int(i),str(m),int(v)] for i,m,v in a.inner.scale_audit_per_rule_snapshot()]
  per_clause=[[int(i),int(p),int(v)] for i,p,v in a.inner.scale_audit_match_clause_snapshot()]
  metadata=[[int(i),int(sym),str(name),int(arity),bool(amb)] for i,sym,name,arity,amb in a.inner.scale_audit_rule_metadata_snapshot()]
  trace_rows,dropped=a.inner.runtime_access_trace_snapshot();trace_counts=Counter()
  for uid,kind,node,res,peer,n in trace_rows:trace_counts[(int(uid),str(kind),"<none>" if res is None else str(res))]+=int(n)
  trace=[{"rule_uid":k[0],"kind":k[1],"resource":k[2],"count":v} for k,v in sorted(trace_counts.items())]
 else:scale={};per_rule=[];per_clause=[];metadata=[];trace=[];dropped=0;work_trace={"rows":[],"dropped":0,"units":0,"by_kind":{},"by_rule_uid":{}}
 message=getattr(a,"_last_turn_inbound",None);attrs=dict(a.s.node(message)["attrs"]) if message is not None else {}
 goals=[g for g in a.s.nodes("Goal") if message is not None and message in a.inner.neighbours(g,"comprehends")]
 goal=None
 if len(goals)==1:
  g=goals[0];ga=dict(a.s.node(g)["attrs"]);evs=list(a.inner.neighbours(g,"transitioned_by"));evs.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
  goal={"id":nid(g),"status":ga.get("lifecycle_status"),"transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in evs],"transition_event_ids":[nid(e) for e in evs],"closed":any(g in a.inner.neighbours(s,"has_closed_goal") for s in a.s.nodes("DiscourseState")),"active":any(g in a.inner.neighbours(s,"has_active_goal") for s in a.s.nodes("DiscourseState"))}
 scene_percepts=list(a.inner.neighbours(scene,"has_percept"))
 classified=sum(len(list(a.inner.neighbours(p,"is_a"))) for p in scene_percepts)
 request_views=[v for v in a.s.nodes("Scene") if a.s.node(v)["attrs"].get("kind")=="request_view" and scene in a.inner.neighbours(v,"source_scene")]
 request_view_percepts=[p for v in request_views for p in a.inner.neighbours(v,"has_percept")]
 request_view_classifications=classify_percepts(a,request_view_percepts)
 request_view_classification_exact=(len(request_views)==1 and len(request_view_percepts)==percept_count and all(x["actual"]==[x["expected"]] for x in request_view_classifications))
 outbound=[]
 for m in a.s.nodes("Message"):
  ma=dict(a.s.node(m)["attrs"])
  if ma.get("from") in ("agent","adapter") and message is not None and message in a.inner.neighbours(m,"responds_to"):
   outbound.append({"text":ma.get("text"),"suppressed":bool(ma.get("turn_reply_suppressed"))})
 outbound_match=any(str(m.get("text") or "").strip()==reply.strip() for m in outbound if not m["suppressed"])
 graph=a.s.graph_to_dict();trace_count=sum(x["count"] for x in trace)
 return {"replicate":rep,"percept_count":percept_count,"arm":arm,"pid":os.getpid(),"boot_ns":boot_ns,"request_wall_ns":wall,"request_process_cpu_ns":cpu,
  "peak_rss_bytes":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024,"reply":reply,"expected_reply":EXPECTED,"reply_matches_expected":reply.strip()==EXPECTED,"reply_semantic_coverage":all(x in reply.lower() for x in REPLY_PROPOSITIONS),
  "route":attrs.get("communication_route"),"goal_count":len(goals),"goal":goal,"scene_id":nid(scene),"noise_microtheory_id":noise_mt,
  "base_concepts_before_noise":base_concepts-NOISE_COUNT,"base_memberships_before_noise":base_memberships-NOISE_COUNT,
  "noise_concept_count":NOISE_COUNT,"noise_membership_count":NOISE_COUNT,"noise_classified_edges":sum(len(list(a.inner.neighbours(c,"is_a"))) for c in [n for n in a.s.nodes("Concept") if str(a.s.node(n)["attrs"].get("name","")).startswith("tractability_noise_concept_")]),
  "scene_percepts":len(scene_percepts),"scene_classification_edge_count":classified,
  "graph_node_count":len(graph.get("nodes",[])),"graph_edge_count":len(graph.get("edges",[])),"semantic_graph_sha256":semantic_digest(graph),
  "scale":scale,"per_rule":per_rule,"per_clause":per_clause,"metadata":metadata,"trace_rows":trace,"trace_dropped":int(dropped),"trace_event_count":trace_count,"operation_work":work_trace,"request_scene_view_count":len(request_views),"request_view_percept_count":len(request_view_percepts),"request_view_classifications":request_view_classifications,"request_view_classification_exact":request_view_classification_exact,
  "outbound_message_count":len(outbound),"outbound_message_alignment":outbound_match,"worker_started_inputs":started,"worker_finished_inputs":lock_inputs()}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==5 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale source lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[(s,r,a) for s in SIZES for r in range(2) for a in ("untraced","audited")];random.Random(20260927).shuffle(jobs);runs=[]
 for percept_count,rep,arm in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep),str(percept_count),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  row=json.loads(p.stdout);runs.append(row);print(f"completed percept_count={percept_count} replicate={rep} arm={arm}",flush=True)
 post=lock_inputs();raw={"schema_version":1,"run_id":"live-describe-scene-percept-scale-v1-20260929","locked_inputs":locked,"post_run_inputs":post,"schedule":jobs,"runs":runs}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 OUT.write_text(json.dumps({"raw_report":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"schedule":jobs,"worker_count":len(runs)},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"raw":str(RAW),"workers":len(runs),"source_stable":post==locked},indent=2))
 if post!=locked or len({r["pid"] for r in runs})!=12:raise SystemExit("worker/source gate failed")
if __name__=="__main__":main()
