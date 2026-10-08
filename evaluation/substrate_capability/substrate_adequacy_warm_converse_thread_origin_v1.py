#!/usr/bin/env python3
"""Source-locked pthread creation call-site census for warm converse."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_ORIGIN_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_thread_origin_v1.py'
PROBE_SOURCE=ROOT/'evaluation/substrate_capability/thread_origin_pthread_probe.c'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_origin_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_origin_v1_raw_20261002.json'
CALLER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1.py'
CALLER_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1_lock_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'
SCHEDULE=[('rayon_default','blas_default',1),('rayon_one','blas_default',1),('rayon_one','blas_one',1),('rayon_default','blas_one',1),
          ('rayon_default','blas_default',2),('rayon_one','blas_default',2),('rayon_one','blas_one',2),('rayon_default','blas_one',2),
          ('rayon_default','blas_default',3),('rayon_one','blas_default',3),('rayon_one','blas_one',3),('rayon_default','blas_one',3)]
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def compiler():return subprocess.run(['gcc','--version'],text=True,capture_output=True,check=True).stdout.splitlines()[0]
def compile_probe(dest):
 subprocess.run(['gcc','-shared','-fPIC','-O2','-fno-omit-frame-pointer','-o',str(dest),str(PROBE_SOURCE),'-ldl','-pthread'],check=True,capture_output=True)
 return sha(dest)
def frozen():
 caller=load(CALLER,'thread_origin_caller')
 base=load(BASE,'thread_origin_base')
 return {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),'probe_source':sha(PROBE_SOURCE),
  'caller_runner':sha(CALLER),'caller_lock_file':sha(CALLER_LOCK),'base_runner':sha(BASE),'base_lock_file':sha(BASE_LOCK),
  'caller_runtime_lock':caller.load_base().frozen(),'base_runtime_lock':base.frozen(),'compiler':compiler()}
def worker(mode,rep,expected):
 from substrate import world_adapter as wa
 Original=wa.WorldAdapter;marker=Path(os.environ['OZMA_THREAD_ORIGIN_MARKER']);counter={'n':0}
 class MarkerAdapter(Original):
  def converse(self,*args,**kwargs):
   n=counter['n'];counter['n']+=1
   if n!=1:return super().converse(*args,**kwargs)
   with marker.open('a') as f:f.write(json.dumps({'phase':'begin','monotonic_ns':time.monotonic_ns()})+'\n');f.flush()
   try:return super().converse(*args,**kwargs)
   finally:
    with marker.open('a') as f:f.write(json.dumps({'phase':'end','monotonic_ns':time.monotonic_ns()})+'\n');f.flush()
 wa.WorldAdapter=MarkerAdapter
 caller=load(CALLER,'thread_origin_caller_worker')
 return caller.worker(mode,rep,expected)
def run_child(rayon,blas,rep,expected,probe):
 env=os.environ.copy();env.update(OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1',PYTHONPATH=f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'evaluation/substrate_capability'}")
 env.pop('RAYON_NUM_THREADS',None);env.pop('OPENBLAS_NUM_THREADS',None)
 if rayon=='rayon_one':env['RAYON_NUM_THREADS']='1'
 if blas=='blas_one':env['OPENBLAS_NUM_THREADS']='1'
 with tempfile.TemporaryDirectory(prefix='ocelot-thread-origin-') as td:
  marker=Path(td)/'markers.jsonl';log=Path(td)/'pthread.tsv';env['OZMA_THREAD_ORIGIN_MARKER']=str(marker);env['OZMA_PTHREAD_LOG']=str(log);env['LD_PRELOAD']=str(probe)
  with tempfile.TemporaryFile(mode='w+t') as out,tempfile.TemporaryFile(mode='w+t') as err:
   proc=subprocess.Popen([sys.executable,str(RUNNER),'--worker',rayon,blas,str(rep)],cwd=ROOT,env=env,text=True,stdout=out,stderr=err)
   proc.wait();out.seek(0);stdout=out.read();err.seek(0);stderr=err.read()
  if proc.returncode:raise RuntimeError(f'{rayon}/{blas}/{rep}: {stderr[-2500:]}')
  result=json.loads(stdout.splitlines()[-1]);marks=[json.loads(x) for x in marker.read_text().splitlines()]
  if [x['phase'] for x in marks]!=['begin','end']:raise RuntimeError(f'invalid target markers: {marks}')
  lo,hi=(x['monotonic_ns'] for x in marks);events=[]
  for line in log.read_text().splitlines() if log.exists() else []:
   p=line.split('\t')
   try:ns=int(p[1])
   except (ValueError,IndexError):continue
   if lo<=ns<=hi:
    events.append({'monotonic_ns':ns,'creator_tid':int(p[2]),'pthread_handle':p[3],
                   'stack_size_bytes':int(p[4]),'frames':p[6:]})
  return {'rayon':rayon,'blas':blas,'rep':rep,'pid':result['worker']['pid'],'target_markers':marks,
          'pthread_events':events,'pthread_event_count':len(events),'rayon_observed':result['observed']['rayon_pool_threads'],
          'worker':result['worker'],'caller_cpu':result['caller_cpu'],'active_after':result['worker']['active_after']}
def main():
 if sys.argv[1:2]==['--worker']:
  lock=json.loads(LOCK.read_text());rayon,blas=sys.argv[2:4];rep=int(sys.argv[4]);print(json.dumps(worker(rayon,rep,lock['sources']['caller_runtime_lock']),sort_keys=True));return
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing to overwrite lock or capture')
  sources=frozen()
  with tempfile.TemporaryDirectory(prefix='ocelot-probe-build-') as td:binary_hash=compile_probe(Path(td)/'pthread_probe.so')
  LOCK.write_text(json.dumps({'schema':'WarmConverseThreadOriginV1Lock','sources':sources,'probe_binary_sha256':binary_hash,'schedule':SCHEDULE},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return
 lock=json.loads(LOCK.read_text())
 if lock['sources']!=frozen():raise SystemExit('source lock drift')
 if RAW.exists():raise SystemExit('capture exists; refusing overwrite')
 with tempfile.TemporaryDirectory(prefix='ocelot-probe-build-') as td:
  probe=Path(td)/'pthread_probe.so';binary_hash=compile_probe(probe)
  if binary_hash!=lock['probe_binary_sha256']:raise SystemExit('compiled probe binary differs from locked hash')
  before=frozen();rows=[]
  for rayon,blas,rep in SCHEDULE:
   row=run_child(rayon,blas,rep,lock['sources']['caller_runtime_lock'],probe);rows.append(row)
   print(json.dumps({'rayon':rayon,'blas':blas,'rep':rep,'pid':row['pid'],'pthread_events':row['pthread_event_count'],
    'wall_ms':round(row['worker']['timing_ns']['target_wall']/1e6,1),'process_cpu_ms':round(row['worker']['timing_ns']['target_cpu']/1e6,1)}),flush=True)
  after=frozen()
 cap={'schema':'WarmConverseThreadOriginV1Capture','lock':lock,'source_before':before,'source_after':after,
  'source_stable':before==after,'probe_binary_sha256':binary_hash,'host':platform.platform(),'logical_cpus':os.cpu_count(),
  'environment_baseline':{'OPENBLAS_NUM_THREADS':os.environ.get('OPENBLAS_NUM_THREADS'),'RAYON_NUM_THREADS':os.environ.get('RAYON_NUM_THREADS')},'rows':rows}
 RAW.write_text(json.dumps(cap,indent=2,sort_keys=True)+'\n');print(json.dumps({'workers':len(rows),'source_stable':cap['source_stable'],'raw':str(RAW.relative_to(ROOT))}))
if __name__=='__main__':main()
