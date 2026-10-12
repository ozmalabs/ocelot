#!/usr/bin/env python3
"""Confirm Goal-bound live self-report lifecycle production and controls."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_TASK_BOUNDARY_V2_1_PREREG_20260927.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_TASK_BOUNDARY_V2_1_AMENDMENT_20260927.md"
SOURCES={"world_adapter":ROOT/"substrate/world_adapter.py","boot_all":ROOT/"substrate/boot_all.py",
 "conversation_action":ROOT/"domains/conversation_action.py","discourse_state":ROOT/"domains/discourse_state.py",
 "reflective_faculty":ROOT/"domains/reflective_faculty.py",
 "native_py":ROOT/"runners/dsl/src/py.rs","native_scale_audit":ROOT/"runners/dsl/src/scale_audit.rs",
 "native_rewrite":ROOT/"runners/dsl/src/rewrite.rs","native_substrate":ROOT/"runners/dsl/src/substrate.rs",
 "native_graph_rules":ROOT/"runners/dsl/src/graph_rules.rs","discourse_seed":ROOT/"seeds/conversation_discourse_state.json",
 "analyzer":ROOT/"scripts/analyze_substrate_live_self_report_task_boundary_v2_1.py"}
LOCK=ROOT/"evaluation/substrate_capability/live_self_report_task_boundary_v2_1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/substrate_live_self_report_task_boundary_v2_1_20260927.json"
PROMPTS=("report your organisation","describe who you are")
EXPECTED_TARGETS=("self_organisation","self_identity")
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
def semantic_graph_digest(graph):
 nodes=[]
 for node in graph.get("nodes",[]):
  attrs=dict(node.get("attrs",{}))
  if node.get("type")=="SystemModel":attrs.pop("ts",None);attrs.pop("runtime_s",None)
  nodes.append({"id":node["id"],"type":node["type"],"attrs":attrs})
 payload={"nodes":nodes,"edges":graph.get("edges",[])}
 return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def width_upper_bound(owned,internal):
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
def boundary_projection(graph,owned):
 owned={int(n) for n in owned};edges=[(int(e["src"]),str(e["type"]),int(e["tgt"])) for e in graph.get("edges",[])]
 incident=[e for e in edges if e[0] in owned or e[2] in owned]
 internal=[e for e in incident if e[0] in owned and e[2] in owned]
 cut=[e for e in incident if (e[0] in owned)!=(e[2] in owned)]
 external={e[2] if e[0] in owned else e[0] for e in cut};types={int(n["id"]):str(n["type"]) for n in graph.get("nodes",[])}
 ect=Counter();nct=Counter()
 for _,typ,_ in cut:ect[typ]+=1
 for n in external:nct[types.get(n,"<missing>")]+=1
 return {"owned_node_ids":sorted(owned),"owned_node_count":len(owned),"internal_edge_count":len(internal),"boundary_incidence_count":len(cut),"boundary_unique_external_node_count":len(external),"boundary_edge_type_counts":dict(sorted(ect.items())),"boundary_external_node_type_counts":dict(sorted(nct.items())),"owned_induced_treewidth_upper_bound":width_upper_bound(owned,internal),"internal_edges":[list(e) for e in sorted(internal)],"boundary_edges":[list(e) for e in sorted(cut)]}
def paired_boundary(graph,owned_a,owned_b):
 a=set(owned_a);b=set(owned_b);edges=[(int(e["src"]),str(e["type"]),int(e["tgt"])) for e in graph.get("edges",[])]
 cross=[e for e in edges if (e[0] in a and e[2] in b) or (e[0] in b and e[2] in a)]
 ext_a={e[2] if e[0] in a else e[0] for e in edges if (e[0] in a)!=(e[2] in a)}
 ext_b={e[2] if e[0] in b else e[0] for e in edges if (e[0] in b)!=(e[2] in b)}
 types={int(n["id"]):str(n["type"]) for n in graph.get("nodes",[])};shared=ext_a&ext_b;counts=Counter(types.get(n,"<missing>") for n in shared)
 return {"direct_cross_task_edge_count":len(cross),"direct_cross_task_edges":[list(e) for e in sorted(cross)],"shared_external_node_count":len(shared),"shared_external_node_type_counts":dict(sorted(counts.items()))}
def independent_boundary_check(graph,owned_a,owned_b,boundaries,pair):
 edges=sorted((int(e["src"]),str(e["type"]),int(e["tgt"])) for e in graph.get("edges",[]))
 types={int(n["id"]):str(n["type"]) for n in graph.get("nodes",[])};ok=True;rows={}
 for key,owned in (("turn_0",set(owned_a)),("turn_1",set(owned_b))):
  expected_internal=[e for e in edges if e[0] in owned and e[2] in owned]
  expected_cut=[e for e in edges if (e[0] in owned)!=(e[2] in owned)]
  actual=boundaries[key]
  ei=[tuple(e) for e in actual["internal_edges"]];ec=[tuple(e) for e in actual["boundary_edges"]]
  external={e[2] if e[0] in owned else e[0] for e in expected_cut}
  type_counts=Counter(types.get(n,"<missing>") for n in external)
  valid=(ei==expected_internal and ec==expected_cut and len(expected_internal)==actual["internal_edge_count"] and len(expected_cut)==actual["boundary_incidence_count"] and len(external)==actual["boundary_unique_external_node_count"] and dict(sorted(type_counts.items()))==actual["boundary_external_node_type_counts"] and all(n in types for n in owned|external))
  rows[key]={"expected_internal_edge_count":len(expected_internal),"expected_boundary_incidence_count":len(expected_cut),"owned_and_external_nodes_resolve":all(n in types for n in owned|external),"exact_edge_lists_match":ei==expected_internal and ec==expected_cut,"valid":valid};ok=ok and valid
 a=set(owned_a);b=set(owned_b)
 expected_cross=[e for e in edges if (e[0] in a and e[2] in b) or (e[0] in b and e[2] in a)]
 ext_a={e[2] if e[0] in a else e[0] for e in edges if (e[0] in a)!=(e[2] in a)}
 ext_b={e[2] if e[0] in b else e[0] for e in edges if (e[0] in b)!=(e[2] in b)}
 shared=ext_a&ext_b;shared_types=Counter(types.get(n,"<missing>") for n in shared)
 pair_valid=(pair["direct_cross_task_edges"]==[list(e) for e in expected_cross] and pair["shared_external_node_count"]==len(shared) and pair["shared_external_node_type_counts"]==dict(sorted(shared_types.items())))
 return {"valid":ok and pair_valid,"by_task":rows,"pair_valid":pair_valid,"expected_direct_cross_task_edge_count":len(expected_cross),"expected_shared_external_node_count":len(shared)}
def task_owned_nodes(a,turn):
 message=next((m for m in a.s.nodes("Message") if nid(m)==int(turn["message_id"])),None)
 if message is None:raise RuntimeError("task inbound Message is absent")
 owned={nid(message)};origin_id=turn.get("origin_event_id")
 if origin_id is not None:owned.add(int(origin_id))
 goals=[g for g in a.s.nodes("Goal") if message in a.inner.neighbours(g,"comprehends")]
 events=set();candidates=set();children=set()
 for goal in goals:
  owned.add(nid(goal));events.update(a.inner.neighbours(goal,"transitioned_by"));events.update(a.inner.neighbours(goal,"originated_in"));candidates.update(a.inner.neighbours(goal,"has_reply_candidate"));children.update(a.inner.neighbours(goal,"has_subgoal"))
 owned.update(nid(x) for x in events|candidates|children)
 for receipt in a.s.nodes("ProductionGateReceipt"):
  if a.s.node(receipt)["attrs"].get("turn_message_id")==nid(message) or message in a.inner.neighbours(receipt,"for_message"):owned.add(nid(receipt))
 for outbound in a.outbound_messages():
  if message in a.responds_to(outbound):owned.add(nid(outbound))
 return owned
def worker(rep):
 started=lock_inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());b0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-b0
 import domains.conversation_action as ca
 original=ca._record_live_goal_event;producer_work=[]
 def measured_event(agent,inbound,goal,kind,*,payload=None):
  if os.environ.get("OZMA_DELEGATE_EVENT_AUDIT_TO_OUTER", "0") == "1":
   t0=time.perf_counter_ns();event=original(agent,inbound,goal,kind,payload=payload);elapsed=time.perf_counter_ns()-t0
   producer_work.append({"kind":kind,"goal_id":nid(goal),"event_id":nid(event) if event is not None else None,"elapsed_ns":elapsed,"audit_capture":"delegated_to_outer_request"})
   return event
  audit=agent.inner;audit.scale_audit_reset();audit.scale_audit_per_rule_reset();audit.scale_audit_set_enabled(True);audit.scale_audit_set_per_rule_enabled(True);t0=time.perf_counter_ns()
  try:
   event=original(agent,inbound,goal,kind,payload=payload);elapsed=time.perf_counter_ns()-t0
   counters={"scale":{str(k):int(v) for k,v in dict(audit.scale_audit_snapshot()).items()},"per_rule":[[int(i),str(m),int(v)] for i,m,v in audit.scale_audit_per_rule_snapshot()],"per_clause":[[int(i),int(pos),int(v)] for i,pos,v in audit.scale_audit_match_clause_snapshot()],"metadata":[[int(i),int(sym),str(name),int(arity),bool(amb)] for i,sym,name,arity,amb in audit.scale_audit_rule_metadata_snapshot()]}
  finally:audit.scale_audit_set_per_rule_enabled(False);audit.scale_audit_set_enabled(False)
  producer_work.append({"kind":kind,"goal_id":nid(goal),"event_id":nid(event) if event is not None else None,"elapsed_ns":elapsed,"counters":counters})
  return event
 ca._record_live_goal_event=measured_event
 turns=[];total=0
 for i,prompt in enumerate(PROMPTS):
  work_start=len(producer_work);t0=time.perf_counter_ns();reply=a.converse(prompt,speech_act="instruction",speaker="alice");elapsed=time.perf_counter_ns()-t0;total+=elapsed
  message=a._last_turn_inbound;ma=a.s.node(message)["attrs"];state=ma.get("discourse_state_id");origin=ma.get("discourse_event_id")
  goals=[g for g in a.s.nodes("Goal") if message in a.inner.neighbours(g,"comprehends")]
  goal=goals[0] if len(goals)==1 else None
  recipient=list(a.inner.neighbours(origin,"to_addressee")) if origin is not None else []
  lifecycle=[e for e in a.inner.neighbours(state,"has_event") if goal is not None and goal in a.inner.neighbours(e,"for_goal")]
  lifecycle.sort(key=lambda e:int(a.s.node(e)["attrs"].get("event_index",-1)))
  turns.append({"turn":i,"prompt":prompt,"expected_self_target":EXPECTED_TARGETS[i],"elapsed_ns":elapsed,"message_id":nid(message),"origin_event_id":nid(origin) if origin is not None else None,
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
 complete_graph=a.s.graph_to_dict()
 owned_sets=[task_owned_nodes(a,t) for t in turns]
 node_ids={int(n["id"]) for n in complete_graph.get("nodes",[])}
 if any(not owned<=node_ids for owned in owned_sets):raise RuntimeError("owned task projection contains missing node IDs")
 task_boundaries={"turn_0":boundary_projection(complete_graph,owned_sets[0]),"turn_1":boundary_projection(complete_graph,owned_sets[1]),"pair":paired_boundary(complete_graph,owned_sets[0],owned_sets[1]),"whole_graph_node_count":len(complete_graph.get("nodes",[])),"whole_graph_edge_count":len(complete_graph.get("edges",[]))}
 boundary_integrity=independent_boundary_check(complete_graph,owned_sets[0],owned_sets[1],task_boundaries,task_boundaries["pair"])
 if not boundary_integrity["valid"]:raise RuntimeError("independent typed-edge cut recomputation failed")
 graph_semantic_sha256=semantic_graph_digest(complete_graph)
 event_counts={k:sum(a.s.node(e)["attrs"].get("kind")==k for s in a.s.nodes("DiscourseState") for e in a.inner.neighbours(s,"has_event"))
  for k in ("instruction","selection","execution","action_result","action_failure")}
 gates=all(t["route"]=="self_report" and t["reply_nonempty"] and t["goal_count"]==1 and t["goal_origin_matches"] and t["origin_event_separate"] and t["goal"]["attrs"].get("self_target")==t["expected_self_target"] and t["goal"]["status"]=="resolved" and t["goal"]["transition_kinds"]==["selection","execution","action_result"] and t["goal"]["transition_links_all_bound"] and t["goal"]["closed"] and not t["goal"]["active"] and [x["kind"] for x in t["lifecycle_events"]]==["selection","execution","action_result"] for t in turns)
 same_recipient=len(turns)==2 and bool(turns[0]["recipient_ids"]) and turns[0]["recipient_ids"]==turns[1]["recipient_ids"]
 distinct=len({t["message_id"] for t in turns})==2 and len({t["origin_event_id"] for t in turns})==2 and len({t["goal"]["goal_id"] for t in turns if t["goal"]})==2
 finished=lock_inputs()
 return {"replicate":rep,"pid":os.getpid(),"boot_ns":boot_ns,"turn_ns_total":total,"turn_ns_median":total/2,"turns":turns,"producer_work":producer_work,"event_counts":event_counts,
  "worker_started_inputs":started,"worker_finished_inputs":finished,"task_boundaries":task_boundaries,"boundary_integrity":boundary_integrity,"whole_graph_semantic_sha256":graph_semantic_sha256,"positive_lifecycle_gate":gates,"same_recipient":same_recipient,"distinct_identity":distinct}
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
 if sys.argv[1:]==["--lock"]:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[0,1,2];random.Random(20260927).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 controls_raw=controls();post=lock_inputs()
 control_checks={"correct_link_selects_only_owner":controls_raw["correct_link"]["statuses"]==["selected","proposed"],
  "omitted_link_selects_no_goal":controls_raw["omitted_link"]["statuses"]==["proposed","proposed"],
  "swapped_link_follows_explicit_edge":controls_raw["swapped_link"]["statuses"]==["proposed","selected"] and controls_raw["swapped_link"]["event_goal_ids"]==[controls_raw["swapped_link"]["goal_ids"][1]] and controls_raw["swapped_link"]["declared_target"]==controls_raw["swapped_link"]["goal_ids"][0],
  "duplicate_result_is_idempotent":controls_raw["duplicate_result"]["status"]=="resolved" and controls_raw["duplicate_result"]["transition_kinds"]==["selection","execution","action_result"] and controls_raw["duplicate_result"]["closed"] and not controls_raw["duplicate_result"]["active"],
  "faculty_failure_blocks_with_identity":controls_raw["faculty_failure"]["goal_status"]=="blocked" and controls_raw["faculty_failure"]["goal_transition_kinds"]==["selection","execution","action_failure"] and controls_raw["faculty_failure"]["closed"] and not controls_raw["faculty_failure"]["active"]}
 checks={"three_distinct_fresh_pids":len(runs)==3 and len({r["pid"] for r in runs})==3,
  "first_prompt_production_route_identity_and_lifecycle":all(r["turns"][0]["route"]=="self_report" and r["turns"][0]["goal_count"]==1 and r["turns"][0]["goal_origin_matches"] and r["turns"][0]["goal"]["status"]=="resolved" and r["turns"][0]["goal"]["transition_kinds"]==["selection","execution","action_result"] and r["turns"][0]["goal"]["transition_links_all_bound"] and r["turns"][0]["goal"]["closed"] and len(r["turns"][0]["producer_work"])==3 for r in runs),
  "second_prompt_route_shortfall_reproduces":all(r["turns"][1]["route"] is None and r["turns"][1]["goal_count"]==0 and not r["turns"][1]["lifecycle_events"] and not r["turns"][1]["producer_work"] for r in runs),
  "event_identity_shape_repeats":len({json.dumps(signature(r),sort_keys=True) for r in runs})==1,
  "all_semantic_controls_pass":all(control_checks.values()),
  "source_stable_through_workers_and_controls":post==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
  "task_boundaries_reproduce":len({json.dumps(r["task_boundaries"],sort_keys=True) for r in runs})==1,
  "semantic_graph_reproduces":len({r["whole_graph_semantic_sha256"] for r in runs})==1}
 payload={"schema_version":1,"run_id":"substrate-live-self-report-task-boundary-v2.1-20260927",
  "claim_boundary":"Three source-locked self-report fixture workers preserve lifecycle behavior and emit complete typed-edge boundaries for two declared task views. Native matcher attribution is retained. The route-shortfall prompt remains separately classified. Boundaries are operational projections, not learned frames or full rule-dependency treewidth; no scale or execution factorization is established.",
  "locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},
  "schedule":jobs,"checks":checks,"control_checks":control_checks,"controls":controls_raw,
  "summary":{"boot_ns_median":statistics.median(r["boot_ns"] for r in runs),"turn_ns_median":statistics.median(r["turn_ns_median"] for r in runs),"replicates":len(runs)},"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"control_checks":control_checks,"summary":payload["summary"]},indent=2))
 if not all(checks.values()):raise SystemExit("self-report task route or source-lock gate failed")
if __name__=="__main__":main()
