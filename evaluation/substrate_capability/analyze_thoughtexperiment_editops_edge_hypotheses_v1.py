#!/usr/bin/env python3
"""Independent gates for edit-operator edge hypothesis generation and transfer."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_editops_edge_hypotheses_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_editops_edge_hypotheses_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_editops_edge_hypotheses_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_editops_edge_hypotheses_v1_analysis_20261002.json'
EXPECTED={'recurrence':'editops_edge_once:out:candidate:has_mint_offer:any','conversation':'editops_edge_once:in:m:responds_to:any'}
TARGET={'recurrence':'mrl_offer_due_once','conversation':'reply_to_adjacency_pair'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text());errors=[]
 if orders.get('lock_sha256')!=sha(LOCK) or scores.get('lock_sha256')!=sha(LOCK) or scores.get('orders_sha256')!=sha(ORDERS):errors.append('capture-to-lock linkage mismatch')
 om={int(r['worker']):r for r in orders['workers']};sm={int(r['worker']):r for r in scores['workers']};want=set(range(lock['workers']))
 if set(om)!=want or set(sm)!=want or len(orders['workers'])!=4 or len(scores['workers'])!=4:errors.append('worker coverage mismatch')
 pids=[r.get('wrapper_pid') for r in orders['workers']+scores['workers']]
 if None in pids or len(set(pids))!=len(pids):errors.append('workers are not unique fresh processes')
 if any(r.get('source_before')!=r.get('source_after') or not r.get('source_stable') for r in orders['workers']+scores['workers']):errors.append('base worker source drift')
 if any(r.get('generation_source')!='domains.edit_ops.find_edge_identity_sites+apply_add_edge_identity_guard' for r in orders['workers']+scores['workers']):errors.append('canonical proposal generator not used')
 checks=[];all_costs=[]
 for worker in sorted(want):
  a,b=om[worker],sm[worker]
  if set(a['families'])!={'recurrence','conversation'} or set(b['families'])!={'recurrence','conversation'}:errors.append(f'family coverage {worker}')
  for family in ('recurrence','conversation'):
   x=a['families'][family];y=b['families'][family];ds=x['descriptors'];outcomes=x['training_outcomes']
   if len(ds)!=4 or len(y['candidate_outcomes'])!=4 or sum(d['label'].startswith('editops_edge_once:') for d in ds)!=3 or sum(d['label'].startswith('composer:') for d in ds)!=1:errors.append(f'proposal coverage {worker}/{family}')
   if len({d['proposal_id'] for d in ds})!=4:errors.append(f'duplicate proposals {worker}/{family}')
   target=TARGET[family];metric=a['editops_generation_by_target'].get(target,{})
   score_metric=b['editops_generation_by_target'].get(target,{})
   if metric.get('site_count')!=3 or score_metric.get('site_count')!=3 or not isinstance(metric.get('generation_ns'),int) or not isinstance(score_metric.get('generation_ns'),int):errors.append(f'canonical generator metrics missing {worker}/{family}')
   counts={o['proposal_id']:sum(bool(t['correct']) for t in o['rows']) for o in outcomes}
   winning_id=x['decision'].get('proposal_id');winning=next((d for d in ds if d['proposal_id']==winning_id),None)
   if not x['decision'].get('ok') or winning is None or winning['label']!=EXPECTED[family]:errors.append(f'wrong selected hypothesis {worker}/{family}')
   if sorted(counts.values())!=[0,0,0,2] or counts.get(winning_id)!=2:errors.append(f'no unique two-of-two training winner {worker}/{family}')
   selected=next((o for o in y['candidate_outcomes'] if o['label']==EXPECTED[family]),None)
   if selected is None or not all(t['correct'] for t in selected['trials']):errors.append(f'heldout failure {worker}/{family}')
   if any(x['output_counts']!=[1,1] for x in x['source_train']):errors.append(f'train source control failed {worker}/{family}')
   if any(not q['correct'] for q in y['source_heldout']):errors.append(f'heldout source control failed {worker}/{family}')
   if not x['primary_rule_unchanged'] or not x['branch_evidence_isolated'] or not all(t['rule_store_stable'] for c in x['training_outcomes'] for t in c['rows']) or not all(t['rule_store_stable'] for c in y['candidate_outcomes'] for t in c['trials']):errors.append(f'host/rule isolation failed {worker}/{family}')
   if sum(all(t['correct'] for t in c['trials']) for c in y['candidate_outcomes'])!=1:errors.append(f'false-scope candidate passed heldout {worker}/{family}')
   if any(x['controls'][c].get('ok') for c in ('all_wrong','tie')):errors.append(f'control did not abstain {worker}/{family}')
   all_costs.append({'worker':worker,'family':family,'generation_train_ns':metric['generation_ns'],'generation_heldout_ns':score_metric['generation_ns'],
    'composer_train_ns':x['compose_ns'],'training_all_candidates_ns':x['training_scoring_ns'],'selector_ns':x['selector_ns'],
    'heldout_all_candidates_ns':y['heldout_scoring_ns']})
  if a.get('source_before')!=a.get('source_after') or b.get('source_before')!=b.get('source_after'):errors.append(f'worker source drift {worker}')
 report={'schema':'ThoughtexperimentEditOpsEdgeHypothesesV1Analysis','gates_pass':not errors,'errors':errors,
  'summary':{'workers':4,'families':['recurrence','conversation'],'family_worker_cells':8,
   'selected_and_heldout_passes':{f:sum(1 for i in want if om[i]['families'][f]['selected_label']==EXPECTED[f] and all(t['correct'] for c in sm[i]['families'][f]['candidate_outcomes'] if c['label']==EXPECTED[f] for t in c['trials'])) for f in ('recurrence','conversation')},
   'median_candidate_generation_ms_by_family':{f:statistics.median(c['generation_train_ns'] for c in all_costs if c['family']==f)/1e6 for f in ('recurrence','conversation')},
   'median_full_training_candidate_scoring_ms_by_family':{f:statistics.median(c['training_all_candidates_ns'] for c in all_costs if c['family']==f)/1e6 for f in ('recurrence','conversation')},
   'median_native_selection_ms_by_family':{f:statistics.median(c['selector_ns'] for c in all_costs if c['family']==f)/1e6 for f in ('recurrence','conversation')},'cost_rows':all_costs}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
