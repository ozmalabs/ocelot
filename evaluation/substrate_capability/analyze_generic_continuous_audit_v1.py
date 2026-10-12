#!/usr/bin/env python3
"""Independent replay and scoring for generic continuous audit v1."""
import hashlib,json,statistics,sys,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/generic_continuous_audit_v1_lock_20261004.json'; RAW=ROOT/'evaluation/reports/generic_continuous_audit_v1_20261004.json'; OUT=ROOT/'evaluation/reports/generic_continuous_audit_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import generic_continuous_audit_v1 as m
 import adaptive_factored_operator_search_v1 as ad
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text()); raw=json.loads(RAW.read_text()); upstream=json.loads(m.ADRAW.read_text()); errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture lock/source binding')
 if m.source_map()!=lock.get('sources') or m.panels()!=lock.get('panels'):errors.append('current source/panel drift')
 if sha(m.ADRAW)!=lock.get('adaptive_capture_sha256') or sha(m.C_RAW)!=lock.get('continuous_capture_sha256'):errors.append('upstream capture drift')
 rows=raw.get('workers',[]); panels=lock.get('panels',[]); ups=upstream.get('workers',[]); n=_native.Substrate(); caps=m.CAPS
 if len(rows)!=20 or len(panels)!=20 or len(ups)!=20:errors.append('panel cardinality')
 sums={cap:{'panels':0,'correct_accepts':0,'false_accepts':0,'help':0,'labels':[]} for cap in caps}; by={t:{cap:{'panels':0,'correct_accepts':0,'false_accepts':0,'help':0,'labels':[]} for cap in caps} for t in m.TASKS}; details=[]
 held={tuple(x) for x in itertools.product((-2.5,-1.5,-.5,.5,1.5,2.5),repeat=4)}
 for i,(w,p,u) in enumerate(zip(rows,panels,ups)):
  for k in ('task','worker','seed'):
   if w.get(k)!=p[k] or p[k]!=u[k]: errors.append(f'{i}: panel mismatch {k}')
  candidate=next((h for h in u.get('final_terms',[]) if h['id']==u.get('accepted_id')),None)
  if w.get('candidate_id')!=u.get('accepted_id') or w.get('candidate_term')!=(None if candidate is None else candidate['term']):errors.append(f'{i}: candidate mismatch')
  forbidden={tuple(map(float,x['row'])) for x in p['training']}|{tuple(map(float,x)) for x in p['selection_pool']}
  expected=m.draw(p['task'],p['seed'],[list(x) for x in forbidden]) if candidate else []
  if w.get('rows')!=expected:errors.append(f'{i}: sampler replay')
  if len(w.get('events',[]))!= (min(len(expected),w.get('first_mismatch_labels') or len(expected))):errors.append(f'{i}: event length')
  mismatch=None
  if candidate:
   for j,(row,e) in enumerate(zip(expected,w['events'])):
    if tuple(row) in forbidden or tuple(row) in held:errors.append(f'{i}: forbidden/holdout overlap')
    if len(row)!=4 or any(not m.LOW<=float(x)<=m.HIGH for x in row):errors.append(f'{i}: sample outside domain')
    pred=ad.classify(n.evaluate(candidate['term'],dict(zip(m.KEYS,row)))); label=bool(m.truth(p['task'],row))
    if (pred,label,pred is label)!=(e.get('prediction'),e.get('label'),e.get('match')):errors.append(f'{i}: oracle transcript mismatch')
    if pred is not label: mismatch=j+1; break
   if mismatch!=w.get('first_mismatch_labels'):errors.append(f'{i}: mismatch stop')
  elif w.get('events') or w.get('first_mismatch_labels') is not None:errors.append(f'{i}: no-candidate behavior')
  exact=bool(candidate and ad.score(n,p['task'],candidate['term'])['exact'])
  expected_out=[]
  for cap in caps:
   stop=mismatch is not None and mismatch<=cap
   decision='request_help' if not candidate or stop else 'accept'
   labels=0 if not candidate else min(cap,len(w.get('events',[])))
   expected_out.append({'cap':cap,'decision':decision,'labels':labels,'correct_accept':decision=='accept' and exact,'false_accept':decision=='accept' and not exact,'help':decision!='accept'})
   if not candidate: labels=0
   if decision!='accept' and candidate: labels=mismatch if stop else min(cap,len(expected))
   s=sums[cap]; t=by[p['task']][cap]
   for d in (s,t):
    d['panels']+=1;d['correct_accepts']+=int(decision=='accept' and exact);d['false_accepts']+=int(decision=='accept' and not exact);d['help']+=int(decision!='accept');d['labels'].append(labels)
  if w.get('outcomes')!=expected_out:errors.append(f'{i}: cap outcome mismatch')
  if w.get('help_control')!={'decision':'request_help','labels':0}:errors.append(f'{i}: help control')
  details.append({'task':p['task'],'worker':p['worker'],'candidate_id':u.get('accepted_id'),'holdout_exact':exact if candidate else None,'first_mismatch_labels':mismatch,'outcomes':expected_out})
 for bundle in [sums,*by.values()]:
  for x in bundle.values():x['median_labels']=statistics.median(x.pop('labels')) if x['labels'] else None
 checks={'paired_20_panel_capture':len(rows)==20,'provenance_current_and_bound':not any('binding' in e or 'drift' in e for e in errors),'uniform_samples_replay_and_are_disjoint':not any('sampler' in e or 'overlap' in e or 'outside' in e for e in errors),'native_candidate_oracle_and_stop_replay':not any('transcript' in e or 'mismatch stop' in e for e in errors),'holdout_scored_after_policy_decision':not any('candidate mismatch' in e or 'cap outcome' in e for e in errors),'help_control_present':not any('help control' in e for e in errors)}
 result={'schema':'GenericContinuousAuditV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'by_cap':sums,'by_task_and_cap':by,'cells':details,'comparison_reference':{'conditioned_audit_analysis_sha256':sha(m.C_OUT),'integer_and_conditioned_results':json.loads(m.C_OUT.read_text()).get('by_task_and_policy')},'claim_boundary':'Task-agnostic uniform sampling for post-search candidate audits on 20 fixed panels; no equivalence certification, resynthesis, or general learning claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
