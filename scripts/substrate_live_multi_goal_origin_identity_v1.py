#!/usr/bin/env python3
"""Measure Goal origin identity across two same-recipient live turns."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_MULTI_GOAL_ORIGIN_IDENTITY_PREREG_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","discourse_state":ROOT/"domains/discourse_state.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json",
 "phase4a_seed":ROOT/"seeds/conversation_deliberation_phase4a.json"}
LOCK=ROOT/"evaluation/substrate_capability/live_multi_goal_origin_identity_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_multi_goal_origin_identity_v1_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,"value") else x)
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),
  "source_sha256":{k:sha(p) for k,p in SOURCES.items()},
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def worker(rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());boot0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-boot0
 records=[];turn_total=0
 for i in range(2):
  before_events={nid(e) for e in a.s.nodes("DiscourseEvent")};before_goals={nid(g) for g in a.s.nodes("Goal")}
  t0=time.perf_counter_ns();reply=a.converse("Check the pressure.",speech_act="instruction",speaker="alice");turn_total+=time.perf_counter_ns()-t0
  message=a._last_turn_inbound;mid=nid(message);mattrs=a.s.node(message)["attrs"]
  event_id=mattrs.get("discourse_event_id");event=event_id if event_id is not None else None;eid=nid(event) if event is not None else None
  new_events=[e for e in a.s.nodes("DiscourseEvent") if nid(e) not in before_events]
  action_goals=[g for g in a.s.nodes("Goal") if nid(g) not in before_goals
    and a.s.node(g)["attrs"].get("source")=="conversation"]
  recipients=[nid(x) for x in a.inner.neighbours(event,"to_addressee")] if event is not None else []
  goal_rows=[]
  for g in action_goals:
   deliberations=[d for d in a.s.nodes("Deliberation") if g in a.inner.neighbours(d,"about_goal")]
   goal_rows.append({"goal_id":nid(g),"attrs":a.s.node(g)["attrs"],
    "comprehends_message":message in a.inner.neighbours(g,"comprehends"),
    "originates_in_event":event is not None and event in a.inner.neighbours(g,"originated_in"),
    "transition_events":[nid(x) for x in a.inner.neighbours(g,"transitioned_by")],
    "deliberations":[{"status":a.s.node(d)["attrs"].get("status"),"candidate_source":a.s.node(d)["attrs"].get("candidate_source")} for d in deliberations]})
  records.append({"turn":i,"reply":reply,"message_id":mid,"event_id":eid,
   "event_attrs":a.s.node(event)["attrs"] if event is not None else None,
   "event_for_goal_edges":[nid(x) for x in a.inner.neighbours(event,"for_goal")] if event is not None else [],
   "event_recipients":recipients,"new_discourse_event_count":len(new_events),"new_action_goal_count":len(action_goals),"goals":goal_rows})
 states={nid(st):st for st in a.s.nodes("DiscourseState")}
 state=a.s.node(a._last_turn_inbound)["attrs"].get("discourse_state_id")
 state_events=list(a.inner.neighbours(state,"has_event")) if state is not None else []
 kinds={k:sum(a.s.node(e)["attrs"].get("kind")==k for e in state_events) for k in ("instruction","selection","execution","action_result")}
 one_to_one=(len(records)==2 and all(r["event_id"] is not None and r["new_discourse_event_count"]==1 and r["new_action_goal_count"]==1 and len(r["goals"])==1 and r["goals"][0]["comprehends_message"] and r["goals"][0]["originates_in_event"] for r in records)
  and len({r["message_id"] for r in records})==2 and len({r["event_id"] for r in records})==2
  and len({r["goals"][0]["goal_id"] for r in records})==2)
 return {"replicate":rep,"pid":os.getpid(),"boot_ns":boot_ns,"turns_ns_total":turn_total,"turn_median_ns":turn_total/2,
  "records":records,"state_event_count":len(state_events),"state_event_kind_counts":kinds,
  "same_recipient":len(records)==2 and records[0]["event_recipients"]==records[1]["event_recipients"] and bool(records[0]["event_recipients"]),
  "one_to_one_origin_mapping":one_to_one,
  "no_lifecycle_events":all(kinds[k]==0 for k in ("selection","execution","action_result")),
  "no_goal_transitions":all(not row["goals"][0]["transition_events"] for row in records if row["goals"])}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260926).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 checks={"three_distinct_fresh_pids":len(runs)==3 and len({x["pid"] for x in runs})==3,
  "all_runs_one_to_one_origin_identity":all(x["one_to_one_origin_mapping"] for x in runs),
  "same_recipient_all_runs":all(x["same_recipient"] for x in runs),
  "no_downstream_lifecycle_events_or_transitions":all(x["no_lifecycle_events"] and x["no_goal_transitions"] for x in runs),
  "full_seed_producer_shape_repeats":len({json.dumps(x["records"],sort_keys=True) for x in runs})==1}
 payload={"schema_version":1,"run_id":"substrate-live-multi-goal-origin-identity-v1-20260926",
  "claim_boundary":"Three fresh full-seed runs show distinct same-recipient live instruction Goals bind to their own inbound Message and DiscourseEvent. No later lifecycle events are emitted on this path; no prevalence/general action claim.",
  "locked_inputs":locked,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},
  "schedule":jobs,"checks":checks,"summary":{"boot_ns_median":statistics.median(x["boot_ns"] for x in runs),
   "turn_median_ns_median":statistics.median(x["turn_median_ns"] for x in runs),
   "operation_event_counts":runs[0]["state_event_kind_counts"]},"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"summary":payload["summary"]},indent=2))
 if not all(checks.values()):raise SystemExit("live multi-Goal origin identity probe failed")
if __name__=="__main__":main()
