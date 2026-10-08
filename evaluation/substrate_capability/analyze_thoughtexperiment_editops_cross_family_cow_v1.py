#!/usr/bin/env python3
"""Independent cross-family CoW candidate-evaluation analysis."""
from __future__ import annotations
import hashlib,importlib.util,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_editops_cross_family_cow_v1_lock_20261003.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_editops_cross_family_cow_v1_orders_20261003.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_editops_cross_family_cow_v1_scores_20261003.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_editops_cross_family_cow_v1_analysis_20261003.json'
FAMILIES=('recurrence','conversation');BACKENDS=('full_copy','shared_graph_pages')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock,orders,scores=(json.loads(p.read_text()) for p in (LOCK,ORDERS,SCORES))
 ow,sw=orders['workers'],scores['workers'];score_by={x['worker']:x for x in sw}
 base_path=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_1.py'
 spec=importlib.util.spec_from_file_location('cross_cow_analysis_base',base_path);base=importlib.util.module_from_spec(spec);sys.modules[spec.name]=base;spec.loader.exec_module(base)
 checks={
  'capture_lock_binding':orders['lock_sha256']==sha(LOCK) and scores['lock_sha256']==sha(LOCK) and scores['orders_sha256']==sha(ORDERS),
  'four_unique_workers_both_stages':len(ow)==len(sw)==4 and {x['worker'] for x in ow}=={0,1,2,3} and {x['worker'] for x in sw}=={0,1,2,3},
  'source_hashes_stable':all(x['source_stable'] and x['source_before']==x['source_after']==lock['sources'] for x in ow+sw),
  'both_families_have_four_candidates':all(set(x['families'])==set(FAMILIES) and all(len(x['families'][f]['descriptors'])==4 and len(x['families'][f]['candidate_rules'])==4 for f in FAMILIES) for x in ow),
  'frozen_candidate_permutations_valid':all(len(x['families'][f]['candidate_order'])==4 and set(x['families'][f]['candidate_order'])==set(range(4)) for x in ow for f in FAMILIES),
  'candidate_rule_ids_bind_to_frozen_descriptors':all(
   [d['proposal_id'] for d in row['descriptors']]==[base.rule_digest(family,rules[base.TARGETS[family]]) for rules in row['candidate_rules']]
   for worker in ow for family,row in worker['families'].items()),
  'paired_backend_semantic_parity_and_primary_isolation':all(
   len(row['training']['full_copy'])==len(row['training']['shared_graph_pages'])==4
   and all(a['primary_unchanged_before_return'] and b['primary_unchanged_before_return']
    and {k:v for k,v in a['result'].items() if k not in ('sequence_runtime_ns',)}=={k:v for k,v in b['result'].items() if k not in ('sequence_runtime_ns',)}
    for a,b in zip(row['training']['full_copy'],row['training']['shared_graph_pages']))
   for worker in ow for row in worker['families'].values()),
  'one_training_winner_selected_each':all(
   sum(r['result']['correct'] for r in row['training']['shared_graph_pages'])==1
   and row['decision'].get('ok') and row['selected_label']==next(r['candidate_label'] for r in row['training']['shared_graph_pages'] if r['result']['correct'])
   for worker in ow for row in worker['families'].values()),
  'all_wrong_and_tie_controls_abstain':all(not row['controls'][k].get('ok') for worker in ow for row in worker['families'].values() for k in ('all_wrong','tie')),
  'source_positive_controls_pass':all(row['result']['correct'] and row['primary_unchanged_before_return'] for worker in ow for family in FAMILIES for row in worker['families'][family]['source_controls'].values()),
  'all_heldout_candidates_scored_and_isolated':all(len(row['heldout'][f][b])==4 and all(x['primary_unchanged_before_return'] for x in row['heldout'][f][b]) for row in sw for f in FAMILIES for b in BACKENDS),
  'selected_repairs_pass_both_heldout_backends':all(all(next(x for x in row['heldout'][f][b] if x['candidate_id']==order['families'][f]['decision'].get('proposal_id'))['result']['correct'] for b in BACKENDS) for row in sw for order in ow if order['worker']==row['worker'] for f in FAMILIES),
  'selected_receipts_return_atomically':all(
   all((r:=worker['adoptions'][f]['receipt_return'])['receipt_parity'] and r['stale_retry_rejected'] and r['stale_retry_unchanged'] and r['primary_rules_preserved']
    and worker['adoptions'][f]['primary_unchanged_before_return'] and len(r['delta'].get('nodes_changed',[]))==1
    and not any(r['delta'].get(k,[]) for k in ('nodes_added','edges_added','edges_changed','nodes_removed','edges_removed'))
    for f in FAMILIES) for worker in sw),
 }
 training_ms={b:[] for b in BACKENDS};heldout_ms={b:[] for b in BACKENDS};snapshot_ms={b:[] for b in BACKENDS};selector_ms=[];adopt_ms=[]
 for worker in ow:
  for f in FAMILIES:
   row=worker['families'][f];selector_ms.append(row['selector_ns']/1e6)
   for b in BACKENDS:
    training_ms[b].append(sum(x['snapshot_ns']+x['rule_patch_ns']+x['branch_execution_ns'] for x in row['training'][b])/1e6)
    snapshot_ms[b].extend(x['snapshot_ns']/1e6 for x in row['training'][b])
 for worker in sw:
  for f in FAMILIES:
   for b in BACKENDS:heldout_ms[b].append(sum(x['snapshot_ns']+x['rule_patch_ns']+x['branch_execution_ns'] for x in worker['heldout'][f][b])/1e6)
   adopt_ms.append(worker['adoptions'][f]['receipt_return']['adopt_ns']/1e6)
 summary={'training_all_candidate_lifecycle_median_ms':{b:statistics.median(v) for b,v in training_ms.items()},
  'heldout_all_candidate_lifecycle_median_ms':{b:statistics.median(v) for b,v in heldout_ms.items()},
  'single_candidate_snapshot_median_ms':{b:statistics.median(v) for b,v in snapshot_ms.items()},
  'selector_median_ms':statistics.median(selector_ms),'receipt_adoption_median_ms':statistics.median(adopt_ms)}
 outcomes={}
 for f in FAMILIES:
  outcomes[f]={}
  for row in ow:
   fr=row['families'][f]; outcomes[f][row['worker']]={'selected':fr['selected_label'],
    'training_winners':[x['candidate_label'] for x in fr['training']['shared_graph_pages'] if x['result']['correct']]}
 result={'schema':'ThoughtexperimentEditOpsCrossFamilyCowV1Analysis','checks':checks,'summary':summary,'training_selection':outcomes,
  'interpretation_boundary':'Two authored task families with supplied faults, cues, training examples, and oracles. Candidate rules are isolated in CoW branches; only proposal receipts return. This does not test automatic target diagnosis or production rule activation.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
