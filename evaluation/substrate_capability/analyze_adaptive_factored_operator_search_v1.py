#!/usr/bin/env python3
"""Independent audit of staged search, oracle events, acceptance, and paired costs."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_20261004.json';OUT=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import adaptive_factored_operator_search_v1 as m
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());fixed=json.loads(m.FACTRAW.read_text());fixed_a=json.loads(m.FACTOUT.read_text());errs=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errs.append('capture source/lock binding')
 if m.source_map()!=lock.get('sources') or m.panels()!=lock.get('panels'):errs.append('current source or panel drift')
 if fixed.get('lock_sha256')!=sha(m.FACTLOCK) or not fixed_a.get('passed'):errs.append('fixed comparison provenance')
 rows=raw.get('workers',[]);fixed_rows=fixed.get('workers',[])
 if len(rows)!=20 or len(fixed_rows)!=20:errs.append('paired worker count')
 n=_native.Substrate();by_task={t:{'panels':0,'accepted_correct':0,'false_accepts':0,'request_help':0,'median_branches':0,'median_active_labels':0,'median_audit_labels':0,'median_total_labels':0,'median_search_wall_s':0,'median_search_cpu_s':0,'median_explored':0,'branch_timeouts':0,'fixed_correct_resolutions':0,'fixed_median_search_wall_s':0,'adaptive_minus_fixed_wall_s':[]} for t in m.TASKS};stash={t:{k:[] for k in ('branches','active','audit','labels','wall','cpu','explored','fixedwall','deltawall')} for t in m.TASKS}
 for i,(w,p,fw) in enumerate(zip(rows,lock['panels'],fixed_rows)):
  t=p['task']
  if any(w.get(k)!=p[k] for k in ('task','worker','seed','training','selection_pool','selection_order')):errs.append(f'{i}:paired panel mismatch')
  if any(w.get(k)!=fw.get(k) for k in ('task','worker','training','selection_pool','selection_order')):errs.append(f'{i}:fixed panel mismatch')
  shift=int(p['seed'])%len(m.OPS);expected_order=list(m.OPS[shift:]+m.OPS[:shift])
  if w.get('branch_order')!=expected_order:errs.append(f'{i}:branch order')
  active_pool=p['selection_order'][:24];audit_pool=p['selection_order'][24:];train=list(p['training']);used_active=[];used_audit=[];survivors={};all_terms={};active=audits=0;audit_candidate=None;audit_streak=0;accept=None;branch_wall=branch_cpu=explored=timeouts=0
  for bi,b in enumerate(w.get('branches',[])):
   op=expected_order[bi]
   if b.get('operator')!=op or b.get('training_before')!=train:errs.append(f'{i}:{op} staged inputs')
   branch_wall+=b.get('wall_ns',0);branch_cpu+=b.get('cpu_ns',0);explored+=b.get('explored',0);timeouts+=int(b.get('halt_reason')=='timeout')
   ids=b.get('term_ids',[])
   for hid in ids:
    if hid not in all_terms:
     h=next((x for x in w.get('final_terms',[]) if x['id']==hid),None)
     if h is None:errs.append(f'{i}:{op} missing candidate descriptor');continue
     all_terms[hid]=h;survivors[hid]=h
   if len(set(ids))!=len(ids):errs.append(f'{i}:{op} duplicate branch term id')
   for hid in ids:
    h=all_terms.get(hid)
    if h and op not in h.get('families',[]):errs.append(f'{i}:{op} term provenance')
    if h:
     for ex in train:
      try:pred=m.classify(n.evaluate(h['term'],m.env(ex['row'])))
      except Exception as e:errs.append(f'{i}:{op} candidate evaluation {e}');continue
      if pred is None or pred!=bool(ex['label']):errs.append(f'{i}:{op} candidate violates branch training')
   for ev in b.get('events',[]):
    kind=ev['kind']
    if kind=='active':
     if active>=m.ACTIVE_BUDGET:errs.append(f'{i}:active label budget')
     avail=[r for r in active_pool if r not in used_active and r not in [x['row'] for x in train]]
     candidates=list(survivors.values());ans=select_discriminating_input(lambda term,e:m.classify(n.evaluate(term,e)),candidates,[m.env(r) for r in avail],[{'inputs':m.env(x['row']),'expected':bool(x['label'])} for x in train])
     q=ev['query']
     if not ans.get('ok') or [float(ans['query'][k]) for k in m.KEYS]!=q or ans.get('entropy_bits')!=ev.get('entropy_bits'):errs.append(f'{i}:active selector replay')
     label=bool(m.truth(t,q))
     if ev.get('label') is not label or ev.get('before')!=[h['id'] for h in candidates]:errs.append(f'{i}:active label/history')
     survivors={hid:h for hid,h in survivors.items() if m.classify(n.evaluate(h['term'],m.env(q))) is label}
     if ev.get('after')!=list(survivors):errs.append(f'{i}:active survivor update')
     train.append({'row':q,'label':int(label)});used_active.append(q);active+=1;audit_candidate=None;audit_streak=0
    elif kind=='audit':
     candidates=list(survivors.values());avail=[r for r in audit_pool if r not in used_audit and r not in [x['row'] for x in train]]
     if len(candidates)!=1 or not avail or list(map(float,avail[0]))!=ev.get('query') or ev.get('candidate_id')!=candidates[0]['id']:errs.append(f'{i}:audit input/candidate')
     if candidates:
      hid=candidates[0]['id'];pred=m.classify(n.evaluate(candidates[0]['term'],m.env(ev['query'])));label=bool(m.truth(t,ev['query']))
      if pred!=ev.get('prediction') or label is not ev.get('label'):errs.append(f'{i}:audit prediction/oracle')
      if audit_candidate!=hid:audit_candidate=hid;audit_streak=0
      if pred is label:audit_streak+=1
      else:survivors={};audit_candidate=None;audit_streak=0
      if ev.get('after')!=list(survivors) or ev.get('audit_streak')!=audit_streak:errs.append(f'{i}:audit survivor/streak')
      if pred is label and audit_streak>=2:accept=hid
      train.append({'row':ev['query'],'label':int(label)});used_audit.append(ev['query']);audits+=1
   if b.get('decision')=='accept' and accept is None:errs.append(f'{i}:premature accept')
   if b.get('decision')=='accept' and bi!=len(w['branches'])-1:errs.append(f'{i}:search continued after accept')
   if active>=m.ACTIVE_BUDGET and accept is None and bi!=len(w['branches'])-1:errs.append(f'{i}:search continued after active budget')
  if accept!=w.get('accepted_id') or w.get('decision')!=('accept' if accept else 'request_help'):errs.append(f'{i}:terminal policy decision')
  if (active,audits)!=(w.get('active_calls'),w.get('audit_calls')) or active>m.ACTIVE_BUDGET or audits>m.AUDIT_BUDGET:errs.append(f'{i}:label accounting')
  if w.get('events')!=[{'branch':b['operator'],**ev} for b in w.get('branches',[]) for ev in b.get('events',[])]:errs.append(f'{i}:event journal')
  scores={x['id']:x['score'] for x in w.get('heldout_scores',[])}
  expected_scores={h['id']:m.score(n,t,h['term']) for h in w.get('final_terms',[])}
  if scores!=expected_scores:errs.append(f'{i}:holdout replay')
  accepted_correct=bool(accept and scores.get(accept,{}).get('exact'));false=bool(accept and not accepted_correct)
  # Fixed v1 was not audited; its endpoint class is scored here independently.
  fs={x['id']:x['score'] for x in fw.get('heldout_scores',[])};fids=fw.get('survivors',[]);fixed_ok=bool(fids) and all(fs.get(x,{}).get('exact') for x in fids)
  task=w['task'];z=stash[task];z['branches'].append(len(w['branches']));z['active'].append(active);z['audit'].append(audits);z['labels'].append(active+audits);z['wall'].append(branch_wall/1e9);z['cpu'].append(branch_cpu/1e9);z['explored'].append(explored);z['fixedwall'].append(sum(x['wall_ns'] for x in fw['branches'].values())/1e9);z['deltawall'].append((branch_wall-sum(x['wall_ns'] for x in fw['branches'].values()))/1e9)
  a=by_task[task];a['panels']+=1;a['accepted_correct']+=int(accepted_correct);a['false_accepts']+=int(false);a['request_help']+=int(w['decision']=='request_help');a['branch_timeouts']+=timeouts;a['fixed_correct_resolutions']+=int(fixed_ok)
 for t,a in by_task.items():
  z=stash[t]
  for name,key in (('median_branches','branches'),('median_active_labels','active'),('median_audit_labels','audit'),('median_total_labels','labels'),('median_search_wall_s','wall'),('median_search_cpu_s','cpu'),('median_explored','explored'),('fixed_median_search_wall_s','fixedwall')):a[name]=statistics.median(z[key])
  a['adaptive_minus_fixed_wall_s']=z['deltawall']
 checks={'locked_twenty_paired_panels':len(rows)==20,'current_sources_and_controls_bound':not any('binding' in e or 'drift' in e or 'panel mismatch' in e for e in errs),'staged_candidate_fit_and_provenance':not any('candidate' in e and ('missing' in e or 'provenance' in e or 'violates' in e or 'evaluation' in e) for e in errs),'active_and_audit_transcripts_replayed':not any('selector' in e or 'label/history' in e or 'survivor' in e or 'audit ' in e or 'journal' in e for e in errs),'decision_and_holdout_audited':not any('terminal' in e or 'premature' in e or 'continued' in e or 'holdout' in e for e in errs),'label_budgets_respected':not any('budget' in e or 'accounting' in e for e in errs)}
 result={'schema':'AdaptiveFactoredOperatorSearchV1Analysis','passed':all(checks.values()) and not errs,'checks':checks,'errors':errs,'by_task':by_task,'claim_boundary':'Residual-conditioned schedule over four authored operator branches and four numeric task families only; no open-ended invention or natural-task generality claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
