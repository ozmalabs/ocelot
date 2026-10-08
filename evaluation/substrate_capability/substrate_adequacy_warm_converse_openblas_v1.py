#!/usr/bin/env python3
"""Uninstrumented source-locked OpenBLAS thread-cap intervention."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_OPENBLAS_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_openblas_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_openblas_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_openblas_v1_raw_20261002.json'
CALLER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1.py'
CALLER_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1_lock_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'
SCHEDULE=[('unset',1),('one_thread',2),('one_thread',3),('unset',4),('unset',5),('one_thread',6)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def frozen():
 caller=load(CALLER,'openblas_caller');base=load(BASE,'openblas_base')
 return {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
  'caller_runner':sha(CALLER),'caller_lock_file':sha(CALLER_LOCK),'base_runner':sha(BASE),'base_lock_file':sha(BASE_LOCK),
  'caller_runtime_lock':caller.load_base().frozen(),'base_runtime_lock':base.frozen()}
def worker(mode,rep,expected):
 caller=load(CALLER,'openblas_caller_worker')
 return caller.worker('default',rep,expected)
def run_child(mode,rep,expected):
 env=os.environ.copy();env.update(OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1',PYTHONPATH=f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'evaluation/substrate_capability'}")
 env.pop('RAYON_NUM_THREADS',None);env.pop('OPENBLAS_NUM_THREADS',None)
 if mode=='one_thread':env['OPENBLAS_NUM_THREADS']='1'
 if 'LD_PRELOAD' in env:env.pop('LD_PRELOAD')
 with tempfile.TemporaryFile(mode='w+t') as out,tempfile.TemporaryFile(mode='w+t') as err:
  proc=subprocess.Popen([sys.executable,str(RUNNER),'--worker',mode,str(rep)],cwd=ROOT,env=env,text=True,stdout=out,stderr=err)
  proc.wait();out.seek(0);stdout=out.read();err.seek(0);stderr=err.read()
 if proc.returncode:raise RuntimeError(f'{mode}/{rep}: {stderr[-2500:]}')
 row=json.loads(stdout.splitlines()[-1]);row['worker']['mode']=mode;row['worker']['rep']=rep
 return row
def main():
 if sys.argv[1:2]==['--worker']:
  lock=json.loads(LOCK.read_text());mode=sys.argv[2];rep=int(sys.argv[3]);print(json.dumps(worker(mode,rep,lock['sources']['base_runtime_lock']),sort_keys=True));return
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing to overwrite lock or capture')
  LOCK.write_text(json.dumps({'schema':'WarmConverseOpenblasV1Lock','sources':frozen(),'schedule':SCHEDULE,
   'environment_baseline':{'OPENBLAS_NUM_THREADS':os.environ.get('OPENBLAS_NUM_THREADS'),'RAYON_NUM_THREADS':os.environ.get('RAYON_NUM_THREADS'),'LD_PRELOAD':os.environ.get('LD_PRELOAD')}},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return
 lock=json.loads(LOCK.read_text())
 if lock['sources']!=frozen():raise SystemExit('source lock drift')
 if RAW.exists():raise SystemExit('capture exists; refusing overwrite')
 before=frozen();rows=[]
 for mode,rep in SCHEDULE:
  row=run_child(mode,rep,lock['sources']['base_runtime_lock']);rows.append(row)
  w=row['worker'];c=row['caller_cpu'];t=w['timing_ns']
  print(json.dumps({'mode':mode,'rep':rep,'pid':w['pid'],'rayon':row['observed']['rayon_pool_threads']['after_target'],
   'wall_ms':round(t['target_wall']/1e6,2),'process_cpu_ms':round(t['target_cpu']/1e6,2),'caller_cpu_ms':round(c['caller_thread_cpu_ns']/1e6,2)}),flush=True)
 after=frozen();cap={'schema':'WarmConverseOpenblasV1Capture','lock':lock,'source_before':before,'source_after':after,
  'source_stable':before==after,'host':platform.platform(),'logical_cpus':os.cpu_count(),'rows':rows}
 RAW.write_text(json.dumps(cap,indent=2,sort_keys=True)+'\n');print(json.dumps({'workers':len(rows),'source_stable':cap['source_stable'],'raw':str(RAW.relative_to(ROOT))}))
if __name__=='__main__':main()
