#!/usr/bin/env python3
"""Independent analysis of Omniglot matcher selection and alphabet transfer."""
from __future__ import annotations
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_omniglot_matcher_selection_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_omniglot_matcher_selection_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_omniglot_matcher_selection_v1_1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_omniglot_matcher_selection_v1_2_analysis_20261002.json'
SYSTEMS=('ordered_dtw','pointset','deformable'); WAY=20; EPISODES=40
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def data_manifest():
 from domains import omniglot_world as ow
 out={}
 for split in ('background','evaluation'):
  base=Path(ow.split_dir(split));files=sorted(p for p in base.rglob('*') if p.is_file());h=hashlib.sha256()
  for p in files:
   rel=p.relative_to(base).as_posix().encode();d=bytes.fromhex(sha(p));h.update(len(rel).to_bytes(4,'big'));h.update(rel);h.update(d)
  out[split]={'root':str(base.relative_to(ROOT)),'file_count':len(files),'sha256':h.hexdigest(),'alphabets':sorted(ow.alphabets(split))}
 return out
def finite(x):
 if isinstance(x,float):return math.isfinite(x)
 if isinstance(x,dict):return all(finite(v) for v in x.values())
 if isinstance(x,list):return all(finite(v) for v in x)
 return True
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 H=lambda p:sha(ROOT/p)
 checks={'source_dataset_lock':True,'alphabet_disjointness':True,'three_fresh_workers_and_seeds':True,
  'paired_episode_identity':True,'complete_training_evidence':True,'unique_training_maximum_selected':True,
  'tie_and_all_wrong_abstain':True,'heldout_absent_from_training_decisions':True,
  'selected_above_chance':True,'heldout_regret_within_five_points':True,
  'branch_isolation_and_residual':True,'finite_recomputable_measurements':True}
 if orders['lock_sha256']!=H('evaluation/substrate_capability/thoughtexperiment_omniglot_matcher_selection_v1_1_lock_20261002.json') or scores['orders_sha256']!=H('evaluation/reports/thoughtexperiment_omniglot_matcher_selection_v1_1_orders_20261002.json'):
  checks['source_dataset_lock']=False
 for rel,digest in lock['sources']['files'].items():
  if not (ROOT/rel).exists() or sha(ROOT/rel)!=digest:checks['source_dataset_lock']=False
 from substrate_rs import _native
 if sha(Path(_native.__file__).resolve())!=lock['sources']['native_binary_sha256'] or data_manifest()!=lock['sources']['dataset']:
  checks['source_dataset_lock']=False
 ds=lock['sources']['dataset']; ba=set(ds['background']['alphabets']);ea=set(ds['evaluation']['alphabets'])
 if ba & ea:checks['alphabet_disjointness']=False
 if (len(orders['workers'])!=3 or len(scores['workers'])!=3
     or len({w['pid'] for w in orders['workers']})!=3 or len({w['pid'] for w in scores['workers']})!=3):checks['three_fresh_workers_and_seeds']=False
 score_by={w['worker']:w for w in scores['workers']};summaries={}
 for order in orders['workers']:
  worker=order['worker'];score=score_by.get(worker)
  if score is None or not order.get('source_stable') or not score.get('source_stable'):
   checks['source_dataset_lock']=False
  if len(order['train_specs'])!=EPISODES or 'heldout_specs' in order:checks['three_fresh_workers_and_seeds']=False
  if len(score.get('heldout_specs',[]))!=EPISODES:checks['three_fresh_workers_and_seeds']=False
  if any(k.startswith('heldout') for k in order):checks['heldout_absent_from_training_decisions']=False
  if order['train_specs'][0]['split']!='background' or score['heldout_specs'][0]['split']!='evaluation':checks['alphabet_disjointness']=False
  if len({x['episode'] for x in order['train_specs']})!=EPISODES or len({x['episode'] for x in score['heldout_specs']})!=EPISODES:checks['three_fresh_workers_and_seeds']=False
  train_rows=order['training_rows'];held_rows=score['heldout_rows']
  if any(r['split']!='background' for r in train_rows) or any(r['split']!='evaluation' for r in held_rows):checks['heldout_absent_from_training_decisions']=False
  for specs,rows in ((order['train_specs'],train_rows),(score['heldout_specs'],held_rows)):
   by_system={s:{r['episode']:r for r in rows if r['system']==s} for s in SYSTEMS}
   for ep in specs:
    keys={by_system[s].get(ep['episode'],{}).get('episode_key_sha256') for s in SYSTEMS}
    if len(keys)!=1 or None in keys:checks['paired_episode_identity']=False
    for s in SYSTEMS:
     r=by_system[s].get(ep['episode'],{})
     if (r.get('query_count')!=WAY or len(r.get('predictions',[]))!=WAY
       or r.get('correct_count')!=sum(p==g for p,g in zip(r.get('predictions',[]),r.get('labels',[])))
       or not r.get('all_predictions_valid')):checks['finite_recomputable_measurements']=False
  acc={s:sum(r['correct_count'] for r in train_rows if r['system']==s)/(EPISODES*WAY) for s in SYSTEMS}
  heldacc={s:sum(r['correct_count'] for r in held_rows if r['system']==s)/(EPISODES*WAY) for s in SYSTEMS}
  best=max(acc.values());winners=[s for s,v in acc.items() if abs(v-best)<1e-12]
  if len(winners)!=1 or order['selected_proposal_id']!=winners[0]:checks['unique_training_maximum_selected']=False
  decision=order['training_decision']
  max_correct=max(sum(r['correct_count'] for r in train_rows if r['system']==s) for s in SYSTEMS)
  if (not decision.get('ok') or decision.get('proposal_id')!=order['selected_proposal_id']
      or decision.get('matching_evidence_count')!=max_correct
      or decision.get('probe_count')!=EPISODES*WAY):checks['complete_training_evidence']=False
  if order['controls']!={'all_wrong':False,'tie':False}:checks['tie_and_all_wrong_abstain']=False
  selected=order['selected_proposal_id']; chance=1/WAY
  if heldacc.get(selected,0)<=chance:checks['selected_above_chance']=False
  regret=max(heldacc.values())-heldacc.get(selected,0)
  if regret>0.05+1e-12:checks['heldout_regret_within_five_points']=False
  if (not order['primary_has_no_candidate_evidence'] or not order['residual_returned']
      or order['branch_node_counts']['before']!=[0,0]
      or order['branch_node_counts']['after']!=[len(SYSTEMS),EPISODES*WAY*len(SYSTEMS)]):
   checks['branch_isolation_and_residual']=False
  required_costs=('train_feature_prep_ns','snapshot_ns','selection_branch_fork_ns','control_branch_fork_ns','graph_selection_ns','residual_return_ns','training_term_calls')
  heldout_costs=('heldout_feature_prep_ns','heldout_term_calls')
  if any(k not in order for k in required_costs) or any(k not in score for k in heldout_costs):checks['finite_recomputable_measurements']=False
  if order.get('training_term_calls')!=len(SYSTEMS)*EPISODES*WAY+3 or score.get('heldout_term_calls')!=len(SYSTEMS)*EPISODES*WAY:checks['finite_recomputable_measurements']=False
  if any(not finite(x) for x in train_rows+held_rows) or not finite(order) or not finite(score):
   checks['finite_recomputable_measurements']=False
  summaries[str(worker)]={'selected':selected,'training_accuracy':acc,'heldout_accuracy':heldacc,
   'heldout_regret':regret,'heldout_hindsight_best':max(heldacc.values()),
   'train_alphabets':sorted({x['alphabet'] for x in order['train_specs']}),
   'heldout_alphabets':sorted({x['alphabet'] for x in score['heldout_specs']})}
 analysis={'schema':'ThoughtexperimentOmniglotMatcherSelectionV1_1Analysis','checks':checks,
  'passed_checks':sum(checks.values()),'check_count':len(checks),'all_checks_pass':all(checks.values()),
  'workers':summaries,'interpretation':'Cross-split selection over supplied matchers; not autonomous concept or matcher invention.'}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_checks_pass':analysis['all_checks_pass'],'passed_checks':analysis['passed_checks'],
  'check_count':analysis['check_count'],'analysis':str(OUT)},indent=2))
 return 0 if analysis['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
