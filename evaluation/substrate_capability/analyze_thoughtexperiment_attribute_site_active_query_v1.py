#!/usr/bin/env python3
"""Analyze attribute-site transfer and CoW/full-copy active-query capture."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/thoughtexperiment_attribute_site_active_query_v1_scores_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_attribute_site_active_query_v1_orders_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_attribute_site_active_query_v1_analysis_20261002.json'
doc=json.loads(RAW.read_text());orders=json.loads(ORDERS.read_text())['workers'];workers=doc['workers'];rows=[(w,r) for w in workers for r in w['active_query_results']]
by_worker={x['worker']:x for x in orders}
summary={}
for mode in ('cow_snapshot','full_copy'):
 summary[mode]={}
 for rate in (0,50,90,99):
  group=[r for _,r in rows if r['mode']==mode and r['alias_rate_percent']==rate]
  metrics=[r['prediction_summary'] for r in group]
  summary[mode][str(rate)]={'n':len(group),'query_discrimination_rate':sum(r['predictions']['fault']!=r['predictions']['proposal'] for r in group)/len(group),
   'proposal_survival_rate':sum(r['survivors_after_oracle']==['proposal'] for r in group)/len(group),
   'random_discrimination_rate':sum(r['random_probe']['discriminates'] for r in group)/len(group),
   'mean_entropy_bits':statistics.mean(r['entropy_bits'] for r in group),
   'mean_query_ms':statistics.mean(r['selector_wall_ns'] for r in group)/1e6,
   'mean_branch_fork_ms':statistics.mean(m['mean_branch_fork_ns'] for m in metrics)/1e6,
   'mean_candidate_patch_ms':statistics.mean(m['mean_candidate_patch_ns'] for m in metrics)/1e6,
   'mean_closure_ms':statistics.mean(m['mean_closure_ns'] for m in metrics)/1e6,
   'mean_total_prediction_ms':statistics.mean(m['mean_prediction_ns'] for m in metrics)/1e6,
   'native_closure_calls_per_pool':statistics.mean(m['n'] for m in metrics)}
checks={'all_sources_stable':all(w['source_stable'] for w in workers),
 'all_fresh_targets_selected':all(by_worker[w['worker']]['target']=='classify_meter_delta' for w in workers),
 'all_graph_terms_select_ordered_attribute_swap':all(by_worker[w['worker']]['operator']=='swap_term_leaf' and by_worker[w['worker']]['site']=="Attr key 'bad_score' -> 'good_score'" for w in workers),
 'all_proposals_match_generic_candidate':all(by_worker[w['worker']]['semantic_candidate_match'] for w in workers),
 'all_primary_targets_preserved':all(by_worker[w['worker']]['primary_target_preserved'] for w in workers) and all(w['primary_preserved'] for w in workers),
 'all_branch_receipts_verified':all(by_worker[w['worker']]['branch_receipts_verified'] and w['branch_receipts_verified'] for w in workers) and all(r['prediction_summary']['all_receipts_verified'] for _,r in rows),
 'all_32_queries_discriminate_and_retain_proposal':all(r['entropy_bits']>0 and r['survivors_after_oracle']==['proposal'] for _,r in rows),
 'all_workers_pass_proposal_heldouts':all(all(len(w['heldout'][m])==4 and all(x['proposal_pass'] for x in w['heldout'][m]) for m in ('cow_snapshot','full_copy')) for w in workers),
 'fault_fails_nonzero_heldouts_each_worker':all(all(any(x['good_score']!=0 and not x['fault_pass'] for x in w['heldout'][m]) for m in ('cow_snapshot','full_copy')) for w in workers),
 'backend_predictions_and_orders_match':all(
  next(r for r in w['active_query_results'] if r['mode']=='cow_snapshot' and r['alias_rate_percent']==rate)['query']==
  next(r for r in w['active_query_results'] if r['mode']=='full_copy' and r['alias_rate_percent']==rate)['query']
  and next(r for r in w['active_query_results'] if r['mode']=='cow_snapshot' and r['alias_rate_percent']==rate)['predictions']==
  next(r for r in w['active_query_results'] if r['mode']=='full_copy' and r['alias_rate_percent']==rate)['predictions']
  and next(r for r in w['active_query_results'] if r['mode']=='cow_snapshot' and r['alias_rate_percent']==rate)['random_probe']['predictions']==
  next(r for r in w['active_query_results'] if r['mode']=='full_copy' and r['alias_rate_percent']==rate)['random_probe']['predictions']
  for w in workers for rate in (0,50,90,99)),
 'heldout_backend_semantic_parity':all(
  w['heldout']['cow_snapshot'][i]['fault']['output']==w['heldout']['full_copy'][i]['fault']['output']
  and w['heldout']['cow_snapshot'][i]['proposal']['output']==w['heldout']['full_copy'][i]['proposal']['output']
  for w in workers for i in range(4)),
 'all_recorded_branches_reach_fixedpoint':(
   all(row['prediction_summary']['all_fixedpoint_zero'] for w in orders for row in w['selections'])
   and all(metric['fixedpoint_work']==0 for w in workers for row in w['active_query_results']
       for metric in row['random_probe']['branch_metrics'].values())
   and all(case[arm]['fixedpoint_work']==0 for w in workers for mode in ('cow_snapshot','full_copy') for case in w['heldout'][mode] for arm in ('fault','proposal'))),
 'all_recorded_receipts_valid':all(row['prediction_summary']['all_receipts_verified'] for w in orders for row in w['selections'])
   and all(metric['receipt_verified'] for w in workers for row in w['active_query_results']
   for metric in row['random_probe']['branch_metrics'].values())
   and all(case[arm]['receipt_verified'] for w in workers for mode in ('cow_snapshot','full_copy') for case in w['heldout'][mode] for arm in ('fault','proposal'))}
out={'schema':'AttributeSiteActiveQueryV1Analysis','checks':checks,'summary_by_backend_and_neutral_rate':summary,
 'mean_snapshot_creation_ms':statistics.mean(w['snapshot_creation_ns'] for w in orders)/1e6,
 'scope':'One newly authored symbolic threshold rule with a prompted ordered attribute swap; isolated predictions via snapshot CoW or full copy; harness owns task, fault, pool and oracle.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
