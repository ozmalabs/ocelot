#!/usr/bin/env python3
"""Independent replay of paired native request-help query experiments."""
from __future__ import annotations
import hashlib,itertools,json,random,statistics,sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/native_candidate_adequacy_query_v1_1_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/native_candidate_adequacy_query_v1_1_lock_20261005.json'
SCRIPT=Path(__file__).resolve();OUT=ROOT/'evaluation/reports/native_candidate_adequacy_query_v1_1_analysis_20261005.json'
TASKS=('additive','product','opposition','inequality');ARMS=('candidate_positive','uniform');FAMILIES=('additive','product');IV=tuple(float(x) for x in range(-3,4));FV=(-2.5,-1.5,-.5,.5,1.5,2.5);THRESHOLD=.98;BUDGET=4
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def target(task,row):
 ax,ay,ex,ey=map(float,row)
 if task=='additive':return ax+ay==ex+ey
 if task=='product':return ax*ay==ex*ey
 if task=='opposition':return ax==-ex and ay==-ey
 return ax!=ex
def formula(f,row):
 ax,ay,ex,ey=map(float,row)
 return ax+ay==ex+ey if f=='additive' else ax*ay==ex*ey
def panel_set():
 out=[];grid=list(itertools.product(IV,repeat=4))
 for ti,task in enumerate(TASKS):
  for worker in range(10):
   seed=930000+ti*100+worker;validation=[]
   for label in (True,False):
    pool=[list(r) for r in grid if target(task,r) is label];random.Random(seed+(0 if label else 1)).shuffle(pool);chosen=[]
    for src in ([r for r in pool if 0.0 in r],[r for r in pool if any(abs(x)==3 for x in r)]):
     n=0
     for row in src:
      if row not in chosen:chosen.append(row);n+=1
      if n==8:break
    for row in pool:
     if len(chosen)>=16:break
     if row not in chosen:chosen.append(row)
    validation.extend({'row':row,'label':label} for row in chosen)
   for arm in ARMS:out.append({'task':task,'worker':worker,'seed':seed,'arm':arm,'validation':validation})
 return out
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(CAPTURE.read_text());expected=panel_set()
 checks={k:True for k in ('capture_lock_match','eighty_expected_workers','source_lock_current','paired_panel_and_balance','native_candidate_predictions','native_score_replay','initial_policy_replay','target_blind_query_order','native_help_after_mismatch','query_and_transfer_disjointness','heldout_prediction_and_score_replay','task_identity_absent')}
 checks['capture_lock_match']=raw['lock_sha256']==sha(LOCK) and raw['locked_inputs']==lock['inputs'] and raw['post_run_inputs']==lock['inputs']
 checks['eighty_expected_workers']=len(raw['workers'])==80 and lock['panels']==expected
 sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'));import native_candidate_adequacy_query_v1_1 as runner
 checks['source_lock_current']=runner.manifest()==lock['inputs']
 by_panel=defaultdict(Counter);summary={t:{a:Counter() for a in ARMS} for t in TASKS};records=[];costs=[]
 integer=list(itertools.product(IV,repeat=4));fractional=list(itertools.product(FV,repeat=4))
 for w,p in zip(raw['workers'],expected):
  task=p['task'];arm=p['arm'];worker=p['worker'];by_panel[(task,worker)][arm]+=1
  checks['paired_panel_and_balance'] &= w['panel']['task_for_scorer_only']==task and w['panel']['worker']==worker and w['panel']['seed']==p['seed'] and w['panel']['arm']==arm and w['panel']['validation_rows']==p['validation']
  val=[x for x in p['validation']];checks['paired_panel_and_balance'] &= len(val)==32 and sum(x['label'] is True for x in val)==16 and sum(x['label'] is False for x in val)==16
  cm={f:Counter() for f in FAMILIES};rawscore={f:0 for f in FAMILIES}
  for x in val:
   y=target(task,x['row'])
   for f in FAMILIES:
    pred=formula(f,x['row']);rawscore[f]+=int(pred==y);cm[f]['tp' if pred and y else 'fp' if pred else 'fn' if y else 'tn']+=1
  scores={f:min(cm[f]['tp']/16,cm[f]['tn']/16) for f in FAMILIES}
  checks['native_score_replay'] &= w['native_min_class_accuracy_scores']==scores and w['native_raw_validation_scores']=={f:float(rawscore[f]) for f in FAMILIES}
  best=max(scores.values());wins=[f for f in FAMILIES if scores[f]==best];adequate=best>=THRESHOLD;selected=wins[0] if adequate and len(wins)==1 else None
  initial='selected' if selected else ('abstain_tie' if adequate else 'request_help')
  checks['initial_policy_replay'] &= w['adequacy_status_before_queries']==('adequate' if adequate else 'model_mismatch') and w['selected_candidate']==selected and w['initial_decision']==initial
  grid=[r for r in integer if tuple(r) not in {tuple(x['row']) for x in p['validation']}]+fractional
  qpool=[r for r in grid if selected is None or arm=='uniform' or formula(selected,r)] if selected is not None else []
  seed=f'native-adequacy-query-v1.1:replicate:{worker}'
  order=sorted(qpool,key=lambda row:hashlib.sha256((seed+':'+json.dumps(list(row),separators=(',',':'))).encode()).hexdigest())[:BUDGET]
  queries=w['query_rows'];checks['target_blind_query_order'] &= [tuple(x['row']) for x in queries]==[tuple(r) for r in order[:len(queries)]] and len(queries)<=BUDGET
  mismatch_seen=False
  for q,row in zip(queries,order):
   y=target(task,row);pred=formula(selected,row) if selected else None;mismatch=pred is not y
   expected_preds={f:formula(f,row) for f in FAMILIES}
   checks['target_blind_query_order'] &= [tuple(x['row']) for x in queries]==[tuple(r) for r in order[:len(queries)]]
   checks['native_candidate_predictions'] &= q['predictions']==expected_preds
   checks['native_help_after_mismatch'] &= q['label_after_query'] is y and q['candidate_prediction'] is pred and q['mismatch'] is mismatch and q['native_decision_after_query']==('request_help' if mismatch else 'selected')
   if mismatch:mismatch_seen=True
  checks['native_help_after_mismatch'] &= len(queries)==(0 if selected is None else (next((i+1 for i,q in enumerate(queries) if q['mismatch']),min(BUDGET,len(order)))))
  final_decision='request_help' if initial=='request_help' or mismatch_seen else initial
  checks['native_help_after_mismatch'] &= w['final_decision']==final_decision and all(q['native_decision_after_query']=='request_help' for q in queries if q['mismatch'])
  qkeys={tuple(q['row']) for q in queries};remain=[r for r in grid if tuple(r) not in qkeys];final=w['final_test_rows']
  checks['query_and_transfer_disjointness'] &= len(final)==len(remain) and [tuple(x['row']) for x in final]==remain and not qkeys.intersection(tuple(x['row']) for x in p['validation'])
  confusion={f:Counter() for f in FAMILIES};selected_correct=0
  for x,row in zip(final,remain):
   y=target(task,row);preds={f:formula(f,row) for f in FAMILIES};checks['native_candidate_predictions'] &= x['predictions']==preds;checks['heldout_prediction_and_score_replay'] &= x['label'] is y and x['predictions']==preds
   for f,pred in preds.items():confusion[f]['tp' if pred and y else 'fp' if pred else 'fn' if y else 'tn']+=1
   chosen_pred=preds[selected] if selected is not None and final_decision=='selected' else None
   checks['heldout_prediction_and_score_replay'] &= x['selected_prediction'] is chosen_pred
   if chosen_pred is not None:selected_correct+=int(chosen_pred is y)
  checks['task_identity_absent'] &= w['task_identity_absent'] is True and w['query_receipt_valid'] is True
  c=summary[task][arm];c['panels']+=1;c['baseline_selected']+=int(selected is not None);c['help_after_query']+=int(final_decision=='request_help' and initial=='selected');c['baseline_help']+=int(initial=='request_help');c['queries']+=len(queries);c['mismatches_found']+=sum(q['mismatch'] for q in queries);c['false_help_controls']+=int(task in ('additive','product') and final_decision=='request_help');c['false_accept_opposition']+=int(task=='opposition' and final_decision=='selected');c['selected_correct_rows']+=selected_correct;c['scored_rows']+=len(final) if final_decision=='selected' else 0
  costs.append(w['worker_cpu_ns']);records.append({'task':task,'worker':worker,'arm':arm,'baseline_candidate':selected,'initial_decision':initial,'queries':len(queries),'counterexamples':sum(q['mismatch'] for q in queries),'final_decision':final_decision,'heldout_selected_accuracy':selected_correct/len(final) if final_decision=='selected' else None,'heldout_rows_after_query':len(final),'candidate_confusion':{f:dict(x) for f,x in confusion.items()}})
 checks['paired_panel_and_balance'] &= all(v=={'candidate_positive':1,'uniform':1} for v in by_panel.values()) and len(by_panel)==40
 result={'schema':'NativeCandidateAdequacyQueryV1_1Analysis','capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(SCRIPT),'checks':checks,'passed':all(checks.values()),'threshold':THRESHOLD,'budget':BUDGET,'per_task_and_arm':{t:{a:dict(c) for a,c in arms.items()} for t,arms in summary.items()},'per_panel':records,'median_worker_cpu_ns':statistics.median(costs) if costs else None,'interpretation_limit':'Fresh finite paired evaluation. Query ordering is performed by the host harness from native predictions; native graph rules compute adequacy and convert queried mismatches to request_help. Supplied menu only; no autonomous hypothesis generation.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'per_task_and_arm':result['per_task_and_arm'],'median_worker_cpu_ns':result['median_worker_cpu_ns'],'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
