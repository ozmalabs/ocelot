#!/usr/bin/env python3
"""Paired traced/untraced replay with per-request native access intervals."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,threading,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_AMENDMENT_20260926.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_V1_5_AMENDMENT_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py","conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py","reflective_faculty":ROOT/"domains/reflective_faculty.py","arc_self_report":ROOT/"scripts/arc_self_report.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json","native_py":ROOT/"runners/dsl/src/py.rs","native_access_trace":ROOT/"runners/dsl/src/access_trace.rs","analyzer":ROOT/"scripts/analyze_substrate_live_describe_scene_threaded_interleaving_v1_5.py"}
BOUNDARY_AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_DESCRIBE_SCENE_BOUNDARY_V1_AMENDMENT_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_access_trace_v2_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_describe_scene_access_trace_v2_20260926.json"
RAW=ROOT/"evaluation/reports/substrate_live_describe_scene_access_trace_v2_workers_raw_20260926.json"
BASELINE="I see the grey thing stays, the yellow counter, and the blue thing moves."
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,"value") else x)
def semantic_graph_digest(graph):
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
 seed_dir=ROOT/"seeds"
 paths.update(seed_dir.glob("*.json"))
 paths.update((seed_dir/"generated").glob("*.json"))
 return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"amendment_sha256":sha(AMENDMENT),"boundary_amendment_sha256":sha(BOUNDARY_AMENDMENT),"runner_sha256":sha(__file__),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"source_closure_sha256":source_closure(),"native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def project(a,st,g):
 tr=list(a.inner.neighbours(g,"transitioned_by"));tr.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
 return {"goal_id":nid(g),"status":a.s.node(g)["attrs"].get("lifecycle_status"),"message_ids":[nid(x) for x in a.inner.neighbours(g,"comprehends")],"origin_ids":[nid(x) for x in a.inner.neighbours(g,"originated_in")],"transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in tr],"transition_event_ids":[nid(e) for e in tr],"child_count":len(list(a.inner.neighbours(g,"has_subgoal"))),"active":g in a.inner.neighbours(st,"has_active_goal"),"closed":g in a.inner.neighbours(st,"has_closed_goal")}
def width_upper_bound(owned, internal):
 adj={n:set() for n in owned}
 for s,_,t in internal:
  if s in adj and t in adj and s!=t:adj[s].add(t);adj[t].add(s)
 width=0;order=[]
 while adj:
  def score(n):
   ns=sorted(adj[n]);missing=sum(1 for i,x in enumerate(ns) for y in ns[i+1:] if y not in adj[x])
   return missing,len(ns),n
  n=min(adj,key=score);ns=set(adj[n]);width=max(width,len(ns));order.append(n)
  for x in ns:adj[x].update(ns-{x});adj[x].discard(n)
  del adj[n]
 return {"value":width,"order":order,"method":"deterministic_min_fill_upper_bound"}
def boundary_projection(graph, owned):
 owned={int(n) for n in owned};edges=[(int(e["src"]),str(e["type"]),int(e["tgt"])) for e in graph.get("edges",[])]
 incident=[e for e in edges if e[0] in owned or e[2] in owned]
 internal=[e for e in incident if e[0] in owned and e[2] in owned]
 cut=[e for e in incident if (e[0] in owned)!=(e[2] in owned)]
 external={e[2] if e[0] in owned else e[0] for e in cut};nt={int(n["id"]):str(n["type"]) for n in graph.get("nodes",[])}
 ect={};nct={}
 for _,et,_ in cut:ect[et]=ect.get(et,0)+1
 for n in external:
  typ=nt.get(n,"<missing>");nct[typ]=nct.get(typ,0)+1
 return {"owned_node_ids":sorted(owned),"owned_node_count":len(owned),"internal_edge_count":len(internal),"boundary_incidence_count":len(cut),"boundary_unique_external_node_count":len(external),"boundary_edge_type_counts":dict(sorted(ect.items())),"boundary_external_node_type_counts":dict(sorted(nct.items())),"owned_induced_treewidth_upper_bound":width_upper_bound(owned,internal),"internal_edges":[list(e) for e in sorted(internal)],"boundary_edges":[list(e) for e in sorted(cut)]}
def scene_task_nodes(a,message,goals):
 events={e for g in goals for e in a.inner.neighbours(g,"transitioned_by") if a.s.has_node(e)}
 candidates={m for g in goals for m in a.inner.neighbours(g,"has_reply_candidate") if a.s.has_node(m)}
 receipts={r for r in a.s.nodes("ProductionGateReceipt") if a.s.node(r)["attrs"].get("turn_message_id")==nid(message) or message in a.inner.neighbours(r,"for_message")}
 outbound={m for m in a.outbound_messages() if message in a.responds_to(m)}
 return {nid(x) for x in {message,*goals,*events,*candidates,*receipts,*outbound}}
def paired_boundary(graph,owned_a,owned_b):
 a=set(owned_a);b=set(owned_b);edges=[(int(e["src"]),str(e["type"]),int(e["tgt"])) for e in graph.get("edges",[])]
 cross=[e for e in edges if (e[0] in a and e[2] in b) or (e[0] in b and e[2] in a)]
 cut_a=boundary_projection(graph,a);cut_b=boundary_projection(graph,b)
 ext_a={e[2] if e[0] in a else e[0] for e in [(int(x["src"]),str(x["type"]),int(x["tgt"])) for x in graph.get("edges",[])] if (e[0] in a)!=(e[2] in a)}
 ext_b={e[2] if e[0] in b else e[0] for e in [(int(x["src"]),str(x["type"]),int(x["tgt"])) for x in graph.get("edges",[])] if (e[0] in b)!=(e[2] in b)}
 types={int(n["id"]):str(n["type"]) for n in graph.get("nodes",[])};shared_nodes=ext_a&ext_b;st={}
 for n in shared_nodes:
  typ=types.get(n,"<missing>");st[typ]=st.get(typ,0)+1
 return {"direct_cross_task_edge_count":len(cross),"direct_cross_task_edges":[list(e) for e in sorted(cross)],"shared_external_node_count":len(shared_nodes),"shared_external_node_type_counts":dict(sorted(st.items()))}
class ObservedLock:
 def __init__(self,inner,attempted,trace_enabled,trace_sink):self.inner=inner;self.attempted=attempted;self.trace_enabled=trace_enabled;self.trace_sink=trace_sink;self.started={};self.depth={}
 def __enter__(self):
  if threading.current_thread().name=="request-B":self.attempted.set()
  self.inner.acquire();name=threading.current_thread().name
  if self.trace_enabled:
   depth=self.depth.get(name,0)
   if depth==0:self.trace_sink("begin",name,None);self.started[name]=(time.perf_counter_ns(),time.thread_time_ns())
   self.depth[name]=depth+1
  return self
 def __exit__(self,*exc):
  try:
   if self.trace_enabled:
    name=threading.current_thread().name;depth=self.depth[name]-1
    if depth==0:
     self.depth.pop(name);wall0,cpu0=self.started.pop(name);self.trace_sink("end",name,(time.perf_counter_ns()-wall0,time.thread_time_ns()-cpu0))
    else:self.depth[name]=depth
  finally:self.inner.release()
  return False
def worker(rep,trace_enabled):
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains.conversation_action import attach_scene
 import domains.conversation_action as ca
 a=WorldAdapter(seeds=());t0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-t0
 a.inner.runtime_access_trace_set_enabled(False);a.inner.runtime_access_trace_reset()
 ctx={"errors":[],"timings":{},"request_traces":{}}
 def trace_sink(action,name,timing):
  if action=="begin":a.inner.runtime_access_trace_reset();a.inner.runtime_access_trace_set_enabled(True);return
  a.inner.runtime_access_trace_set_enabled(False);rows,dropped=a.inner.runtime_access_trace_snapshot()
  ctx["request_traces"][name]={"wall_ns":timing[0],"thread_cpu_ns":timing[1],"dropped":int(dropped),"event_rows":[{"rule_uid":int(uid),"kind":str(kind),"node":None if node is None else int(node),"resource":None if resource is None else str(resource),"peer":None if peer is None else int(peer),"count":int(count)} for uid,kind,node,resource,peer,count in rows]}
  ctx["request_traces"][name]["event_count"]=sum(row["count"] for row in ctx["request_traces"][name]["event_rows"])
 attach_scene(a,[{"kind":"static","colour":"grey"},{"kind":"meter","colour":"yellow"},{"kind":"mover","colour":"blue","responds_to_my_action":False}])
 lock_attempted=threading.Event();observed_lock=ObservedLock(a._conversation_lock,lock_attempted,trace_enabled,trace_sink);a._conversation_lock=observed_lock
 a_selected=threading.Event();release_a=threading.Event();b_started=threading.Event();b_selected=threading.Event();b_completed=threading.Event()
 original=ca._record_live_goal_event
 def wrapped(agent,inbound,goal,kind,*,payload=None):
  audit=agent.inner;audit.scale_audit_reset();audit.scale_audit_per_rule_reset();audit.scale_audit_set_enabled(True);audit.scale_audit_set_per_rule_enabled(True);t0=time.perf_counter_ns()
  try:
   event=original(agent,inbound,goal,kind,payload=payload);elapsed=time.perf_counter_ns()-t0
   counters={"scale":{str(k):int(v) for k,v in dict(audit.scale_audit_snapshot()).items()},"per_rule":[[int(i),str(m),int(v)] for i,m,v in audit.scale_audit_per_rule_snapshot()]}
  finally:audit.scale_audit_set_per_rule_enabled(False);audit.scale_audit_set_enabled(False)
  ctx.setdefault("producer_work",[]).append({"thread":threading.current_thread().name,"kind":kind,"goal_id":nid(goal),"event_id":nid(event) if event is not None else None,"elapsed_ns":elapsed,"counters":counters})
  tname=threading.current_thread().name
  if kind=="selection" and tname=="request-A":
   ctx["a_message"]=inbound;ctx["a_goal"]=goal;st=agent.s.node(inbound)["attrs"]["discourse_state_id"]
   ctx["a_pause"]=project(agent,st,goal);a_selected.set()
   if not release_a.wait(45):ctx["errors"].append("A barrier timeout")
  elif kind=="selection" and tname=="request-B":
   b_selected.set();ctx["b_message"]=inbound;ctx["b_goal"]=goal
  elif kind=="action_result" and tname=="request-B":
   ctx["b_result_goal"]=goal;ctx["b_completed_before_release"]=not release_a.is_set();b_completed.set();release_a.set()
  return event
 ca._record_live_goal_event=wrapped
 replies={}
 def call(label):
  try:
   if label=="B":b_started.set()
   wall0=time.perf_counter_ns();cpu0=time.thread_time_ns()
   replies[label]=a.converse("describe what you see",speech_act="instruction",speaker="alice")
   ctx["timings"][label]={"wall_ns":time.perf_counter_ns()-wall0,"thread_cpu_ns":time.thread_time_ns()-cpu0}
  except BaseException as e:ctx["errors"].append({"thread":label,"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()})
 A=threading.Thread(target=call,args=("A",),name="request-A");A.start()
 if not a_selected.wait(45):ctx["errors"].append("A selection timeout")
 B=threading.Thread(target=call,args=("B",),name="request-B");B.start()
 lock_attempted.wait(10);b_was_serialized=lock_attempted.is_set() and not b_selected.is_set();release_a.set()
 A.join(90);B.join(90);release_a.set();ca._record_live_goal_event=original
 if trace_enabled:a.inner.runtime_access_trace_set_enabled(False)
 observed_lock.trace_enabled=False
 alive=A.is_alive() or B.is_alive()
 if alive:ctx["errors"].append("thread join timeout")
 am=ctx.get("a_message");bm=ctx.get("b_message");st=a.s.node(am)["attrs"].get("discourse_state_id") if am is not None else None
 ag=[g for g in a.s.nodes("Goal") if am is not None and am in a.inner.neighbours(g,"comprehends")]
 bg=[g for g in a.s.nodes("Goal") if bm is not None and bm in a.inner.neighbours(g,"comprehends")]
 es=list(a.inner.neighbours(st,"has_event")) if st is not None else [];es.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
 event_rows=[{"kind":a.s.node(e)["attrs"].get("kind"),"for_goal_ids":[nid(g) for g in a.inner.neighbours(e,"for_goal")]} for e in es]
 final={"a":[project(a,st,g) for g in ag],"b":[project(a,st,g) for g in bg]}
 event_order=[x["kind"] for x in event_rows]==["instruction","selection","execution","action_result","instruction","selection","execution","action_result"]
 identity=(len(ag)==1 and len(bg)==1 and ag[0]!=bg[0] and final["a"][0]["message_ids"]==[nid(am)] and final["b"][0]["message_ids"]==[nid(bm)] and final["a"][0]["origin_ids"]==[nid(a.s.node(am)["attrs"]["discourse_event_id"])] and final["b"][0]["origin_ids"]==[nid(a.s.node(bm)["attrs"]["discourse_event_id"])])
 lifecycle=identity and all(final[k][0]["transition_kinds"]==["selection","execution","action_result"] and final[k][0]["status"]=="resolved" and final[k][0]["closed"] and not final[k][0]["active"] and final[k][0]["child_count"]==3 for k in ("a","b"))
 pause=ctx.get("a_pause",{}).get("status")=="selected" and ctx.get("a_pause",{}).get("active") and not ctx.get("a_pause",{}).get("closed")
 parity=all(str(replies.get(k))==BASELINE for k in ("A","B"))
 trace_events,trace_dropped=a.inner.runtime_access_trace_snapshot()
 access=a.inner.rule_access_sets();rule_names={int(a.inner.rule_metadata(int(row[0]))["rule_uid"]):str(row[1]) for row in access}
 trace_rows=[]
 for request_name,request in ctx["request_traces"].items():
  for row in request["event_rows"]:trace_rows.append({**row,"rule_name":rule_names.get(row["rule_uid"]),"request":request_name})
 a_owned=scene_task_nodes(a,am,ag) if am is not None else set();b_owned=scene_task_nodes(a,bm,bg) if bm is not None else set();complete_graph=a.s.graph_to_dict()
 task_boundaries={"a":boundary_projection(complete_graph,a_owned),"b":boundary_projection(complete_graph,b_owned),"pair":paired_boundary(complete_graph,a_owned,b_owned),"whole_graph_node_count":len(complete_graph.get("nodes",[])),"whole_graph_edge_count":len(complete_graph.get("edges",[]))}
 graph_sha=semantic_graph_digest(complete_graph);raw_graph_sha=hashlib.sha256(json.dumps(complete_graph,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
 trace_dropped=sum(r["dropped"] for r in ctx["request_traces"].values())
 return {"replicate":rep,"trace_enabled":trace_enabled,"pid":os.getpid(),"boot_ns":boot_ns,"worker_started_inputs":started,"worker_finished_inputs":lock_inputs(),"errors":ctx["errors"],"b_completed_while_a_blocked":ctx.get("b_completed_before_release",False),"b_was_serialized":b_was_serialized,"a_pause":ctx.get("a_pause"),"final":final,"event_rows":event_rows,"producer_work":ctx.get("producer_work",[]),"replies":{k:str(v) for k,v in replies.items()},"call_timings":ctx["timings"],"event_order_gate":event_order,"identity_gate":identity,"lifecycle_gate":lifecycle,"pause_gate":bool(pause),"reply_parity":parity,"threads_joined":not alive,"whole_graph_semantic_sha256":graph_sha,"whole_graph_raw_sha256":raw_graph_sha,"task_boundaries":task_boundaries,"request_traces":ctx["request_traces"],"access_trace":{"event_rows":trace_rows,"distinct_event_rows":len(trace_rows),"event_count":sum(r["count"] for r in trace_rows),"dropped":int(trace_dropped),"rules_observed":sorted({r["rule_uid"] for r in trace_rows}),"owned_node_event_counts":{"a":sum(r["count"] for r in trace_rows if r["node"] in a_owned or r["peer"] in a_owned),"b":sum(r["count"] for r in trace_rows if r["node"] in b_owned or r["peer"] in b_owned)}}}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==4 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),sys.argv[3]=="traced"),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260926).shuffle(jobs);runs=[]
 arms=[(rep,traced) for rep in jobs for traced in (True,False)];random.Random(20260927).shuffle(arms)
 for rep,traced in arms:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep),"traced" if traced else "untraced"],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=lock_inputs();pairs={rep:{r["trace_enabled"]:r for r in runs if r["replicate"]==rep} for rep in jobs}
 semantic_keys=("replies","event_rows","final","event_order_gate","identity_gate","lifecycle_gate","pause_gate","reply_parity","whole_graph_semantic_sha256","task_boundaries")
 checks={"three_paired_replicates_and_six_processes":len(runs)==6 and len({r["pid"] for r in runs})==6 and all(set(p)=={True,False} for p in pairs.values()),"all_threads_joined_without_errors":all(r["threads_joined"] and not r["errors"] for r in runs),"source_stable_workers_and_postrun":post==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),"schedule_and_lifecycle_gates_both_arms":all(r["b_was_serialized"] and r["pause_gate"] and not r["b_completed_while_a_blocked"] and r["event_order_gate"] and r["identity_gate"] and r["lifecycle_gate"] and r["reply_parity"] for r in runs),"whole_graph_and_semantic_parity_within_pairs":all(all(pairs[rep][True][k]==pairs[rep][False][k] for k in semantic_keys) for rep in jobs),"per_request_trace_intervals_complete":all(set(r["request_traces"])==({"request-A","request-B"} if r["trace_enabled"] else set()) and (not r["trace_enabled"] or all(x["event_count"]>0 and x["dropped"]==0 for x in r["request_traces"].values())) for r in runs),"untraced_arms_emit_no_access_events":all(not r["access_trace"]["event_rows"] and r["access_trace"]["event_count"]==0 for r in runs if not r["trace_enabled"]),"traced_trace_totals_reconcile":all(r["access_trace"]["event_count"]==sum(x["event_count"] for x in r["request_traces"].values()) for r in runs if r["trace_enabled"])}
 raw={"run_id":"substrate-live-describe-scene-access-trace-v2-workers-20260926","locked_inputs":locked,"runs":runs}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True,default=str)+"\n")
 traced=[r for r in runs if r["trace_enabled"]];untraced=[r for r in runs if not r["trace_enabled"]];call_summary={}
 for request_name,call_label in (("request-A","A"),("request-B","B")):
  call_summary[request_name]={"traced_wall_median_ns":statistics.median(r["call_timings"][call_label]["wall_ns"] for r in traced),"untraced_wall_median_ns":statistics.median(r["call_timings"][call_label]["wall_ns"] for r in untraced),"traced_thread_cpu_median_ns":statistics.median(r["call_timings"][call_label]["thread_cpu_ns"] for r in traced),"untraced_thread_cpu_median_ns":statistics.median(r["call_timings"][call_label]["thread_cpu_ns"] for r in untraced),"trace_event_count_median":statistics.median(r["request_traces"][request_name]["event_count"] for r in traced),"trace_wall_interval_median_ns":statistics.median(r["request_traces"][request_name]["wall_ns"] for r in traced),"trace_cpu_interval_median_ns":statistics.median(r["request_traces"][request_name]["thread_cpu_ns"] for r in traced)}
 payload={"schema_version":1,"run_id":"substrate-live-describe-scene-access-trace-v2-20260926","claim_boundary":"Three paired traced/untraced replicates preserve exact replies, lifecycle, task boundaries and whole-graph digest under the same authored concurrent schedule. Native access trace rows are partial and only cover selected operations inside each serialized request lock interval. Three pairs give a fixture-specific instrumentation and per-request work estimate, not general overhead, full access coverage, natural-task prevalence or tractability evidence.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"schedule":jobs,"checks":checks,"summary":{"paired_replicates":len(jobs),"worker_processes":len(runs),"boot_ns_median":statistics.median(r["boot_ns"] for r in runs),"per_request":call_summary,"trace_dropped_total":sum(r["access_trace"]["dropped"] for r in traced)},"raw_workers_path":str(RAW.relative_to(ROOT)),"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"raw_workers":str(RAW),"checks":checks,"summary":payload["summary"]},indent=2))
 if not all(checks.values()):raise SystemExit("paired describe-scene access-trace gate failed")
if __name__=="__main__":main()
