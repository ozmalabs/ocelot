#!/usr/bin/env python3
"""Repeat typed-graph isomorphism diagnostics across Phase 4A scale cells."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_PHASE4A_GOAL_IDENTITY_GRAPH_ISOMORPHISM_PREREG_20260926.md"
BASE=ROOT/"scripts/substrate_phase4a_produced_goal_identity_v1.py"
SEED=ROOT/"seeds/conversation_deliberation_phase4a.json"
MATERIALIZER=ROOT/"domains/conversation_deliberation.py"
LOCK=ROOT/"evaluation/substrate_capability/phase4a_goal_identity_graph_isomorphism_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_phase4a_goal_identity_graph_isomorphism_v1_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"base_runner_sha256":sha(BASE),
  "seed_sha256":sha(SEED),"materializer_sha256":sha(MATERIALIZER),
  "native_extension_sha256":sha(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale graph-isomorphism lock")
 env=dict(os.environ);env.setdefault("OZMA_NO_LLM","1");env.setdefault("OZMA_SEED_PERSIST_DISABLED","1")
 env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 jobs=[(n,r,a) for n in (2,4,8) for r in range(3) for a in ("full","scoped")];random.Random(20260927).shuffle(jobs)
 runs=[]
 for n,rep,arm in jobs:
  code=("import importlib.util,json; from substrate_rs._native import Substrate; "+
   "old=Substrate.graph_to_dict; box={}; "+
   "def_record=None\n")
  # Define the wrapper in an exec block to keep the extension method monkeypatch local to this worker.
  code += ("def record(self):\n graph=old(self); box['graph']=graph; return graph\n"+
   "Substrate.graph_to_dict=record\n"+
   f"spec=importlib.util.spec_from_file_location('phase4a_probe',{str(BASE)!r}); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"+
   f"r=m.worker({n},{rep},{arm!r}); r['graph_snapshot']=box['graph']; print(json.dumps(r,sort_keys=True,default=str))")
  p=subprocess.run([sys.executable,"-c",code],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  runs.append(json.loads(p.stdout))
 payload={"schema_version":1,"run_id":"phase4a-goal-identity-graph-isomorphism-v1-20260926",
  "locked_inputs":locked,"lock_sha256":sha(LOCK),"environment":{"python":sys.version,"platform":platform.platform()},
  "schedule":[list(j) for j in jobs],"worker_count":len(runs),"runs":runs}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n")
 print(json.dumps({"output":str(OUT),"worker_count":len(runs),"unique_pids":len({r['pid'] for r in runs})},indent=2))
if __name__=="__main__":main()
