#!/usr/bin/env python3
"""Test ProblemShape eventization while retaining the seed's original rule slots."""
from __future__ import annotations
import hashlib,json,os,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_RULE_ORDER_PRESERVATION_V1_2_AMENDMENT_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_rule_order_preservation_v1_2_lock_20260925.json'
CORPUS_LOCK=ROOT/'evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_2_20260925.json'
BASE=ROOT/'scripts/substrate_problem_shape_population_scale.py';CAND=ROOT/'scripts/substrate_problem_shape_all_transitions.py'
BASE_HELPER=ROOT/'scripts/substrate_problem_shape_induction_economics.py'
SEED_TRANSFORM=ROOT/'scripts/substrate_problem_shape_rule_order_seed_transform.py'
PRIOR_RAW=ROOT/'evaluation/reports/substrate_problem_shape_global_rule_attribution_20260925.json'
PRIOR_ANALYSIS=ROOT/'evaluation/reports/substrate_problem_shape_global_rule_attribution_analysis_20260925.json'
OUT=ROOT/'evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_2_20260925.json'
PART=ROOT/'evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_2_partial_20260925.json'
MIXES=['recognition','recurrent_residual'];N=32

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seed_corpus_digest():
 rows=[]
 for p in sorted((ROOT/'seeds').glob('*.json')):
  rows.append((p.name,sha(p)))
 for p in sorted((ROOT/'seeds/generated').glob('*.json')):
  rows.append((f'generated/{p.name}',sha(p)))
 payload=json.dumps(rows,separators=(',',':')).encode()
 return hashlib.sha256(payload).hexdigest()
def locked():
 paths={'preregistration':PREREG,'runner':Path(__file__),'corpus_lock':CORPUS_LOCK,'baseline_worker':BASE,'candidate_worker':CAND,
 'baseline_helper':BASE_HELPER,'seed_transformer':SEED_TRANSFORM,'prior_raw':PRIOR_RAW,'prior_analysis':PRIOR_ANALYSIS,
 'baseline_population_raw':ROOT/'evaluation/reports/substrate_problem_shape_population_scale_20260925.json',
 'problem_shape':ROOT/'domains/problem_shape.py','solver_dispatch':ROOT/'domains/solver_dispatch.py','decomposition':ROOT/'domains/problem_decomposition.py',
 'bigville':ROOT/'worlds/bigville_can_beliefs.py','shape_seed':ROOT/'seeds/problem_shape_growth.json','decode_seed':ROOT/'seeds/shape_decode_loop.json',
 'cast_seed':ROOT/'seeds/bigville_cast100.json','native':ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so',
 'build_manifest':ROOT/'runners/dsl/python/substrate_rs/_native.build.json','cargo_lock':ROOT/'runners/dsl/Cargo.lock'}
 return {k:sha(v) for k,v in paths.items()}
def make_seed_dir():
 env={**os.environ,'PYTHONPATH':f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'scripts'}"}
 code="import json;from scripts.substrate_problem_shape_rule_order_seed_transform import build;print(json.dumps(build()))"
 raw=json.loads(subprocess.check_output([sys.executable,'-c',code],cwd=ROOT,env=env,text=True).strip())
 return raw['seed_dir'],raw['manifest_sha256']
def run_worker(arm,mix,seed_dir):
 if arm=='baseline':module='substrate_problem_shape_population_scale';args=f"32,'{mix}','dynamic'"
 else:module='substrate_problem_shape_all_transitions';args=f"32,'{mix}',True,{seed_dir!r}"
 code=f"import json,sys;sys.path[:0]=['.','runners/dsl/python','scripts'];import {module} as m;m.SIZES=[2,4,8,16,32];r=m.worker({args});print(json.dumps(r,sort_keys=True));sys.exit(0 if r['all_checks_pass'] else 2)"
 env={**os.environ,'PYTHONPATH':f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'scripts'}",'PYTHONHASHSEED':'0'}
 p=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=900)
 if p.returncode:raise RuntimeError(f'{arm}/{mix} failed: {p.stdout[-1200:]} {p.stderr[-1200:]}')
 r=json.loads(p.stdout.strip().splitlines()[-1])
 if not r.get('all_checks_pass'):raise RuntimeError(f'{arm}/{mix} worker gate failed')
 if not all('all_rule_scale_audit' in x for x in r['records']):raise RuntimeError('full per-rule rows missing')
 return r
