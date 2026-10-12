#!/usr/bin/env python3
"""Confirm Goal-bound live self-report lifecycle production and controls."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_INTEGRATION_PREREG_20260926.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_V1_7_AMENDMENT_20260926.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py",
 "reflective_faculty":ROOT/"domains/reflective_faculty.py","discourse_seed":ROOT/"seeds/conversation_discourse_state.json",
 "analyzer":ROOT/"scripts/analyze_substrate_live_self_report_lifecycle_identity_integration_v1_7.py"}
LOCK=ROOT/"evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_7_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_7_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,"value") else x)
def source_closure():
 paths=set()
 for folder in (ROOT/"domains",ROOT/"substrate",ROOT/"runners/dsl/python"):
  paths.update(p for p in folder.rglob("*.py") if "__pycache__" not in p.parts)
 seed_dir=ROOT/"seeds";paths.update(seed_dir.glob("*.json"));paths.update((seed_dir/"generated").glob("*.json"))
 return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"amendment_sha256":sha(AMENDMENT),"runner_sha256":sha(__file__),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"source_closure_sha256":source_closure(),
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def project(a,goal):
 ga=a.s.node(goal)["attrs"]
 evs=list(a.inner.neighbours(goal,"transitioned_by"))
 evs.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
 return {"goal_id":nid(goal),"attrs":ga,"status":ga.get("lifecycle_status"),
  "transition_event_ids":[nid(e) for e in evs],"transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in evs],
  "transition_event_indices":[int(a.s.node(e)["attrs"].get("event_index",-1)) for e in evs],
  "transition_links_all_bound":all(goal in a.inner.neighbours(e,"for_goal") for e in evs),
  "closed":any(goal in a.inner.neighbours(s,"has_closed_goal") for s in a.s.nodes("DiscourseState")),
  "active":any(goal in a.inner.neighbours(s,"has_active_goal") for s in a.s.nodes("DiscourseState"))}
def worker(rep):
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());b0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-b0
 import domains.conversation_action as ca
 original=ca._record_live_goal_event;producer_work=[]
 def measured_event(agent,inbound,goal,kind,*,payload=None):
  audit=agent.inner;audit.scale_audit_reset();audit.scale_audit_per_rule_reset();audit.scale_audit_set_enabled(True);audit.scale_audit_set_per_rule_enabled(True);t0=time.perf_counter_ns()
  try:
   event=original(agent,inbound,goal,kind,payload=payload);elapsed=time.perf_counter_ns()-t0
   counters={"scale":{str(k):int(v) for k,v in dict(audit.scale_audit_snapshot()).items()},"per_rule":[[int(i),str(m),int(v)] for i,m,v in audit.scale_audit_per_rule_snapshot()]}
  finally:audit.scale_audit_set_per_rule_enabled(False);audit.scale_audit_set_enabled(False)
  producer_work.append({"kind":kind,"goal_id":nid(goal),"event_id":nid(event) if event is not None else None,"elapsed_ns":elapsed,"counters":counters})
  return event
 ca._record_live_goal_event=measured_event
 turns=[];total=0
 for i in range(2):
  work_start=len(producer_work);t0=time.perf_counter_ns();reply=a.converse("report your organisation",speech_act="instruction",speaker="alice");elapsed=time.perf_counter_ns()-t0;total+=elapsed
  message=a._last_turn_inbound;ma=a.s.node(message)["attrs"];state=ma.get("discourse_state_id");origin=ma.get("discourse_event_id")
  goals=[g for g in a.s.nodes("Goal") if message in a.inner.neighbours(g,"comprehends")]
  goal=goals[0] if len(goals)==1 else None
  recipient=list(a.inner.neighbours(origin,"to_addressee")) if origin is not None else []
  lifecycle=[e for e in a.inner.neighbours(state,"has_event") if goal is not None and goal in a.inner.neighbours(e,"for_goal")]
  lifecycle.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
  turns.append({"turn":i,"elapsed_ns":elapsed,"message_id":nid(message),"origin_event_id":nid(origin) if origin is not None else None,
   "recipient_ids":[nid(x) for x in recipient],"route":ma.get("communication_route"),"reply_nonempty":bool(reply),
   "reply_mentions_organisation":"organis" in str(reply).lower(),"goal_count":len(goals),
   "goal":project(a,goal) if goal is not None else None,
   "goal_origin_matches":goal is not None and origin in a.inner.neighbours(goal,"originated_in"),
   "lifecycle_events":[{"id":nid(e),"kind":a.s.node(e)["attrs"].get("kind"),"event_index":a.s.node(e)["attrs"].get("event_index"),
    "payload":a.s.node(e)["attrs"].get("payload"),"for_goal_ids":[nid(g) for g in a.inner.neighbours(e,"for_goal")]} for e in lifecycle]})
  turns[-1]["producer_work"]=producer_work[work_start:]
  turn_events={x["id"] for x in turns[-1]["lifecycle_events"]}
  turns[-1]["origin_event_separate"]=(turns[-1]["origin_event_id"] not in turn_events)
 ca._record_live_goal_event=original
 event_counts={k:sum(a.s.node(e)["attrs"].get("kind")==k for s in a.s.nodes("DiscourseState") for e in a.inner.neighbours(s,"has_event"))
  for k in ("instruction","selection","execution","action_result","action_failure")}
 gates=all(t["route"]=="self_report" and t["reply_nonempty"] and t["reply_mentions_organisation"] and t["goal_count"]==1 and t["goal_origin_matches"] and t["origin_event_separate"] and t["goal"]["status"]=="resolved" and t["goal"]["transition_kinds"]==["selection","execution","action_result"] and t["goal"]["transition_links_all_bound"] and t["goal"]["closed"] and not t["goal"]["active"] and [x["kind"] for x in t["lifecycle_events"]]==["selection","execution","action_result"] for t in turns)
 same_recipient=len(turns)==2 and bool(turns[0]["recipient_ids"]) and turns[0]["recipient_ids"]==turns[1]["recipient_ids"]
 distinct=len({t["message_id"] for t in turns})==2 and len({t["origin_event_id"] for t in turns})==2 and len({t["goal"]["goal_id"] for t in turns if t["goal"]})==2
 finished=lock_inputs()
 return {"replicate":rep,"pid":os.getpid(),"boot_ns":boot_ns,"turn_ns_total":total,"turn_ns_median":total/2,"turns":turns,"producer_work":producer_work,"event_counts":event_counts,
  "worker_started_inputs":started,"worker_finished_inputs":finished,"positive_lifecycle_gate":gates,"same_recipient":same_recipient,"distinct_identity":distinct}
def controls():
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains.discourse_state import ensure_discourse_state,open_goal,record_event
 from substrate.boot_core import load_seeds_into
 def fixture(label):
  a=WorldAdapter(seeds=());load_seeds_into(a.s,a.agent,["conversation_discourse_state"])
  user=a.attach_chat_world("identity_control_user")["interlocutor"]
  state=ensure_discourse_state(a,conversation_id=label,addressee=user)
  origins=[record_event(a,state,kind="request",speaker=user,addressee=a.agent) for _ in range(2)]
  goals=[open_goal(a,state,kind=f"control_{i}",origin_event=origins[i],addressee=user) for i in range(2)]
  return a,state,origins,goals
 c={}
 a,s,o,g=fixture("correct_link");e=record_event(a,s,kind="selection",goal=g[0],payload={"declared_target":nid(g[0])});a.inner.run_rules()
 c["correct_link"]={"event_goal_ids":[nid(x) for x in a.inner.neighbours(e,"for_goal")],"statuses":[a.s.node(x)["attrs"].get("lifecycle_status") for x in g],"expected":["selected","proposed"]}
 a,s,o,g=fixture("omitted_link");e=record_event(a,s,kind="selection",payload={"declared_target":nid(g[0])});a.inner.run_rules()
 c["omitted_link"]={"event_goal_ids":[nid(x) for x in a.inner.neighbours(e,"for_goal")],"statuses":[a.s.node(x)["attrs"].get("lifecycle_status") for x in g],"expected":["proposed","proposed"]}
 a,s,o,g=fixture("swapped_link");e=record_event(a,s,kind="selection",goal=g[1],payload={"declared_target":nid(g[0])});a.inner.run_rules()
 c["swapped_link"]={"declared_target":nid(g[0]),"goal_ids":[nid(x) for x in g],"event_goal_ids":[nid(x) for x in a.inner.neighbours(e,"for_goal")],"statuses":[a.s.node(x)["attrs"].get("lifecycle_status") for x in g],"expected":["proposed","selected"]}
 a,s,o,g=fixture("duplicate_result");
 for kind in ("selection","execution","action_result","action_result"):
  record_event(a,s,kind=kind,goal=g[0],payload={"declared_target":nid(g[0])});a.inner.run_rules()
 c["duplicate_result"]={"status":a.s.node(g[0])["attrs"].get("lifecycle_status"),"transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in sorted(a.inner.neighbours(g[0],"transitioned_by"),key=lambda z:int(a.s.node(z)["attrs"].get("event_index",-1)))],"result_event_count":sum(a.s.node(e)["attrs"].get("kind")=="action_result" for e in a.inner.neighbours(s,"has_event")),"active":g[0] in a.inner.neighbours(s,"has_active_goal"),"closed":g[0] in a.inner.neighbours(s,"has_closed_goal"),"expected_status":"resolved","expected_transition_kinds":["selection","execution","action_result"]}
 a=WorldAdapter(seeds=());load_all_seeds(a)
 from domains import reflective_faculty
 from unittest.mock import patch
 with patch.object(reflective_faculty,"reflect",side_effect=RuntimeError("preregistered faculty failure")):
  a.converse("report your organisation",speech_act="instruction",speaker="alice")
 m=a._last_turn_inbound;ma=a.s.node(m)["attrs"];gs=[g for g in a.s.nodes("Goal") if m in a.inner.neighbours(g,"comprehends")];state=ma.get("discourse_state_id")
 fgoal=gs[0] if len(gs)==1 else None
 c["faculty_failure"]={"route":ma.get("communication_route"),"goal_status":a.s.node(fgoal)["attrs"].get("lifecycle_status") if fgoal is not None else None,
  "event_kinds":[a.s.node(e)["attrs"].get("kind") for e in sorted(a.inner.neighbours(state,"has_event"),key=lambda z:int(a.s.node(z)["attrs"].get("event_index",-1)))],
  "goal_transition_kinds":[a.s.node(e)["attrs"].get("kind") for e in sorted(a.inner.neighbours(fgoal,"transitioned_by"),key=lambda z:int(a.s.node(z)["attrs"].get("event_index",-1)))] if fgoal is not None else [],
  "active":fgoal in a.inner.neighbours(state,"has_active_goal") if fgoal is not None else None,
  "closed":fgoal in a.inner.neighbours(state,"has_closed_goal") if fgoal is not None else None,
  "reply_observed":bool(a.reply_for_inbound(m)) if hasattr(a,"reply_for_inbound") else None}
 return c
def signature(r):
 return [{"route":t["route"],"reply_nonempty":t["reply_nonempty"],"reply_mentions_organisation":t["reply_mentions_organisation"],
  "goal_status":t["goal"]["status"] if t["goal"] else None,"transition_kinds":t["goal"]["transition_kinds"] if t["goal"] else [],
  "event_kinds":[e["kind"] for e in t["lifecycle_events"]],"all_bound":t["goal"]["transition_links_all_bound"] if t["goal"] else False} for t in r["turns"]]
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260926).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 controls_raw=controls();post=lock_inputs()
 control_checks={"correct_link_selects_only_owner":controls_raw["correct_link"]["statuses"]==["selected","proposed"],
  "omitted_link_selects_no_goal":controls_raw["omitted_link"]["statuses"]==["proposed","proposed"],
  "swapped_link_follows_explicit_edge":controls_raw["swapped_link"]["statuses"]==["proposed","selected"] and controls_raw["swapped_link"]["event_goal_ids"]==[controls_raw["swapped_link"]["goal_ids"][1]] and controls_raw["swapped_link"]["declared_target"]==controls_raw["swapped_link"]["goal_ids"][0],
  "duplicate_result_is_idempotent":controls_raw["duplicate_result"]["status"]=="resolved" and controls_raw["duplicate_result"]["transition_kinds"]==["selection","execution","action_result"] and controls_raw["duplicate_result"]["closed"] and not controls_raw["duplicate_result"]["active"],
  "faculty_failure_blocks_with_identity":controls_raw["faculty_failure"]["goal_status"]=="blocked" and controls_raw["faculty_failure"]["goal_transition_kinds"]==["selection","execution","action_failure"] and controls_raw["faculty_failure"]["closed"] and not controls_raw["faculty_failure"]["active"]}
 checks={"three_distinct_fresh_pids":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "production_route_identity_and_lifecycle":all(r["positive_lifecycle_gate"] and r["same_recipient"] and r["distinct_identity"] for r in runs),
  "event_identity_shape_repeats":len({json.dumps(signature(r),sort_keys=True) for r in runs})==1,
  "all_semantic_controls_pass":all(control_checks.values()),
  "source_stable_through_workers_and_controls":post==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs)}
 payload={"schema_version":1,"run_id":"substrate-live-self-report-lifecycle-identity-integration-v1_7-20260926",
  "claim_boundary":"One live held self-report route now emits Goal-bound lifecycle events and native identity-constrained transitions. V1.7 measures production helper work under a full-seed source closure lock. Five controls test owner link, omission, swapped link, duplicate result, and faculty failure. This does not generalize to other action routes, external effects, or scale.",
  "locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},
  "schedule":jobs,"checks":checks,"control_checks":control_checks,"controls":controls_raw,
  "summary":{"boot_ns_median":statistics.median(r["boot_ns"] for r in runs),"turn_ns_median":statistics.median(r["turn_ns_median"] for r in runs),"replicates":len(runs)},"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"control_checks":control_checks,"summary":payload["summary"]},indent=2))
 if not all(checks.values()):raise SystemExit("lifecycle identity integration gate failed")
if __name__=="__main__":main()
