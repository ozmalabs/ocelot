#!/usr/bin/env python3
"""Audit residual provenance, native candidates, selection, and holdout outcomes."""
import hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/residual_triggered_resynthesis_v1_2_lock_20261004.json';RAW=ROOT/'evaluation/reports/residual_triggered_resynthesis_v1_2_20261004.json';OUT=ROOT/'evaluation/reports/residual_triggered_resynthesis_v1_2_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import residual_triggered_resynthesis_v1_2 as m
 import adaptive_factored_operator_search_v1 as ad
 import term_conditioned_audit_v1 as ta
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text()); up=json.loads(m.UR.read_text()); audits=json.loads(m.TRAW.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture/source binding')
 if m.source_map()!=lock.get('sources') or m.panels()!=lock.get('panels'):errors.append('current source/panel drift')
 if sha(m.UR)!=lock['upstream_capture_sha256'] or sha(m.TRAW)!=lock['audit_capture_sha256']:errors.append('upstream capture drift')
 if not json.loads(m.UA.read_text()).get('passed') or not json.loads(m.TO.read_text()).get('passed'):errors.append('upstream analysis failure')
 rows=raw.get('workers',[]);panels=lock['panels'];urows=up['workers'];arows=audits['workers'];n=_native.Substrate();held=set(itertools.product(lock['heldout_values'],repeat=4))
 arm_summary={name:{'triggered_panels':0,'accepted_exact':0,'accepted_false':0,'help':0,'exact_candidate_pool':0,'median_search_wall_ns':None,'median_search_cpu_ns':None,'median_selection_labels':None} for name in ('no_residual_control','residual_arm')}; rawcost={k:[] for k in arm_summary};
 for i,(w,p,u,a) in enumerate(zip(rows,panels,urows,arows)):
  for k in ('task','worker'):
   if w.get(k)!=p[k] or p[k]!=u[k] or p[k]!=a[k]:errors.append(f'{i}: panel mismatch {k}')
  residual=None
  for e in a.get('events',[]):
   if not e['match']:
    residual={'row':e['row'],'label':int(e['label']),'candidate_prediction':e['prediction']};break
  if w.get('triggered')!=bool(residual) or w.get('residual')!=residual:errors.append(f'{i}: trigger/residual provenance')
  if not residual:
   if w.get('no_residual_control') is not None or w.get('residual_arm') is not None:errors.append(f'{i}: unexpected untriggered search')
   continue
  order=w.get('operator_order'); expected=list(m.OPS[int(p['seed'])%len(m.OPS):]+m.OPS[:int(p['seed'])%len(m.OPS)])
  if order!=expected:errors.append(f'{i}: branch order')
  original=[(dict(zip(m.KEYS,map(float,x['row']))),float(x['label'])) for x in p['training']]
  augmented=original+[(dict(zip(m.KEYS,map(float,residual['row']))),float(residual['label']))]
  for armname,examples in (('no_residual_control',original),('residual_arm',augmented)):
   arm=w[armname]; cands=arm.get('candidate_terms',[]); byid={h['id']:h for h in cands}
   if len(byid)!=len(cands):errors.append(f'{i}:{armname}:duplicate candidate id')
   for h in cands:
    hid='term_'+hashlib.sha256(json.dumps(h['term'],sort_keys=True,separators=(',',':')).encode()).hexdigest()[:16]
    if hid!=h['id']:errors.append(f'{i}:{armname}:candidate id hash')
    for env,y in examples:
     pred=ad.classify(n.evaluate(h['term'],env))
     if pred is not bool(y):errors.append(f'{i}:{armname}:candidate fails acquired examples')
   ids={h['id'] for h in cands}
   if any(cid not in ids for b in arm.get('branches',[]) for cid in b.get('candidate_ids',[])):errors.append(f'{i}:{armname}:branch candidate missing')
   survivors=cands.copy();used=set();expected_labels=[];pool=[dict(zip(m.KEYS,map(float,r))) for r in p['selection_order']]
   while len(survivors)>1 and len(expected_labels)<m.SELECTOR_LABEL_BUDGET:
    avail=[e for e in pool if tuple(float(e[k]) for k in m.KEYS) not in used]
    ans=select_discriminating_input(lambda term,e:ad.classify(n.evaluate(term,e)),survivors,avail,[])
    if not ans.get('ok'):break
    q=ans['query'];row=[float(q[k]) for k in m.KEYS];label=bool(ad.truth(p['task'],row));before=len(survivors)
    survivors=[h for h in survivors if ad.classify(n.evaluate(h['term'],q)) is label];used.add(tuple(row));expected_labels.append({'row':row,'label':label,'before':before,'after':len(survivors),'selector_entropy_bits':ans.get('entropy_bits')})
   if arm.get('selection_labels')!=expected_labels or arm.get('final_survivor_ids')!=[h['id'] for h in survivors]:errors.append(f'{i}:{armname}:selection replay')
   decision='accept' if len(survivors)==1 else 'request_help';selected=survivors[0] if decision=='accept' else None
   if arm.get('decision')!=decision or arm.get('selected_id')!=(None if selected is None else selected['id']):errors.append(f'{i}:{armname}:decision mismatch')
   scored=survivors if selected else cands; expected_scores=[{'id':h['id'],'score':ad.score(n,p['task'],h['term'])} for h in scored]
   if arm.get('scored_candidates')!=expected_scores:errors.append(f'{i}:{armname}:holdout score mismatch')
   exact_pool=any(ad.score(n,p['task'],h['term'])['exact'] for h in cands)
   su=arm_summary[armname];su['triggered_panels']+=1;su['exact_candidate_pool']+=int(exact_pool)
   su['accepted_exact']+=int(bool(selected and expected_scores[0]['score']['exact']));su['accepted_false']+=int(bool(selected and not expected_scores[0]['score']['exact']));su['help']+=int(not selected)
   rawcost[armname].append((arm['search_wall_ns'],arm['search_cpu_ns'],len(arm['selection_labels'])))
 for name,vals in rawcost.items():
  if vals:
   import statistics
   arm_summary[name]['median_search_wall_ns']=statistics.median(x[0] for x in vals);arm_summary[name]['median_search_cpu_ns']=statistics.median(x[1] for x in vals);arm_summary[name]['median_selection_labels']=statistics.median(x[2] for x in vals)
 checks={'paired_trigger_cohort':sum(bool(w.get('triggered')) for w in rows)==sum(bool(any(not e['match'] for e in a.get('events',[]))) for a in arows),'source_and_upstream_binding':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'residual_is_first_observed_mismatch':not any('trigger/residual' in e for e in errors),'branch_terms_fit_acquired_examples':not any('candidate fails' in e for e in errors),'candidate_and_selector_replay':not any('candidate id' in e or 'selection replay' in e or 'decision mismatch' in e for e in errors),'holdout_rescoring':not any('holdout score' in e for e in errors)}
 result={'schema':'ResidualTriggeredResynthesisV1_2Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'triggered_panel_count':sum(bool(w.get('triggered')) for w in rows),'total_panel_count':len(rows),'by_arm':arm_summary,'claim_boundary':'Paired harness-triggered bounded synthesis after one observed counterexample on the registered four-family numeric tasks; no installation, persistent adoption, or open-ended self-improvement.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
