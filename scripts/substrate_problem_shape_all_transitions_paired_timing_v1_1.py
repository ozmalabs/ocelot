#!/usr/bin/env python3
"""Three randomized fresh-process timing pairs for N=8 all-transition eventization."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, random, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from substrate_problem_shape_induction_economics import sha
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_PAIRED_TIMING_V1_1_AMENDMENT_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_all_transitions_paired_timing_v1_1_lock_20260925.json'
BASE_RUNNER=ROOT/'scripts/substrate_problem_shape_population_scale.py'
CAND_RUNNER=ROOT/'scripts/substrate_problem_shape_all_transitions.py'
BASE_RAW=ROOT/'evaluation/reports/substrate_problem_shape_population_scale_20260925.json'
SEEDS=[ROOT/'seeds/problem_shape_growth.json',ROOT/'seeds/shape_decode_loop.json',ROOT/'seeds/bigville_cast100.json']
def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT/"runners/dsl/python"}:{ROOT/"scripts"}'}
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
 if stale: raise SystemExit(f'native build stale:\n{stale}')
 lock=json.loads(LOCK.read_text()); locked={'preregistration_sha256':sha(PREREG),'baseline_runner_sha256':sha(BASE_RUNNER),'candidate_runner_sha256':sha(CAND_RUNNER),'baseline_raw_sha256':sha(BASE_RAW),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),'seed_hashes':{p.name:sha(p) for p in SEEDS}}
 if any(lock.get(k)!=v for k,v in locked.items()): raise SystemExit('paired timing lock mismatch')
 rng=random.Random(20260927);
 orders=[['baseline','candidate']]*3+[['candidate','baseline']]*3; rng.shuffle(orders); pairs=[]; processes=[]
 for i,order in enumerate(orders,1):
  arms={}
  for arm in order:
   if arm=='baseline': cmd=[sys.executable,str(BASE_RUNNER),'--worker-size','8','--worker-mix','recurrent_residual','--worker-codebook','dynamic']
   else: cmd=[sys.executable,str(CAND_RUNNER),'--worker-size','8','--worker-mix','recurrent_residual']
   p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if p.returncode:
    try: payload=json.loads(p.stdout)
    except Exception: payload={'stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode}
    arms[arm]={'worker_failed':True,'output':payload}
    break
   record=json.loads(p.stdout); pid=record.get('process_id')
   ok=record.get('all_checks_pass') if arm=='candidate' else record.get('all_checks_pass')
   arms[arm]={'process_id':pid,'semantic_checks_pass':bool(ok),'record':record}
   processes.append(pid)
  pairs.append({'pair':i,'execution_order':order,'arms':arms,
                'complete':set(arms)=={'baseline','candidate'},
                'semantic_checks_pass':set(arms)=={'baseline','candidate'} and all(arms[x].get('semantic_checks_pass') for x in ('baseline','candidate'))})
  print(json.dumps({'pair':i,'order':order,'complete':pairs[-1]['complete'],'semantic_checks_pass':pairs[-1]['semantic_checks_pass']}),flush=True)
  if not pairs[-1]['complete']: break
  if not pairs[-1]['semantic_checks_pass']: break
 unique=len(processes)==len(set(processes)) and len(processes)==2*len(pairs)
 clean=all(p['complete'] and p['semantic_checks_pass'] for p in pairs) and len(pairs)==3 and unique
 for p in pairs:
  if not p['complete']: continue
  b=p['arms']['baseline']['record']; c=p['arms']['candidate']['record']
  bw=sum(r['wall_time_ns'] for r in b['records']); cw=sum(r['treatment_observation_wall_ns'] for r in c['records'])
  p['baseline_observation_wall_ns']=bw; p['candidate_observation_wall_ns']=cw; p['ratio_candidate_over_baseline']=cw/bw
  p['candidate_index_maintenance_ns']=c['host_index_maintenance_ns_total']
  p['candidate_problem_shape_candidate_pairs']=c['problem_shape_candidate_pairs_total']
  p['candidate_problem_shape_term_evaluations']=c['problem_shape_term_evaluations_total']
 result={'schema_version':1,'run_id':f'ps-all-transitions-paired-timing-v1-1-{time.strftime("%Y%m%dT%H%M%SZ",time.gmtime())}',
  'preregistration':{'path':str(PREREG.relative_to(ROOT)),'sha256':sha(PREREG)},'lock':{'path':str(LOCK.relative_to(ROOT)),'sha256':sha(LOCK)},
  'baseline_runner_sha256':sha(BASE_RUNNER),'candidate_runner_sha256':sha(CAND_RUNNER),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),
  'baseline_raw_sha256':sha(BASE_RAW),'seed_hashes':{p.name:sha(p) for p in SEEDS},'python':sys.version,'platform':platform.platform(),
  'rng_seed':20260927,'pairs':pairs,'unique_process_ids':unique,'all_checks_pass':clean,
  'interpretation_limit':'six balanced exploratory fresh-process pairs on only N=8 recurrent-residual for the all-transition candidate; no substrate-wide claim'}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'all_checks_pass':clean,'pairs':len(pairs)})); return 0 if clean else 2
if __name__=='__main__':raise SystemExit(main())
