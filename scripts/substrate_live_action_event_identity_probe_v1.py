#!/usr/bin/env python3
"""Replicate event/Goal identity production on one live instruction turn."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_ACTION_EVENT_IDENTITY_PREREG_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","discourse_state":ROOT/"domains/discourse_state.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json",
 "phase4a_seed":ROOT/"seeds/conversation_deliberation_phase4a.json"}
LOCK=ROOT/"evaluation/substrate_capability/live_action_event_identity_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_action_event_identity_v1_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,"value") else x)
def lock_inputs():
 from substrate_rs import _native
 src={k:sha(p) for k,p in SOURCES.items()}
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_sha256":src,
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def worker(rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());boot0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-boot0
 pre_events={nid(n) for n in a.s.nodes("DiscourseEvent")};pre_goals={nid(n) for n in a.s.nodes("Goal")}
 turn0=time.perf_counter_ns();reply=a.converse("Check the pressure.",speech_act="instruction",speaker="alice");turn_ns=time.perf_counter_ns()-turn0
 mid=a._last_turn_inbound;mid_id=nid(mid);attrs=a.s.node(mid)["attrs"];state=attrs.get("discourse_state_id");event=attrs.get("discourse_event_id")
 event_id=nid(event) if event is not None else None
 new_events=[n for n in a.s.nodes("DiscourseEvent") if nid(n) not in pre_events]
 new_goals=[n for n in a.s.nodes("Goal") if nid(n) not in pre_goals]
 state_events=list(a.inner.neighbours(state,"has_event")) if state is not None else []
 event_kind_counts={kind:sum(a.s.node(e)["attrs"].get("kind")==kind for e in state_events)
  for kind in ("instruction","selection","execution","action_result")}
 goal_rows=[]
 for g in new_goals:
  gid=nid(g);linked=mid in a.inner.neighbours(g,"comprehends");origin=event is not None and event in a.inner.neighbours(g,"originated_in")
  transitions=[]
  for te in a.inner.neighbours(g,"transitioned_by"):
   ta=a.s.node(te)["attrs"];transitions.append({"event_id":nid(te),"kind":ta.get("kind"),"event_index":ta.get("event_index")})
  ds=[d for d in a.s.nodes("Deliberation") if g in a.inner.neighbours(d,"about_goal")]
  goal_rows.append({"goal_id":gid,"attrs":a.s.node(g)["attrs"],"comprehends_inbound":linked,
   "originated_in_inbound_event":origin,"transition_events":transitions,
   "deliberations":[{"id":nid(d),"status":a.s.node(d)["attrs"].get("status"),
    "candidate_source":a.s.node(d)["attrs"].get("candidate_source")} for d in ds]})
 return {"replicate":rep,"pid":os.getpid(),"reply":reply,"boot_ns":boot_ns,"turn_ns":turn_ns,
  "inbound_message_id":mid_id,"discourse_state_id":nid(state) if state is not None else None,
  "inbound_event_id":event_id,"new_discourse_events":[{"id":nid(e),"attrs":a.s.node(e)["attrs"],
   "for_goal_edges":[nid(g) for g in a.inner.neighbours(e,"for_goal")]} for e in new_events],
  "new_goal_count":len(new_goals),"new_goal_rows":goal_rows,"state_event_count":len(state_events),
  "state_event_kind_counts":event_kind_counts,
  "gates":{"one_instruction_event":len(new_events)==1 and event_id is not None
    and a.s.node(event)["attrs"].get("kind")=="instruction",
   "new_action_goal_bound_to_input":any(r["attrs"].get("source")=="conversation" and r["comprehends_inbound"] and r["originated_in_inbound_event"] for r in goal_rows),
   "no_operation_lifecycle_events":all(event_kind_counts[k]==0 for k in ("selection","execution","action_result")),
   "no_transition_by_operation_event":all(not row["transition_events"] for row in goal_rows)}}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260926).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  runs.append(json.loads(p.stdout))
 checks={"three_fresh_pids":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "all_worker_gates_pass":all(all(r["gates"].values()) for r in runs),
  "same_event_and_goal_shape":len({json.dumps({"event":r["new_discourse_events"],"goals":r["new_goal_rows"],"kinds":r["state_event_kind_counts"]},sort_keys=True) for r in runs})==1}
 payload={"schema_version":1,"run_id":"substrate-live-action-event-identity-v1-20260926",
  "claim_boundary":"One live full-seed instruction path, three fresh processes. Confirms that this path creates inbound event/Goal provenance but no selection/execution/action_result DiscourseEvents. Does not claim other producers are absent or assess task performance.",
  "locked_inputs":locked,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},
  "schedule":jobs,"checks":checks,"runs":runs,
  "summary":{"boot_ns_median":__import__("statistics").median(r["boot_ns"] for r in runs),
   "turn_ns_median":__import__("statistics").median(r["turn_ns"] for r in runs),
   "operation_event_counts":runs[0]["state_event_kind_counts"],"new_goal_count":runs[0]["new_goal_count"]}}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n")
 print(json.dumps({"output":str(OUT),"checks":checks,"summary":payload["summary"]},indent=2))
 if not all(checks.values()):raise SystemExit("live event identity probe failed; raw report preserved")
if __name__=="__main__":main()
