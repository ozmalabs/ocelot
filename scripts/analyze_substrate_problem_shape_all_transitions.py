#!/usr/bin/env python3
"""Verify and analyze the locked all-transition eventization sweep."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_problem_shape_all_transitions_20260925.json'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_all_transitions_lock_20260925.json'
BASE=ROOT/'evaluation/reports/substrate_problem_shape_population_scale_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'evaluation/reports/substrate_problem_shape_all_transitions_analysis_20260925.json');a=ap.parse_args()
 d=json.loads(RAW.read_text()); l=json.loads(LOCK.read_text())
 if d['baseline_raw_sha256']!=sha(BASE) or d['runner_sha256']!=l['runner_sha256'] or d['native_sha256']!=l['native_sha256'] or not d['all_checks_pass'] or not d['unique_worker_pids'] or len(d['records'])!=6:raise SystemExit('lock/process/semantic gate invalid')
 rows=[]
 for r in d['records']:
  b=r['baseline'];t=sum(x['treatment_observation_wall_ns'] for x in r['records']);bt=b['total_observe_wall_ns']
  rule_work={}
  for obs in r['records']:
   for z in obs['problem_shape_rule_scale_audit']:
    k=f"{z['rule_name']}:{z['metric']}";rule_work[k]=rule_work.get(k,0)+z['count']
  rows.append({'worker_id':r['worker_id'],'size':r['population_size'],'mix':r['task_mix'],'baseline_wall_ns':bt,'treatment_wall_ns':t,'wall_delta_percent':100*(t/bt-1),'baseline_candidate_pairs':b['problem_shape_candidate_pairs_total'],'treatment_candidate_pairs':r['problem_shape_candidate_pairs_total'],'candidate_pair_delta_percent':100*(r['problem_shape_candidate_pairs_total']/b['problem_shape_candidate_pairs_total']-1),'baseline_term_evaluations':b['problem_shape_term_evaluations_total'],'treatment_term_evaluations':r['problem_shape_term_evaluations_total'],'term_evaluation_delta_percent':100*(r['problem_shape_term_evaluations_total']/b['problem_shape_term_evaluations_total']-1),'host_index_event_maintenance_ns':r['host_index_maintenance_ns_total'],'problem_shape_rule_work':rule_work,'semantic_checks':r['checks']})
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'baseline_sha256':sha(BASE),'runner_sha256':sha(ROOT/'scripts/substrate_problem_shape_all_transitions.py'),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),'all_semantics_pass':True,'unique_worker_pids':True,'records':rows,'interpretation':{'N8_recurrent':'ProblemShape candidate pairs 263→66 (−74.9%); Term evaluations 2011→1008 (−49.9%). `ps_redecode` remains at 38 candidate pairs and 438 Term evaluations, reflecting the retained codebook-wide invalidation scan.','timing':'One run per cell; mixed direction, exploratory only.','scope':'The prototype eventizes routine stages in one synthetic workload family. It does not establish natural-task frequency or production-scale costs.'}}
 a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({'workers':len(rows),'all_semantics_pass':True,'analysis':str(a.output.relative_to(ROOT))}))
if __name__=='__main__':main()
