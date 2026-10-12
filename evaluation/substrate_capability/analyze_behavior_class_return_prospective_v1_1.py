#!/usr/bin/env python3
"""Independent replay of the fresh finite-class policy capture."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
import behavior_class_return_prospective_v1 as run
from substrate_rs import _native
from domains.contract_query import select_discriminating_input
LOCK=ROOT/'evaluation/substrate_capability/behavior_class_return_prospective_v1_lock_20261003.json';RAW=ROOT/'evaluation/reports/behavior_class_return_prospective_v1_20261003.json';OUT=ROOT/'evaluation/reports/behavior_class_return_prospective_v1_1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def partition(native,ids,candidates,pool):
 groups={}
 for hid in ids:
  h=candidates[hid];sig=[]
  for row in pool:
   try:v=native.evaluate(h['term'],run.env(row));key=[type(v).__name__,v]
   except Exception as e:key=['error',type(e).__name__]
   sig.append(key)
  k=json.dumps(sig,sort_keys=True,separators=(',',':'));groups.setdefault(k,[]).append(hid)
 return sorted([sorted(x) for x in groups.values()])
def score(native,task,h,panel):
 errors=invalid=0;rows=[r for r in itertools.product(run.HELDOUT,repeat=4) if r!=(0.,0.,0.,0.)]
 for r in rows:
  try:v=native.evaluate(h['term'],run.env(r))
  except Exception:invalid+=1;continue
  y=run.truth(task,r)
  if type(v)is not bool:invalid+=1
  elif v!=y:errors+=1
 return {'id':h['id'],'family':h['family'],'exact':errors==0 and invalid==0,'fp_fn_errors':errors,'invalid':invalid,'n':len(rows)}
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());errors=[]
 try:
  if run.source_map()!=lock['sources'] or raw.get('sources')!=lock['sources']:errors.append('source map mismatch')
  if raw.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
  expected=run.build_panels()
  if lock.get('panels')!=expected:errors.append('panel reconstruction mismatch')
 except Exception as e:errors.append('provenance: '+str(e));expected=[]
 if len(raw.get('workers',[]))!=25:errors.append('worker count mismatch')
 native=_native.Substrate();task_rows={};policy_rows=[]
 for i,w in enumerate(raw.get('workers',[])):
  if i>=len(expected):break
  p=expected[i]
  if (w.get('task'),w.get('worker'),w.get('seed'),w.get('training'))!=(p['task'],p['worker'],p['seed'],p['training']):errors.append(f"worker {i}: panel mismatch")
  candidates={}
  for arm in w.get('family_searches',[]):
   for h in arm.get('hypotheses',[]):
    if h['id'] in candidates:errors.append(f"worker {i}: duplicate candidate id")
    candidates[h['id']]=h
  policy_map={(x.get('domain'),x.get('policy')):x for x in w.get('policies',[])}
  if set(policy_map)!={('zero_aware','help'),('zero_aware','class'),('nonzero','class')}:errors.append(f"worker {i}: policy set mismatch")
  for (domain,kind),r in policy_map.items():
   pool=p[domain+'_pool']+p[domain+'_challenge_pool'];selection=p[domain+'_order'];challenge=p[domain+'_challenge_order']
   survivors=list(candidates.values());obs=[];used=[];expected_checks=[]
   steps=r.get('steps',[]);step_index=0;returned_early=False
   while survivors and step_index<run.LABEL_BUDGET:
    if kind=='class':
     cls=partition(native,[h['id'] for h in survivors],candidates,pool)
     expected_checks.append({'survivor_ids':sorted(h['id'] for h in survivors),'classes':cls})
     if len(cls)==1:
      returned_early=True
      break
    challenge_count=sum(x['phase']=='challenge' for x in steps[:step_index])
    if len(survivors)==1:
     if challenge_count>=run.POST_CHALLENGE:break
     row=next((x for x in challenge if x not in used),None)
     if row is None:break
     phase='challenge';q=run.env(row)
    else:
     avail=[run.env(x) for x in selection if x not in used]
     if not avail:break
     choice=select_discriminating_input(lambda t,e:native.evaluate(t,e),survivors,avail,obs)
     if not choice.get('ok'):break
     q=choice['query'];row=[float(q[k]) for k in run.KEYS];phase='selection'
    if step_index>=len(steps):
     errors.append(f"worker {i}/{kind}/{domain}: missing recorded action")
     break
    st=steps[step_index]
    if st['phase']!=phase or st['row']!=row:
     errors.append(f"worker {i}/{kind}/{domain}: selected action mismatch")
    if st['before']!=len(survivors) or st['label']!=bool(run.truth(p['task'],tuple(st['row']))):
     errors.append(f"worker {i}: before/label mismatch")
    kept=[]
    for h in survivors:
     try:v=native.evaluate(h['term'],run.env(st['row']))
     except Exception:continue
     if type(v)is bool and v==st['label']:kept.append(h)
    if st['after']!=len(kept):errors.append(f"worker {i}: survivor transition mismatch")
    survivors=kept;used.append(st['row']);obs.append({'inputs':run.env(st['row']),'expected':st['label']});step_index+=1
   if step_index!=len(steps):errors.append(f"worker {i}/{kind}/{domain}: unconsumed recorded steps")
   if kind=='class' and survivors and not returned_early:
    expected_checks.append({'survivor_ids':sorted(h['id'] for h in survivors),'classes':partition(native,[h['id'] for h in survivors],candidates,pool)})
   got_checks=[{'survivor_ids':sorted(x['survivor_ids']),'classes':sorted([sorted(c) for c in x['classes']])} for x in r.get('class_checks',[])]
   expected_checks=[{'survivor_ids':x['survivor_ids'],'classes':x['classes']} for x in expected_checks]
   if kind=='class' and got_checks!=expected_checks:errors.append(f"worker {i}/{kind}/{domain}: decision class replay mismatch")
   final_classes=partition(native,[h['id'] for h in survivors],candidates,pool) if survivors else []
   if r.get('survivor_ids_at_stop')!=[h['id'] for h in survivors]:errors.append(f"worker {i}: terminal survivor mismatch")
   if sorted([sorted(c) for c in r.get('audit_classes',[])])!=final_classes or r.get('behavior_classes_at_stop')!=len(final_classes):errors.append(f"worker {i}: terminal class audit mismatch")
   if kind=='class' and survivors and len(final_classes)==1 and r.get('returned_class_size')!=len(survivors):errors.append(f"worker {i}: class-return cardinality mismatch")
   if kind=='class' and len(final_classes)==1 and survivors:
    expected_ids=set(final_classes[0])
    if set(r.get('returned_ids',[]))!=expected_ids:errors.append(f"worker {i}: class return member mismatch")
   returned=[]
   for h in r.get('returned_terms',[]):
    if h['id'] not in candidates and not str(h['id']).startswith('help:'):errors.append(f"worker {i}: returned unknown candidate")
    got=score(native,p['task'],h,p)
    returned.append(got)
   if returned!=r.get('returned_scores'):errors.append(f"worker {i}: heldout score replay mismatch")
   if bool(returned) and all(x['exact'] for x in returned)!=r.get('all_returned_exact'):errors.append(f"worker {i}: aggregate exact mismatch")
   helpobj=r.get('help');needs_help=bool(not (kind=='class' and survivors and len(final_classes)==1) and (not survivors or r['stop'] in ('selector_abstention','query_pool_exhausted','challenge_pool_exhausted','label_budget')))
   if bool(helpobj)!=needs_help:errors.append(f"worker {i}/{kind}/{domain}: help decision mismatch")
   if helpobj and (helpobj.get('calls')!=1 or helpobj.get('family')!=run.HINT[p['task']]):errors.append(f"worker {i}: help callback mismatch")
   cls_single=bool(survivors) and len(final_classes)==1
   row={'task':p['task'],'worker':p['worker'],'policy':kind,'domain':domain,'labels':r['labels'],'survivors':len(survivors),'classes':len(final_classes),'returned_hypotheses':len(returned),'all_returned_exact':bool(returned) and all(x['exact'] for x in returned),'contains_exact_candidate':any(x['exact'] for x in returned),'exact_candidates':sum(x['exact'] for x in returned),'false_candidates':sum(not x['exact'] for x in returned),'help_calls':int(bool(helpobj)),'help_ns':0 if not helpobj else helpobj['wall_ns'],'synthesis_ns':w['synthesis_total_ns'],'selector_ns':r['cost']['selector_ns'],'class_ns':r['cost']['class_decision_ns'],'class_evals':r['cost']['class_decision_term_evaluations'],'returned_class':bool(kind=='class' and cls_single and r['stop']=='single_behavior_class')}
   policy_rows.append(row);task_rows.setdefault((kind,domain),[]).append(row)
 policies={}
 for key,rs in task_rows.items():
  k,d=key;policies[k+':'+d]={'panels':len(rs),'labels_total':sum(x['labels'] for x in rs),'labels_median':statistics.median(x['labels'] for x in rs),'successful_panels':sum(x['all_returned_exact'] for x in rs),'panels_with_any_exact_candidate':sum(x['contains_exact_candidate'] for x in rs),'exact_candidates_total':sum(x['exact_candidates'] for x in rs),'false_candidates_total':sum(x['false_candidates'] for x in rs),'harmful_or_inexact_panels':sum(not x['all_returned_exact'] for x in rs),'returned_classes':sum(x['returned_class'] for x in rs),'help_calls':sum(x['help_calls'] for x in rs),'help_ns_total':sum(x['help_ns'] for x in rs),'synthesis_ns_total':sum(x['synthesis_ns'] for x in rs),'selector_ns_total':sum(x['selector_ns'] for x in rs),'class_ns_total':sum(x['class_ns'] for x in rs),'class_ns_median_per_panel':statistics.median(x['class_ns'] for x in rs),'class_evaluations_total':sum(x['class_evals'] for x in rs)}
 result={'schema':'BehaviorClassReturnProspectiveV1Analysis','passed':not errors,'errors':errors,'source_hashes':{'lock':sha(LOCK),'capture':sha(RAW),'analyzer':sha(Path(__file__))},'policies':policies,'limits':['five authored numeric relations, five fresh panels each','finite class pools and finite fractional holdout','task-specific help callback is harness-supplied','one host and no persistent rule adoption'],'rows':policy_rows}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'errors':errors,'policies':policies},indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
