#!/usr/bin/env python3
"""Independent integrity and outcome analysis for FSDD matcher selection v1."""
from __future__ import annotations
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_fsdd_matcher_selection_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_analysis_20261002.json'
RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_fsdd_matcher_selection_v1.py'
FSDD=ROOT/'data/fsdd-current/free-spoken-digit-dataset-26eb9aaf76e81b692f806f9140c2d2777410d7a1/recordings'
SYSTEMS=('ordered_dtw','pointset','matched_filter'); WAY=10; FOLDS=3
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def corpus_hash():
 h=hashlib.sha256();files=sorted(FSDD.glob('*.wav'))
 for p in files:
  rel=p.relative_to(ROOT).as_posix().encode();d=bytes.fromhex(sha(p));h.update(len(rel).to_bytes(4,'big'));h.update(rel);h.update(d)
 return {'path':str(FSDD.relative_to(ROOT)),'file_count':len(files),'sha256':h.hexdigest(),
  'speakers':sorted({p.name.split('_')[1] for p in files}),'digits':list(range(WAY)),'recordings_per_speaker_digit':50}
def finite(x):
 if isinstance(x,float):return math.isfinite(x)
 if isinstance(x,dict):return all(finite(v) for v in x.values())
 if isinstance(x,list):return all(finite(v) for v in x)
 return True
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 checks={k:True for k in ('source_dataset_lock','six_speaker_fold_coverage','speaker_and_recording_disjointness',
  'paired_queries_and_gallery','feature_and_prediction_validity','training_evidence_recomputes',
  'unique_training_maximum_selected','tie_and_all_wrong_abstain','heldout_absent_from_orders',
  'selected_above_chance','heldout_regret_within_five_points','branch_isolation_residual_and_costs')}
 H=lambda p:sha(ROOT/p)
 if orders.get('lock_sha256')!=H('evaluation/substrate_capability/thoughtexperiment_fsdd_matcher_selection_v1_lock_20261002.json') or scores.get('orders_sha256')!=H('evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_orders_20261002.json'):
  checks['source_dataset_lock']=False
 for rel,digest in lock['sources']['files'].items():
  if not (ROOT/rel).exists() or sha(ROOT/rel)!=digest:checks['source_dataset_lock']=False
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale
 if sha(Path(_native.__file__).resolve())!=lock['sources']['native_binary_sha256'] or corpus_hash()!=lock['sources']['corpus'] or build_is_stale(str(ROOT)):
  checks['source_dataset_lock']=False
 ow=orders.get('workers',[]);sw=scores.get('workers',[])
 if len(ow)!=FOLDS or len(sw)!=FOLDS:checks['six_speaker_fold_coverage']=False
 if len({w.get('pid') for w in ow})!=FOLDS or len({w.get('pid') for w in sw})!=FOLDS:checks['six_speaker_fold_coverage']=False
 score_by={w.get('fold'):w for w in sw};summaries={};heldout_seen=[]
 for order in ow:
  fold=order.get('fold');score=score_by.get(fold)
  if score is None:checks['six_speaker_fold_coverage']=False;continue
  fs=order['fold_spec'];heldout=fs['heldout_speakers'];train=fs['training_speakers'];heldout_seen.extend(heldout)
  if len(heldout)!=2 or len(train)!=4 or set(heldout)&set(train) or set(heldout)|set(train)!=set(lock['sources']['corpus']['speakers']):checks['six_speaker_fold_coverage']=False
  if not order.get('source_stable') or not score.get('source_stable'):checks['source_dataset_lock']=False
  train_specs=order.get('training_specs',[]);test_specs=score.get('heldout_specs',[])
  if len(train_specs)!=400 or len(test_specs)!=200 or any(k.startswith('heldout') for k in order):checks['heldout_absent_from_orders']=False
  galleries=[x for x in train_specs if x['kind']=='gallery'];queries=[x for x in train_specs if x['kind']=='query']
  if len(galleries)!=200 or len(queries)!=200 or len({x['path'] for x in train_specs})!=400 or len({x['path'] for x in test_specs})!=200:checks['speaker_and_recording_disjointness']=False
  if {x['speaker'] for x in galleries+queries}!=set(train) or {x['speaker'] for x in test_specs}!=set(heldout):checks['speaker_and_recording_disjointness']=False
  if {x['digit'] for x in galleries+queries+test_specs}!=set(range(WAY)):checks['speaker_and_recording_disjointness']=False
  if set(x['path'] for x in train_specs)&set(x['path'] for x in test_specs):checks['speaker_and_recording_disjointness']=False
  tr=order.get('training_rows',[]);te=score.get('heldout_rows',[])
  if {r['system'] for r in tr}!={*SYSTEMS} or {r['system'] for r in te}!={*SYSTEMS}:checks['paired_queries_and_gallery']=False
  trmap={r['system']:r for r in tr};temap={r['system']:r for r in te}
  base_train=trmap.get(SYSTEMS[0],{});base_test=temap.get(SYSTEMS[0],{})
  train_ids={p['query_id'] for p in base_train.get('predictions',[])};test_ids={p['query_id'] for p in base_test.get('predictions',[])}
  if len(train_ids)!=200 or len(test_ids)!=200:checks['paired_queries_and_gallery']=False
  for s in SYSTEMS:
   r=trmap.get(s,{});e=temap.get(s,{})
   if ({p['query_id'] for p in r.get('predictions',[])}!=train_ids or {p['query_id'] for p in e.get('predictions',[])}!=test_ids
       or r.get('gallery_digest')!=base_train.get('gallery_digest') or e.get('gallery_digest')!=base_test.get('gallery_digest')
       or r.get('gallery_count')!=200 or e.get('gallery_count')!=200):checks['paired_queries_and_gallery']=False
   for row,specs in ((r,queries),(e,test_specs)):
    preds=row.get('predictions',[]);expected={(x['speaker'],x['digit'],x['index']) for x in specs}
    if (row.get('query_count')!=len(specs) or len(preds)!=len(specs)
      or {(p['speaker'],p['digit'],p['index']) for p in preds}!=expected
      or any(p.get('prediction') not in range(WAY) or p.get('correct')!=(p.get('prediction')==p.get('digit')) for p in preds)):
     checks['feature_and_prediction_validity']=False
    if row.get('distance_comparison_cells')!=len(specs)*200 or not finite(row):checks['feature_and_prediction_validity']=False
   correct=sum(p['correct'] for p in r.get('predictions',[]))
   if r.get('correct_count')!=correct:checks['training_evidence_recomputes']=False
  train_acc={s:sum(p['correct'] for p in trmap[s]['predictions'])/200 for s in SYSTEMS}
  test_acc={s:sum(p['correct'] for p in temap[s]['predictions'])/200 for s in SYSTEMS}
  best=max(train_acc.values());winners=[s for s,v in train_acc.items() if abs(v-best)<1e-12]
  selected=order.get('selected_proposal_id')
  if len(winners)!=1 or selected!=winners[0]:checks['unique_training_maximum_selected']=False
  decision=order.get('decision',{});max_n=max(sum(p['correct'] for p in trmap[s]['predictions']) for s in SYSTEMS)
  if not decision.get('ok') or decision.get('proposal_id')!=selected or decision.get('matching_evidence_count')!=max_n or decision.get('probe_count')!=600:
   checks['training_evidence_recomputes']=False
  if order.get('controls')!={'all_wrong':False,'tie':False}:checks['tie_and_all_wrong_abstain']=False
  if test_acc.get(selected,0)<=0.10:checks['selected_above_chance']=False
  regret=max(test_acc.values())-test_acc.get(selected,0)
  if regret>0.05+1e-12:checks['heldout_regret_within_five_points']=False
  if (not order.get('primary_has_no_candidate_evidence') or not order.get('residual_returned')
   or order.get('branch_node_counts',{}).get('before')!=[0,0]
   or order.get('branch_node_counts',{}).get('after')!=[3,600]
   or order.get('training_query_gallery_cells')!=120000 or score.get('heldout_query_gallery_cells')!=120000
   or order.get('prediction_term_calls')!=600 or score.get('prediction_term_calls')!=600):
   checks['branch_isolation_residual_and_costs']=False
  cost_keys=('feature_prep_ns','snapshot_ns','branch_fork_ns','control_branch_fork_ns','graph_selection_ns','residual_return_ns')
  if any(not isinstance(order.get(k),int) or order[k]<0 for k in cost_keys) or not isinstance(score.get('feature_prep_ns'),int):checks['branch_isolation_residual_and_costs']=False
  summaries[str(fold)]={'training_accuracy':train_acc,'selected':selected,'heldout_accuracy':test_acc,
   'heldout_hindsight_best':max(test_acc.values()),'heldout_regret':regret,
   'per_speaker':{s:temap[selected]['per_speaker'].get(s) for s in heldout},
   'per_digit':temap[selected]['per_digit']}
 if sorted(heldout_seen)!=sorted(lock['sources']['corpus']['speakers']):checks['six_speaker_fold_coverage']=False
 result={'schema':'ThoughtexperimentFSDDMatcherSelectionV1Analysis','checks':checks,
  'passed_checks':sum(checks.values()),'check_count':len(checks),'all_checks_pass':all(checks.values()),
  'folds':summaries,'interpretation':'Speaker-disjoint selection among three supplied native matchers on a six-speaker corpus; not autonomous matcher invention or population-level speech recognition.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_checks_pass':result['all_checks_pass'],'passed_checks':result['passed_checks'],'check_count':len(checks),'analysis':str(OUT)},indent=2))
 return 0 if result['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
