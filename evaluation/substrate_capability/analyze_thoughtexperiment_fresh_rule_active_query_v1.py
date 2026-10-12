#!/usr/bin/env python3
"""Analyze cross-family fresh-rule active query capture."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/thoughtexperiment_fresh_rule_active_query_v1_scores_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_fresh_rule_active_query_v1_orders_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_fresh_rule_active_query_v1_analysis_20261002.json'
doc=json.loads(RAW.read_text());orders=json.loads(ORDERS.read_text())['workers'];workers=doc['workers'];rows=[(w,r) for w in workers for r in w['active_query_results']]
by_worker={x['worker']:x for x in orders}
summary={}
for rate in (0,50,90,99):
 group=[r for _,r in rows if r['alias_rate_percent']==rate]
 summary[str(rate)]={'n':len(group),'query_discrimination_rate':sum(r['predictions']['fault']!=r['predictions']['proposal'] for r in group)/len(group),
  'proposal_survival_rate':sum(r['survivors_after_oracle']==['proposal'] for r in group)/len(group),
  'random_discrimination_rate':sum(r['random_probe']['discriminates'] for r in group)/len(group),
  'mean_entropy_bits':statistics.mean(r['entropy_bits'] for r in group),
  'mean_query_ms':statistics.mean(r['selector_wall_ns'] for r in group)/1e6,
  'mean_native_closure_calls':statistics.mean(len(r['prediction_metrics']) for r in group)}
checks={'all_sources_stable':all(w['source_stable'] for w in workers),
 'all_fresh_targets_selected':all(by_worker[w['worker']]['target']=='classify_meter_mode' for w in workers),
 'all_graph_terms_select_flip':all(by_worker[w['worker']]['operator']=='flip_comparison' for w in workers),
 'all_proposals_match_generic_candidate':all(by_worker[w['worker']]['semantic_candidate_match'] for w in workers),
 'all_primary_targets_preserved':all(by_worker[w['worker']]['primary_target_preserved'] for w in workers) and all(w['primary_preserved'] for w in workers),
 'all_branch_receipts_verified':all(by_worker[w['worker']]['branch_receipts_verified'] and w['branch_receipts_verified'] for w in workers),
 'all_16_queries_discriminate_and_retain_proposal':all(r['entropy_bits']>0 and r['survivors_after_oracle']==['proposal'] for _,r in rows),
 'all_workers_pass_proposal_heldouts':all(len(w['heldout'])==4 and all(x['proposal_pass'] for x in w['heldout']) for w in workers),
 'fault_fails_nonzero_heldouts_each_worker':all(any(x['score']!=0 and not x['fault_pass'] for x in w['heldout']) for w in workers),
 'all_recorded_branches_reach_fixedpoint':(
   all(metric['fixedpoint_work']==0 for w in workers for row in w['active_query_results']
       for metric in [*row['prediction_metrics'].values(),*row['random_probe']['branch_metrics'].values()])
   and all(case[arm]['fixedpoint_work']==0 for w in workers for case in w['heldout'] for arm in ('fault','proposal')))}
out={'schema':'FreshRuleActiveQueryV1Analysis','checks':checks,'summary_by_neutral_rate':summary,
 'scope':'One newly authored symbolic threshold rule; prompted structural choice; harness owns task, fault, pool and oracle.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
