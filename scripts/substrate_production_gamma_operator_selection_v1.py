#!/usr/bin/env python3
"""Measure graph-authored operator selection through production synthesis."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault("OZMA_NO_LLM","1"); os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
from domains.engine_provenance import engine_preamble,engine_provenance,rust_source_fingerprint
engine_preamble()
import substrate_rs as srs
import domains.prog_synthesis as psy

STEM="production_gamma_operator_selection_v1_20261001"
LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json"
RAW=ROOT/f"evaluation/reports/{STEM}_raw.json"
PROTOCOL="docs/research/engine_substrate/SUBSTRATE_PRODUCTION_GAMMA_OPERATOR_SELECTION_V1_PREREG_20261001.md"
RUNNER="scripts/substrate_production_gamma_operator_selection_v1.py"
ANALYZER="scripts/analyze_substrate_production_gamma_operator_selection_v1.py"
SOURCES=(PROTOCOL,RUNNER,ANALYZER,"domains/prog_synthesis.py","domains/engine_provenance.py",
 "domains/code_writing.py","domains/prog_retrieval.py","domains/prog_moves.py","domains/prog_exact.py",
 "seeds/program_synthesis.json","seeds/program_synthesis_grounding.json","seeds/program_synthesis_opgrammar.json",
 "seeds/code_write_request_cues.json","seeds/exact_families.json","runners/dsl/src/synth_enumerate.rs",
 "runners/dsl/src/prog_eval.rs","runners/dsl/src/term.rs","runners/dsl/src/py.rs",
 "runners/dsl/src/graph_rules.rs","runners/dsl/src/substrate.rs",
 "runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
REQUEST="write a function mapping each integer input to its output from examples"
TASKS={
 "modulo":{"train":[0,1,2,3],"heldout":list(range(4,12)),"target":"x % 2"},
 "factorial":{"train":list(range(6)),"heldout":[6,7,8],"target":"x!"},
}
REPETITIONS,SEED,PARENT_TIMEOUT_S=5,20261001,15.0


def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()


def target(task:str,x:int): return x%2 if task=="modulo" else math.factorial(x)


def payload()->dict:
 native=Path(srs._native.__file__).resolve()
 return {"schema":STEM,"source_sha256":{p:sha(ROOT/p) for p in SOURCES},
  "native":{"path":str(native),"sha256":sha(native)},
  "build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),
  "engine_provenance":engine_provenance(),"rust_source_fingerprint":rust_source_fingerprint(str(ROOT)),
  "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
  "design":{"request":REQUEST,"tasks":TASKS,"repetitions":REPETITIONS,"seed":SEED,
   "candidate_limit":200000,"entrypoint":"ensure_program_synthesis -> ingest_spec -> pump",
   "explicit_ops":None,"factorial_in_native_op_table":False}}


def worker(task:str,rep:int)->dict:
 before=payload(); spec=TASKS[task]
 sub=srs.Substrate(); agent=sub.add_node("Agent",{})
 psy.ensure_program_synthesis(sub,sub._inner,agent)
 examples=[({"value":x},target(task,x)) for x in spec["train"]]
 message=psy.ingest_spec(sub,agent,REQUEST,examples,name=f"gamma_{task}")
 t0,c0=time.perf_counter_ns(),time.process_time_ns(); psy.pump(sub,agent)
 wall,cpu=time.perf_counter_ns()-t0,time.process_time_ns()-c0
 goals=sub.in_neighbours(message,"about_message")
 if len(goals)!=1: raise RuntimeError(f"expected one goal, got {len(goals)}")
 goal=goals[0]; result=psy.read_goal(sub,goal); ga=sub.node(goal)["attrs"]; ma=sub.node(message)["attrs"]
 program=result.get("program"); roots=sub.neighbours(program,"ir_subgraph") if program is not None else []
 held=[]
 if len(roots)==1:
  for x in spec["heldout"]:
   evaluation=sub._inner.evaluate({"type":"ProgEval","prog":{"type":"Var","name":"p"},
    "env":{"type":"Var","name":"e"},"oracles":None,"fuel":10000,"field":""},
    {"p":roots[0],"e":{"value":x}})
   pred=evaluation.get("result") if evaluation.get("halted") and evaluation.get("trap") is None else None
   expected=target(task,x); held.append({"x":x,"predicted":pred,"expected":expected,
     "trap":evaluation.get("trap"),"exact":pred==expected})
 program_attrs=result.get("program_attrs") or {}
 admitted=ga.get("ps_enum_gamma_ops_admitted")
 post=payload()
 return {"kind":"worker","task":task,"repetition":rep,"pid":os.getpid(),"stable":before==post,
  "request":REQUEST,"message_explicit_ops":ma.get("ps_enum_ops"),
  "status":result.get("status"),"gap_reason":result.get("gap_reason"),
  "enumerate_outcome":result.get("enumerate_outcome"),"rungs":result.get("rungs"),
  "candidate_count":ga.get("ps_enum_tested"),"solution_size":ga.get("ps_enum_solution_size"),
  "gamma_used":ga.get("ps_enum_gamma_ops_used"),"gamma_ops":admitted.split(",") if admitted else [],
  "program_count":len(sub.nodes("Program")),"program_json":program_attrs.get("program"),
  "ir":result.get("ir"),"ir_root_count":len(roots),"heldout":held,
  "pump_wall_ns":wall,"pump_cpu_ns":cpu,"peak_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
  "engine_provenance":post["engine_provenance"]}


def main()->None:
 p=argparse.ArgumentParser();p.add_argument("--lock",action="store_true");p.add_argument("--worker",nargs=2);a=p.parse_args()
 current=payload()
 if a.lock:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(current,indent=2,sort_keys=True)+"\n");print(LOCK);return
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=current:raise SystemExit("missing/stale source lock")
 if a.worker:
  print(json.dumps(worker(a.worker[0],int(a.worker[1])),sort_keys=True,default=str));return
 if RAW.exists():raise SystemExit(f"refusing to overwrite {RAW}")
 schedule=[(task,r) for task in TASKS for r in range(REPETITIONS)];random.Random(SEED).shuffle(schedule)
 env=dict(os.environ);env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 rows=[];start=time.perf_counter()
 for i,(task,rep) in enumerate(schedule,1):
  try:
   proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",task,str(rep)],cwd=ROOT,
      env=env,text=True,capture_output=True,timeout=PARENT_TIMEOUT_S)
   if proc.returncode:row={"kind":"worker_error","task":task,"repetition":rep,"error":proc.stderr[-3000:]}
   else:row=json.loads(proc.stdout.strip().splitlines()[-1])
  except subprocess.TimeoutExpired:row={"kind":"worker_error","task":task,"repetition":rep,"error":"parent timeout"}
  rows.append(row);print(f"{i}/{len(schedule)} {task} r={rep} {row['kind']} status={row.get('status')}",flush=True)
 raw={"protocol":STEM,"lock":current,"schedule":[list(x) for x in schedule],"workers":rows,
      "elapsed_s":time.perf_counter()-start,"environment":{"python":sys.version,"platform":platform.platform()}}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True,default=str)+"\n")
 print(json.dumps({"raw":str(RAW),"workers":len(rows),"errors":sum(r.get("kind")!="worker" for r in rows)}))


if __name__=="__main__":main()
