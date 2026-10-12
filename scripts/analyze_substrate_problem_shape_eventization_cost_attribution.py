#!/usr/bin/env python3
"""Validate and decompose detailed N=32 ProblemShape worker records."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_problem_shape_eventization_cost_attribution_20260925.json'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_eventization_cost_attribution_lock_20260925.json'
OUT=ROOT/'evaluation/reports/substrate_problem_shape_eventization_cost_attribution_analysis_20260925.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def total_metric(worker,rule,metric):
 return sum(x['count'] for row in worker['records'] for x in row.get('problem_shape_rule_scale_audit',[]) if x['rule_name']==rule and x['metric']==metric)
def total_audit(worker,key):
 return sum(int(row.get('scale_audit',{}).get(key,0)) for row in worker['records'])
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())
 if raw['provenance']['lock_sha256']!=sha(LOCK) or raw['provenance']['locked_inputs']!=lock:raise SystemExit('provenance lock mismatch')
 if lock['runner']!=sha(ROOT/'scripts/substrate_problem_shape_eventization_cost_attribution.py'):raise SystemExit('runner drift')
 pids=[w['process_id'] for pair in raw['workers'].values() for w in pair.values()]
 if len(pids)!=4 or len(set(pids))!=4 or not raw['all_semantic_gates_pass']:raise SystemExit('worker semantic/process gate failed')
 result={}
 for mix,arms in raw['workers'].items():
  b,c=arms['baseline'],arms['candidate']
  base_wall=sum(x['wall_time_ns'] for x in b['records']); cand_wall=sum(x['treatment_observation_wall_ns'] for x in c['records'])
  creation=sum(x['host_observation_creation_ns'] for x in c['records']);index=sum(x['host_index_maintenance_ns'] for x in c['records']);closure=sum(x['native_closure_wall_ns'] for x in c['records'])
  ps_base=total_metric(b,'','term_evaluations');ps_cand=total_metric(c,'','term_evaluations')
  global_metrics={}
  for key in ('term_evals_total','cand_tested','rule_enumerations','where_evals','graph_writes','term_units_total'):
   bv,cv=total_audit(b,key),total_audit(c,key)
   global_metrics[key]={'baseline':bv,'candidate':cv,'relative_reduction':(bv-cv)/bv if bv else None}
  global_metrics['non_problem_shape_term_evaluations']={'baseline':global_metrics['term_evals_total']['baseline']-b['problem_shape_term_evaluations_total'],'candidate':global_metrics['term_evals_total']['candidate']-c['problem_shape_term_evaluations_total']}
  result[mix]={'all_substrate_scale_audit':global_metrics,'baseline_observation_wall_ns':base_wall,'candidate_observation_wall_ns':cand_wall,'candidate_over_baseline_wall_ratio':cand_wall/base_wall,
    'candidate_component_ns':{'observation_creation':creation,'host_index_event_maintenance':index,'native_rule_closure':closure,'remaining_receipt_other_and_timer_residual':cand_wall-creation-index-closure},
    'candidate_component_fraction_of_total':{'observation_creation':creation/cand_wall,'host_index_event_maintenance':index/cand_wall,'native_rule_closure':closure/cand_wall,'remaining_receipt_other_and_timer_residual':(cand_wall-creation-index-closure)/cand_wall},
    'problem_shape_candidate_pairs':{'baseline':b['problem_shape_candidate_pairs_total'],'candidate':c['problem_shape_candidate_pairs_total'],'relative_reduction':1-c['problem_shape_candidate_pairs_total']/b['problem_shape_candidate_pairs_total']},
    'problem_shape_term_evaluations':{'baseline':b['problem_shape_term_evaluations_total'],'candidate':c['problem_shape_term_evaluations_total'],'relative_reduction':1-c['problem_shape_term_evaluations_total']/b['problem_shape_term_evaluations_total']},
    'ps_mint_candidate_pairs':{'baseline':total_metric(b,'ps_mint','candidate_pairs'),'candidate':total_metric(c,'ps_mint','candidate_pairs')},
    'ps_mint_term_evaluations':{'baseline':total_metric(b,'ps_mint','term_evaluations'),'candidate':total_metric(c,'ps_mint','term_evaluations')},
    'worker_peak_rss_bytes':{'baseline':b.get('peak_rss_bytes',b.get('process_peak_rss_bytes')),'candidate':c.get('peak_rss_bytes',c.get('process_peak_rss_bytes'))}}
 out={'schema_version':1,'analysis':'problem-shape-eventization-cost-attribution-independent-readback','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'all_gates_pass':True,'unique_process_ids':True,'N':32,'summaries_by_mix':result,'interpretation_limit':raw['interpretation_limit']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
