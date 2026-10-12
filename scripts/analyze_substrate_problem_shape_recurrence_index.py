#!/usr/bin/env python3
"""Analyze the locked ProblemShape recurrence-index prototype sweep."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_problem_shape_recurrence_index_20260925.json'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_recurrence_index_lock_20260925.json'
BASE=ROOT/'evaluation/reports/substrate_problem_shape_population_scale_20260925.json'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,default=ROOT/'evaluation/reports/substrate_problem_shape_recurrence_index_analysis_20260925.json'); a=ap.parse_args()
 raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text())
 if raw['baseline_raw_sha256']!=sha(BASE) or raw['native_sha256']!=lock['native_sha256'] or raw['runner_sha256']!=lock['runner_sha256']:
  raise SystemExit('source hash mismatch')
 if not raw['all_checks_pass'] or not raw['unique_worker_pids'] or len(raw['records'])!=6: raise SystemExit('semantic or fresh-process gate failed')
 out=[]
 for r in raw['records']:
  b=r['baseline']; t=sum(x['treatment_observation_wall_ns'] for x in r['records']); base=b['total_observe_wall_ns']
  row={'worker_id':r['worker_id'],'size':r['population_size'],'mix':r['task_mix'],
       'baseline_wall_ns':base,'treatment_wall_ns':t,'wall_delta_percent':100*(t/base-1),
       'host_index_maintenance_ns':r['host_index_maintenance_ns_total'],
       'baseline_candidate_pairs':b['problem_shape_candidate_pairs_total'],'treatment_candidate_pairs':r['problem_shape_candidate_pairs_total'],
       'candidate_pair_delta_percent':100*(r['problem_shape_candidate_pairs_total']/b['problem_shape_candidate_pairs_total']-1),
       'baseline_term_evaluations':b['problem_shape_term_evaluations_total'],'treatment_term_evaluations':r['problem_shape_term_evaluations_total'],
       'term_evaluation_delta_percent':100*(r['problem_shape_term_evaluations_total']/b['problem_shape_term_evaluations_total']-1),
       'baseline_ps_mint_candidate_pairs':b['ps_mint_candidate_pairs_total'],'treatment_ps_mint_candidate_pairs':r['ps_mint_candidate_pairs_total'],
       'baseline_ps_mint_term_evaluations':b['ps_mint_term_evaluations_total'],'treatment_ps_mint_term_evaluations':r['ps_mint_term_evaluations_total'],
       'treatment_peak_rss_bytes':r['process_peak_rss_bytes'],'semantic_checks':r['checks']}
  out.append(row)
 analysis={'schema_version':1,'raw_sha256':sha(RAW),'baseline_sha256':sha(BASE),'runner_sha256':sha(ROOT/'scripts/substrate_problem_shape_recurrence_index.py'),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),'lock_sha256':sha(LOCK),'all_semantics_pass':True,'unique_worker_pids':True,'records':out,
 'interpretation':{'candidate_only': 'At N=8 recurrent-residual, ps_mint candidate pairs fall from 38 to 6 and term evaluations from 358 to 116. Total ProblemShape term evaluations fall from 2011 to 1769; candidate pairs fall from 263 to 231.','timing':'Across six single-run cells, treatment observation time ranges from 6.9% faster to 9.9% slower. This is noisy exploratory evidence and establishes neither a speedup nor a slowdown.','scope':'Four ProblemShape rule match paths remain globally driven; no general complexity or natural-task claim follows.'}}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n'); print(json.dumps({'output':str(a.output.relative_to(ROOT)),'all_semantics_pass':True,'workers':len(out)})); return 0
if __name__=='__main__':raise SystemExit(main())
