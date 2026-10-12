#!/usr/bin/env python3
"""Fresh-process, source-locked repetition of the live ARC self-repair episode."""
import hashlib,json,os,platform,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_live_self_repair_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_LIVE_SELF_REPAIR_V1_PREREG_20261005.md'
EPISODE=ROOT/'scripts/jabberwock_live_self_repair.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_live_self_repair_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_live_self_repair_v1_20261005.json'
DIRECT=('scripts/gen_action_corr_seed.py','scripts/avatar_run_world.py','worlds/arc.py','substrate/world_adapter.py','substrate/boot_all.py','substrate/seed_loader.py','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_paths():
 dirs=('substrate','domains','worlds','runners/dsl/src','runners/dsl/python/substrate_rs')
 tree_files=[p for d in dirs for p in (ROOT/d).rglob('*') if p.is_file() and (p.suffix in ('.py','.rs') or p.name in ('Cargo.toml','Cargo.lock'))]
 seed_files=[p for d in (ROOT/'seeds',ROOT/'seeds/generated') for p in d.glob('*.json')]
 return tuple(sorted(set((RUNNER,ANALYZER,PROTOCOL,EPISODE,*(ROOT/x for x in DIRECT),*tree_files,*seed_files))))
def frozen():
 from substrate_rs import _native
 ps=source_paths();binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def one(rep):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source lock mismatch before live episode')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'scripts')))
 start=time.perf_counter_ns();cpu=time.process_time_ns()
 p=subprocess.Popen([sys.executable,str(EPISODE)],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:out,err=p.communicate(timeout=240)
 except subprocess.TimeoutExpired:
  p.kill();p.communicate();raise RuntimeError(f'live episode {rep} exceeded 240 seconds')
 wall=time.perf_counter_ns()-start;cpu_ns=time.process_time_ns()-cpu;after=frozen()
 if after!=locked:raise RuntimeError('source lock mismatch after live episode')
 fault=re.search(r'auto-minted from the live measure: True \(frame (\d+)\); auto-repaired: True \(frame (\d+)\)',out)
 gate=re.search(r"gate outcome: '([^']*)'; self axis_kind at end of committed run: '([^']*)'",out)
 return {'replicate':rep,'pid':p.pid,'exit_code':p.returncode,'wall_ns':wall,'parent_cpu_ns':cpu_ns,'minted_frame':int(fault.group(1)) if fault else None,'repaired_frame':int(fault.group(2)) if fault else None,'gate_outcome':gate.group(1) if gate else None,'final_axis_kind':gate.group(2) if gate else None,'pass_banner':'PASS —' in out,'stdout':out,'stderr':err,'sources_before':before,'sources_after':after}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentLiveSelfRepairV1Lock','sources':frozen(),'fresh_process_replicates':3},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run')
 locked=json.loads(LOCK.read_text())['sources']
 if frozen()!=locked:raise SystemExit('source lock mismatch before capture')
 rows=[one(i) for i in range(3)]
 if frozen()!=locked:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentLiveSelfRepairV1','lock_sha256':sha(LOCK),'host':platform.platform(),'python':sys.version,'runs':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
