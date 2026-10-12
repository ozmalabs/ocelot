#!/usr/bin/env python3
"""Source-locked races through WorldAdapter's graph handles and public API."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,threading,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SHARED_NATIVE_FACADE_SERIALIZATION_V1_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py","conversation_action":ROOT/"domains/conversation_action.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json","native_py":ROOT/"runners/dsl/src/py.rs"}
LOCK=ROOT/"evaluation/substrate_capability/shared_native_facade_serialization_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_shared_native_facade_serialization_v1_20260926.json"
BASELINE="I see the grey thing stays, the yellow counter, and the blue thing moves."
OPS=("adapter_tick","inner_node","s_node","s_inner_node","second_facade_node")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def goal_projection(agent,st,goal):
 events=list(agent.inner.neighbours(goal,"transitioned_by"));events.sort(key=lambda e:int(agent.s.node(e)["attrs"].get("event_index",-1)))
 return {"goal_id":int(goal.value),"status":agent.s.node(goal)["attrs"].get("lifecycle_status"),"message_ids":[int(x.value) for x in agent.inner.neighbours(goal,"comprehends")],"origin_ids":[int(x.value) for x in agent.inner.neighbours(goal,"originated_in")],"transition_kinds":[agent.s.node(e)["attrs"].get("kind") for e in events],"active":goal in agent.inner.neighbours(st,"has_active_goal"),"closed":goal in agent.inner.neighbours(st,"has_closed_goal"),"child_count":len(list(agent.inner.neighbours(goal,"has_subgoal")))}
class ObservedRLock:
 def __init__(self,inner,attempted,entered):self.inner=inner;self.attempted=attempted;self.entered=entered
 def __enter__(self):
  name=threading.current_thread().name
  if name in self.attempted:self.attempted[name].set()
  self.inner.acquire()
  if name in self.entered:self.entered[name].set()
  return self
 def __exit__(self,*exc):self.inner.release();return False
def worker(rep):
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter, _AdapterNativeFacade
 from substrate.boot_all import load_all_seeds
 from domains.conversation_action import attach_scene
 import domains.conversation_action as ca
 agent=WorldAdapter(seeds=());load_all_seeds(agent)
 attach_scene(agent,[{"kind":"static","colour":"grey"},{"kind":"meter","colour":"yellow"},{"kind":"mover","colour":"blue","responds_to_my_action":False}])
 second_facade=_AdapterNativeFacade(agent.inner._native)
 same_lock_initially=second_facade._lock is agent._conversation_lock
 names={"race-"+op for op in OPS};attempted={n:threading.Event() for n in names};entered={n:threading.Event() for n in names}
 observed_lock=ObservedRLock(agent._conversation_lock,attempted,entered)
 agent._conversation_lock=observed_lock
 agent.inner._lock=observed_lock
 second_facade._lock=observed_lock
 selected=threading.Event();release=threading.Event();ctx={"errors":[],"operations":{}}
 original=ca._record_live_goal_event
 def record(a,inbound,goal,kind,*,payload=None):
  result=original(a,inbound,goal,kind,payload=payload)
  if kind=="selection" and threading.current_thread().name=="request-A":
   ctx["message"]=inbound;ctx["goal"]=goal;ctx["pause_status"]=a.s.node(goal)["attrs"].get("lifecycle_status");selected.set()
   if not release.wait(60):ctx["errors"].append("A barrier timeout")
  return result
 ca._record_live_goal_event=record
 def conversation():
  try:ctx["reply"]=agent.converse("describe what you see",speech_act="instruction",speaker="alice")
  except BaseException as exc:ctx["errors"].append({"thread":"A","type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()})
 def operation(op):
  try:
   if op=="adapter_tick":value=agent.tick()
   elif op=="inner_node":value=agent.inner.node(agent.agent)
   elif op=="s_node":value=agent.s.node(agent.agent)
   elif op=="s_inner_node":value=agent.s._inner.node(agent.agent)
   else:value=second_facade.node(agent.agent)
   ctx["operations"][op]=(int(value) if isinstance(value,int) else value.get("type"))
  except BaseException as exc:ctx["errors"].append({"thread":op,"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()})
 A=threading.Thread(target=conversation,name="request-A");A.start()
 if not selected.wait(60):ctx["errors"].append("A selection timeout")
 racers=[threading.Thread(target=operation,args=(op,),name="race-"+op) for op in OPS]
 for t in racers:t.start()
 all_attempted=all(attempted[n].wait(15) for n in names)
 none_entered_early=all(not entered[n].is_set() for n in names)
 pause_gate=ctx.get("pause_status")=="selected" and all_attempted and none_entered_early
 release.set();A.join(90)
 for t in racers:t.join(90)
 ca._record_live_goal_event=original
 joined=not A.is_alive() and all(not t.is_alive() for t in racers)
 mid=ctx.get("message");goal=ctx.get("goal");state=agent.s.node(mid)["attrs"].get("discourse_state_id") if mid is not None else None
 goals=[g for g in agent.s.nodes("Goal") if mid is not None and mid in agent.inner.neighbours(g,"comprehends")]
 events=list(agent.inner.neighbours(state,"has_event")) if state is not None else [];events.sort(key=lambda e:int(agent.s.node(e)["attrs"].get("event_index",-1)))
 kinds=[agent.s.node(e)["attrs"].get("kind") for e in events]
 lifecycle=(len(goals)==1 and goals[0]==goal and goal_projection(agent,state,goal)["status"]=="resolved" and goal_projection(agent,state,goal)["closed"] and not goal_projection(agent,state,goal)["active"] and goal_projection(agent,state,goal)["transition_kinds"]==["selection","execution","action_result"] and goal_projection(agent,state,goal)["child_count"]==3)
 identity=(len(goals)==1 and goal_projection(agent,state,goal)["message_ids"]==[int(mid.value)] and goal_projection(agent,state,goal)["origin_ids"]==[int(agent.s.node(mid)["attrs"]["discourse_event_id"].value)])
 stable=lock_inputs()
 return {"replicate":rep,"pid":os.getpid(),"worker_started_inputs":started,"worker_finished_inputs":stable,"errors":ctx["errors"],"attempted":{k:v.is_set() for k,v in attempted.items()},"entered":{k:v.is_set() for k,v in entered.items()},"pause_gate":pause_gate,"joined":joined,"operations":ctx["operations"],"operation_set_complete":set(ctx["operations"])==set(OPS),"second_facade_initial_shared_lock":same_lock_initially,"conversation_reply":str(ctx.get("reply")),"reply_parity":str(ctx.get("reply"))==BASELINE,"event_kinds":kinds,"event_order_gate":kinds==["instruction","selection","execution","action_result"],"identity_gate":identity,"lifecycle_gate":lifecycle}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260926).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=lock_inputs();checks={"three_distinct_processes":len({r["pid"] for r in runs})==3,"sources_stable":post==locked and all(r["worker_started_inputs"]==locked==r["worker_finished_inputs"] for r in runs),"all_five_contenders_wait_then_enter":all(r["pause_gate"] and all(r["attempted"].values()) and all(r["entered"].values()) for r in runs),"facades_share_lock_identity":all(r["second_facade_initial_shared_lock"] for r in runs),"conversation_reply_and_lifecycle":all(r["reply_parity"] and r["event_order_gate"] and r["identity_gate"] and r["lifecycle_gate"] for r in runs),"all_operations_and_threads_clean":all(r["operation_set_complete"] and r["joined"] and not r["errors"] for r in runs),"normalized_shape_repeats":len({json.dumps({k:r[k] for k in ("pause_gate","event_order_gate","identity_gate","lifecycle_gate","reply_parity","operation_set_complete")},sort_keys=True) for r in runs})==1}
 payload={"schema_version":1,"run_id":"substrate-shared-native-facade-serialization-v1-20260926","claim_boundary":"Five adapter graph-handle/public API calls, including a second facade around the same native substrate, contend with one live conversation. Raw handles retained before wrapping and external native callers remain outside this test.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"schedule":jobs,"checks":checks,"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not checks["three_distinct_processes"] or not checks["sources_stable"]:raise SystemExit("capture invalid")
if __name__=="__main__":main()
