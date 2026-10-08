#!/usr/bin/env python3
"""Independent replay of adequacy threshold, native selection, and test grid."""
from __future__ import annotations
import hashlib,itertools,json,statistics,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/native_candidate_adequacy_v1_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/native_candidate_adequacy_v1_lock_20261005.json'
PANEL_LOCK=ROOT/'evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1_lock_20261003.json'
RUNNER=ROOT/'evaluation/substrate_capability/native_candidate_adequacy_v1.py'
SCRIPT=Path(__file__).resolve();OUT=ROOT/'evaluation/reports/native_candidate_adequacy_v1_analysis_20261005.json'
VALUES=(-2.5,-1.5,-.5,.5,1.5,2.5);HELD=tuple(itertools.product(VALUES,repeat=4));FAMILIES=('additive','product');THRESHOLD=24
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def truth(task,row):
 ax,ay,ex,ey=map(float,row)
 if task=='additive':return ax+ay==ex+ey
 if task=='product':return ax*ay==ex*ey
 return ax==-ex and ay==-ey
def formula(family,row):
 ax,ay,ex,ey=map(float,row)
 return ax+ay==ex+ey if family=='additive' else ax*ay==ex*ey
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());source=json.loads(PANEL_LOCK.read_text())
 expected=[p for p in source['panels'] if p['task'] in ('additive','product','opposition')]
 checks={k:True for k in ('capture_lock_match','fifteen_expected_panels','source_lock_current','panel_strata_exact',
  'candidate_menu_and_predictions','validation_scores_replay','threshold_status_replay',
  'selection_or_refusal_replay','target_identity_absent','labels_revealed_after_receipt',
  'heldout_labels_and_predictions','positive_control_transfer','challenge_is_out_of_menu')}
 checks['capture_lock_match']=data['lock_sha256']==sha(LOCK) and data['locked_inputs']==lock['inputs'] and data['post_run_inputs']==lock['inputs']
 checks['fifteen_expected_panels']=len(data['workers'])==15 and len(expected)==15
 sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'));import native_candidate_adequacy_v1 as runner
 checks['source_lock_current']=runner.manifest()==lock['inputs']
 by_task={t:Counter() for t in ('additive','product','opposition')};per_panel=[];costs=[]
 for worker,panel in zip(data['workers'],expected):
  rec=worker['panel'];task=panel['task'];scores={f:0 for f in FAMILIES}
  checks['panel_strata_exact'] &= rec['task_for_scorer_only']==task and rec['worker']==panel['worker'] and rec['seed']==panel['seed']
  checks['candidate_menu_and_predictions'] &= worker['candidate_ids']==list(FAMILIES)
  checks['target_identity_absent'] &= worker['episode_graph_task_attribute_absent'] and worker['graph_task_identity_absent']
  validation=[x for x in worker['examples'] if x['split']=='validation'];test=[x for x in worker['examples'] if x['split']=='test']
  checks['panel_strata_exact'] &= len(validation)==32 and len(test)==1296
  checks['panel_strata_exact'] &= [x['row'] for x in validation]==panel['selection_pool'] and [tuple(x['row']) for x in test]==list(HELD)
  for item in validation:
   y=truth(task,item['row']);checks['panel_strata_exact'] &= item['label'] is y
   for f in FAMILIES:
    pred=formula(f,item['row']);checks['candidate_menu_and_predictions'] &= item['predictions'][f] is pred;scores[f]+=int(pred==y)
  checks['validation_scores_replay'] &= worker['native_validation_scores']==scores
  best=max(scores.values());winners=[f for f in FAMILIES if scores[f]==best]
  expected_adequacy='adequate' if best>=THRESHOLD else 'model_mismatch'
  checks['threshold_status_replay'] &= worker['adequacy_threshold']==THRESHOLD and worker['adequacy_status']==expected_adequacy
  if best<THRESHOLD:
   expected_selection=None;expected_status='abstained_model_mismatch'
  elif len(winners)==1:
   expected_selection=winners[0];expected_status='selected'
  else:
   expected_selection=None;expected_status='abstained_candidate_tie'
  checks['selection_or_refusal_replay'] &= worker['selected_candidate']==expected_selection and worker['selection_status']==expected_status
  confusion={f:Counter({'tp':0,'fp':0,'fn':0,'tn':0}) for f in FAMILIES};selected_correct=0
  for item in test:
   y=truth(task,item['row']);checks['heldout_labels_and_predictions'] &= item['label'] is y
   for f in FAMILIES:
    pred=formula(f,item['row']);checks['candidate_menu_and_predictions'] &= item['predictions'][f] is pred
    bucket='tp' if pred and y else 'fp' if pred else 'fn' if y else 'tn';confusion[f][bucket]+=1
   if expected_selection is None:
    checks['heldout_labels_and_predictions'] &= item['selected_prediction'] is None
   else:
    pred=formula(expected_selection,item['row']);checks['heldout_labels_and_predictions'] &= item['selected_prediction'] is pred
    selected_correct+=int(pred==y)
  checks['labels_revealed_after_receipt'] &= worker['label_reveal_receipt'] is True
  family_exact={f:confusion[f]['fp']==0 and confusion[f]['fn']==0 for f in FAMILIES}
  if task in ('additive','product'):
   expected_selection_family=task
   checks['positive_control_transfer'] &= expected_selection==expected_selection_family and family_exact[task]
  else:
   checks['challenge_is_out_of_menu'] &= not any(family_exact.values())
  row={'task':task,'worker':panel['worker'],'validation_scores':scores,'best_score':best,
   'adequacy_status':worker['adequacy_status'],'selection_status':worker['selection_status'],
   'selected_candidate':expected_selection,'selected_correct':selected_correct,
   'selected_coverage':1296 if expected_selection else 0,'selected_accuracy':selected_correct/1296 if expected_selection else None,
   'candidate_confusion':{f:dict(c) for f,c in confusion.items()},'candidate_exact_on_grid':family_exact,
   'validation_closure_ns':worker['validation_closure_ns'],'score_closure_ns':worker['selection_score_closure_ns'],
   'diagnosis_closure_ns':worker['diagnosis_closure_ns'],'selection_commit_closure_ns':worker['selection_commit_closure_ns'],
   'worker_cpu_ns':worker['worker_cpu_ns'],'peak_rss_kib':worker['worker_peak_rss_kib']}
  per_panel.append(row);costs.append(row);by_task[task]['panels']+=1
  by_task[task]['mismatch_status']+=int(expected_adequacy=='model_mismatch')
  by_task[task]['selected']+=int(expected_selection is not None)
  by_task[task]['correct_family_choice']+=int(expected_selection==task)
  by_task[task]['selected_correct']+=selected_correct
  by_task[task]['candidate_exact_cases']+=int(any(family_exact.values()))
 summary={task:{**dict(c),'mismatch_rate':c['mismatch_status']/c['panels'],'selection_rate':c['selected']/c['panels']} for task,c in by_task.items()}
 result={'schema':'NativeCandidateAdequacyV1Analysis','run_id':'native-candidate-adequacy-v1-analysis-20261005',
  'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(SCRIPT),
  'checks':checks,'passed':all(checks.values()),'adequacy_threshold':THRESHOLD,
  'per_task':summary,'per_panel':per_panel,
  'medians':{k:statistics.median(x[k] for x in costs) for k in ('validation_closure_ns','score_closure_ns','diagnosis_closure_ns','selection_commit_closure_ns','worker_cpu_ns','peak_rss_kib')},
  'interpretation_boundary':'A fixed validation threshold applied by native graph rules detects adequacy for a supplied additive/product menu on three authored numeric relations. This is not learned calibration, a general probability guarantee, or grammar expansion.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'passed':result['passed'],'checks':checks,'per_task':summary,'medians':result['medians'],'output':OUT.relative_to(ROOT).as_posix()}))
 return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
