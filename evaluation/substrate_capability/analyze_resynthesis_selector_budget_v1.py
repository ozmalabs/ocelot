#!/usr/bin/env python3
"""Independent audit of selector-budget extension."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/resynthesis_selector_budget_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/resynthesis_selector_budget_v1_20261004.json';OUT=ROOT/'evaluation/reports/resynthesis_selector_budget_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import resynthesis_selector_budget_v1 as m
 import residual_triggered_resynthesis_v1_2 as s
 import adaptive_factored_operator_search_v1 as ad
 from domains.contract_query import select_discriminating_input
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());panels,up=m.inputs();errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock['sources']:errors.append('capture/lock/source binding')
 if m.source_map()!=lock['sources'] or panels!=lock['panels']:errors.append('source/panel drift')
 if sha(m.SRAW)!=lock['upstream_capture_sha256'] or not json.loads(m.SOUT.read_text()).get('passed'):errors.append('upstream evidence')
 if len(raw.get('workers',[]))!=20:errors.append('panel count')
 n=_native.Substrate();held=set(itertools.product(s.HELD,repeat=4));agg={str(c):{'panels':0,'exact_accept':0,'false_accept':0,'help':0,'labels':[]} for c in lock['caps']};by={}
 for i,(w,p,up) in enumerate(zip(raw['workers'],panels,json.loads(m.SRAW.read_text())['workers'])):
  if w.get('task')!=p['task'] or w.get('worker')!=p['worker'] or w.get('triggered')!=up['triggered']:errors.append(f'{i}: panel mismatch')
  if not up['triggered']:
   if w.get('arms')!={}:errors.append(f'{i}: unexpected arms');continue
  pool=[dict(zip(s.KEYS,map(float,x))) for x in p['selection_order']]; forbidden={tuple(map(float,x['row'])) for x in p['training']};forbidden|={tuple(map(float,x)) for x in p['selection_pool']}
  for name in ('no_residual_control','residual_arm'):
   base=up[name];a=w['arms'][name];cands=base['candidate_terms'];survivors=cands.copy();used=set();events=[]
   for e in base['selection_labels']:
    row=e['row'];q=dict(zip(s.KEYS,row));survivors=[h for h in survivors if ad.classify(n.evaluate(h['term'],q)) is bool(e['label'])];used.add(tuple(row));events.append(dict(e))
   checkpoints={}
   for cap in lock['caps']:
    target=len(pool) if cap=='all' else cap
    while len(events)<target and len(survivors)>1:
     avail=[e for e in pool if tuple(float(e[k]) for k in s.KEYS) not in used]
     if not avail:break
     ans=select_discriminating_input(lambda term,e:ad.classify(n.evaluate(term,e)),survivors,avail,[])
     if not ans.get('ok'):break
     q=ans['query'];row=[float(q[k]) for k in s.KEYS];label=bool(ad.truth(p['task'],row));before=len(survivors)
     survivors=[h for h in survivors if ad.classify(n.evaluate(h['term'],q)) is label];used.add(tuple(row));events.append({'row':row,'label':label,'before':before,'after':len(survivors),'selector_entropy_bits':ans.get('entropy_bits')})
    decision='accept' if len(survivors)==1 else 'request_help'
    checkpoints[str(cap)]={'cumulative_labels':len(events),'candidate_count':len(survivors),'decision':decision,'survivor_ids':[h['id'] for h in survivors]}
   if a.get('extension_events')!=events[len(base['selection_labels']):] or a.get('all_events')!=events or a.get('checkpoints')!=checkpoints:errors.append(f'{i}:{name}:selector transcript')
   seen_rows=set()
   for e in events:
    row=tuple(map(float,e['row']))
    if row in held or row in forbidden:errors.append(f'{i}:{name}:query overlap')
    if row in seen_rows:errors.append(f'{i}:{name}:repeated query')
    seen_rows.add(row)
   by.setdefault(name,{str(c):{'panels':0,'exact_accept':0,'false_accept':0,'help':0,'labels':[]} for c in lock['caps']})
   for cap in lock['caps']:
    state=checkpoints[str(cap)];decision=state['decision'];exact=False
    if decision=='accept':
     h=next(x for x in cands if x['id']==state['survivor_ids'][0]);exact=ad.score(n,p['task'],h['term'])['exact']
    for bucket in (agg[str(cap)],by[name][str(cap)]):
     bucket['panels']+=1;bucket['exact_accept']+=int(decision=='accept' and exact);bucket['false_accept']+=int(decision=='accept' and not exact);bucket['help']+=int(decision!='accept');bucket['labels'].append(state['cumulative_labels'])
 for bundle in [agg,*by.values()]:
  for v in bundle.values():v['median_labels']=statistics.median(v.pop('labels')) if v['labels'] else None
 checks={'provenance_current_and_bound':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'twenty_panel_pairing':len(raw.get('workers',[]))==20,'selector_transcript_replayed':not any('transcript' in e for e in errors),'disjoint_oracle_queries':not any('overlap' in e for e in errors),'holdout_outcomes_recomputed':len(errors)==0}
 result={'schema':'ResynthesisSelectorBudgetV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'by_cap':agg,'by_arm_and_cap':by,'claim_boundary':'Additional active oracle labels on fixed candidate pools; no new synthesis, and no equivalence guarantee.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
