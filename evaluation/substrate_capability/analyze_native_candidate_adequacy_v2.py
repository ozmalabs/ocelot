#!/usr/bin/env python3
"""Independent replay of balanced adequacy, selection, and sealed transfer."""
from __future__ import annotations
import hashlib,itertools,json,statistics,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/native_candidate_adequacy_v2_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/native_candidate_adequacy_v2_lock_20261005.json'
RUNNER=ROOT/'evaluation/substrate_capability/native_candidate_adequacy_v2.py'
SCRIPT=Path(__file__).resolve();OUT=ROOT/'evaluation/reports/native_candidate_adequacy_v2_analysis_20261005.json'
TASKS=('additive','product','opposition','inequality');FAMILIES=('additive','product');IV=tuple(float(x) for x in range(-3,4));FV=(-2.5,-1.5,-.5,.5,1.5,2.5);THRESHOLD=.75
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def truth(task,row):
 ax,ay,ex,ey=map(float,row)
 if task=='additive':return ax+ay==ex+ey
 if task=='product':return ax*ay==ex*ey
 if task=='opposition':return ax==-ex and ay==-ey
 return ax!=ex
def formula(family,row):
 ax,ay,ex,ey=map(float,row)
 return ax+ay==ex+ey if family=='additive' else ax*ay==ex*ey
