#!/usr/bin/env python3
"""Independent review of active ordered-site choice capture."""
import json,statistics,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
orders=json.loads((ROOT/'evaluation/reports/thoughtexperiment_attribute_site_active_choice_v2_orders_20261002.json').read_text())
scores=json.loads((ROOT/'evaluation/reports/thoughtexperiment_attribute_site_active_choice_v2_scores_20261002.json').read_text())
ow=orders['workers'];sw=scores['workers'];cells=[(w,c) for w in ow for c in w['choices']]
results=[r for w in sw for r in w['results']]
held=[(w,h) for w in sw for h in w['heldout']]
by_worker={w['worker']:w for w in sw}
checks={
 'four_complete_workers':len(ow)==4 and len(sw)==4 and all(len(w['choices'])==8 for w in ow) and all(len(w['results'])==8 for w in sw),
 'cue_free_composer_abstains':all(w['meta']['composition_built'] is False for w in ow),
 'both_ordered_swap_candidates_enumerated':all({'swap_term_leaf:bad_score->good_score','swap_term_leaf:good_score->bad_score'}.issubset(set(w['meta']['candidate_labels'])) for w in ow),
 'all_query_pools_have_100_inputs':all(len(c['pool'])==100 and c['selected'].get('ok') for _,c in cells),
 'all_queries_reach_three_hypothesis_binary_maximum':all(c['selected'].get('partition_count')==2 and math.isclose(c['selected'].get('entropy_bits',0.0),math.log2(3)-2/3,abs_tol=1e-12) for _,c in cells),
 'each_prediction_pool_covers_three_hypotheses':all({m['hypothesis'] for m in c['predictions']}=={'fault','forward','reverse'} and len(c['predictions'])==300 for _,c in cells),
 'oracle_retains_forward_only_all_conditions':all(r['survivors']==['forward'] for r in results),
 'graph_term_selects_same_unique_winner':all(r['graph_decision'].get('ok') and r['graph_decision'].get('proposal_id')==r['survivors'][0] and r['graph_decision'].get('matching_evidence_count')==1 for r in results),
 'compact_residual_returned_to_primary':all(r['residual_returned_to_primary'] for r in results) and all(w['primary_contains_only_residuals'] for w in sw),
 'graph_tie_and_zero_controls_abstain':all(w['controls']['tie_abstains'] and w['controls']['zero_match_abstains'] for w in sw),
 'graph_input_validation_fails_closed':all(w['controls']['duplicate_namespace_rejected'] and w['controls']['incomplete_coverage_rejected'] and w['controls']['incomplete_rejection_did_not_mutate_graph'] for w in sw),
 'forward_passes_all_heldouts':all(h['predictions']['forward']==h['expected'] for _,h in held),
 'fault_fails_nonzero_heldout_each_worker':all(any(h['env']['good_score']!=0 and h['predictions']['fault']!=h['expected'] for h in w['heldout']) for w in sw),
 'reverse_fails_nonzero_heldout_each_worker':all(any(h['env']['good_score']!=0 and h['predictions']['reverse']!=h['expected'] for h in w['heldout']) for w in sw),
 'all_branches_verified_and_fixedpoint':all(m['receipt_verified'] and m['fixedpoint_work']==0 for _,c in cells for m in c['predictions']),
 'primary_preserved_in_order_and_score':all(w['primary_preserved'] for w in ow) and all(w['primary_preserved'] for w in sw),
 'source_hashes_match_across_stages':all(w['source_hashes']==sw[w['worker']]['source_hashes'] for w in ow),
 'random_probe_is_not_better_than_selector':sum(r['random_probe']['predictions']['fault']!=r['random_probe']['predictions']['forward'] for r in results)<=sum(r['predictions']['fault']!=r['predictions']['forward'] for r in results),
}
cost={'mean_composer_attempt_ms':statistics.mean(w['meta']['composer_ns'] for w in ow)/1e6,
 'mean_host_candidate_enumeration_ms':statistics.mean(w['meta']['enumerator_ns'] for w in ow)/1e6,
 'mean_selector_wall_ms':statistics.mean(c['selector_wall_ns'] for _,c in cells)/1e6,
 'mean_selector_cpu_ms':statistics.mean(c['selector_cpu_ns'] for _,c in cells)/1e6,
 'mean_branch_fork_ms':statistics.mean(m['branch_fork_ns'] for _,c in cells for m in c['predictions'])/1e6,
 'mean_candidate_patch_ms':statistics.mean(m['candidate_patch_ns'] for _,c in cells for m in c['predictions'])/1e6,
 'mean_closure_ms':statistics.mean(m['closure_ns'] for _,c in cells for m in c['predictions'])/1e6,
 'active_queries':len(results),'host_generated_hypotheses_per_worker':3}
out={'schema':'AttributeSiteActiveChoiceV2Analysis','checks':checks,'all_checks_pass':all(checks.values()),'cost_summary':cost,
 'preregistered_entropy_check':'one bit is mathematically unattainable for a binary-output partition of three hypotheses; all queries attain the 0.918295834-bit 1-vs-2 maximum',
 'mean_graph_term_selection_ms':statistics.mean(r['graph_decision_ns'] for r in results)/1e6,
 'mean_selection_branch_fork_ms':statistics.mean(r['selection_branch_fork_ns'] for r in results)/1e6,
 'mean_residual_return_ms':statistics.mean(r['residual_return_ns'] for r in results)/1e6,
 'scope':'Native-Term active query selection and graph-resident unique candidate scoring among three host-supplied hypotheses on one fresh rule; cue-free composer abstains; oracle released after orders freeze.'}
print(json.dumps(out,indent=2,sort_keys=True))
if not out['all_checks_pass']:raise SystemExit(1)
