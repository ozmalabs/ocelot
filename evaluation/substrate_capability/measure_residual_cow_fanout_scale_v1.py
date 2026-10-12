#!/usr/bin/env python3
"""Source-locked 1M-node extension of the residual CoW fanout workload."""
import hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'evaluation/substrate_capability/measure_residual_cow_fanout_memory_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/RESIDUAL_COW_FANOUT_SCALE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_residual_cow_fanout_scale_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/residual_cow_fanout_scale_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/residual_cow_fanout_scale_v1_20261002.json'
SIZE=1_000_000; FANOUTS=(1,4,16); BACKENDS=('full_copy','shared_graph_pages'); REPEATS=3

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('residual_cow_fanout_memory_v1_scale_base',BASE)
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
 return mod
def frozen():
 base=load_base()
 return {'runner':sha(Path(__file__).resolve()),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
         'base_runner':sha(BASE),'base_protocol':sha(base.PROTOCOL),'base_analyzer':sha(base.ANALYZER),
         'base_lock':sha(base.LOCK),'base_sources':base.frozen()}
def worker(backend,fanout,rep):
 base=load_base();base.SIZE=SIZE
 row=base.worker(backend,fanout,rep)
 if row['noise_nodes']!=SIZE: raise RuntimeError('base worker did not apply scale override')
 row['scale_protocol']='ResidualCowFanoutScaleV1';row['scale_noise_nodes']=SIZE
 return row
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],int(args[2]),int(args[3])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists(): raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ResidualCowFanoutScaleV1Lock','sources':frozen(),'size':SIZE,
   'fanouts':FANOUTS,'backends':BACKENDS,'repeats':REPEATS},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']: raise SystemExit('usage: --lock, --run, or --worker BACKEND FANOUT REPEAT')
 if not Path('/proc/self/smaps_rollup').exists(): raise SystemExit('Linux smaps_rollup required')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']: raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 schedule=[(b,f,r) for r in range(REPEATS) for f in FANOUTS for b in BACKENDS]
 for b,f,r in schedule:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',b,str(f),str(r)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1800)
  if p.returncode: raise RuntimeError(f'worker {b}/{f}/{r}: {p.stderr[-2500:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  print(f'completed {b} fanout={f} repeat={r}; {len(rows)}/{len(schedule)}',flush=True)
 if frozen()!=lock['sources']: raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ResidualCowFanoutScaleV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'schedule':[list(x) for x in schedule],'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__': raise SystemExit(main())
