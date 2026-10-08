#!/usr/bin/env python3
"""Locked default-vs-oracle-grammar intervention on a hinge map."""
from __future__ import annotations
import hashlib, json, os, random, subprocess, sys, time, resource
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
from domains.engine_provenance import engine_preamble, engine_provenance
engine_preamble()
import substrate_rs as srs
import domains.prog_synthesis as psy

STEM="synthesis_rung3_hinge_grammar_contrast_v1_20260929"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SYNTHESIS_RUNG3_HINGE_GRAMMAR_CONTRAST_V1_PREREG_20260929.md"
LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json"
RAW=ROOT/f"evaluation/reports/{STEM}_raw.jsonl"
ANALYZER=ROOT/"scripts/analyze_substrate_synthesis_rung3_hinge_grammar_contrast_v1.py"
TASK="hinge_shear_balanced"
REPETITIONS=5
SCHEDULE_SEED=20260929
ARMS={"default":None,"oracle_grammar":["Plus","Minus","Max","TupleOf"]}
TRAIN=[(r,c) for c in (0,1,2,3) for r in (0,1)]
HOLDOUT=[(0,4),(2,4),(1,5),(4,5),(2,6),(5,6)]
SOURCES=(
 "domains/prog_synthesis.py","domains/engine_provenance.py","domains/code_writing.py",
 "domains/prog_retrieval.py","seeds/program_synthesis.json",
 "seeds/program_synthesis_grounding.json","seeds/program_synthesis_opgrammar.json",
 "seeds/code_write_request_cues.json","seeds/exact_families.json",
 "runners/dsl/src/synth_enumerate.rs","runners/dsl/src/prog_eval.rs",
 "runners/dsl/src/term.rs","runners/dsl/src/py.rs","runners/dsl/src/graph_rules.rs",
 "runners/dsl/src/substrate.rs","runners/dsl/python/substrate_rs/__init__.py",
 "runners/dsl/python/substrate_rs/_native.build.json")

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()

def target(r,c): return (r+max(c-1,0),c)

def lock_body():
 return {"schema":1,"protocol":STEM,"task":TASK,
         "formula":"(r+max(c-1,0),c)",
         "request":"write a function map_hinge that returns a transformed pair",
         "training":[{"inputs":{"r":r,"c":c},"output":list(target(r,c))} for r,c in TRAIN],
         "heldout":[{"inputs":{"r":r,"c":c},"output":list(target(r,c))} for r,c in HOLDOUT],
         "arms":ARMS,"repetitions":REPETITIONS,"schedule_seed":SCHEDULE_SEED,
         "default_candidate_cap":200000,"entrypoint":"ensure_program_synthesis -> ingest_spec -> pump"}

def lock_payload():
 native=Path(srs._native.__file__).resolve()
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),
         "analyzer_sha256":sha(ANALYZER),"source_sha256":{p:sha(ROOT/p) for p in SOURCES},
         "native_extension":{"path":str(native),"sha256":sha(native)},
         "engine_provenance":engine_provenance(),"inputs":lock_body()}

