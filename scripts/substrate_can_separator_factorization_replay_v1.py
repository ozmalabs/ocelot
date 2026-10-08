#!/usr/bin/env python3
"""Fresh-process, source/native-locked replay of the CAN separator envelope."""
from __future__ import annotations
import contextlib,hashlib,io,json,os,platform,random,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_CAN_SEPARATOR_FACTORIZATION_REPLAY_PREREG_20260926.md"
BASE=ROOT/"scripts/can_separator_factorization_envelope.py"
SOURCES={"jt":ROOT/"domains/can_junction_tree.py","width":ROOT/"domains/graph_treewidth.py","graph_rs":ROOT/"runners/dsl/src/graph.rs","py_rs":ROOT/"runners/dsl/src/py.rs"}
LOCK=ROOT/"evaluation/substrate_capability/can_separator_factorization_replay_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/can_separator_factorization_replay_v1_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"wrapper_sha256":sha(__file__),"base_runner_sha256":sha(BASE),"source_sha256":{k:sha(v) for k,v in SOURCES.items()},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def worker(rep,raw_out,result_out):
 start=lock_inputs()
 import can_separator_factorization_envelope as base
 base.OUT=Path(raw_out)
 with contextlib.redirect_stdout(io.StringIO()):base.main()
 payload=json.loads(Path(raw_out).read_text());end=lock_inputs()
 envelope={"replicate":rep,"pid":os.getpid(),"started_inputs":start,"finished_inputs":end,"base_capture":payload}
 Path(result_out).write_text(json.dumps(envelope,sort_keys=True)+"\n")
 return {"replicate":rep,"pid":os.getpid(),"stable_inputs":start==end}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==5 and sys.argv[1]=="--worker":
  r=worker(int(sys.argv[2]),sys.argv[3],sys.argv[4]);print(json.dumps(r));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1");env["PYTHONPATH"]=str(ROOT/"runners/dsl/python")+os.pathsep+str(ROOT)+os.pathsep+env.get("PYTHONPATH","")
 runs=[];worker_summaries=[]
 with tempfile.TemporaryDirectory(prefix="can-separator-replay-") as td:
  for rep in range(3):
   raw=Path(td)/f"worker_{rep}_raw.json";result=Path(td)/f"worker_{rep}_envelope.json"
   proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(rep),str(raw),str(result)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=120)
   worker_summaries.append(json.loads(proc.stdout));runs.append(json.loads(result.read_text()))
 post=lock_inputs();base_ok=lambda r:len(r["base_capture"].get("runs",[]))==96 and all(r["base_capture"]["checks"].values())
 checks={"three_fresh_workers":len({r["pid"] for r in runs})==3,"worker_and_parent_source_stability":post==locked and all(r["started_inputs"]==locked==r["finished_inputs"] for r in runs),"all_workers_have_96_valid_cases":all(base_ok(r) for r in runs),"source_sha_matches_native_manifest":all(r["base_capture"]["source_sha256"]["domains/can_junction_tree.py"]==locked["source_sha256"]["jt"] and r["base_capture"]["source_sha256"]["domains/graph_treewidth.py"]==locked["source_sha256"]["width"] for r in runs)}
 payload={"schema_version":1,"run_id":"can-separator-factorization-current-source-replay-v1-20260926","claim_boundary":"Three fresh current-source replays of the 96 explicit shared-separator cases; source/native provenance and exact cost-law checks, not evidence of automatic frame discovery or natural locality.","locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},"worker_summaries":worker_summaries,"checks":checks,"workers":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("replay validity failed")
if __name__=="__main__":main()
