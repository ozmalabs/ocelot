#!/usr/bin/env python3
"""Locked synthesis capture for off-support ambiguity and refusal controls."""
from __future__ import annotations
import hashlib,json,os,random,subprocess,sys,time,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
from domains.engine_provenance import engine_preamble,engine_provenance
engine_preamble()
import substrate_rs as srs
import domains.prog_synthesis as psy
STEM="synthesis_offsupport_ambiguity_v1_1_20261001"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SYNTHESIS_OFFSUPPORT_AMBIGUITY_V1_PREREG_20261001.md"
LOCK=ROOT/f"evaluation/substrate_capability/{STEM}_lock.json"
RAW=ROOT/f"evaluation/reports/{STEM}_raw.jsonl"
ANALYZER=ROOT/"scripts/analyze_substrate_synthesis_offsupport_ambiguity_v1_1.py"
REPETITIONS=5; SEED=20261001
TASKS={
 "ambiguous_square":{"request":"write a function mapping each input to its output from examples",
  "training":[[0,0],[1,1]],"heldout":[-3,-2,2,3]},
 "disambiguated_square":{"request":"write a function mapping each input to its output from examples",
  "training":[[-2,4],[-1,1],[0,0],[1,1],[2,4]],"heldout":[-4,-3,3,4]},
 "contradictory_square":{"request":"write a function mapping each input to its output from examples",
  "training":[[0,0],[0,1],[1,1]],"heldout":[-1,2]},
}
TASK_ORDER=list(TASKS); SOURCES=("docs/research/engine_substrate/SUBSTRATE_SYNTHESIS_OFFSUPPORT_AMBIGUITY_V1_1_AMENDMENT_20261001.md",
 "domains/prog_synthesis.py","domains/engine_provenance.py","domains/code_writing.py",
 "domains/prog_retrieval.py","seeds/program_synthesis.json","seeds/program_synthesis_grounding.json",
 "seeds/program_synthesis_opgrammar.json","seeds/code_write_request_cues.json","seeds/exact_families.json",
 "runners/dsl/src/synth_enumerate.rs","runners/dsl/src/prog_eval.rs","runners/dsl/src/term.rs",
 "runners/dsl/src/py.rs","runners/dsl/src/graph_rules.rs","runners/dsl/src/substrate.rs",
 "runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def target(t,x):return x*x
def body():
 return {"schema":1,"protocol":STEM,"tasks":json.loads(json.dumps(TASKS)),"task_order":TASK_ORDER,
  "repetitions":REPETITIONS,"schedule_seed":SEED,"candidate_cap":200000,
  "entrypoint":"ensure_program_synthesis -> ingest_spec -> pump"}
def payload():
 native=Path(srs._native.__file__).resolve()
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"analyzer_sha256":sha(ANALYZER),
  "source_sha256":{p:sha(ROOT/p) for p in SOURCES},"native_extension":{"path":str(native),"sha256":sha(native)},
  "engine_provenance":engine_provenance(),"inputs":body()}
