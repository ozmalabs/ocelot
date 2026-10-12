#!/usr/bin/env python3
"""Summarize the locked three-pair ProblemShape timing follow-up."""
import argparse,hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_problem_shape_recurrence_index_paired_timing_20260925.json'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_recurrence_index_paired_timing_lock_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',type=Path,default=ROOT/'evaluation/reports/substrate_problem_shape_recurrence_index_paired_timing_analysis_20260925.json'); a=ap.parse_args()
 r=json.loads(RAW.read_text()); l=json.loads(LOCK.read_text())
 if r['lock']['sha256']!=sha(LOCK) or r['candidate_runner_sha256']!=l['candidate_runner_sha256'] or r['native_sha256']!=l['native_sha256'] or not r['all_checks_pass']: raise SystemExit('locked paired run or semantic gate invalid')
 ratios=[p['ratio_candidate_over_baseline'] for p in r['pairs']]
 rows=[{'pair':p['pair'],'order':p['execution_order'],'baseline_wall_ns':p['baseline_observation_wall_ns'],'candidate_wall_ns':p['candidate_observation_wall_ns'],'candidate_over_baseline':p['ratio_candidate_over_baseline'],'delta_percent':100*(p['ratio_candidate_over_baseline']-1),'index_maintenance_ns':p['candidate_index_maintenance_ns']} for p in r['pairs']]
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'pairs':rows,'median_candidate_over_baseline':statistics.median(ratios),'median_delta_percent':100*(statistics.median(ratios)-1),'min_delta_percent':min(100*(x-1) for x in ratios),'max_delta_percent':max(100*(x-1) for x in ratios),'faster_pairs':sum(x<1 for x in ratios),'all_semantic_checks_pass':True,'interpretation':'Exploratory only: three randomized fresh-process pairs for one N=8 recurrent-residual workload; paired timing varies in sign and is not a substrate-wide speed claim.'}
 a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({'median_delta_percent':out['median_delta_percent'],'range_percent':[out['min_delta_percent'],out['max_delta_percent']],'pairs':len(rows)}))
if __name__=='__main__':main()
