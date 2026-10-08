#!/usr/bin/env python3
"""Larger-N fresh-process continuation of the ProblemShape population sweep."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_V2_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_population_scale_v2_lock_20260927.json'
OUT=ROOT/'evaluation/reports/problem_shape_population_scale_v2_20260927.json'
V1=ROOT/'scripts/substrate_problem_shape_population_scale.py'
MEASURE=ROOT/'scripts/substrate_problem_shape_induction_economics.py'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
SIZES=[16,32,64];MIXES=['recognition','recurrent_residual'];MODES=['dynamic','frozen']
SCHEDULE=[(n,m,c) for n in SIZES for m in MIXES for c in MODES]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def runtime_inputs():
 spec=importlib.util.spec_from_file_location('seed_provenance',PROVENANCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.inputs()
def inputs():return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'reused_v1_worker_sha256':sha(V1),'measurement_helper_sha256':sha(MEASURE),'runtime_inputs':runtime_inputs(),'configuration':{'sizes':SIZES,'mixes':MIXES,'codebook_modes':MODES,'fresh_process_per_cell':True}}
def worker(n,m,c):
 spec=importlib.util.spec_from_file_location('problem_shape_population_v1',V1);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod.worker(n,m,c)
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:
  r=worker(int(os.environ['OCEL0_PS_N']),os.environ['OCEL0_PS_MIX'],os.environ['OCEL0_PS_MODE']);print(json.dumps(r,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale v2 ProblemShape source lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT / "runners/dsl/python"}:{ROOT / "scripts"}'}
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')) )"],cwd=ROOT,env=env,text=True).strip()
 if stale:raise SystemExit(f'native build stale: {stale}')
 runs=[]
 for n,m,c in SCHEDULE:
  childenv=env.copy();childenv.update(OCEL0_PS_N=str(n),OCEL0_PS_MIX=m,OCEL0_PS_MODE=c)
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=childenv,text=True,capture_output=True,timeout=240)
  record=json.loads(p.stdout) if p.stdout.strip() else {'worker_error':p.stderr}
  record.update({'v2_cell':{'N':n,'mix':m,'codebook':c},'worker_returncode':p.returncode,'worker_stderr':p.stderr,'worker_inputs':inputs()})
  runs.append(record);print(f'completed N={n} mix={m} codebook={c} rc={p.returncode}',file=sys.stderr,flush=True)
 after=inputs();checks={'twelve_workers':len(runs)==12,'twelve_unique_pids':len({r.get('process_id') for r in runs})==12,'one_each_factorial_cell':len({(r['v2_cell']['N'],r['v2_cell']['mix'],r['v2_cell']['codebook']) for r in runs})==12,'parent_source_stable':after==locked,'child_source_locks_match':all(r.get('worker_inputs')==locked for r in runs),'all_worker_native_gates_pass':all(r.get('all_checks_pass') and r.get('worker_returncode')==0 for r in runs)}
 report={'schema_version':1,'run_id':'problem-shape-population-scale-v2-20260927','locked_inputs':locked,'post_run_inputs':after,'schedule':SCHEDULE,'checks':checks,'all_checks_pass':all(checks.values()),'runs':runs,'claim_boundary':'Fresh-process N=16/32/64 continuation of one authored ProblemShape pathway; candidate counts are instrumented mechanism work. Not natural residual prevalence, broad induction, or uninstrumented timing.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('ProblemShape v2 scale gates failed')
if __name__=='__main__':main()