def worker(task,rep):
 pre=payload(); spec=TASKS[task]; examples=[({"value":x},y) for x,y in spec["training"]]
 s=srs.Substrate(); agent=s.add_node("Agent",{}); psy.ensure_program_synthesis(s,s._inner,agent)
 msg=psy.ingest_spec(s,agent,spec["request"],examples,name=task)
 w0,c0=time.perf_counter_ns(),time.process_time_ns(); psy.pump(s,agent); wall,cpu=time.perf_counter_ns()-w0,time.process_time_ns()-c0
 goals=s.in_neighbours(msg,"about_message")
 if len(goals)!=1:raise RuntimeError(f"expected one goal, got {len(goals)}")
 g=goals[0]; result=psy.read_goal(s,g); ga=s.node(g)["attrs"]; ma=s.node(msg)["attrs"]
 held=[]; roots=[]
 if result.get("status")=="accepted" and result.get("program") is not None:
  roots=s.neighbours(result["program"],"ir_subgraph")
  for x in spec["heldout"]:
   pred=None; trap="ir_root_count"
   if len(roots)==1:
    out=s._inner.evaluate({"type":"ProgEval","prog":{"type":"Var","name":"p"},"env":{"type":"Var","name":"e"},
      "oracles":None,"fuel":10000,"field":""},{"p":roots[0],"e":{"value":x}})
    trap=out.get("trap")
    if trap is None and out.get("halted"):pred=out.get("result")
   held.append({"input":x,"expected":target(task,x),"predicted":pred,"trap":trap,"exact":pred==target(task,x)})
 programs=[]
 for n in s.nodes("Program"):
  a=s.node(n)["attrs"]; programs.append({"node":str(n),"name":a.get("name"),"program_json":a.get("program")})
 post=payload()
 return {"kind":"worker","task":task,"repetition":rep,"pid":os.getpid(),"request":spec["request"],"source_native_stable":pre==post,
  "status":result.get("status"),"gap_reason":result.get("gap_reason"),"rungs":result.get("rungs"),
  "enumerate_outcome":result.get("enumerate_outcome"),"program_count":len(programs),"programs":programs,
  "ir_root_count":len(roots),"heldout":held,"facts":{k:ga.get(k) for k in (
    "ps_enum_tested","ps_enum_distinct","ps_enum_solution_size","ps_enum_gamma_ops_admitted",
    "ps_enum_gamma_ops_used","ps_enum_ops","ps_enum_operator_shape","ps_enum_grounded_constants")},
  "message_facts":{k:ma.get(k) for k in ("ps_tokens","ps_enum_ops","ps_enum_operator_shape","ps_operator_shape_selected")},
  "pump_wall_ns":wall,"pump_cpu_ns":cpu,"peak_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
  "engine_provenance":post["engine_provenance"]}
def main():
 if sys.argv[1:]==["--lock"]:
  LOCK.parent.mkdir(parents=True,exist_ok=True); LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+"\n"); print(f"locked {LOCK.relative_to(ROOT)}"); return
 if len(sys.argv)==4 and sys.argv[1]=="--worker":
  os.environ["OZMA_NO_LLM"]="1"; os.environ["OZMA_SEED_PERSIST_DISABLED"]="1"; print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True)); return
 if sys.argv[1:]:raise SystemExit("usage: runner.py [--lock | --worker TASK REP]")
 if not LOCK.exists() or json.loads(LOCK.read_text())!=payload():raise SystemExit("missing/stale lock; preserve evidence and amend")
 if RAW.exists():raise SystemExit(f"refusing to overwrite {RAW}")
 os.environ["OZMA_NO_LLM"]="1"; os.environ["OZMA_SEED_PERSIST_DISABLED"]="1"
 schedule=[(t,r) for r in range(REPETITIONS) for t in TASK_ORDER]; random.Random(SEED).shuffle(schedule)
 rows=[]; start=time.perf_counter_ns()
 for i,(task,rep) in enumerate(schedule,1):
  p=subprocess.run([sys.executable,str(__file__),"--worker",task,str(rep)],cwd=ROOT,env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
  if p.returncode:row={"kind":"worker","task":task,"repetition":rep,"worker_failed":True,"returncode":p.returncode,"stdout_tail":p.stdout[-1000:],"stderr_tail":p.stderr[-2000:]}
  else:
   try:row=json.loads(p.stdout.strip().splitlines()[-1])
   except Exception as e:row={"kind":"worker","task":task,"repetition":rep,"worker_failed":True,"parse_error":str(e)}
  rows.append(row); print(f"worker={i}/15 task={task} rep={rep+1} status={row.get('status')} candidates={(row.get('facts') or {}).get('ps_enum_tested')}",flush=True)
 locked=json.loads(LOCK.read_text()); post=payload()
 with RAW.open("x",encoding="utf-8") as f:
  f.write(json.dumps({"kind":"header","run_id":STEM,"lock":locked,"schedule":[list(x) for x in schedule]},sort_keys=True,separators=(",",":"))+"\n")
  for row in rows:f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
  f.write(json.dumps({"kind":"footer","source_native_stable":post==locked,"post_lock_payload":post,"capture_wall_ns":time.perf_counter_ns()-start},sort_keys=True,separators=(",",":"))+"\n")
 print(f"raw={RAW.relative_to(ROOT)} workers={len(rows)}")
if __name__=="__main__":main()
