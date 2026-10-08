#!/usr/bin/env python3
"""Allocator attribution for concurrent recurrence branch cancellation."""
import ctypes,hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
BASE=ROOT/'evaluation/substrate_capability/measure_thoughtexperiment_recurrence_cancel_scale_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_cancel_scale_v1_lock_20261002.json'
BASE_CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_recurrence_cancel_scale_v1_20261002.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_CANCEL_ALLOCATOR_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_cancel_allocator_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_cancel_allocator_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_cancel_allocator_v1_20261002.json'
BACKENDS=('full_copy','shared_pages');REPEATS=3
class MallInfo2(ctypes.Structure):
 _fields_=[(n,ctypes.c_size_t) for n in ('arena','ordblks','smblks','hblks','hblkhd','usmblks','fsmblks','uordblks','fordblks','keepcost')]
LIBC=ctypes.CDLL(None)
if not hasattr(LIBC,'mallinfo2') or not hasattr(LIBC,'malloc_trim'):raise RuntimeError('glibc mallinfo2/malloc_trim required')
LIBC.mallinfo2.restype=MallInfo2;LIBC.malloc_trim.argtypes=[ctypes.c_size_t];LIBC.malloc_trim.restype=ctypes.c_int
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('recurrence_cancel_scale_allocator_base',BASE)
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
 from substrate_rs import _native
 return {'runner':sha(Path(__file__).resolve()),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
  'parent_runner':sha(BASE),'parent_lock':sha(BASE_LOCK),'parent_capture':sha(BASE_CAPTURE),
  'parent_sources':json.loads(BASE_LOCK.read_text())['sources'],'loaded_native_binary':sha(Path(_native.__file__).resolve()),
  'glibc_mallinfo2':True}
def memory():
 out={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  k,sep,v=line.partition(':')
  if sep and k in {'Rss','Pss','Private_Dirty','Private_Clean','Shared_Dirty','Shared_Clean','Swap'}:out[k]=int(v.strip().split()[0])*1024
 m=LIBC.mallinfo2();out.update({'glibc_arena_bytes':int(m.arena),'glibc_inuse_bytes':int(m.uordblks+m.hblkhd),
  'glibc_uordblks_bytes':int(m.uordblks),'glibc_mmap_bytes':int(m.hblkhd),
  'glibc_free_arena_bytes':int(m.fordblks),'glibc_keepcost_bytes':int(m.keepcost)})
 return out
def worker(backend,rep):
 base=load_base();stages={};orig_memory=base.smaps;orig_collect=base.gc.collect;count={'n':0}
 def instrumented():return memory()
 def collect(*args,**kwargs):
  result=orig_collect(*args,**kwargs);count['n']+=1
  if count['n']==1:stages['host_baseline']=memory()
  elif count['n']==2:stages['after_half_cancelled']=memory()
  elif count['n']==3:
   stages['after_all_released_before_trim']=memory()
   stages['malloc_trim_return']=int(LIBC.malloc_trim(0))
   stages['after_malloc_trim']=memory()
  return result
 base.smaps=instrumented;base.gc.collect=collect
 try:row=base.worker(backend,rep)
 finally:base.smaps=orig_memory;base.gc.collect=orig_collect
 if count['n']!=3:raise RuntimeError(f'expected 3 lifecycle gc checkpoints, saw {count["n"]}')
 row['allocator_lifecycle_stages']=stages;row['allocator_sampled_peak']={k:v for k,v in row['sampled_peak_bytes'].items() if k.startswith('glibc_')}
 return row
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],int(args[2])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceCancelAllocatorV1Lock','sources':frozen(),
   'backends':BACKENDS,'repeats':REPEATS,'size':1000000,'fanout':8,'cancel_count':4,'candidate_count':64,'sampler_ms':10},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker BACKEND REPEAT')
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
 for rep in range(REPEATS):
  for backend in (BACKENDS if rep%2==0 else tuple(reversed(BACKENDS))):
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',backend,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1800)
   if p.returncode:raise RuntimeError(f'worker {backend}/{rep}: {p.stderr[-3000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]));print(f'completed {backend} repeat={rep}; {len(rows)}/6',flush=True)
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceCancelAllocatorV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
