#!/usr/bin/env python3
"""Current-source sampled join-order estimator on a task-derived rule."""
from __future__ import annotations
import hashlib, itertools, json, os, random, subprocess, sys, time, tracemalloc
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_ANAPHORA_ORDER_ESTIMATOR_V1_PREREG_20260929.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_ANAPHORA_ORDER_ESTIMATOR_V1_1_AMENDMENT_20260929.md"
LOCK=ROOT/"evaluation/substrate_capability/anaphora_order_estimator_v1_1_lock_20260929.json"
RAW=ROOT/"evaluation/reports/anaphora_order_estimator_v1_1_raw_20260929.json"
OUT=ROOT/"evaluation/reports/anaphora_order_estimator_v1_1_20260929.json"
ANALYSIS=ROOT/"evaluation/reports/anaphora_order_estimator_v1_1_analysis_20260929.json"
RUN_ID="task-derived-anaphora-order-estimator-v1.1-20260929"
RULE="rule_anaphoric_it_resolves_to_prior_about_concept"
BASE=(
 ("m","has_mention","mention"),
 ("m","responds_to","m_prev"),
 ("m_prev","has_intent","intent_prev"),
 ("intent_prev","about_concept","c"),
)
# Requested representative orders and their realized order under the currently
# locked installer, derived from the preceding v1.2 all-permutation replay.
ORDER_REQUESTS=((0,1,3,2),(1,0,2,3),(1,3,0,2),(1,2,0,3),
                (2,1,3,0),(2,0,3,1),(2,3,1,0),(3,0,2,1))
REALIZED_ORDERS=((0,1,2,3),(1,0,2,3),(1,2,0,3),(1,2,3,0),
                 (2,1,0,3),(2,1,3,0),(2,3,1,0),(3,2,1,0))
BUDGETS=(8,32,128)
DISTRACTORS=("answer","idea","plan","story")
SOURCES=(
 "seeds/intent.json","seeds/conversation.json","seeds/psychology.json","seeds/relations.json","seeds/faculty_lessons.json",
 "tests/test_intent_migrated.py","substrate/world_adapter.py","substrate/boot_core.py","substrate/seeds.py","domains/seed_registry.py",
 "domains/comprehend_text.py","domains/construction_grammar.py","domains/comprehend_question.py","domains/instruction_reading.py",
 "domains/self_model.py","domains/wordplay.py","domains/preposition_roles.py",
 "runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/src/graph.rs","runners/dsl/src/scale_audit.rs",
 "runners/dsl/python/substrate_rs/_native.build.json","scripts/substrate_run_manifest.py",
 "evaluation/reports/substrate_task_derived_anaphora_join_order_v1_2_analysis_20260929.json",
 "evaluation/substrate_capability/task_derived_anaphora_join_order_v1_2_lock_20260929.json",
)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale
 paths=(*SOURCES,"scripts/substrate_task_derived_anaphora_order_estimator_v1_1.py","scripts/analyze_substrate_task_derived_anaphora_order_estimator_v1_1.py",str(PROTOCOL.relative_to(ROOT)),str(AMENDMENT.relative_to(ROOT)))
 return {"files":{p:sha(ROOT/p) for p in paths},"native_sha256":sha(Path(_native.__file__).resolve()),"native_path":str(Path(_native.__file__).resolve()),"build_stale":build_is_stale(str(ROOT)),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}

