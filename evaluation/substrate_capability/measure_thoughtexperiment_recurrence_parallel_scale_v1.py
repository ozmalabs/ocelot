#!/usr/bin/env python3
"""One-million-node extension of the recurrence sequential/concurrent wave."""
import hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_wave_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_wave_v1_lock_20261001.json'
BASE_CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_recurrence_parallel_wave_v1_raw_20261001.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_PARALLEL_SCALE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_parallel_scale_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_scale_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_parallel_scale_v1_20261002.json'
SIZE=1_000_000;FANOUT=8;BACKENDS=('full_copy','shared_pages');REPEATS=3

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('recurrence_parallel_wave_base_scale_v1',BASE)
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
 from substrate_rs import _native
 base=load_base()
 return {'runner':sha(Path(__file__).resolve()),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
  'parent_runner':sha(BASE),'parent_lock_reference':sha(BASE_LOCK),'parent_capture_reference':sha(BASE_CAPTURE),
  'inherited_current_sources':{p:sha(ROOT/p) for p in base.SOURCES},
  'loaded_native_binary':sha(Path(_native.__file__).resolve())}
def worker(backend,rep):
 base=load_base();base.SIZE=SIZE;base.FANOUTS=(FANOUT,)
 row=base.worker(backend,FANOUT,rep)
 if row.get('noise_nodes')!=SIZE:raise RuntimeError('base scale override failed')
 row['scale_protocol']='ThoughtexperimentRecurrenceParallelScaleV1'
 return row
def available_memory_bytes():
 for line in Path('/proc/meminfo').read_text().splitlines():
  if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
 raise RuntimeError('MemAvailable unavailable')
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],int(args[2])),sort_keys=True,default=str,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceParallelScaleV1Lock','sources':frozen(),
   'size':SIZE,'fanout':FANOUT,'backends':BACKENDS,'repeats':REPEATS,'candidate_count':64},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker BACKEND REPEAT')
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
 for rep in range(REPEATS):
  if available_memory_bytes()<12*1024**3:raise SystemExit('available memory below preregistered 12 GiB floor')
  order=BACKENDS if rep%2==0 else tuple(reversed(BACKENDS))
  for backend in order:
   if available_memory_bytes()<12*1024**3:raise SystemExit('available memory fell below 12 GiB floor')
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',backend,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1800)
   if p.returncode:raise RuntimeError(f'worker {backend}/{rep}: {p.stderr[-3000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]));print(f'completed {backend} repeat={rep}; {len(rows)}/6',flush=True)
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceParallelScaleV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'available_memory_at_capture_start_bytes':available_memory_bytes(),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),
  'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
