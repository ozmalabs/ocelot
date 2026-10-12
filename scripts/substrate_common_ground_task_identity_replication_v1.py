#!/usr/bin/env python3
"""Replicate same-addressee Goal identity controls on common-ground stress input."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_COMMON_GROUND_TASK_IDENTITY_REPLICATION_PREREG_20260926.md"
FIXTURE=ROOT/"tests/fixtures/conversational_manifold/phase3_common_ground_stress.json"
SEED=ROOT/"seeds/conversation_discourse_state.json"
MAT=ROOT/"domains/discourse_state.py"
LOCK=ROOT/"evaluation/substrate_capability/common_ground_task_identity_replication_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_common_ground_task_identity_replication_v1_20260926.json"
ARMS=("temporal","recipient","explicit");CAP=100000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,"value") else x)
def digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"fixture_sha256":sha(FIXTURE),
  "seed_sha256":sha(SEED),"materializer_sha256":sha(MAT),"native_extension_sha256":sha(Path(_native.__file__).resolve()),
  "native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "rewrite_sha256":sha(ROOT/"runners/dsl/src/rewrite.rs"),"py_sha256":sha(ROOT/"runners/dsl/src/py.rs"),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def patch_rules(inner,arm):
 names={"discourse_goal_select","discourse_goal_execute","discourse_goal_resolve"}; rows=inner.export_rules()
 targets=[(i,r) for i,r in enumerate(rows) if r.get("name") in names and r.get("active",True)]
 if len(targets)!=3:raise RuntimeError("expected three active discourse lifecycle rules")
 for i,_ in targets:
  if not inner.remove_rule(i):raise RuntimeError("failed to remove lifecycle rule")
 new=[]
 for _,prior in targets:
  r={k:v for k,v in prior.items() if k not in {"active","batch","content_hash","mutation_protected","revision","rule_uid"}}
  r["name"]=f"{r['name']}_{arm}_identity_replication"
  if arm=="recipient":r["match"] += [["goal","for_addressee","recipient"],["event","to_addressee","recipient"]]
  elif arm=="explicit":r["match"] += [["event","for_goal","goal"]]
  new.append(int(inner.add_rule(r)))
 return new
def worker(arm,rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_core import load_seeds_into
 from domains.discourse_state import ensure_common_ground,ensure_discourse_state,open_goal,record_event
 fixture=json.loads(FIXTURE.read_text());a=WorldAdapter(seeds=());load_seeds_into(a.s,a.agent,["conversation_discourse_state"])
 patched=patch_rules(a.inner,arm);person=a.attach_chat_world("shared_user");user=person["interlocutor"]
 state=ensure_discourse_state(a,conversation_id="common_ground_identity_replication",addressee=user);ensure_common_ground(a,state,addressee=user)
 goals=[];events=[];event_idx={};frames={};active=-1;frame_count=0;checkpoints=[];construction_ns=0
 # Task provenance comes only from frozen fixture sequence boundaries, used as the independent oracle.
 intended={4:0,5:0,6:0,7:1,8:1,9:1}
 for row in fixture["events"]:
  i=int(row["index"]);kind=row["kind"];rel=row["relation"]
  if rel in {"origin","unsolicited"}:active=frame_count;frame_count+=1
  topic="calendar" if i<5 else "location";t0=time.perf_counter_ns()
  if kind=="request":
   payload={"common_ground_delta":"calendar_request"} if i==0 else None
   event=record_event(a,state,kind=kind,speaker=user,addressee=a.agent,topic=topic,expectation="action",interaction_mode=row["mode"],payload=payload)
   goal=open_goal(a,state,kind=f"task_{len(goals)}",origin_event=event,addressee=user);goals.append(goal)
  elif kind=="observation":event=record_event(a,state,kind=kind,speaker=user,addressee=a.agent,topic=topic,interaction_mode=row["mode"])
  elif kind=="assertion":event=record_event(a,state,kind=kind,speaker=user,addressee=a.agent,topic=topic,interaction_mode=row["mode"],payload={"common_ground_delta":"calendar_shared"})
  elif kind in {"selection","execution"}:event=record_event(a,state,kind=kind,speaker=a.agent,addressee=user,interaction_mode=row["mode"])
  elif kind=="action_result":
   claim="calendar_checked" if i==6 else "location_shared"
   event=record_event(a,state,kind=kind,speaker=a.agent,addressee=user,interaction_mode=row["mode"],payload={"common_ground_delta":claim})
  else:raise RuntimeError(f"unhandled fixture kind {kind}")
  construction_ns+=time.perf_counter_ns()-t0;eid=nid(event);events.append(eid);event_idx[eid]=i;frames[eid]=active
  if arm=="explicit" and i in intended:a.inner.add_edge_unchecked(event,"for_goal",goals[intended[i]])
  a.inner.scale_audit_reset();a.inner.scale_audit_set_enabled(True);w,c=time.perf_counter_ns(),time.process_time_ns()
  report=dict(a.inner.run_rules_report(CAP,False));wall,cpu=time.perf_counter_ns()-w,time.process_time_ns()-c
  counters={str(k):int(v) for k,v in dict(a.inner.scale_audit_snapshot()).items()};a.inner.scale_audit_set_enabled(False)
  paths={str(j):sorted(event_idx[nid(x)] for x in a.inner.neighbours(g,"transitioned_by") if nid(x) in event_idx) for j,g in enumerate(goals)}
  checkpoints.append({"event_index":i,"event_id":eid,"frame":active,"status":report.get("status"),"progress_steps":int(report.get("progress_steps",0)),"counters":counters,"wall_ns":wall,"cpu_ns":cpu,"paths":paths,"graph_digest":digest(a.inner.graph_to_dict())})
 final_paths={str(j):sorted(event_idx[nid(x)] for x in a.inner.neighbours(g,"transitioned_by") if nid(x) in event_idx) for j,g in enumerate(goals)}
 grounds=sorted(tuple(sorted(a.s.node(n)["attrs"].get("claims",[]))) for n in a.s.nodes("CommonGround"))
 expected={"0":[4,5,6],"1":[7,8,9]}
 return {"arm":arm,"replicate":rep,"pid":os.getpid(),"event_count":len(events),"frame_count":frame_count,
  "goal_count":len(goals),"patched_rule_indices":patched,"fixture_links_added":sum(1 for i in intended if arm=="explicit"),
  "checkpoints":checkpoints,"final_paths":final_paths,"expected_paths":expected,
  "task_oracle_pass":final_paths==expected,"all_checkpoints_fixed":all(c["status"]=="fixed_point" for c in checkpoints),
  "common_grounds":grounds,"expected_common_grounds":[["calendar_request","calendar_shared"],["calendar_checked","location_shared"]],
  "common_ground_oracle_pass":grounds==[("calendar_checked","location_shared"),("calendar_request","calendar_shared")],
  "final_digest":digest(a.inner.graph_to_dict()),"construction_ns":construction_ns,
  "peak_rss_kib":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==4 and sys.argv[1]=="--worker":print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[(arm,rep) for arm in ARMS for rep in range(3)];random.Random(20260926).shuffle(jobs);runs=[]
 for arm,rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",arm,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 by={(x["arm"],x["replicate"]):x for x in runs};checks={"nine_workers_unique_pids":len(runs)==9 and len({x["pid"] for x in runs})==9,
  "all_workers_materialize_locked_fixture":all(x["event_count"]==10 and x["frame_count"]==2 and x["goal_count"]==2 for x in runs),
  "all_checkpoints_fixed":all(x["all_checkpoints_fixed"] for x in runs),
  "expected_identity_controls_fail":all(not by[(arm,r)]["task_oracle_pass"] for arm in ("temporal","recipient") for r in range(3)),
  "explicit_identity_task_oracle_passes":all(by[("explicit",r)]["task_oracle_pass"] for r in range(3)),
  "common_ground_oracle_all_arms":all(x["common_ground_oracle_pass"] for x in runs),
  "within_arm_final_graphs_reproduce":all(len({by[(arm,r)]["final_digest"] for r in range(3)})==1 for arm in ARMS),
  "fixture_input_links_explicit_only":all(x["fixture_links_added"]==(6 if x["arm"]=="explicit" else 0) for x in runs)}
 summary={}
 for arm in ARMS:
  rows=[]
  for rep in range(3):
   x=by[(arm,rep)];cnt={};
   for cp in x["checkpoints"]:
    for k,v in cp["counters"].items():cnt[k]=cnt.get(k,0)+int(v)
   rows.append({"replicate":rep,"task_oracle_pass":x["task_oracle_pass"],"final_paths":x["final_paths"],
    "candidate_pairs":cnt.get("cand_tested",0),"term_evaluations":cnt.get("term_evals_total",0),
    "closure_wall_ns":sum(c["wall_ns"] for c in x["checkpoints"]),"construction_ns":x["construction_ns"],
    "peak_rss_kib":x["peak_rss_kib"]})
  summary[arm]={"per_replicate":rows}
  for k in ("candidate_pairs","term_evaluations","closure_wall_ns","construction_ns","peak_rss_kib"):
   v=[r[k] for r in rows];summary[arm][k+"_median"]=statistics.median(v);summary[arm][k+"_range"]=[min(v),max(v)]
 payload={"schema_version":1,"run_id":"substrate-common-ground-task-identity-replication-v1-20260926",
  "claim_boundary":"Independent authored two-goal same-recipient fixture; explicit input links supplied only in candidate arm; not production identity integration or natural prevalence.",
  "locked_inputs":locked,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},
  "schedule":[list(j) for j in jobs],"checks":checks,"summary":summary,"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"summary":summary},indent=2))
 if not all(checks.values()):raise SystemExit("task-identity replication failed; preserve raw capture")
if __name__=="__main__":main()
