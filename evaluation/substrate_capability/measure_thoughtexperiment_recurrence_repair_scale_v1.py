#!/usr/bin/env python3
"""Million-node scale extension for isolated recurrence-rule repair."""
import hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_repair_memory_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_repair_memory_v1_lock_20261001.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_REPAIR_SCALE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_repair_scale_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_repair_scale_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_20261002.json'
SIZE=1_000_000;BACKENDS=('full_copy','shared_pages');REPEATS=3

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('thoughtexperiment_recurrence_repair_memory_base',BASE)
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
 from substrate_rs import _native
 base=load_base()
 return {'runner':sha(Path(__file__).resolve()),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
  'base_runner':sha(BASE),'base_lock':sha(BASE_LOCK),'base_sources':json.loads(BASE_LOCK.read_text())['sources'],
  'loaded_native_binary':sha(Path(_native.__file__).resolve()),'base_source_list':list(base.SOURCES)}
def worker(backend,rep):
 base=load_base()
 row=base.worker(SIZE,backend,rep)
 row['scale_protocol']='ThoughtexperimentRecurrenceRepairScaleV1'
 if row.get('size')!=SIZE:raise RuntimeError('base worker scale mismatch')
 return row
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],int(args[2])),sort_keys=True,default=str,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceRepairScaleV1Lock','sources':frozen(),
   'size':SIZE,'backends':BACKENDS,'repeats':REPEATS,'sampler_ms':10,'closure_sweeps':5},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker BACKEND REPEAT')
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if not Path('/proc/self/smaps_rollup').exists():raise SystemExit('Linux smaps_rollup required')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for rep in range(REPEATS):
  order=list(BACKENDS) if rep%2==0 else list(reversed(BACKENDS))
  for backend in order:
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',backend,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1200)
   if p.returncode:raise RuntimeError(f'worker {backend}/{rep}: {p.stderr[-2500:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
   print(f'completed {backend} repeat={rep}; {len(rows)}/6',flush=True)
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceRepairScaleV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
