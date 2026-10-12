#!/usr/bin/env python3
"""Independent audit of integer/continuous confirmation and help controls."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/continuous_singleton_audit_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/continuous_singleton_audit_v1_20261004.json';OUT=ROOT/'evaluation/reports/continuous_singleton_audit_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import continuous_singleton_audit_v1 as m
 import adaptive_factored_operator_search_v1 as prev
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());up=json.loads(m.ADRAW.read_text());up_analysis=json.loads(m.ADOUT.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture/lock/source binding')
 if m.source_map()!=lock.get('sources') or m.panels()!=lock.get('panels'):errors.append('current source/panel drift')
 if sha(m.ADRAW)!=lock.get('adaptive_capture_sha256') or not up_analysis.get('passed'):errors.append('adaptive control provenance')
 rows=raw.get('workers',[])
 if len(rows)!=20 or len(up.get('workers',[]))!=20:errors.append('paired panel count')
 native=_native.Substrate();by={t:{p:{'panels':0,'correct_accepts':0,'false_accepts':0,'help':0,'audit_labels':[]} for p in ('integer','continuous','help')} for t in m.TASKS};details=[]
 heldout_set={tuple(x) for x in itertools.product(m.HELD,repeat=4)}
 for i,(w,p,base) in enumerate(zip(rows,lock['panels'],up['workers'])):
  if any(w.get(k)!=p[k] for k in ('task','worker','seed','training','selection_pool','selection_order')):errors.append(f'{i}:panel mismatch')
  if any(base.get(k)!=p[k] for k in ('task','worker','seed','training','selection_pool','selection_order')):errors.append(f'{i}:upstream panel mismatch')
  hid=base.get('accepted_id');candidate=next((h for h in base.get('final_terms',[]) if h['id']==hid),None)
  if w.get('candidate_id')!=hid or w.get('candidate_term')!=(None if not candidate else candidate['term']):errors.append(f'{i}:candidate binding')
  # The baseline is only the accepted candidate's terminal integer audit, not
  # any earlier rejected singleton in the same search trace.
  last=[e for b in base.get('branches',[]) if b.get('decision')=='accept' for e in b.get('events',[]) if e.get('kind')=='audit' and e.get('candidate_id')==hid]
  if w.get('integer_audit_events')!=last:errors.append(f'{i}:integer audit binding')
  continuous_decision='request_help';continuous_calls=0;continuous_correct=False;continuous_false=False
  forbidden={tuple(map(float,x['row'])) for x in p['training']}|{tuple(map(float,x)) for x in p['selection_pool']}
  generated=m.audit_rows(p['task'],p['seed'],forbidden) if candidate else []
  if w.get('continuous_audit_examples')!=generated:errors.append(f'{i}:continuous generator replay')
  if candidate:
   continuous_decision='accept'
   for j,(x,event) in enumerate(zip(generated,w.get('continuous_events',[]))):
    row=x['row'];q=dict(zip(m.KEYS,row));pred=prev.classify(native.evaluate(candidate['term'],q));label=bool(m.truth(p['task'],row))
    if tuple(row) in heldout_set or tuple(row) in forbidden:errors.append(f'{i}:audit overlap')
    if x.get('kind')!=('positive' if label else 'negative') or x.get('label')!=int(label):errors.append(f'{i}:audit balance/label')
    if pred!=event.get('prediction') or label is not event.get('label') or (pred is label)!=event.get('match'):errors.append(f'{i}:continuous oracle replay')
    continuous_calls+=1
    if pred is not label:continuous_decision='request_help';break
   if len(w.get('continuous_events',[]))!=continuous_calls:errors.append(f'{i}:continuous stopping transcript')
   continuous_correct=continuous_decision=='accept' and prev.score(native,p['task'],candidate['term'])['exact']
   continuous_false=continuous_decision=='accept' and not continuous_correct
  else:
   if w.get('continuous_events') or w.get('continuous_policy_decision')!='request_help':errors.append(f'{i}:missing-candidate action')
  if w.get('continuous_policy_decision')!=continuous_decision or w.get('continuous_policy_labels')!=continuous_calls:errors.append(f'{i}:continuous terminal decision/cost')
  if w.get('help_control_decision')!='request_help' or w.get('help_control_labels')!=0:errors.append(f'{i}:help control')
  integer_correct=bool(hid and prev.score(native,p['task'],candidate['term'])['exact'])
  integer_false=bool(hid and not integer_correct)
  for policy,has_candidate,correct,false,calls in (('integer',bool(hid),integer_correct,integer_false,len(last)),('continuous',bool(hid),continuous_correct,continuous_false,continuous_calls),('help',False,False,False,0)):
   s=by[p['task']][policy];s['panels']+=1;s['correct_accepts']+=int(correct);s['false_accepts']+=int(false);s['help']+=int(not (correct or false));s['audit_labels'].append(calls)
  details.append({'task':p['task'],'worker':p['worker'],'candidate_id':hid,'holdout_exact':integer_correct if hid else None,'integer_audit_labels':len(last),'continuous_decision':continuous_decision,'continuous_labels':continuous_calls,'continuous_holdout_correct':continuous_correct if hid else None})
 for task,policies in by.items():
  for s in policies.values():s['median_audit_labels']=statistics.median(s.pop('audit_labels'))
 checks={'twenty_paired_outcomes':len(rows)==20,'current_sources_and_capture_bound':not any('binding' in e or 'drift' in e or 'provenance' in e or 'panel mismatch' in e for e in errors),'continuous_examples_balanced_and_disjoint':not any('generator' in e or 'overlap' in e or 'balance' in e for e in errors),'integer_and_continuous_oracle_transcripts':not any('audit ' in e or 'oracle' in e or 'stopping' in e for e in errors),'holdout_scoring_after_policy_decisions':not any('candidate binding' in e or 'terminal decision' in e or 'holdout' in e for e in errors),'help_control_present':not any('help control' in e for e in errors)}
 result={'schema':'ContinuousSingletonAuditV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'by_task_and_policy':by,'cells':details,'claim_boundary':'Post-search audit distribution comparison over four authored numeric task families; no resynthesis or open-ended capability claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
