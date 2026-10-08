#!/usr/bin/env python3
"""Probe live held self-report origin and lifecycle-event production."""
from __future__ import annotations
import hashlib, json, os, platform, random, statistics, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_PRODUCER_PREREG_20260926.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_PRODUCER_V1_1_AMENDMENT_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py",
 "discourse_state":ROOT/"domains/discourse_state.py",
 "conversation_action":ROOT/"domains/conversation_action.py",
 "reflective_faculty":ROOT/"domains/reflective_faculty.py",
 "self_model":ROOT/"domains/self_model.py",
 "discourse_seed":ROOT/"seeds/conversation_discourse_state.json"}
LOCK=ROOT/"evaluation/substrate_capability/live_self_report_lifecycle_producer_v1_1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_self_report_lifecycle_producer_v1_1_20260926.json"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x): return int(x.value if hasattr(x,"value") else x)
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"amendment_sha256":sha(AMENDMENT),"runner_sha256":sha(__file__),
  "source_sha256":{k:sha(p) for k,p in SOURCES.items()},
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def worker(rep):
 started_inputs=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());t0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-t0
 turns=[];total=0
 for i in range(2):
  start=time.perf_counter_ns()
  reply=a.converse("report your organisation",speech_act="instruction",speaker="alice")
  elapsed=time.perf_counter_ns()-start;total+=elapsed
  message=a._last_turn_inbound;mid=nid(message);ma=a.s.node(message)["attrs"]
  event=ma.get("discourse_event_id");eid=nid(event) if event is not None else None
  state=ma.get("discourse_state_id")
  goals=[g for g in a.s.nodes("Goal") if message in a.inner.neighbours(g,"comprehends")]
  recipients=list(a.inner.neighbours(event,"to_addressee")) if event is not None else []
  rows=[]
  for g in goals:
   ga=a.s.node(g)["attrs"]
   ds=[d for d in a.s.nodes("Deliberation") if g in a.inner.neighbours(d,"about_goal")]
   rows.append({"goal_id":nid(g),"attrs":ga,"originates_in_event":event is not None and event in a.inner.neighbours(g,"originated_in"),
    "transition_events":[nid(x) for x in a.inner.neighbours(g,"transitioned_by")],
    "deliberations":[{"status":a.s.node(d)["attrs"].get("status"),"candidate_source":a.s.node(d)["attrs"].get("candidate_source")} for d in ds]})
  turns.append({"turn":i,"elapsed_ns":elapsed,"message_id":mid,"event_id":eid,
   "event_attrs":a.s.node(event)["attrs"] if event is not None else None,
   "event_recipients":[nid(x) for x in recipients],
   "event_for_goal_edges":[nid(x) for x in a.inner.neighbours(event,"for_goal")] if event is not None else [],
   "communication_route":ma.get("communication_route"),"reply_nonempty":bool(reply),
   "reply_mentions_organisation":"organis" in str(reply).lower(),"goal_count":len(goals),"goals":rows})
 events=list(a.inner.neighbours(state,"has_event")) if state is not None else []
 kinds={k:sum(a.s.node(e)["attrs"].get("kind")==k for e in events) for k in ("instruction","selection","execution","action_result")}
 valid=all(t["communication_route"]=="self_report" and t["reply_nonempty"] and t["reply_mentions_organisation"] and t["goal_count"]==1 and len(t["goals"])==1 and t["goals"][0]["attrs"].get("source")=="conversation" and t["goals"][0]["attrs"].get("kind")=="report_self" and t["goals"][0]["attrs"].get("self_target")=="self_organisation" and t["goals"][0]["originates_in_event"] for t in turns)
 finished_inputs=lock_inputs()
 return {"replicate":rep,"pid":os.getpid(),"boot_ns":boot_ns,"turns_ns_total":total,"turn_median_ns":total/2,"turns":turns,"event_counts":kinds,"event_count":len(events),
  "worker_started_inputs":started_inputs,"worker_finished_inputs":finished_inputs,
  "positive_route_and_origin_gate":valid,"same_recipient":len(turns)==2 and bool(turns[0]["event_recipients"]) and turns[0]["event_recipients"]==turns[1]["event_recipients"],
  "distinct_turn_identity":len({x["message_id"] for x in turns})==2 and len({x["event_id"] for x in turns})==2 and len({x["goals"][0]["goal_id"] for x in turns if x["goals"]})==2,
  "lifecycle_gap":all(kinds[k]==0 for k in ("selection","execution","action_result")) and all(not g["transition_events"] for t in turns for g in t["goals"]) and all(not t["event_for_goal_edges"] for t in turns)}
def signature(run):
 return [{"route":t["communication_route"],"reply_nonempty":t["reply_nonempty"],"reply_mentions_organisation":t["reply_mentions_organisation"],
  "event_kind":(t["event_attrs"] or {}).get("kind"),"goal_attrs":{k:t["goals"][0]["attrs"].get(k) for k in ("kind","predicate","object","self_target","source")} if t["goals"] else None,
  "recipient_count":len(t["event_recipients"]),"goal_origin":t["goals"][0]["originates_in_event"] if t["goals"] else False} for t in run["turns"]]
def main():
 if sys.argv[1:]==["--lock"]: print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker": print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked: raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260926).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post_run_inputs=lock_inputs()
 checks={"three_distinct_fresh_pids":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "live_self_report_route_and_origin_repeat":all(r["positive_route_and_origin_gate"] for r in runs),
  "same_recipient_and_distinct_identity":all(r["same_recipient"] and r["distinct_turn_identity"] for r in runs),
  "lifecycle_events_and_transitions_absent":all(r["lifecycle_gap"] for r in runs),
  "producer_shape_repeats":len({json.dumps(signature(r),sort_keys=True) for r in runs})==1,
  "source_stable_through_all_workers":post_run_inputs==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs)}
 payload={"schema_version":1,"run_id":"substrate-live-self-report-lifecycle-producer-v1_1-20260926",
  "claim_boundary":"Three fresh full-seed runs establish a repeated live held self-report route with distinct Goal-to-origin provenance. That route emits no discourse selection/execution/action_result events or Goal transitions. No claim about every action route or durable execution receipts.",
  "locked_inputs":locked,"post_run_inputs":post_run_inputs,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"schedule":jobs,"checks":checks,
  "summary":{"boot_ns_median":statistics.median(r["boot_ns"] for r in runs),"turn_ns_median":statistics.median(r["turn_median_ns"] for r in runs),"event_counts":runs[0]["event_counts"]},"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n")
 print(json.dumps({"output":str(OUT),"checks":checks,"summary":payload["summary"]},indent=2))
 if not all(checks.values()): raise SystemExit("live self-report lifecycle producer probe failed")
if __name__=="__main__": main()
