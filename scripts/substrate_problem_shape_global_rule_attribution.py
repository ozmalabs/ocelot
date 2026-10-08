#!/usr/bin/env python3
"""Repeated paired N=32 readback of all native per-rule scale counters."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_GLOBAL_RULE_ATTRIBUTION_PREREG_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_global_rule_attribution_lock_20260925.json'
BASE=ROOT/'scripts/substrate_problem_shape_population_scale.py';CAND=ROOT/'scripts/substrate_problem_shape_all_transitions.py'
BASE_HELPER=ROOT/'scripts/substrate_problem_shape_induction_economics.py'
BASE_RAW=ROOT/'evaluation/reports/substrate_problem_shape_population_scale_20260925.json'
OUT=ROOT/'evaluation/reports/substrate_problem_shape_global_rule_attribution_20260925.json'
PART=ROOT/'evaluation/reports/substrate_problem_shape_global_rule_attribution_partial_20260925.json'
MIXES=['recognition','recurrent_residual'];N=32

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def locked():
 paths={'preregistration':PREREG,'runner':Path(__file__),'baseline_worker':BASE,'candidate_worker':CAND,'baseline_helper':BASE_HELPER,'baseline_raw':BASE_RAW,
 'problem_shape':ROOT/'domains/problem_shape.py','solver_dispatch':ROOT/'domains/solver_dispatch.py','decomposition':ROOT/'domains/problem_decomposition.py','bigville':ROOT/'worlds/bigville_can_beliefs.py',
 'shape_seed':ROOT/'seeds/problem_shape_growth.json','decode_seed':ROOT/'seeds/shape_decode_loop.json','cast_seed':ROOT/'seeds/bigville_cast100.json',
 'native':ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so','build_manifest':ROOT/'runners/dsl/python/substrate_rs/_native.build.json','cargo_lock':ROOT/'runners/dsl/Cargo.lock'}
 return {k:sha(v) for k,v in paths.items()}
def worker(arm,mix):
 module='substrate_problem_shape_population_scale' if arm=='baseline' else 'substrate_problem_shape_all_transitions'
 args=f"32,'{mix}','dynamic'" if arm=='baseline' else f"32,'{mix}'"
 code=f"import json,sys;sys.path[:0]=['.','runners/dsl/python','scripts'];import {module} as m;m.SIZES=[2,4,8,16,32];r=m.worker({args});print(json.dumps(r,sort_keys=True));sys.exit(0 if r['all_checks_pass'] else 2)"
 env={**os.environ,'PYTHONPATH':f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'scripts'}"}
 proc=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
 if proc.returncode:raise RuntimeError(f'{arm}/{mix} worker failed: {proc.stdout[-1000:]} {proc.stderr[-1000:]}')
 r=json.loads(proc.stdout.strip().splitlines()[-1])
 if not r.get('all_checks_pass'):raise RuntimeError(f'{arm}/{mix} worker gate failed')
 if not all('all_rule_scale_audit' in x for x in r['records']):raise RuntimeError('full per-rule audit missing')
 return r
def summarize_worker(arm,r):
 if arm=='baseline': wall=[x['wall_time_ns'] for x in r['records']];cpu=[x['cpu_time_ns'] for x in r['records']]
 else:wall=[x['treatment_observation_wall_ns'] for x in r['records']];cpu=[x['treatment_observation_cpu_ns'] for x in r['records']]
 return {'arm':arm,'process_id':r['process_id'],'all_checks_pass':r['all_checks_pass'],'boot_wall_ns':r.get('full_seed_boot_wall_ns',r.get('full_seed_boot_wall_ns',0)),
 'peak_rss_bytes':r.get('peak_rss_bytes',r.get('process_peak_rss_bytes',0)),'wall_ns_total':sum(wall),'cpu_ns_total':sum(cpu),
 'status_initial':[x.get('observation_status_initial') for x in r['records']],'status_final':[x.get('observation_status_final') for x in r['records']],
 'mints_by_step':[int(x.get('mint_count_delta',0)) for x in r['records']],
 'global_scale_audit':{k:sum(int(x.get('scale_audit',{}).get(k,0)) for x in r['records']) for k in ('cand_tested','term_evals_total','rule_enumerations','where_evals','graph_writes','term_units_total')},
 'problem_shape_candidate_pairs':r['problem_shape_candidate_pairs_total'],'problem_shape_term_evaluations':r['problem_shape_term_evaluations_total'],
 'records':r['records']}
def main():
 actual=locked()
 if json.loads(LOCK.read_text())!=actual:raise SystemExit('global attribution lock mismatch')
 env={**os.environ,'PYTHONPATH':f"{ROOT}:{ROOT/'runners/dsl/python'}"}
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale;print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
 if stale:raise SystemExit(f'native build stale: {stale}')
 if PART.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior output/checkpoint')
 rng=random.Random(20260927);schedule=[]
 for mix in MIXES:
  orders=[['baseline','candidate'] for _ in range(3)]+[['candidate','baseline'] for _ in range(3)];rng.shuffle(orders)
  schedule += [(mix,o) for o in orders]
 rng.shuffle(schedule);seen=set();pairs=[]
 for i,(mix,order) in enumerate(schedule,1):
  arms={}
  for arm in order:
   r=worker(arm,mix);sm=summarize_worker(arm,r)
   if sm['process_id'] in seen:raise RuntimeError('worker PID reused')
   seen.add(sm['process_id']);arms[arm]=sm
  b,c=arms['baseline'],arms['candidate'];parity=b['status_initial']==c['status_initial'] and b['status_final']==c['status_final'] and b['mints_by_step']==c['mints_by_step']
  pairs.append({'pair':i,'mix':mix,'N':N,'order':order,'semantic_parity':parity,'wall_ratio':c['wall_ns_total']/b['wall_ns_total'],'cpu_ratio':c['cpu_ns_total']/b['cpu_ns_total'],'arms':arms})
  print(json.dumps({'pair':i,'mix':mix,'order':order,'semantic_parity':parity,'wall_ratio':pairs[-1]['wall_ratio']}),flush=True)
  PART.write_text(json.dumps({'completed_pairs':pairs,'locked_inputs':actual,'lock_sha256':sha(LOCK)},indent=2,sort_keys=True)+'\n')
 result={'schema_version':1,'run_id':'problem-shape-global-rule-attribution-20260925','run_state':'locked_exploratory_paired_per_rule_attribution','design':{'N':N,'mixes':MIXES,'pairs_per_mix':6,'worker_count':len(seen),'order_balance_per_mix':{'baseline_first':3,'candidate_first':3},'rng_seed':20260927},
 'all_gates_pass':len(seen)==24 and all(p['semantic_parity'] for p in pairs),'unique_process_ids':len(seen)==24,'pairs':pairs,
 'provenance':{'locked_inputs':actual,'lock_sha256':sha(LOCK),'native_sha256':actual['native'],'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty_worktree':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'python':sys.version,'platform':platform.platform()},
 'interpretation_limit':'Six paired fresh-process runs per authored workload at N=32; exploratory timing and native scale-audit attribution, not natural-task prevalence or substrate-wide complexity.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');PART.unlink();print(json.dumps({'all_gates_pass':result['all_gates_pass'],'unique_process_ids':result['unique_process_ids'],'output':str(OUT)}));return 0 if result['all_gates_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
