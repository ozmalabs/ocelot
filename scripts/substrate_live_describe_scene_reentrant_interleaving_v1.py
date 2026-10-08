#!/usr/bin/env python3
"""Exercise live describe-scene reentrancy between selection and execution."""
from __future__ import annotations
import hashlib, json, os, platform, random, statistics, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_DESCRIBE_SCENE_REENTRANT_INTERLEAVING_PREREG_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py",
 "reflective_faculty":ROOT/"domains/reflective_faculty.py","arc_self_report":ROOT/"scripts/arc_self_report.py",
 "discourse_seed":ROOT/"seeds/conversation_discourse_state.json"}
LOCK=ROOT/"evaluation/substrate_capability/live_describe_scene_reentrant_interleaving_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_describe_scene_reentrant_interleaving_v1_20260926.json"
BASELINE="I see the grey thing stays, the yellow counter, and the blue thing moves."
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x): return int(x.value if hasattr(x,"value") else x)
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def project(a,state,goal):
 es=list(a.inner.neighbours(goal,"transitioned_by"));es.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
 return {"goal_id":nid(goal),"status":a.s.node(goal)["attrs"].get("lifecycle_status"),
  "origin_ids":[nid(x) for x in a.inner.neighbours(goal,"originated_in")],"message_ids":[nid(x) for x in a.inner.neighbours(goal,"comprehends")],
  "transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in es],"child_count":len(list(a.inner.neighbours(goal,"has_subgoal"))),
  "active":goal in a.inner.neighbours(state,"has_active_goal"),"closed":goal in a.inner.neighbours(state,"has_closed_goal")}
