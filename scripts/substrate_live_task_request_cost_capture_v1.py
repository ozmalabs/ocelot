#!/usr/bin/env python3
"""Three-repeat fresh-process driver for live task lock-scoped matcher work."""
from __future__ import annotations
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORKER=ROOT/'scripts/substrate_live_task_request_cost_capture_v1_worker.py'
LOCK=ROOT/'evaluation/substrate_capability/live_task_request_cost_capture_v1_lock_20260927.json'
RAW=ROOT/'evaluation/reports/substrate_live_task_request_cost_capture_v1_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_live_task_request_cost_capture_v1_20260927.json'
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import assert_measuring_engine
spec=importlib.util.spec_from_file_location('request_cost_worker',WORKER);worker_mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker_mod)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 assert_measuring_engine()
 if sys.argv[1:]==['--lock']:
  locked=worker_mod.lock_inputs();LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':locked},indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=worker_mod.lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale source/native lock; run --lock after protocol and code are frozen')
 env={**os.environ,'OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1'};runs=[]
 for rep in range(3):
  proc=subprocess.run([sys.executable,str(WORKER),'--worker',str(rep),'traced'],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  runs.append(json.loads(proc.stdout))
 post=worker_mod.lock_inputs()
 raw={'run_id':'substrate-live-task-request-cost-capture-v1-20260927','locked_inputs':locked,'post_run_inputs':post,'runs':runs}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(raw,indent=2,sort_keys=True,default=str)+'\n')
 stable=post==locked and all(r['worker_started_inputs']==locked==r['worker_finished_inputs'] for r in runs)
 summary={'schema_version':1,'raw_workers_path':str(RAW.relative_to(ROOT)),'raw_sha256':sha(RAW),'worker_count':len(runs),'all_worker_inputs_stable':stable,'lock_sha256':sha(LOCK),'claim_boundary':'Lock-scoped candidate work for two serialized requests in one authored current-source describe_scene fixture. Analyzer owns gates and interpretation.'}
 OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2))
 if not stable:raise SystemExit('source/native fingerprint changed during capture; raw output is invalid for gated analysis')
if __name__=='__main__':main()
