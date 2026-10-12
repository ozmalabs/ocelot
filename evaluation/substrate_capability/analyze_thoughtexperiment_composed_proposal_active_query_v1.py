#!/usr/bin/env python3
"""Analyze composed proposal active-query capture."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/thoughtexperiment_composed_proposal_active_query_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_composed_proposal_active_query_v1_analysis_20261002.json'
doc=json.loads(RAW.read_text()); workers=doc['workers']; rows=[(w,r) for w in workers for r in w['active_query_results']]
summary={}
for rate in (0,50,90,99):
 group=[r for _,r in rows if r['alias_rate_percent']==rate]
 summary[str(rate)]={'n':len(group),'selector_discrimination_rate':sum(r['query']['predictions']['fault']!=r['query']['predictions']['proposal'] for r in group)/len(group),
  'proposal_survival_rate':sum(r['survivors_after_oracle']==['proposal'] for r in group)/len(group),
  'random_discrimination_rate':sum(r['random_probe']['discriminates'] for r in group)/len(group),
  'mean_entropy_bits':statistics.mean(r['entropy_bits'] for r in group),'mean_selector_ms':statistics.mean(r['selector_wall_ns'] for r in group)/1e6}
checks={'all_sources_stable':all(w['source_stable'] for w in workers),
 'all_proposals_match_host_candidate':all(w['proposal_host_reference_match'] is not None for w in json.loads((ROOT/'evaluation/reports/thoughtexperiment_composed_proposal_active_query_v1_orders_20261002.json').read_text())['workers']),
 'all_queries_discriminate_and_select_proposal':all(r['entropy_bits']>0 and r['survivors_after_oracle']==['proposal'] for _,r in rows),
 'all_proposals_pass_heldout':all(w['proposal_outcome']['utility']==1.0 and w['proposal_outcome']['receipt_verified'] and w['proposal_outcome']['primary_preserved'] for w in workers),
 'all_faults_fail_heldout':all(w['fault_outcome']['utility']==0.0 for w in workers)}
out={'schema':'ComposedProposalActiveQueryV1Analysis','checks':checks,'summary_by_alias_rate':summary,
 'scope':'One authored control-kind family; prompted target/operator selection; Python still owns task, fault, pool, oracle and materialization.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
