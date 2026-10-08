#!/usr/bin/env python3
"""Independent replay of native relation-family scoring and sealed transfer."""
from __future__ import annotations
import hashlib,itertools,json,statistics
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/native_primitive_family_selection_transfer_v1_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/native_primitive_family_selection_transfer_v1_lock_20261005.json'
PANEL_LOCK=ROOT/'evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1_lock_20261003.json'
RUNNER=ROOT/'evaluation/substrate_capability/native_primitive_family_selection_transfer_v1.py'
SCRIPT=Path(__file__).resolve();OUT=ROOT/'evaluation/reports/native_primitive_family_selection_transfer_v1_analysis_20261005.json'
VALUES=(-2.5,-1.5,-.5,.5,1.5,2.5);HELD=tuple(itertools.product(VALUES,repeat=4));FAMILIES=('additive','product')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def truth(task,row):
 ax,ay,ex,ey=map(float,row)
 return ax+ay==ex+ey if task=='additive' else ax*ay==ex*ey
def formula(family,row):
 ax,ay,ex,ey=map(float,row)
 return ax+ay==ex+ey if family=='additive' else ax*ay==ex*ey
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());panels=json.loads(PANEL_LOCK.read_text())
 expected=[p for p in panels['panels'] if p['task'] in ('additive','product')]
 checks={k:True for k in ('capture_lock_match','ten_locked_panels','source_lock_current','candidate_menu_exact',
  'validation_test_split_exact','candidate_predictions_replay','native_validation_scores_replay',
  'native_unique_choice_or_refusal','hidden_task_not_in_graph','labels_revealed_after_capture',
  'selected_predictions_replay','test_labels_replay')}
 checks['capture_lock_match']=data['lock_sha256']==sha(LOCK) and data['locked_inputs']==lock['inputs'] and data['post_run_inputs']==lock['inputs']
 checks['ten_locked_panels']=len(data['workers'])==10 and len(expected)==10
 import sys;sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
 import native_primitive_family_selection_transfer_v1 as runner
 checks['source_lock_current']=runner.manifest()==lock['inputs']
 all_examples=[];per_panel=[];task_stats={t:Counter() for t in ('additive','product')};costs=[]
 for worker,panel in zip(data['workers'],expected):
  d=worker['panel'];task=panel['task'];checks['candidate_menu_exact'] &= worker['candidate_ids']==list(FAMILIES)
  checks['candidate_menu_exact'] &= d['task_for_scorer_only']==task and d['worker']==panel['worker'] and d['seed']==panel['seed']
  checks['hidden_task_not_in_graph'] &= worker['episode_graph_task_attribute_absent'] and worker['graph_task_identity_absent']
  validation=[x for x in worker['examples'] if x['split']=='validation'];test=[x for x in worker['examples'] if x['split']=='test']
  checks['validation_test_split_exact'] &= len(validation)==len(panel['selection_pool'])==32 and len(test)==1296
  checks['validation_test_split_exact'] &= [x['row'] for x in validation]==panel['selection_pool'] and [tuple(x['row']) for x in test]==list(HELD)
  checks['validation_test_split_exact'] &= not ({tuple(x['row']) for x in validation}&set(HELD))
  scores={f:0 for f in FAMILIES}
  for row in validation:
   y=truth(task,row['row'])
   checks['validation_test_split_exact'] &= row['label'] is y
   for f in FAMILIES:
    pred=formula(f,row['row']);checks['candidate_predictions_replay'] &= row['predictions'][f] is pred
    scores[f]+=int(pred==y)
  checks['native_validation_scores_replay'] &= worker['native_validation_scores']==scores
  top=max(scores.values());winners=[f for f in FAMILIES if scores[f]==top]
  if len(winners)==1:checks['native_unique_choice_or_refusal'] &= worker['selected_candidate']==winners[0]
  else:checks['native_unique_choice_or_refusal'] &= worker['selected_candidate'] is None
  checks['labels_revealed_after_capture'] &= worker['label_reveal_receipt'] is True
  confusion={f:{'tp':0,'fp':0,'fn':0,'tn':0} for f in FAMILIES};sel_correct=sel_covered=0
  for row in test:
   y=truth(task,row['row']);checks['test_labels_replay'] &= row['label'] is y
   for f in FAMILIES:
    pred=formula(f,row['row']);checks['candidate_predictions_replay'] &= row['predictions'][f] is pred
    key=('tp' if pred and y else 'fp' if pred else 'fn' if y else 'tn');confusion[f][key]+=1
   if worker['selected_candidate'] is not None:
    pred=formula(worker['selected_candidate'],row['row']);sel_covered+=1;sel_correct+=int(pred==y)
    checks['selected_predictions_replay'] &= row['selected_prediction'] is pred
   else:checks['selected_predictions_replay'] &= row['selected_prediction'] is None
  family_exact={f:confusion[f]['fp']==0 and confusion[f]['fn']==0 for f in FAMILIES}
  result={'task':task,'worker':panel['worker'],'validation_scores':scores,'selection':worker['selected_candidate'],
   'selected_correct':sel_correct,'selected_covered':sel_covered,'selected_accuracy':sel_correct/sel_covered if sel_covered else None,
   'candidate_confusion':confusion,'candidate_exact_on_grid':family_exact,
   'candidate_family_correct':worker['selected_candidate']==task if worker['selected_candidate'] else None,
   'validation_closure_ns':worker['validation_closure_ns'],'score_closure_ns':worker['selection_score_closure_ns'],
   'selection_commit_ns':worker['selection_commit_closure_ns'],'worker_cpu_ns':worker['worker_cpu_ns'],
   'peak_rss_kib':worker['worker_peak_rss_kib']}
  per_panel.append(result);costs.append(result)
  task_stats[task]['panels']+=1;task_stats[task]['ties']+=int(worker['selected_candidate'] is None)
  task_stats[task]['correct_family_selections']+=int(worker['selected_candidate']==task)
  task_stats[task]['covered_test_panels']+=int(sel_covered>0)
  task_stats[task]['selected_correct']+=sel_correct;task_stats[task]['selected_covered']+=sel_covered
  for f in FAMILIES:task_stats[task][f+'_fp']+=confusion[f]['fp'];task_stats[task][f+'_fn']+=confusion[f]['fn']
 summary={t:{**dict(v),'selection_accuracy':v['correct_family_selections']/v['panels'],
  'tie_rate':v['ties']/v['panels'],'selected_corner_accuracy':v['selected_correct']/v['selected_covered'] if v['selected_covered'] else None} for t,v in task_stats.items()}
 exact_grid={'additive':all(x['candidate_exact_on_grid']['additive'] for x in per_panel if x['task']=='additive'),
  'product':all(x['candidate_exact_on_grid']['product'] for x in per_panel if x['task']=='product')}
 checks['test_labels_replay'] &= all(exact_grid.values())
 result={'schema':'NativePrimitiveFamilySelectionTransferV1Analysis','run_id':'native-primitive-family-selection-transfer-v1-analysis-20261005',
  'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'analysis_script_sha256':sha(SCRIPT),
  'checks':checks,'passed':all(checks.values()),'per_task':summary,'per_panel':per_panel,
  'candidate_family_exact_grid':exact_grid,
  'medians':{k:statistics.median(x[k] for x in costs) for k in ('validation_closure_ns','score_closure_ns','selection_commit_ns','worker_cpu_ns','peak_rss_kib')},
  'interpretation_boundary':'Native graph rules score and select between two supplied numeric relations using validation labels, then transfer the selected relation to a sealed grid. This is a separate input family from the visual selector experiment, but it uses ten previously authored numeric panels and a two-candidate supplied menu. It is not open-ended operator invention or general self-improvement.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'passed':result['passed'],'checks':checks,'per_task':summary,'candidate_family_exact_grid':exact_grid,'output':OUT.relative_to(ROOT).as_posix()}))
 return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
