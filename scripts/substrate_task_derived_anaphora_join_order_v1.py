#!/usr/bin/env python3
"""Native order replay on the two-turn anaphora task."""
from __future__ import annotations
import hashlib, itertools, json, os, random, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_ANAPHORA_JOIN_ORDER_V1_PREREG_20260928.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_ANAPHORA_JOIN_ORDER_V1_1_AMENDMENT_20260928.md"
LOCK=ROOT/"evaluation/substrate_capability/task_derived_anaphora_join_order_v1_lock_20260928.json"
RAW=ROOT/"evaluation/reports/substrate_task_derived_anaphora_join_order_v1_workers_raw_20260928.json"
OUT=ROOT/"evaluation/reports/substrate_task_derived_anaphora_join_order_v1_20260928.json"
SOURCES=(
 "seeds/intent.json","seeds/conversation.json","seeds/psychology.json","seeds/relations.json","seeds/faculty_lessons.json",
 "tests/test_intent_migrated.py","substrate/world_adapter.py","substrate/boot_core.py",
 "substrate/seeds.py","domains/seed_registry.py","runners/dsl/src/rewrite.rs",
 "runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/src/graph.rs",
 "runners/dsl/src/scale_audit.rs","runners/dsl/python/substrate_rs/_native.build.json",
 "scripts/substrate_run_manifest.py",
)
PERMS=tuple(itertools.permutations(range(4)))
CLAUSES=(
 ["m","has_mention","mention"],
 ["m","responds_to","m_prev"],
 ["m_prev","has_intent","intent_prev"],
 ["intent_prev","about_concept","c"],
)
RULE="rule_anaphoric_it_resolves_to_prior_about_concept"
RUN_ID="substrate-task-derived-anaphora-join-order-v1-20260928"

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale
 return {"files":{p:sha(ROOT/p) for p in (*SOURCES,"scripts/substrate_task_derived_anaphora_join_order_v1.py","scripts/analyze_substrate_task_derived_anaphora_join_order_v1.py",str(PROTOCOL.relative_to(ROOT)),str(AMENDMENT.relative_to(ROOT)))},
         "native_sha256":sha(Path(_native.__file__).resolve()),"native_path":str(Path(_native.__file__).resolve()),"build_stale":build_is_stale(str(ROOT)),
         "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def nid(x): return int(x.value if hasattr(x,"value") else x)
def task_output(wa,mid):
 mention=next((n for n in wa.inner.neighbours(mid,"has_mention") if wa.s.node(n)["attrs"].get("text")=="it"),None)
 refs=[] if mention is None else list(wa.inner.neighbours(mention,"refers_to"))
 concept_names=sorted(str(wa.s.node(n)["attrs"].get("name")) for n in refs)
 intent=wa.intent_of(mid)
 about=[] if intent is None else list(wa.inner.neighbours(intent,"about_concept"))
 about_names=sorted(str(wa.s.node(n)["attrs"].get("name")) for n in about)
 return {"intent_exists":intent is not None,"it_refers_to":concept_names,"intent_about_concept":about_names}
def worker(label,rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_core import load_seeds_into
 indices=tuple(map(int,label))
 if len(indices)!=4 or set(indices)!=set(range(4)): raise ValueError(label)
 wa=WorldAdapter(seeds=())
 load_seeds_into(wa.s,wa.agent,["intent"])
 inner=wa.inner;rows=inner.export_rules();target=[(i,r) for i,r in enumerate(rows) if r.get("name")==RULE and r.get("active",True)]
 if len(target)!=1: raise RuntimeError(f"expected one active {RULE}, got {len(target)}")
 old_i,prior=target[0]
 rule={k:v for k,v in prior.items() if k not in {"active","batch","content_hash","mutation_protected","revision","rule_uid"}}
 requested=[prior["match"][i] for i in indices]
 rule["match"]=requested
 if not inner.remove_rule(old_i): raise RuntimeError("could not remove target rule")
 new_i=int(inner.add_rule(rule));installed=inner.export_rules()[new_i]["match"]
 first=wa.receive_utterance("the question matters",speech_act="statement",speaker="user")
 wa.comprehend()
 second=wa.receive_utterance("answer it",speech_act="statement",speaker="user")
 inner.scale_audit_reset();inner.scale_audit_per_rule_reset();inner.scale_audit_set_per_rule_enabled(True);inner.scale_audit_set_enabled(True)
 started=time.perf_counter_ns();second_progress=int(wa.comprehend());elapsed=time.perf_counter_ns()-started
 global_counters={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()}
 per=[list(x) for x in inner.scale_audit_per_rule_snapshot()]
 clauses=[list(x) for x in inner.scale_audit_match_clause_snapshot()]
 metadata=[list(x) for x in inner.scale_audit_rule_metadata_snapshot()]
 inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False)
 terminal=dict(inner.run_rules_report(1,False));output=task_output(wa,second);graph=inner.graph_to_dict()
 # IDs are deterministic for this fixed two-turn task; canonical row sorting
 # removes incidental dictionary/list order while preserving IDs and values.
 canonical=json.dumps(graph,sort_keys=True,separators=(",",":"),default=str)
 expected={"intent_exists":True,"it_refers_to":["question"],"intent_about_concept_contains":["question"]}
 task_pass=(output["intent_exists"] and output["it_refers_to"]==["question"] and "question" in output["intent_about_concept"])
 return {"permutation":label,"replicate":rep,"pid":os.getpid(),"requested_match":requested,"installed_match":installed,
         "first_message":nid(first),"second_message":nid(second),"second_closure_progress":second_progress,
         "second_closure_elapsed_ns_audit_on":elapsed,"terminal_report":terminal,"task_output":output,
         "expected_task_output":expected,"task_oracle_pass":task_pass,
         "graph_sha256":hashlib.sha256(canonical.encode()).hexdigest(),"global_counters":global_counters,
         "per_rule_counters":per,"clause_counters":clauses,"rule_metadata":metadata}
def jobs(): return [("".join(map(str,p)),r) for p in PERMS for r in range(2)]
def main():
 if len(sys.argv)>1 and sys.argv[1]=="--worker":
  before=fingerprint();w=worker(sys.argv[2],int(sys.argv[3]));after=fingerprint()
  print(json.dumps({"before":before,"after":after,"worker":w},sort_keys=True,default=str));return 0
 if sys.argv[1:]==["--lock"]:
  if fingerprint()["build_stale"]: raise SystemExit("native build is stale")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"locked_inputs":fingerprint()},indent=2,sort_keys=True)+"\n");print(LOCK);return 0
 from substrate_run_manifest import capture_run_manifest,finish_console_capture,start_console_capture
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine();locked=fingerprint()
 if locked["build_stale"]: raise SystemExit("native build is stale")
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked: raise SystemExit("missing or stale source/native lock")
 started=datetime.now(timezone.utc).isoformat();capture=start_console_capture(RUN_ID)
 env=dict(os.environ);env["PYTHONHASHSEED"]="0";schedule=jobs();random.Random(20260928).shuffle(schedule);runs=[]
 logs=[];logdir=ROOT/"evaluation/run_logs";logdir.mkdir(parents=True,exist_ok=True)
 for i,(label,rep) in enumerate(schedule,1):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",label,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True)
  log=logdir/f"{RUN_ID}_{i:03d}.log";log.write_text("STDOUT\n"+cp.stdout+"\nSTDERR\n"+cp.stderr)
  logs.append({"path":str(log.relative_to(ROOT)),"sha256":sha(log),"returncode":cp.returncode,"permutation":label,"replicate":rep})
  if cp.returncode:
   runs.append({"worker_error":{"returncode":cp.returncode,"stderr":cp.stderr[-4000:]},"permutation":label,"replicate":rep})
   print(f"worker {i}/48 permutation={label} replicate={rep} FAILED log={log}",flush=True)
  else:
   try:
    runs.append(json.loads(cp.stdout))
    print(f"worker {i}/48 permutation={label} replicate={rep} output={runs[-1]['worker']['task_output']}",flush=True)
   except (json.JSONDecodeError,KeyError) as exc:
    runs.append({"worker_error":{"returncode":cp.returncode,"error":str(exc),"stdout":cp.stdout[-4000:],"stderr":cp.stderr[-4000:]},"permutation":label,"replicate":rep})
    print(f"worker {i}/48 permutation={label} replicate={rep} INVALID_OUTPUT log={log}",flush=True)
  partial={"schema_version":1,"run_id":RUN_ID,"run_state":"partial","locked_inputs":locked,"post_run_inputs":fingerprint(),"child_logs":logs,"runs":runs}
  RAW.with_suffix(".partial.json").write_text(json.dumps(partial,indent=2,sort_keys=True)+"\n")
 post=fingerprint();raw={"schema_version":1,"run_id":RUN_ID,"locked_inputs":locked,"post_run_inputs":post,"child_logs":logs,"runs":runs}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 logref=finish_console_capture(capture)
 ok=(post==locked and len(runs)==48 and all("worker" in x for x in runs))
 manifest=capture_run_manifest(run_id=RUN_ID,runner="scripts/substrate_task_derived_anaphora_join_order_v1.py",protocol_files=(str(PROTOCOL.relative_to(ROOT)),str(AMENDMENT.relative_to(ROOT)),str(LOCK.relative_to(ROOT))),source_files=SOURCES,analysis_files=("scripts/analyze_substrate_task_derived_anaphora_join_order_v1.py",),data_files=("tests/test_intent_migrated.py",),started_utc=started,exit_status=0 if ok else 1,stdout_stderr_capture=logref,child_processes=logs)
 OUT.write_text(json.dumps({"schema_version":1,"run_id":RUN_ID,"raw_path":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"run_manifest":manifest},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"worker_count":len(runs),"source_stable":post==locked,"raw":str(RAW.relative_to(ROOT))},indent=2))
 return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