def summary(arm,r):
 wall=[x['wall_time_ns'] for x in r['records']] if arm=='baseline' else [x['treatment_observation_wall_ns'] for x in r['records']]
 cpu=[x['cpu_time_ns'] for x in r['records']] if arm=='baseline' else [x['treatment_observation_cpu_ns'] for x in r['records']]
 return {'arm':arm,'process_id':r['process_id'],'all_checks_pass':r['all_checks_pass'],'peak_rss_bytes':r.get('peak_rss_bytes',r.get('process_peak_rss_bytes',0)),
 'wall_ns_total':sum(wall),'cpu_ns_total':sum(cpu),'status_initial':[x.get('observation_status_initial') for x in r['records']],
 'status_final':[x.get('observation_status_final') for x in r['records']],'mints_by_step':[int(x.get('mint_count_delta',0)) for x in r['records']],
 'active_problem_shape_rule_positions':r['active_problem_shape_rule_positions'],'active_rule_order_sha256':r['active_rule_order_sha256'],'problem_shape_candidate_pairs_total':r['problem_shape_candidate_pairs_total'],
 'problem_shape_term_evaluations_total':r['problem_shape_term_evaluations_total'],
 'global_scale_audit':{k:sum(int(x.get('scale_audit',{}).get(k,0)) for x in r['records']) for k in ('cand_tested','term_evals_total','rule_enumerations','where_evals','graph_writes','term_units_total')},'records':r['records']}
def main():
 actual=locked()
 if json.loads(LOCK.read_text())!=actual:raise SystemExit('rule-order preservation lock mismatch')
 corpus=json.loads(CORPUS_LOCK.read_text())
 if corpus.get('corpus_digest')!=seed_corpus_digest():raise SystemExit('seed corpus drift')
 seed_dir,manifest_hash=make_seed_dir()
 env={**os.environ,'PYTHONPATH':f"{ROOT}:{ROOT/'runners/dsl/python'}"}
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale;print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
 if stale:raise SystemExit(f'native build stale: {stale}')
 if PART.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior run/checkpoint')
 rng=random.Random(20260928);schedule=[]
 for mix in MIXES:
  orders=[['baseline','candidate'] for _ in range(3)]+[['candidate','baseline'] for _ in range(3)];rng.shuffle(orders);schedule.extend((mix,o) for o in orders)
 rng.shuffle(schedule);pairs=[];pids=set()
 for i,(mix,order) in enumerate(schedule,1):
  arms={}
  for arm in order:
   r=run_worker(arm,mix,seed_dir);z=summary(arm,r)
   if z['process_id'] in pids:raise RuntimeError('duplicate process id')
   pids.add(z['process_id']);arms[arm]=z
  b,c=arms['baseline'],arms['candidate']
  parity=(b['status_initial']==c['status_initial'] and b['status_final']==c['status_final'] and b['mints_by_step']==c['mints_by_step'])
  positions_match=(b['active_rule_order_sha256']==c['active_rule_order_sha256'] and sorted(b['active_problem_shape_rule_positions'],key=b['active_problem_shape_rule_positions'].get)==sorted(c['active_problem_shape_rule_positions'],key=c['active_problem_shape_rule_positions'].get))
  pairs.append({'pair':i,'mix':mix,'N':N,'order':order,'semantic_parity':parity,'active_rule_order_match':positions_match,
   'wall_ratio':c['wall_ns_total']/b['wall_ns_total'],'cpu_ratio':c['cpu_ns_total']/b['cpu_ns_total'],'arms':arms})
  print(json.dumps({'pair':i,'mix':mix,'order':order,'semantic_parity':parity,'active_rule_order_match':positions_match,'wall_ratio':pairs[-1]['wall_ratio']}),flush=True)
  PART.write_text(json.dumps({'completed_pairs':pairs,'locked_inputs':actual,'lock_sha256':sha(LOCK),'seed_dir':seed_dir,'transformed_manifest_sha256':manifest_hash},indent=2,sort_keys=True)+'\n')
  if not parity or not positions_match:raise RuntimeError(f'pair {i} failed semantic or active-rule-order gate; checkpoint preserved')
 result={'schema_version':1,'run_id':'problem-shape-rule-order-preservation-v1.2-20260925','run_state':'locked_exploratory_order_control','design':{'N':N,'mixes':MIXES,'pairs_per_mix':6,'worker_count':len(pids),'rng_seed':20260929,'preserved_seed_rule_positions':True,'order_gate':'full_active_rule_name_sequence_sha256_plus_problem_shape_relative_order','pythonhashseed':'0'},
 'seed_dir':seed_dir,'transformed_manifest_sha256':manifest_hash,'all_gates_pass':len(pids)==24 and all(p['semantic_parity'] and p['active_rule_order_match'] for p in pairs),
 'unique_process_ids':len(pids)==24,'pairs':pairs,'provenance':{'locked_inputs':actual,'lock_sha256':sha(LOCK),'seed_corpus_digest':seed_corpus_digest(),
 'native_sha256':actual['native'],'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty_worktree':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'python':sys.version,'platform':platform.platform()},
 'interpretation_limit':'This isolates eventized ProblemShape rule positions on two authored N=32 workloads; exploratory and not substrate-wide performance or natural-task evidence.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');PART.unlink();print(json.dumps({'all_gates_pass':result['all_gates_pass'],'unique_process_ids':result['unique_process_ids'],'output':str(OUT)}));return 0 if result['all_gates_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
