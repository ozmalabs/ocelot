#!/usr/bin/env python3
"""Measure native Goal ownership under interleaved lifecycle events."""
from __future__ import annotations
import hashlib, json, os, platform, random, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_NATIVE_GOAL_LIFECYCLE_INTERLEAVING_PREREG_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py",
 "discourse_state":ROOT/"domains/discourse_state.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json"}
LOCK=ROOT/"evaluation/substrate_capability/native_goal_lifecycle_interleaving_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_native_goal_lifecycle_interleaving_v1_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,"value") else x)
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def boot():
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());load_all_seeds(a);return a
def fixture(a,label):
 from domains.discourse_state import ensure_discourse_state,record_event,open_goal
 user=a.attach_chat_world("interleave_"+label)["interlocutor"]
 st=ensure_discourse_state(a,conversation_id="interleave_"+label,addressee=user)
 origins=[record_event(a,st,kind="request",speaker=user,addressee=a.agent,payload={"task":x}) for x in ("A","B")]
 goals=[open_goal(a,st,kind="interleave_"+x,origin_event=origins[i],addressee=user) for i,x in enumerate(("A","B"))]
 return st,origins,goals
def projection(a,st,goals):
 out=[]
 for g in goals:
  events=list(a.inner.neighbours(g,"transitioned_by"));events.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
  out.append({"goal_id":nid(g),"status":a.s.node(g)["attrs"].get("lifecycle_status"),
   "transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in events],
   "active":g in a.inner.neighbours(st,"has_active_goal"),"closed":g in a.inner.neighbours(st,"has_closed_goal")})
 return out
def worker(rep):
 started=lock_inputs()
 from domains.discourse_state import record_event
 a=boot();st,origins,goals=fixture(a,"main_"+str(rep))
 schedule=[(0,"selection"),(1,"selection"),(1,"execution"),(0,"execution"),(0,"action_result"),(1,"action_result")]
 checkpoints=[]
 for owner,kind in schedule:
  e=record_event(a,st,kind=kind,speaker=a.agent,goal=goals[owner],payload={"declared_owner":nid(goals[owner])});a.inner.run_rules()
  checkpoints.append({"kind":kind,"owner_goal_id":nid(goals[owner]),"event_id":nid(e),
   "for_goal_ids":[nid(g) for g in a.inner.neighbours(e,"for_goal")],"goals":projection(a,st,goals)})
 expected=[["selected","proposed"],["selected","selected"],["selected","executing"],
  ["executing","executing"],["resolved","executing"],["resolved","resolved"]]
 positive=len(checkpoints)==6 and all(cp["for_goal_ids"]==[cp["owner_goal_id"]] and [g["status"] for g in cp["goals"]]==expected[i] for i,cp in enumerate(checkpoints))
 positive=positive and all(checkpoints[-1]["goals"][i]["closed"] and not checkpoints[-1]["goals"][i]["active"] for i in (0,1))
 ms,mo,mg=fixture(a,"missing_"+str(rep));me=record_event(a,ms,kind="selection",speaker=a.agent,payload={"declared_owner":nid(mg[0])});a.inner.run_rules()
 missing={"for_goal_ids":[nid(g) for g in a.inner.neighbours(me,"for_goal")],"goals":projection(a,ms,mg)}
 xs,xo,xg=fixture(a,"ambiguous_"+str(rep));ae=record_event(a,xs,kind="selection",speaker=a.agent,goal=xg[0],payload={"declared_owner":nid(xg[0])})
 a.inner.add_edge_unchecked(ae,"for_goal",xg[1]);a.inner.run_rules()
 ambiguous={"for_goal_ids":[nid(g) for g in a.inner.neighbours(ae,"for_goal")],"goals":projection(a,xs,xg)}
 return {"replicate":rep,"pid":os.getpid(),"worker_started_inputs":started,"worker_finished_inputs":lock_inputs(),
  "checkpoints":checkpoints,"positive_identity_gate":positive,"missing_owner":missing,"ambiguous_owner":ambiguous}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260926).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=lock_inputs();valid=len(runs)==3 and len({r["pid"] for r in runs})==3 and post==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked and len(r["checkpoints"])==6 for r in runs)
 checks={"capture_valid":valid,"interleaved_explicit_owner_oracle":all(r["positive_identity_gate"] for r in runs),
  "missing_owner_rejected":all(not r["missing_owner"]["for_goal_ids"] and all(g["status"]=="proposed" for g in r["missing_owner"]["goals"]) for r in runs),
  "ambiguous_owner_rejected":all(len(r["ambiguous_owner"]["for_goal_ids"])==2 and all(g["status"]=="proposed" for g in r["ambiguous_owner"]["goals"]) for r in runs)}
 payload={"schema_version":1,"run_id":"substrate-native-goal-lifecycle-interleaving-v1-20260926","claim_boundary":"Explicit owner identity is measured under interleaved native lifecycle events. Missing and ambiguous owner semantics are separate. Not thread concurrency or production scheduler evidence.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"schedule":jobs,"checks":checks,"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not valid:raise SystemExit("capture validity failed")
if __name__=="__main__":main()
