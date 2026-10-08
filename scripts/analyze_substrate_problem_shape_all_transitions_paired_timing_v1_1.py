#!/usr/bin/env python3
"""Independently validate and summarize the balanced six-pair run."""
import argparse,hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_problem_shape_all_transitions_paired_timing_v1_1_20260925.json'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_all_transitions_paired_timing_v1_1_lock_20260925.json'
COORD=ROOT/'scripts/substrate_problem_shape_all_transitions_paired_timing_v1_1.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'evaluation/reports/substrate_problem_shape_all_transitions_paired_timing_v1_1_analysis_20260925.json');a=ap.parse_args()
 r=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text())
 if r['lock']['sha256']!=sha(LOCK) or r['candidate_runner_sha256']!=lock['candidate_runner_sha256'] or r['native_sha256']!=lock['native_sha256']:raise SystemExit('worker artifact lock mismatch')
 ps=r['pairs']
 if len(ps)!=6 or not all(p['complete'] and p['semantic_checks_pass'] for p in ps):raise SystemExit('one or more pair/semantic worker checks failed')
 pids=[p['arms'][arm]['process_id'] for p in ps for arm in ('baseline','candidate')]
 if len(pids)!=12 or len(set(pids))!=12 or not r['unique_process_ids']:raise SystemExit('process identity gate failed')
 orders=[tuple(p['execution_order']) for p in ps]
 if orders.count(('baseline','candidate'))!=3 or orders.count(('candidate','baseline'))!=3:raise SystemExit('paired order is not balanced')
 ratios=[p['ratio_candidate_over_baseline'] for p in ps]
 rows=[{'pair':p['pair'],'order':p['execution_order'],'baseline_wall_ns':p['baseline_observation_wall_ns'],'candidate_wall_ns':p['candidate_observation_wall_ns'],'ratio':p['ratio_candidate_over_baseline'],'delta_percent':100*(p['ratio_candidate_over_baseline']-1),'host_index_event_maintenance_ns':p['candidate_index_maintenance_ns']} for p in ps]
 out={'schema_version':1,'raw_sha256':sha(RAW),'execution_lock_sha256':sha(LOCK),'coordinator_script_sha256_post_run':sha(COORD),'pre_run_coordinator_hash_was_locked':False,'raw_runner_aggregate_flag':r['all_checks_pass'],'aggregate_flag_correction':'The coordinator hard-coded a three-pair completion check; six complete semantically valid pairs were run. This independent validator checks the preregistered six-pair requirements directly.','pair_count':6,'balanced_orders':True,'unique_process_ids':True,'all_worker_semantics_pass':True,'pairs':rows,'median_candidate_over_baseline':statistics.median(ratios),'median_delta_percent':100*(statistics.median(ratios)-1),'delta_range_percent':[min(100*(x-1) for x in ratios),max(100*(x-1) for x in ratios)],'candidate_faster_pairs':sum(x<1 for x in ratios),'interpretation':'Exploratory timing evidence for one N=8 recurrent-residual workload; timing range is wide and sample remains small. The raw report is retained with its erroneous aggregate flag.'}
 a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'pair_count':6,'median_delta_percent':out['median_delta_percent'],'range':out['delta_range_percent'],'independent_validation_pass':True}))
if __name__=='__main__':main()