def estimate_order(edges_by_type, out_idx, in_idx, order, budget, seed):
 rng=random.Random(seed); states=[{}]; population=1.0; estimated_work=0.0; probes=0; stage_rows=[]
 for ci in order:
  sv, et, tv=BASE[ci]; parents=states if len(states)<=budget else rng.sample(states,budget)
  views=[]
  for st in parents:
   if sv in st and tv in st: view=out_idx.get((st[sv],et),()); mode="both"
   elif sv in st: view=out_idx.get((st[sv],et),()); mode="out"
   elif tv in st: view=in_idx.get((st[tv],et),()); mode="in"
   else: view=edges_by_type.get(et,()); mode="all"
   views.append((st,view,mode))
  estimated_candidates=population*(sum(len(v) for _,v,_ in views)/max(1,len(views)))
  estimated_work+=estimated_candidates
  per_parent=max(1,budget//max(1,len(views)));next_states=[];survivor_estimates=[]
  for st,view,mode in views:
   n=len(view)
   if n==0: survivor_estimates.append(0.0);continue
   k=min(n,per_parent);indices=list(range(n)) if n<=k else sorted(rng.sample(range(n),k));good=0
   for ix in indices:
    src,tgt=view[ix];probes+=1
    if sv in st and st[sv]!=src: continue
    if tv in st and st[tv]!=tgt: continue
    nxt=dict(st);nxt[sv]=src;nxt[tv]=tgt;next_states.append(nxt);good+=1
   survivor_estimates.append(n*good/k if k else 0.0)
  child_population=sum(survivor_estimates)/max(1,len(survivor_estimates))
  population*=child_population
  if len(next_states)>budget: states=rng.sample(next_states,budget)
  else: states=next_states
  stage_rows.append({"clause_index":ci,"estimated_candidates":estimated_candidates,"sampled_candidate_probes":probes,"estimated_survivors":population})
  if not states or population<=0: break
 return {"order":list(order),"estimated_candidate_tests":estimated_work,"estimated_complete_bindings":population,"sampled_candidate_probes":probes,"stage_rows":stage_rows}

def score_orders(graph,d,rep,budget):
 by_type={};out_idx={};in_idx={}
 for e in graph["edges"]:
  et=str(e["type"]);src=e["src"];tgt=e["tgt"];pair=(src,tgt)
  by_type.setdefault(et,[]).append(pair);out_idx.setdefault((src,et),[]).append(pair);in_idx.setdefault((tgt,et),[]).append(pair)
 scores=[]
 for oi,order in enumerate(REALIZED_ORDERS):
  scores.append(estimate_order(by_type,out_idx,in_idx,order,budget,seed=91000+d*1000+rep*100+budget*10+oi))
 chosen=min(range(len(scores)),key=lambda i:(scores[i]["estimated_candidate_tests"],tuple(scores[i]["order"])))
 return {"budget":budget,"scores":scores,"selected_order_index":chosen,"selected_order":list(REALIZED_ORDERS[chosen])}

def task_output(wa,mid):
 mention=next((n for n in wa.inner.neighbours(mid,"has_mention") if wa.s.node(n)["attrs"].get("text")=="it"),None)
 refs=[] if mention is None else list(wa.inner.neighbours(mention,"refers_to"))
 refnames=sorted(str(wa.s.node(n)["attrs"].get("name")) for n in refs)
 intent=wa.intent_of(mid);about=[] if intent is None else list(wa.inner.neighbours(intent,"about_concept"))
 aboutnames=sorted(str(wa.s.node(n)["attrs"].get("name")) for n in about)
 return {"intent_exists":intent is not None,"it_refers_to":refnames,"intent_about_concept":aboutnames}

def install_request(inner,request_idx):
 rows=inner.export_rules();targets=[(i,r) for i,r in enumerate(rows) if r.get("name")==RULE and r.get("active",True)]
 if len(targets)!=1: raise RuntimeError(f"expected one target rule, found {len(targets)}")
 old_i,prior=targets[0]
 rule={k:v for k,v in prior.items() if k not in {"active","batch","content_hash","mutation_protected","revision","rule_uid"}}
 rule["match"]=[list(BASE[i]) for i in ORDER_REQUESTS[request_idx]]
 if not inner.remove_rule(old_i): raise RuntimeError("remove target rule failed")
 new_i=int(inner.add_rule(rule));installed=tuple(BASE.index(tuple(x)) for x in inner.export_rules()[new_i]["match"])
 return new_i,installed

def worker(d,mode,rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_core import load_seeds_into
 wa=WorldAdapter(seeds=());load_seeds_into(wa.s,wa.agent,["intent"]);inner=wa.inner
 before=fingerprint()
 for word in DISTRACTORS[:d]:
  wa.receive_utterance(f"the {word} matters",speech_act="statement",speaker="user");wa.comprehend()
 wa.receive_utterance("the question matters",speech_act="statement",speaker="user");wa.comprehend()
 final_mid=wa.receive_utterance("answer it",speech_act="statement",speaker="user")
 pregraph=inner.graph_to_dict();predictions={};planning_times={}
 if mode.startswith("exact_"): used_budgets=BUDGETS
 elif mode.startswith("plain_B"): used_budgets=(int(mode.removeprefix("plain_B")),)
 else: used_budgets=()
 for b in used_budgets:
  cpu0=time.process_time_ns();wall0=time.perf_counter_ns();predictions[b]=score_orders(pregraph,d,rep,b)
  planning_times[b]={"cpu_ns":time.process_time_ns()-cpu0,"wall_ns":time.perf_counter_ns()-wall0}
 # Separate estimator allocation diagnostic; its timing is excluded.
 tracemalloc.start()
 for b in used_budgets: score_orders(pregraph,d,rep,b)
 _,planner_peak=tracemalloc.get_traced_memory();tracemalloc.stop()
 selected_request=None;installed=None;install_ns=0
 if mode.startswith("exact_"):
  idx=int(mode.split("_")[1]);selected_request=idx
 elif mode.startswith("plain_B"):
  budget=int(mode.removeprefix("plain_B"));pred=predictions[budget];selected_request=next(i for i,o in enumerate(REALIZED_ORDERS) if tuple(o)==tuple(pred["selected_order"]))
 if selected_request is not None:
  t=time.perf_counter_ns();_,installed=install_request(inner,selected_request);install_ns=time.perf_counter_ns()-t
 else:
  rule=next(r for r in inner.export_rules() if r.get("name")==RULE and r.get("active",True))
  installed=tuple(BASE.index(tuple(x)) for x in rule["match"])
 if mode.startswith("exact_") and installed!=REALIZED_ORDERS[int(mode.split("_")[1])]:
  raise RuntimeError(f"requested exact order did not install: cell={mode} realized={installed}")
 if mode.startswith("plain_B") and installed!=tuple(predictions[int(mode.removeprefix("plain_B"))]["selected_order"]):
  raise RuntimeError(f"selected estimator order did not install: cell={mode} realized={installed}")
 audited=mode.startswith("exact_")
 inner.scale_audit_reset();inner.scale_audit_per_rule_reset();inner.scale_audit_set_per_rule_enabled(audited);inner.scale_audit_set_enabled(audited)
 t0=time.perf_counter_ns();progress=int(wa.comprehend());elapsed=time.perf_counter_ns()-t0
 global_counters={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()} if audited else {}
 per=[list(x) for x in inner.scale_audit_per_rule_snapshot()] if audited else []
 clauses=[list(x) for x in inner.scale_audit_match_clause_snapshot()] if audited else []
 metadata=[list(x) for x in inner.scale_audit_rule_metadata_snapshot()] if audited else []
 inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False)
 terminal=dict(inner.run_rules_report(1,False));graph=inner.graph_to_dict();canon=json.dumps(graph,sort_keys=True,separators=(",",":"),default=str)
 output=task_output(wa,final_mid)
 checks=bool(output["intent_exists"] and output["it_refers_to"]==["question"] and "question" in output["intent_about_concept"])
 target_id=-1;candidate_tests=-1
 if audited:
  meta=[m for m in metadata if str(m[2])==RULE]
  if len(meta)==1:
   target_id=int(meta[0][0]);rows=[int(v) for i,k,v in per if int(i)==target_id and str(k)=="candidate_tests"]
   if len(rows)==1:candidate_tests=rows[0]
 after=fingerprint()
 return {"distractors":d,"mode":mode,"replicate":rep,"pid":os.getpid(),"before":before,"after":after,"installed_order":list(installed),"estimator_predictions":predictions,"estimator_planning_times":planning_times,"estimator_python_peak_bytes":planner_peak,"order_install_ns":install_ns,"closure_ns":elapsed,"closure_progress":progress,"terminal_report":terminal,"task_output":output,"task_oracle_pass":checks,"graph_sha256":hashlib.sha256(canon.encode()).hexdigest(),"graph_node_count":len(graph["nodes"]),"graph_edge_count":len(graph["edges"]),"audit_enabled":audited,"target_rule_id":target_id,"target_candidate_tests":candidate_tests,"global_counters":global_counters,"per_rule_counters":per,"clause_counters":clauses}

def jobs():
 out=[]
 for d in (0,2,4):
  for rep in range(2):
   for i in range(8):out.append((d,f"exact_{i}",rep))
   out.extend((d,mode,rep) for mode in ("plain_source","plain_B8","plain_B32","plain_B128"))
 return out

def main():
 if len(sys.argv)>1 and sys.argv[1]=="--worker":
  w=worker(int(sys.argv[2]),sys.argv[3],int(sys.argv[4]));print(json.dumps(w,sort_keys=True,default=str));return 0
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine()
 if sys.argv[1:]==["--lock"]:
  f=fingerprint()
  if f["build_stale"]:raise SystemExit("native build is stale")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"locked_inputs":f},indent=2,sort_keys=True)+"\n");print(LOCK);return 0
 locked=fingerprint()
 if locked["build_stale"]:raise SystemExit("native build is stale")
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale source/native lock")
 from substrate_run_manifest import capture_run_manifest,finish_console_capture,start_console_capture
 started=datetime.now(timezone.utc).isoformat();capture=start_console_capture(RUN_ID);env=dict(os.environ);env["PYTHONHASHSEED"]="0";runs=[];logs=[]
 logdir=ROOT/"evaluation/run_logs";logdir.mkdir(parents=True,exist_ok=True)
 for i,(d,mode,rep) in enumerate(jobs(),1):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(d),mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True)
  log=logdir/f"{RUN_ID}_{i:03d}.log";log.write_text("STDOUT\n"+cp.stdout+"\nSTDERR\n"+cp.stderr)
  logs.append({"path":str(log.relative_to(ROOT)),"sha256":sha(log),"returncode":cp.returncode,"distractors":d,"mode":mode,"replicate":rep})
  if cp.returncode:
   runs.append({"worker_error":{"returncode":cp.returncode,"stderr":cp.stderr[-4000:]},"distractors":d,"mode":mode,"replicate":rep})
   print(f"worker {i}/72 FAILED {mode} D={d} rep={rep}",flush=True)
  else:
   runs.append(json.loads(cp.stdout));print(f"worker {i}/72 {mode} D={d} rep={rep} order={runs[-1]['installed_order']}",flush=True)
  partial={"schema_version":1,"run_id":RUN_ID,"run_state":"partial","locked_inputs":locked,"post_run_inputs":fingerprint(),"child_logs":logs,"runs":runs}
  RAW.with_suffix(".partial.json").write_text(json.dumps(partial,indent=2,sort_keys=True)+"\n")
 post=fingerprint();raw={"schema_version":1,"run_id":RUN_ID,"locked_inputs":locked,"post_run_inputs":post,"child_logs":logs,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 logref=finish_console_capture(capture);ok=post==locked and len(runs)==72 and all("worker_error" not in x for x in runs)
 manifest=capture_run_manifest(run_id=RUN_ID,runner="scripts/substrate_task_derived_anaphora_order_estimator_v1_1.py",protocol_files=(str(PROTOCOL.relative_to(ROOT)),str(AMENDMENT.relative_to(ROOT)),str(LOCK.relative_to(ROOT))),source_files=SOURCES,analysis_files=("scripts/analyze_substrate_task_derived_anaphora_order_estimator_v1_1.py",),data_files=("tests/test_intent_migrated.py",),started_utc=started,exit_status=0 if ok else 1,stdout_stderr_capture=logref,child_processes=logs)
 OUT.write_text(json.dumps({"schema_version":1,"run_id":RUN_ID,"raw_path":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"run_manifest":manifest},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"worker_count":len(runs),"source_stable":post==locked,"raw":str(RAW.relative_to(ROOT))},indent=2));return 0 if ok else 1
if __name__=="__main__":raise SystemExit(main())