def run_worker(arm,rep):
 pre=lock_payload(); s=srs.Substrate(); agent=s.add_node("Agent",{})
 psy.ensure_program_synthesis(s,s._inner,agent)
 train=[({"r":r,"c":c},target(r,c)) for r,c in TRAIN]
 msg=psy.ingest_spec(s,agent,lock_body()["request"],train)
 supplied=ARMS[arm]
 if supplied is not None: s.set_attr(msg,"ps_enum_ops",list(supplied))
 start_wall,start_cpu=time.perf_counter_ns(),time.process_time_ns()
 psy.pump(s,agent)
 wall_ns,cpu_ns=time.perf_counter_ns()-start_wall,time.process_time_ns()-start_cpu
 goals=s.in_neighbours(msg,"about_message")
 if len(goals)!=1: raise RuntimeError(f"expected one Goal, found {len(goals)}")
 goal=goals[0]; result=psy.read_goal(s,goal); attrs=s.node(goal)["attrs"]
 held=[]; roots=[]
 if result.get("status")=="accepted" and result.get("program") is not None:
  roots=s.neighbours(result["program"],"ir_subgraph")
  for r,c in HOLDOUT:
   env={"r":r,"c":c}; expected=list(target(r,c)); pred=None; trap="no_ir_root"
   if len(roots)==1:
    out=s._inner.evaluate({"type":"ProgEval","prog":{"type":"Var","name":"p"},
       "env":{"type":"Var","name":"e"},"oracles":None,"fuel":10000,"field":""},
       {"p":roots[0],"e":env})
    trap=out.get("trap")
    if trap is None and out.get("halted"):
     value=out.get("result"); pred=list(value) if isinstance(value,(list,tuple)) else value
   held.append({"inputs":env,"expected":expected,"predicted":pred,"trap":trap,
                "exact":pred==expected})
 programs=[]
 for node in s.nodes("Program"):
  a=s.node(node)["attrs"]
  programs.append({"node":str(node),"name":a.get("name"),"program_json":a.get("program")})
 post=lock_payload()
 return {"kind":"worker","arm":arm,"repetition":rep,"task":TASK,
   "source_native_stable":pre==post,"status":result.get("status"),
   "gap_reason":result.get("gap_reason"),"rungs":result.get("rungs"),
   "enumerate_outcome":result.get("enumerate_outcome"),
   "enumerate_note":result.get("enumerate_note"),"attempts":result.get("attempts"),
   "program_count":len(programs),"programs":programs,"ir_root_count":len(roots),
   "heldout":held,"facts":{k:attrs.get(k) for k in (
      "ps_enum_tested","ps_enum_distinct","ps_enum_solution_size",
      "ps_enum_gamma_ops_admitted","ps_enum_gamma_ops_used","ps_enum_ops",
      "ps_enum_operator_shape","ps_enum_grounded_constants","ps_status","ps_gap_reason")},
   "pump_wall_ns":wall_ns,"pump_cpu_ns":cpu_ns,
   "peak_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
   "engine_provenance":post["engine_provenance"]}

def main():
 if sys.argv[1:]==["--lock"]:
  LOCK.parent.mkdir(parents=True,exist_ok=True)
  LOCK.write_text(json.dumps(lock_payload(),indent=2,sort_keys=True)+"\n")
  print(f"locked {LOCK.relative_to(ROOT)}"); return
 if len(sys.argv)==4 and sys.argv[1]=="--worker":
  os.environ["OZMA_NO_LLM"]="1"; os.environ["OZMA_SEED_PERSIST_DISABLED"]="1"
  print(json.dumps(run_worker(sys.argv[2],int(sys.argv[3])),sort_keys=True)); return
 if sys.argv[1:]: raise SystemExit("usage: runner.py [--lock | --worker ARM REP]")
 if not LOCK.exists() or json.loads(LOCK.read_text())!=lock_payload():
  raise SystemExit("missing/stale source/task lock; preserve old evidence and amend")
 if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
 os.environ["OZMA_NO_LLM"]="1"; os.environ["OZMA_SEED_PERSIST_DISABLED"]="1"
 schedule=[(arm,rep) for rep in range(REPETITIONS) for arm in ARMS]
 random.Random(SCHEDULE_SEED).shuffle(schedule)
 rows=[]; start=time.perf_counter_ns()
 for i,(arm,rep) in enumerate(schedule,1):
  p=subprocess.run([sys.executable,str(__file__),"--worker",arm,str(rep)],cwd=ROOT,
       env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
  if p.returncode:
   row={"kind":"worker","arm":arm,"repetition":rep,"task":TASK,"worker_failed":True,
        "returncode":p.returncode,"stdout_tail":p.stdout[-1000:],"stderr_tail":p.stderr[-2000:]}
  else:
   try: row=json.loads(p.stdout.strip().splitlines()[-1])
   except Exception as e: row={"kind":"worker","arm":arm,"repetition":rep,"task":TASK,
          "worker_failed":True,"parse_error":str(e),"stdout_tail":p.stdout[-1000:],"stderr_tail":p.stderr[-2000:]}
  rows.append(row)
  print(f"worker={i}/10 arm={arm} rep={rep+1} status={row.get('status')} tested={(row.get('facts') or {}).get('ps_enum_tested')}",flush=True)
 post=lock_payload(); locked=json.loads(LOCK.read_text())
 with RAW.open("x",encoding="utf-8") as f:
  f.write(json.dumps({"kind":"header","run_id":STEM,"lock":locked,
       "schedule":[list(x) for x in schedule]},sort_keys=True,separators=(",",":"))+"\n")
  for row in rows: f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
  f.write(json.dumps({"kind":"footer","source_native_stable":post==locked,
       "post_lock_payload":post,"capture_wall_ns":time.perf_counter_ns()-start},
       sort_keys=True,separators=(",",":"))+"\n")
 print(f"raw={RAW.relative_to(ROOT)} workers={len(rows)}")

if __name__=="__main__": main()
