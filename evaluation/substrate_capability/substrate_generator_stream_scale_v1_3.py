#!/usr/bin/env python3
"""Paired fresh-process scale panel for batch and streaming version-space synthesis."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENERATOR_STREAM_SCALE_V1_3_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_generator_stream_scale_v1_4.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_generator_stream_scale_v1_3_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_generator_stream_scale_v1_3_raw_20261002.json'
SOURCE_PATHS=('domains/generator.py','domains/engine_provenance.py','runners/dsl/src/term.rs',
 'runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs',
 'runners/dsl/src/sym.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py')
SIZES=(9,11);PROBE_COUNTS=(12,);REPLICATES=3;POOL_TIMEOUT_S=12.0;PARENT_TIMEOUT_S=16.0;POOL_LIMIT=10000
ADDRESS_SPACE_LIMIT_BYTES=2*1024*1024*1024
OPS=('Plus','Times','Minus','Div');CONSTS=(0,1,2,-1);SEED=20261004
TRAIN={'n':1.0};TRAIN_LABEL=1.0;HELDOUT=(13,17,23,31)
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def frozen():
 from substrate_rs import _native
 rows={p:sha(ROOT/p) for p in SOURCE_PATHS}
 for p in (RUNNER,PROTOCOL,ANALYZER):rows[str(p.relative_to(ROOT))]=sha(p)
 native=Path(_native.__file__).resolve()
 rows['loaded_native_binary'] = sha(native)
 manifest=ROOT/'runners/dsl/python/substrate_rs/_native.build.json'
 rows['native_build_manifest']=sha(manifest)
 return rows
def approx_heap(value,seen=None):
 import sys
 if seen is None:seen=set()
 i=id(value)
 if i in seen:return 0
 seen.add(i);n=sys.getsizeof(value)
 if isinstance(value,dict):n+=sum(approx_heap(k,seen)+approx_heap(v,seen) for k,v in value.items())
 elif isinstance(value,(list,tuple,set,frozenset)):n+=sum(approx_heap(x,seen) for x in value)
 elif hasattr(value,'__dict__'):n+=approx_heap(vars(value),seen)
 return n
def jsonable(value):
 if isinstance(value,(tuple,list)):return [jsonable(x) for x in value]
 if isinstance(value,dict):return {str(k):jsonable(v) for k,v in value.items()}
 if isinstance(value,(str,int,float,bool)) or value is None:return value
 return repr(value)
def hypothesis_digest(hypotheses):
 rows=[{'term':x.get('term_str'),'signature':jsonable(x.get('signature'))} for x in hypotheses]
 return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def worker(size,probe_count,replicate,stream):
 before=frozen()
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native engine')
 import substrate_rs as srs
 from domains.generator import synthesize
 sub=srs.Substrate()
 envs=[{'n':float(n)} for n in range(probe_count)]
 resource.setrlimit(resource.RLIMIT_AS,(ADDRESS_SPACE_LIMIT_BYTES,ADDRESS_SPACE_LIMIT_BYTES))
 t0=time.perf_counter_ns();c0=time.process_time_ns()
 result=synthesize(sub,[(TRAIN,TRAIN_LABEL)],ops=OPS,consts=CONSTS,max_size=size,
  timeout_s=POOL_TIMEOUT_S,probe_envs=envs,max_solutions=POOL_LIMIT,
  saturate_k=999999,include_output_constants=False,stream_cohort=stream)
 wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-c0
 hypotheses=result.get('hypotheses',[])
 held=[];target_present=False;training_consistent=0;exact_terms=[]
 for h in hypotheses:
  sig=h.get('signature');consistent=(isinstance(sig,(tuple,list)) and len(sig)>0
   and isinstance(sig[0],(tuple,list)) and len(sig[0])==2 and sig[0][0]=='num'
   and abs(float(sig[0][1])-TRAIN_LABEL)<=1e-9)
  training_consistent+=bool(consistent)
  correct=True
  held_predictions=[]
  for n in HELDOUT:
   prediction=h['term'].evaluate({'n':float(n)},sub)
   answer=float(n*(n+1)//2)
   held_predictions.append(prediction)
   if not isinstance(prediction,(int,float)) or abs(float(prediction)-answer)>1e-9:correct=False
  if correct:target_present=True
  held.append(correct)
  if correct:exact_terms.append({'term':h.get('term_str'),'heldout_predictions':held_predictions})
 digest=hypothesis_digest(hypotheses)
 after=frozen()
 if before!=after:raise RuntimeError('source drift inside worker')
 rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return {'size_cap':size,'probe_count':probe_count,'replicate':replicate,'mode':'stream' if stream else 'batch',
  'pid':os.getpid(),'training_example_count':1,'source_stable':before==after,'source_before':before,'source_after':after,
  'halt_reason':result.get('halt_reason'),'complete':result.get('halt_reason')=='max_size',
  'explored_terms':result.get('explored'),'distinct_behaviors':result.get('distinct'),
  'hypothesis_count':len(hypotheses),'hypothesis_sha256':digest,
  'training_consistent_hypothesis_count':training_consistent,
  'target_hypothesis_present':target_present,'heldout_exact_hypothesis_count':sum(held),
  'heldout_exact_terms':exact_terms,
  'heldout_count':len(HELDOUT),'synthesis_wall_ns':wall,'synthesis_cpu_ns':cpu,
  'process_peak_rss_native_units':rss,'process_peak_rss_units':'KiB' if sys.platform.startswith('linux') else 'platform_native',
  'address_space_limit_bytes':ADDRESS_SPACE_LIMIT_BYTES,
  'approx_hypothesis_heap_bytes':approx_heap(hypotheses)}
def main():
 from domains.engine_provenance import build_is_stale,engine_provenance,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'SubstrateGeneratorStreamScaleV1_3Lock','sources':frozen(),
   'engine':engine_provenance(),'rust_source_fingerprint':rust_source_fingerprint(str(ROOT)),
  'sizes':SIZES,'probe_counts':PROBE_COUNTS,'replicates':REPLICATES,'modes':['batch','stream'],
  'timeout_s':POOL_TIMEOUT_S,'parent_timeout_s':PARENT_TIMEOUT_S,'address_space_limit_bytes':ADDRESS_SPACE_LIMIT_BYTES,
  'hypothesis_limit':POOL_LIMIT,'seed':SEED,'training':{'n':1,'output':1},
   'heldout':list(HELDOUT),'ops':OPS,'constants':CONSTS,'include_output_constants':False},indent=2,sort_keys=True)+'\n')
  print(LOCK);return
 if sys.argv[1:2]==['--worker']:
  row=worker(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]=='stream')
  print(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False));return
 if sys.argv[1:]==['--capture']:
  if RAW.exists() or not LOCK.exists():raise SystemExit('missing lock or capture exists')
  locked=json.loads(LOCK.read_text())
  if frozen()!=locked['sources']:raise SystemExit('source drift from lock')
  schedule=[(z,p,r,m) for r in range(REPLICATES) for z in SIZES for p in PROBE_COUNTS for m in ('batch','stream')]
  random.Random(SEED).shuffle(schedule);workers=[]
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'}
  for size,probes,rep,mode in schedule:
   cmd=[sys.executable,str(RUNNER),'--worker',str(size),str(probes),str(rep),mode]
   start=time.perf_counter_ns()
   try:p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=PARENT_TIMEOUT_S)
   except subprocess.TimeoutExpired as exc:
    workers.append({'size_cap':size,'probe_count':probes,'replicate':rep,'mode':mode,
     'capture_status':'parent_timeout','parent_timeout_s':PARENT_TIMEOUT_S,
     'parent_wall_ns':time.perf_counter_ns()-start,
     'stderr_tail':str(exc.stderr or '')[-1000:]})
    continue
   if p.returncode:
    stderr=p.stderr[-1000:]
    memory_failure=any(token in stderr.lower() for token in ('memoryerror','cannot allocate memory','memory allocation of','std::bad_alloc'))
    workers.append({'size_cap':size,'probe_count':probes,'replicate':rep,'mode':mode,
     'capture_status':'address_space_failure' if memory_failure else 'worker_error',
     'return_code':p.returncode,'parent_wall_ns':time.perf_counter_ns()-start,'stderr_tail':stderr})
    continue
   row=json.loads(p.stdout.strip().splitlines()[-1]);row['capture_status']='completed'
   row['parent_wall_ns']=time.perf_counter_ns()-start;workers.append(row)
  if frozen()!=locked['sources']:raise SystemExit('source drift during capture')
  RAW.write_text(json.dumps({'schema':'SubstrateGeneratorStreamScaleV1_3Raw','lock_sha256':sha(LOCK),
   'schedule_seed':SEED,'workers':workers,'host':platform.platform(),
   'capture_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True,allow_nan=False)+'\n')
  print(RAW);return
 raise SystemExit('use --lock, --capture, or --worker SIZE PROBES REPLICATE batch|stream')
if __name__=='__main__':main()
