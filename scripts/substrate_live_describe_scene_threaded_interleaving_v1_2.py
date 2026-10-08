#!/usr/bin/env python3
"""Measure two concurrent live describe requests on one WorldAdapter."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,threading,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_PREREG_20260926.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_V1_2_AMENDMENT_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py","conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py","reflective_faculty":ROOT/"domains/reflective_faculty.py","arc_self_report":ROOT/"scripts/arc_self_report.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json","native_py":ROOT/"runners/dsl/src/py.rs"}
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_threaded_interleaving_v1_2_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_2_20260926.json"
BASELINE="I see the grey thing stays, the yellow counter, and the blue thing moves."
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,"value") else x)
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"amendment_sha256":sha(AMENDMENT),"runner_sha256":sha(__file__),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def project(a,st,g):
 tr=list(a.inner.neighbours(g,"transitioned_by"));tr.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
 return {"goal_id":nid(g),"status":a.s.node(g)["attrs"].get("lifecycle_status"),"message_ids":[nid(x) for x in a.inner.neighbours(g,"comprehends")],"origin_ids":[nid(x) for x in a.inner.neighbours(g,"originated_in")],"transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in tr],"transition_event_ids":[nid(e) for e in tr],"child_count":len(list(a.inner.neighbours(g,"has_subgoal"))),"active":g in a.inner.neighbours(st,"has_active_goal"),"closed":g in a.inner.neighbours(st,"has_closed_goal")}
class ObservedLock:
 def __init__(self,inner,attempted):self.inner=inner;self.attempted=attempted
 def __enter__(self):
  if threading.current_thread().name=="request-B":self.attempted.set()
  self.inner.acquire();return self
 def __exit__(self,*exc):self.inner.release();return False
def worker(rep):
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains.conversation_action import attach_scene
 import domains.conversation_action as ca
 a=WorldAdapter(seeds=());t0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-t0
 lock_attempted=threading.Event();a._conversation_lock=ObservedLock(a._conversation_lock,lock_attempted)
 attach_scene(a,[{"kind":"static","colour":"grey"},{"kind":"meter","colour":"yellow"},{"kind":"mover","colour":"blue","responds_to_my_action":False}])
 a_selected=threading.Event();release_a=threading.Event();b_started=threading.Event();b_selected=threading.Event();b_completed=threading.Event();ctx={"errors":[],"timings":{}}
 original=ca._record_live_goal_event
 def wrapped(agent,inbound,goal,kind,*,payload=None):
  event=original(agent,inbound,goal,kind,payload=payload)
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
   replies[label]=a.converse("describe what you see",speech_act="instruction",speaker="alice")
  except BaseException as e:ctx["errors"].append({"thread":label,"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()})
 A=threading.Thread(target=call,args=("A",),name="request-A");A.start()
 if not a_selected.wait(45):ctx["errors"].append("A selection timeout")
 B=threading.Thread(target=call,args=("B",),name="request-B");B.start()
 lock_attempted.wait(10);b_was_serialized=lock_attempted.is_set() and not b_selected.is_set();release_a.set()
 A.join(90);B.join(90);release_a.set();ca._record_live_goal_event=original
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
 return {"replicate":rep,"pid":os.getpid(),"boot_ns":boot_ns,"worker_started_inputs":started,"worker_finished_inputs":lock_inputs(),"errors":ctx["errors"],"b_completed_while_a_blocked":ctx.get("b_completed_before_release",False),"b_was_serialized":b_was_serialized,"a_pause":ctx.get("a_pause"),"final":final,"event_rows":event_rows,"replies":{k:str(v) for k,v in replies.items()},"event_order_gate":event_order,"identity_gate":identity,"lifecycle_gate":lifecycle,"pause_gate":bool(pause),"reply_parity":parity,"threads_joined":not alive}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260926).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=lock_inputs();checks={"three_distinct_processes":len(runs)==3 and len({r["pid"] for r in runs})==3,"all_threads_joined_without_errors":all(r["threads_joined"] and not r["errors"] for r in runs),"source_stable_workers_and_postrun":post==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),"B_serialized_until_A_finishes":all(r["b_was_serialized"] and r["pause_gate"] and not r["b_completed_while_a_blocked"] for r in runs),"event_order_and_identity":all(r["event_order_gate"] and r["identity_gate"] and r["lifecycle_gate"] for r in runs),"baseline_reply_parity":all(r["reply_parity"] for r in runs),"normalized_shape_repeats":len({json.dumps({k:r[k] for k in ("event_order_gate","identity_gate","lifecycle_gate","pause_gate","reply_parity")},sort_keys=True) for r in runs})==1}
 payload={"schema_version":1,"run_id":"substrate-live-describe-scene-threaded-interleaving-v1_2-20260926","claim_boundary":"Two live threads on one WorldAdapter overlap with B completing while A waits after selection; ownership and terminal lifecycle are measured. This is controlled route-specific concurrency, not arbitrary adapter/thread safety.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"schedule":jobs,"checks":checks,"summary":{"replicates":len(runs),"boot_ns_median":statistics.median(r["boot_ns"] for r in runs)},"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"summary":payload["summary"]},indent=2))
 if not checks["three_distinct_processes"] or not checks["source_stable_workers_and_postrun"]:raise SystemExit("threaded capture validity failed")
if __name__=="__main__":main()
