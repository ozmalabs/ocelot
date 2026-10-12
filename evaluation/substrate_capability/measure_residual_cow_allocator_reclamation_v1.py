#!/usr/bin/env python3
"""Add glibc allocator samples to the actual residual CoW fanout workflow."""
from __future__ import annotations
import ctypes,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/RESIDUAL_COW_ALLOCATOR_RECLAMATION_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/residual_cow_allocator_reclamation_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/residual_cow_allocator_reclamation_v1_20261002.json'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_residual_cow_allocator_reclamation_v1.py'
BACKENDS=('full_copy','shared_graph_pages');FANOUT=16;REPEATS=3
class MallInfo2(ctypes.Structure):
 _fields_=[(name,ctypes.c_size_t) for name in ('arena','ordblks','smblks','hblks','hblkhd','usmblks','fsmblks','uordblks','fordblks','keepcost')]
LIBC=ctypes.CDLL(None)
if not hasattr(LIBC,'mallinfo2') or not hasattr(LIBC,'malloc_trim'):
 raise RuntimeError('glibc mallinfo2/malloc_trim required')
LIBC.mallinfo2.restype=MallInfo2;LIBC.malloc_trim.argtypes=[ctypes.c_size_t];LIBC.malloc_trim.restype=ctypes.c_int
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 import measure_residual_cow_fanout_memory_v1 as fanout
 return {'fanout_sources':fanout.frozen(),'runner':sha(RUNNER),'protocol':sha(PROTOCOL),
  'analyzer':sha(ANALYZER),'host':platform.platform(),'libc_mallinfo2':True}
def alloc():
 m=LIBC.mallinfo2()
 return {'glibc_arena_bytes':int(m.arena),'glibc_inuse_bytes':int(m.uordblks+m.hblkhd),
  'glibc_uordblks_bytes':int(m.uordblks),'glibc_mmap_bytes':int(m.hblkhd),
  'glibc_free_arena_bytes':int(m.fordblks),'glibc_keepcost_bytes':int(m.keepcost)}
def worker(backend,repeat):
 import measure_residual_cow_fanout_memory_v1 as fanout
 before=frozen();original=fanout.smaps;calls={'n':0}
 def instrumented_smaps():
  calls['n']+=1;row=original();row.update(alloc())
  # The fanout runner samples this sixth and final stage after dropping branch refs.
  if calls['n']==6:
   row['malloc_trim_return']=int(LIBC.malloc_trim(0))
   trimmed=original();trimmed.update(alloc())
   row.update({f'post_trim_{k}':v for k,v in trimmed.items()})
  return row
 fanout.smaps=instrumented_smaps
 try:result=fanout.worker(backend,FANOUT,repeat)
 finally:fanout.smaps=original
 after=frozen()
 result.update({'allocator_wrapper_source_before':before,'allocator_wrapper_source_after':after,
  'allocator_wrapper_source_stable':before==after,'allocator_sample_count':calls['n']})
 return result
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],int(args[2])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ResidualCowAllocatorReclamationV1Lock','sources':frozen(),
   'backends':BACKENDS,'fanout':FANOUT,'repeats':REPEATS,'host_nodes':100000},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker BACKEND REPEAT')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for repeat in range(REPEATS):
  for backend in BACKENDS:
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',backend,str(repeat)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
   if p.returncode:raise RuntimeError(f'worker {backend}/{repeat}: {p.stderr[-3000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ResidualCowAllocatorReclamationV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