def worker(rep):
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains.conversation_action import attach_scene
 import domains.conversation_action as ca
 a=WorldAdapter(seeds=());t0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-t0
 attach_scene(a,[{"kind":"static","colour":"grey"},{"kind":"meter","colour":"yellow"},{"kind":"mover","colour":"blue","responds_to_my_action":False}])
 original=ca._record_live_goal_event;ctx={"triggered":False};nested_ns=[]
 def wrapped(agent,inbound,goal,kind,*,payload=None):
  event=original(agent,inbound,goal,kind,payload=payload)
  if kind=="selection" and not ctx["triggered"]:
   ctx["triggered"]=True;ctx["a_message"]=inbound;ctx["a_goal"]=goal
   st=agent.s.node(inbound)["attrs"]["discourse_state_id"]
   ctx["a_pause"]=project(agent,st,goal)
   t=time.perf_counter_ns();ctx["b_reply"]=agent.converse("describe what you see",speech_act="instruction",speaker="alice");nested_ns.append(time.perf_counter_ns()-t)
   ctx["b_message"]=agent._last_turn_inbound
   bg=[g for g in agent.s.nodes("Goal") if ctx["b_message"] in agent.inner.neighbours(g,"comprehends")]
   ctx["b_goals"]=bg
   ctx["after_b"]={"a":project(agent,st,goal),"b":[project(agent,st,g) for g in bg]}
  return event
 ca._record_live_goal_event=wrapped
 t0=time.perf_counter_ns()
 try: a_reply=a.converse("describe what you see",speech_act="instruction",speaker="alice")
 finally: ca._record_live_goal_event=original
 a_ns=time.perf_counter_ns()-t0
 am=ctx.get("a_message");bm=ctx.get("b_message");state=a.s.node(am)["attrs"].get("discourse_state_id") if am is not None else None
 ag=[g for g in a.s.nodes("Goal") if am is not None and am in a.inner.neighbours(g,"comprehends")]
 bg=[g for g in a.s.nodes("Goal") if bm is not None and bm in a.inner.neighbours(g,"comprehends")]
 final={"a":[project(a,state,g) for g in ag],"b":[project(a,state,g) for g in bg]}
 es=list(a.inner.neighbours(state,"has_event")) if state is not None else [];es.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
 event_rows=[{"kind":a.s.node(e)["attrs"].get("kind"),"for_goal_ids":[nid(g) for g in a.inner.neighbours(e,"for_goal")]} for e in es]
 order=[("instruction",[]),("selection",[nid(ctx["a_goal"])]),("instruction",[]),
  ("selection",[nid(bg[0])] if len(bg)==1 else []),("execution",[nid(bg[0])] if len(bg)==1 else []),
  ("action_result",[nid(bg[0])] if len(bg)==1 else []),("execution",[nid(ctx["a_goal"])]),("action_result",[nid(ctx["a_goal"])])]
 observed=[(x["kind"],x["for_goal_ids"]) for x in event_rows]
 pause=ctx.get("a_pause",{});after=ctx.get("after_b",{})
 paused=(pause.get("status")=="selected" and pause.get("active") and not pause.get("closed")
  and after.get("a",{}).get("status")=="selected" and after.get("a",{}).get("active")
  and len(after.get("b",[]))==1 and after["b"][0]["status"]=="resolved" and after["b"][0]["closed"] and not after["b"][0]["active"]
  and len(final["a"])==1 and final["a"][0]["status"]=="resolved" and final["a"][0]["closed"] and not final["a"][0]["active"])
 identity=(len(ag)==1 and len(bg)==1 and ag[0]!=bg[0]
  and final["a"][0]["message_ids"]==[nid(am)] and final["b"][0]["message_ids"]==[nid(bm)]
  and final["a"][0]["origin_ids"]==[nid(a.s.node(am)["attrs"]["discourse_event_id"])]
  and final["b"][0]["origin_ids"]==[nid(a.s.node(bm)["attrs"]["discourse_event_id"])]
  and final["a"][0]["transition_kinds"]==["selection","execution","action_result"]
  and final["b"][0]["transition_kinds"]==["selection","execution","action_result"]
  and final["a"][0]["child_count"]==3 and final["b"][0]["child_count"]==3)
 return {"replicate":rep,"pid":os.getpid(),"boot_ns":boot_ns,"a_ns":a_ns,"b_reentrant_ns":nested_ns[0] if nested_ns else None,
  "a_reply":str(a_reply),"b_reply":str(ctx.get("b_reply")),"reply_parity":str(a_reply)==BASELINE and str(ctx.get("b_reply"))==BASELINE,
  "event_rows":event_rows,"a_pause":pause,"after_b":after,"final":final,"event_order_gate":observed==order,
  "identity_gate":identity,"pause_state_gate":bool(paused),"worker_started_inputs":started,"worker_finished_inputs":lock_inputs()}
def main():
 if sys.argv[1:]==["--lock"]: print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker": print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked: raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260926).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=lock_inputs();checks={"three_fresh_processes":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "source_stable_workers_and_postrun":post==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
  "live_event_order_reentrant":all(r["event_order_gate"] for r in runs),"identity_and_lifecycle_pause_gates":all(r["identity_gate"] and r["pause_state_gate"] for r in runs),
  "reply_parity":all(r["reply_parity"] for r in runs),"normalized_shape_repeats":len({json.dumps({k:r[k] for k in ("event_order_gate","identity_gate","pause_state_gate","reply_parity")},sort_keys=True) for r in runs})==1}
 payload={"schema_version":1,"run_id":"substrate-live-describe-scene-reentrant-interleaving-v1-20260926","claim_boundary":"Same-thread reentrant calls on one live WorldAdapter preserve Goal ownership and lifecycle while request B completes during request A's selected/active interval. Not threaded concurrency.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"schedule":jobs,"checks":checks,"summary":{"replicates":len(runs),"boot_ns_median":statistics.median(r["boot_ns"] for r in runs),"a_ns_median":statistics.median(r["a_ns"] for r in runs),"b_reentrant_ns_median":statistics.median(r["b_reentrant_ns"] for r in runs)},"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"summary":payload["summary"]},indent=2))
 if not all(checks.values()): raise SystemExit("reentrant live producer gate failed")
if __name__=="__main__": main()
