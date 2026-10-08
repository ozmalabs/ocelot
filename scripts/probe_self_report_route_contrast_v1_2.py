#!/usr/bin/env python3
"""Fresh-process, source-locked conversation route contrast panel."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_2_AMENDMENT_20260927.md"
OUT=ROOT/"evaluation/reports/self_report_route_contrast_v1_2_20260927.json"
RUNTIME_SLABS=ROOT/"data/slabs"
STIMULI=[
 ("A","report your organisation"),("B","describe your organisation"),
 ("C","tell me about your organisation"),("D","report your purpose"),
 ("E","describe yourself"),("F","tell me about yourself"),
 ("G","what do you do?"),("H","what does florpification mean?"),
 ("I","florpification is a new word"),("J","what is organisation?"),
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def study_source_lock():
 import substrate_live_self_report_dimension_frame_v1 as frame
 slabs={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(RUNTIME_SLABS.glob("*")) if p.is_file()}
 scripts={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/"scripts").rglob("*.py")) if "__pycache__" not in p.parts}
 return {"code_and_seed_lock":frame.lock_inputs(),"runtime_slab_sha256":slabs,"script_module_sha256":scripts}
def worker(stimulus_id,text,rep):
 import time
 stage=time.perf_counter();print(f"worker {stimulus_id}/{rep}: start",file=sys.stderr,flush=True)
 import substrate_live_self_report_dimension_frame_v1 as frame
 started=study_source_lock()
 print(f"worker {stimulus_id}/{rep}: lock {time.perf_counter()-stage:.1f}s",file=sys.stderr,flush=True)
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());boot=load_all_seeds(a)
 print(f"worker {stimulus_id}/{rep}: boot {time.perf_counter()-stage:.1f}s",file=sys.stderr,flush=True)
 import domains.comprehend_text as comprehend
 captured=[];original=comprehend.comprehend_text
 def observe(*args,**kwargs):
  result=original(*args,**kwargs);captured.append(result);return result
 comprehend.comprehend_text=observe
 try:reply=str(a.converse(text,speech_act="instruction",speaker="alice"))
 finally:comprehend.comprehend_text=original
 print(f"worker {stimulus_id}/{rep}: converse {time.perf_counter()-stage:.1f}s",file=sys.stderr,flush=True)
 m=a._last_turn_inbound;attrs=dict(a.s.node(m)["attrs"]);c=captured[-1] if captured else None
 dispatch=(getattr(c,"dispatch",None) or {}) if c is not None else {}
 graph=a.s.graph_to_dict();finished=study_source_lock()
 print(f"worker {stimulus_id}/{rep}: graph+lock {time.perf_counter()-stage:.1f}s",file=sys.stderr,flush=True)
 return {"stimulus_id":stimulus_id,"text":text,"replicate":rep,"pid":os.getpid(),"reply":reply,
  "route":attrs.get("communication_route"),"instruction_outcome":attrs.get("instruction_outcome"),
  "message_comprehension_attrs":{k:v for k,v in attrs.items() if k.startswith("comp_")},
  "comprehension":{"kind":getattr(c,"kind",None),"intent":getattr(c,"intent",None),"dispatch":dispatch},
  "loaded_seed_count":len(boot.get("loaded_seed_ids",[])),"loaded_seed_ids":boot.get("loaded_seed_ids",[]),"failed_seeds":boot.get("failed",[]),
  "graph_nodes":len(graph.get("nodes",[])),"graph_edges":len(graph.get("edges",[])),"semantic_graph_sha256":frame.semantic_digest(graph),
  "worker_start_lock":started,"worker_end_lock":finished}
def main():
 import substrate_live_self_report_dimension_frame_v1 as frame
 if sys.argv[1:2]==["--worker"]:
  _,_,sid,text,rep=sys.argv;print(json.dumps(worker(sid,text,int(rep)),sort_keys=True,default=str));return
 driver={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"source_lock":study_source_lock()}
 if sys.argv[1:]==["--lock"]:
  print(json.dumps(driver,indent=2,sort_keys=True));return
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 jobs=[(sid,text,rep) for sid,text in STIMULI for rep in range(3)];random.Random(20260927).shuffle(jobs);rows=[]
 for sid,text,rep in jobs:
  p=subprocess.run([sys.executable,"-u",str(Path(__file__).resolve()),"--worker",sid,text,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  rows.append(json.loads(p.stdout));print(f"completed stimulus={sid} replicate={rep}",flush=True)
 post=study_source_lock();payload={"schema_version":1,"run_id":"self-report-route-contrast-v1.2-20260927","driver_lock":driver,"post_run_source_lock":post,"schedule":[list(j) for j in jobs],"runs":rows,"environment":{"python":sys.version,"platform":platform.platform()}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
 pids={r["pid"] for r in rows};source_ok=post==driver["source_lock"] and all(r["worker_start_lock"]==driver["source_lock"]==r["worker_end_lock"] for r in rows)
 print(json.dumps({"output":str(OUT),"workers":len(rows),"unique_pids":len(pids),"source_stable":source_ok},indent=2))
 if len(pids)!=30 or not source_ok:raise SystemExit("source or fresh-worker gate failed")
if __name__=="__main__":main()
