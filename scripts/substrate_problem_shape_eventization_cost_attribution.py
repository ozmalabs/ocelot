#!/usr/bin/env python3
"""Capture detailed per-step timings from one N=32 worker per arm and mix."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_EVENTIZATION_COST_ATTRIBUTION_PREREG_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_eventization_cost_attribution_lock_20260925.json'
BASE=ROOT/'scripts/substrate_problem_shape_population_scale.py'; CAND=ROOT/'scripts/substrate_problem_shape_all_transitions.py'
OUT=ROOT/'evaluation/reports/substrate_problem_shape_eventization_cost_attribution_20260925.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def locked():
 ps={'preregistration':PREREG,'runner':Path(__file__),'baseline_worker':BASE,'candidate_worker':CAND,
 'problem_shape':ROOT/'domains/problem_shape.py','solver_dispatch':ROOT/'domains/solver_dispatch.py','decomposition':ROOT/'domains/problem_decomposition.py',
 'bigville':ROOT/'worlds/bigville_can_beliefs.py','shape_seed':ROOT/'seeds/problem_shape_growth.json','decode_seed':ROOT/'seeds/shape_decode_loop.json',
 'cast_seed':ROOT/'seeds/bigville_cast100.json','native':ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so',
 'build_manifest':ROOT/'runners/dsl/python/substrate_rs/_native.build.json','cargo_lock':ROOT/'runners/dsl/Cargo.lock'}
 return {k:sha(v) for k,v in ps.items()}
def run_worker(arm,mix):
 mod='substrate_problem_shape_population_scale' if arm=='baseline' else 'substrate_problem_shape_all_transitions'
 args=f"32,'{mix}','dynamic'" if arm=='baseline' else f"32,'{mix}'"
 code=f"import json,sys;sys.path[:0]=['.','runners/dsl/python','scripts'];import {mod} as m;m.SIZES=[2,4,8,16,32];r=m.worker({args});print(json.dumps(r,sort_keys=True));sys.exit(0 if r['all_checks_pass'] else 2)"
 env={**os.environ,'PYTHONPATH':f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'scripts'}"}
 p=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
 if p.returncode: raise RuntimeError(f'{arm}/{mix} failed: {p.stdout[-1000:]} {p.stderr[-1000:]}')
 r=json.loads(p.stdout.strip().splitlines()[-1])
 if not r.get('all_checks_pass'): raise RuntimeError(f'{arm}/{mix} semantic gate failed')
 return r

def main():
 actual=locked()
 if json.loads(LOCK.read_text())!=actual: raise SystemExit('cost attribution lock mismatch')
 env={**os.environ,'PYTHONPATH':f"{ROOT}:{ROOT/'runners/dsl/python'}"}
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale;print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
 if stale: raise SystemExit(f'native build stale: {stale}')
 out={}; pids=[]
 for mix,order in [('recognition',['baseline','candidate']),('recurrent_residual',['candidate','baseline'])]:
  out[mix]={}
  for arm in order:
   raw=run_worker(arm,mix)
   if raw['process_id'] in pids: raise RuntimeError('duplicate process id')
   pids.append(raw['process_id']);out[mix][arm]=raw
   print(json.dumps({'mix':mix,'arm':arm,'pid':raw['process_id'],'all_checks_pass':raw['all_checks_pass']}),flush=True)
 result={'schema_version':1,'run_id':'problem-shape-eventization-cost-attribution-20260925','run_state':'locked_exploratory_component_diagnostic',
  'design':{'N':32,'mixes':['recognition','recurrent_residual'],'one_worker_per_arm_and_mix':True,'order_by_mix':{'recognition':['baseline','candidate'],'recurrent_residual':['candidate','baseline']}},
  'all_semantic_gates_pass':all(r['all_checks_pass'] for pair in out.values() for r in pair.values()),'unique_process_ids':len(pids)==4,
  'workers':out,'provenance':{'locked_inputs':actual,'lock_sha256':sha(LOCK),'native_sha256':actual['native'],'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty_worktree':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'python':sys.version,'platform':platform.platform()},
  'interpretation_limit':'One fresh process per arm/mix; descriptive candidate decomposition only, no causal or paired speedup inference.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'all_semantic_gates_pass':result['all_semantic_gates_pass'],'unique_process_ids':result['unique_process_ids'],'output':str(OUT)}));return 0 if result['all_semantic_gates_pass'] and result['unique_process_ids'] else 2
if __name__=='__main__':raise SystemExit(main())