def expected_panels():
 panels=[];grid=list(itertools.product(IV,repeat=4))
 for ti,task in enumerate(TASKS):
  for worker in range(10):
   seed=730000+ti*100+worker;validation=[]
   for label in (True,False):
    pool=[list(r) for r in grid if truth(task,r) is label]
    import random
    random.Random(seed+(0 if label else 1)).shuffle(pool)
    chosen=[]
    for src in ([r for r in pool if 0.0 in r],[r for r in pool if any(abs(x)==3 for x in r)]):
     n=0
     for row in src:
      if row not in chosen:chosen.append(row);n+=1
      if n==8:break
    for row in pool:
     if len(chosen)>=16:break
     if row not in chosen:chosen.append(row)
    validation.extend({'row':row,'label':label} for row in chosen)
   panels.append({'task':task,'worker':worker,'seed':seed,'validation':validation})
 return panels
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());expected=expected_panels()
 checks={k:True for k in ('capture_lock_match','forty_expected_panels','source_lock_current','balanced_validation_and_coverage','candidate_predictions','native_score_replay','decision_policy_replay','task_identity_absent','label_reveal_receipts','heldout_grid_and_transfer')}
 checks['capture_lock_match']=data['lock_sha256']==sha(LOCK) and data['locked_inputs']==lock['inputs'] and data['post_run_inputs']==lock['inputs']
 checks['forty_expected_panels']=len(data['workers'])==40 and lock['panels']==expected
 sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'));import native_candidate_adequacy_v2 as runner
 checks['source_lock_current']=runner.manifest()==lock['inputs']
 per_task={t:Counter() for t in TASKS};records=[];costs=[]
 intgrid=list(itertools.product(IV,repeat=4));fracgrid=list(itertools.product(FV,repeat=4))
 for worker,panel in zip(data['workers'],expected):
  task=panel['task'];rec=worker['panel'];val=[e for e in worker['examples'] if e['split']=='validation'];test=[e for e in worker['examples'] if e['split']=='test']
  checks['balanced_validation_and_coverage'] &= rec['task_for_scorer_only']==task and rec['worker']==panel['worker'] and rec['seed']==panel['seed'] and rec['validation_rows']==panel['validation']
  checks['balanced_validation_and_coverage'] &= len(val)==32 and sum(x['label'] is True for x in val)==16 and sum(x['label'] is False for x in val)==16
  for y in (True,False):
   strata=[x['row'] for x in val if x['label'] is y]
   checks['balanced_validation_and_coverage'] &= any(0.0 in r for r in strata) and any(any(abs(float(v))==3 for v in r) for r in strata)
  scores={f:Counter() for f in FAMILIES};raw={f:0 for f in FAMILIES}
  for item in val:
   y=truth(task,item['row']);checks['balanced_validation_and_coverage'] &= item['label'] is y
   for f in FAMILIES:
    pred=formula(f,item['row']);checks['candidate_predictions'] &= item['predictions'][f] is pred
    raw[f]+=int(pred==y);scores[f]['tp' if pred and y else 'fp' if pred else 'fn' if y else 'tn']+=1
  ba={f:(scores[f]['tp']/16+scores[f]['tn']/16)/2 for f in FAMILIES}
  checks['native_score_replay'] &= worker['native_validation_scores']==ba and worker['native_raw_validation_scores']==raw
  best=max(ba.values());winners=[f for f in FAMILIES if ba[f]==best]
  adequate=best>=THRESHOLD;chosen=winners[0] if adequate and len(winners)==1 else None
  status='adequate' if adequate else 'model_mismatch';decision='selected' if chosen else ('abstain_tie' if adequate else 'request_help')
  checks['decision_policy_replay'] &= worker['adequacy_threshold']==THRESHOLD and worker['adequacy_status']==status and worker['selected_candidate']==chosen and worker['decision']==decision
  checks['decision_policy_replay'] &= worker['selection_status']==('selected' if chosen else ('abstained_candidate_tie' if adequate else 'request_help'))
  checks['task_identity_absent'] &= worker['episode_graph_task_attribute_absent'] and worker['graph_task_identity_absent']
  validation_keys={tuple(x['row']) for x in panel['validation']};expected_test=[r for r in intgrid if r not in validation_keys]+fracgrid
  checks['heldout_grid_and_transfer'] &= len(test)==3665 and [tuple(x['row']) for x in test]==expected_test
  confusion={f:Counter() for f in FAMILIES};correct=0
  for item,row in zip(test,expected_test):
   y=truth(task,row);checks['heldout_grid_and_transfer'] &= item['label'] is y
   for f in FAMILIES:
    pred=formula(f,row);checks['candidate_predictions'] &= item['predictions'][f] is pred
    confusion[f]['tp' if pred and y else 'fp' if pred else 'fn' if y else 'tn']+=1
   pred=formula(chosen,row) if chosen else None
   checks['heldout_grid_and_transfer'] &= item['selected_prediction'] is pred
   if pred is not None:correct+=int(pred==y)
  checks['label_reveal_receipts'] &= worker['label_reveal_receipt'] is True
  per_task[task]['panels']+=1;per_task[task]['request_help']+=int(decision=='request_help');per_task[task]['selected']+=int(decision=='selected');per_task[task]['ties']+=int(decision=='abstain_tie');per_task[task]['correct_family_choice']+=int(chosen==task)
  per_task[task]['selected_correct_rows']+=correct;per_task[task]['selected_rows']+=len(test) if chosen else 0
  per_task[task]['false_accept']+=int(task in ('opposition','inequality') and chosen is not None);per_task[task]['false_help']+=int(task in ('additive','product') and chosen is None)
  costs.append(worker['worker_cpu_ns'])
  records.append({'task':task,'worker':panel['worker'],'raw_scores':raw,'balanced_accuracy':ba,'decision':decision,'selected':chosen,'selected_accuracy':correct/len(test) if chosen else None,'candidate_confusion_heldout':{f:dict(c) for f,c in confusion.items()}})
 summary={t:{**dict(c),'request_help_rate':c['request_help']/c['panels'],'selection_rate':c['selected']/c['panels'],'false_accept_rate':c['false_accept']/c['panels'],'false_help_rate':c['false_help']/c['panels']} for t,c in per_task.items()}
 result={'schema':'NativeCandidateAdequacyV2Analysis','capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(SCRIPT),'checks':checks,'passed':all(checks.values()),'threshold':THRESHOLD,'per_task':summary,'per_panel':records,'median_worker_cpu_ns':statistics.median(costs) if costs else None,'interpretation_boundary':'Finite four-relation evaluation of a supplied additive/product candidate menu using native class-balanced adequacy scores. It does not test open-ended primitive invention or autonomous self-improvement.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'per_task':summary,'median_worker_cpu_ns':result['median_worker_cpu_ns'],'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
