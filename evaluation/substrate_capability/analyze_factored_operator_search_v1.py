#!/usr/bin/env python3
"""Independent audit and paired comparison for factored operator search."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/factored_operator_search_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/factored_operator_search_v1_20261004.json';OUT=ROOT/'evaluation/reports/factored_operator_search_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import factored_operator_search_v1 as m
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());errors=[];up=json.loads(m.UPRAW.read_text());upan=json.loads(m.UPAN.read_text())
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture/lock/source binding')
 if m.source_map()!=lock.get('sources') or m.panels()!=lock.get('panels'):errors.append('current source/panel drift')
 if up.get('lock_sha256')!=sha(m.UPLOCK) or not upan.get('passed'):errors.append('paired baseline provenance')
 rows=raw.get('workers',[])
 if len(rows)!=20 or len(up.get('workers',[]))!=20:errors.append('paired worker count')
 n=_native.Substrate();summary={t:{'panels':0,'exact_union_candidates':0,'branch_exact_coverage':{o:0 for o in m.OPS},'branch_timeouts':{o:0 for o in m.OPS},'branch_wall_s':{o:[] for o in m.OPS},'branch_cpu_s':{o:[] for o in m.OPS},'union_candidate_count':[],'correct_resolutions':0,'false_singletons':0,'empty_final':0,'unresolved':0,'oracle_calls':[],'query_evaluations':[],'total_search_wall_s':[],'total_search_cpu_s':[]} for t in m.TASKS}
 for i,(w,p,b) in enumerate(zip(rows,lock['panels'],up.get('workers',[]))):
  if any(w.get(k)!=p[k] for k in ('task','worker','training','selection_pool','selection_order')):errors.append(f'{i}:panel mismatch')
  if any(w.get(k)!=b.get(k) for k in ('task','worker','training','selection_pool','selection_order')):errors.append(f'{i}:paired panel mismatch')
  by={h['id']:h for h in w.get('candidates',[])}
  if len(by)!=len(w.get('candidates',[])):errors.append(f'{i}:duplicate candidate id')
  for h in by.values():
   canon=json.dumps(h['term'],sort_keys=True,separators=(',',':'));want='term_'+hashlib.sha256(canon.encode()).hexdigest()[:16]
   if h['id']!=want or not h['families'] or any(o not in m.OPS for o in h['families']):errors.append(f'{i}:candidate identity/provenance')
   for x in p['training']:
    try:v=m.classify(n.evaluate(h['term'],m.env(x['row'])))
    except Exception as e:errors.append(f'{i}:candidate evaluation {e}');continue
    if v is None or v!=bool(x['label']):errors.append(f'{i}:candidate does not fit initial labels')
  scores={h['id']:m.score(n,p['task'],h['term']) for h in by.values()}
  if [{'id':h['id'],'score':scores[h['id']]} for h in by.values()]!=w.get('heldout_scores'):errors.append(f'{i}:holdout rescore')
  for op,branch in w.get('branches',{}).items():
   if op not in m.OPS:errors.append(f'{i}:unknown branch')
   ids=branch['terms']
   if any(x not in by or op not in by[x]['families'] for x in ids):errors.append(f'{i}:{op} branch provenance')
   sm=summary[p['task']];sm['branch_timeouts'][op]+=int(branch['halt_reason']=='timeout');sm['branch_wall_s'][op].append(branch['wall_ns']/1e9);sm['branch_cpu_s'][op].append(branch['cpu_ns']/1e9)
   sm['branch_exact_coverage'][op]+=int(any(scores[x]['exact'] for x in ids))
  if set(w.get('branches',{}))!=set(m.OPS):errors.append(f'{i}:incomplete branch matrix')
  current=list(by.values());train=list(p['training']);used=[];evals=0;attempts=0
  for step in w.get('steps',[]):
   avail=[r for r in p['selection_order'] if r not in used and r not in [x['row'] for x in train]];evals+=len(current)*len(avail);attempts+=1
   ans=select_discriminating_input(lambda term,e:m.classify(n.evaluate(term,e)),current,[m.env(r) for r in avail],[{'inputs':m.env(x['row']),'expected':bool(x['label'])} for x in train]);q=step['query']
   if not ans.get('ok') or [float(ans['query'][k]) for k in m.KEYS]!=q or ans.get('entropy_bits')!=step.get('entropy_bits'):errors.append(f'{i}:query replay')
   y=bool(m.truth(p['task'],q))
   if step.get('label') is not y:errors.append(f'{i}:oracle label')
   before=len(current);current=[h for h in current if m.classify(n.evaluate(h['term'],m.env(q))) is y]
   if step.get('before')!=before or step.get('after')!=len(current):errors.append(f'{i}:survivor transition')
   used.append(q);train.append({'row':q,'label':int(y)})
  if w.get('selector_abstain_reason'):
   avail=[r for r in p['selection_order'] if r not in used and r not in [x['row'] for x in train]];ans=select_discriminating_input(lambda term,e:m.classify(n.evaluate(term,e)),current,[m.env(r) for r in avail],[{'inputs':m.env(x['row']),'expected':bool(x['label'])} for x in train])
   if ans.get('ok') or ans.get('reason')!=w['selector_abstain_reason']:errors.append(f'{i}:terminal selector replay')
   evals+=len(current)*len(avail);attempts+=1
  if w.get('survivors')!=[h['id'] for h in current] or w.get('selector_candidate_input_evaluations')!=evals or w.get('selector_attempts')!=attempts or w.get('oracle_calls')!=len(w.get('steps',[])):errors.append(f'{i}:query work accounting')
  exactids={hid for hid,s in scores.items() if s['exact']};final=w.get('survivors',[]);resolved=bool(final) and all(x in exactids for x in final);sm=summary[p['task']];sm['panels']+=1;sm['exact_union_candidates']+=int(bool(exactids));sm['union_candidate_count'].append(len(by));sm['correct_resolutions']+=int(resolved);sm['false_singletons']+=int(len(final)==1 and not resolved);sm['empty_final']+=int(not final);sm['unresolved']+=int(bool(final) and not resolved);sm['oracle_calls'].append(len(w['steps']));sm['query_evaluations'].append(evals);sm['total_search_wall_s'].append(sum(x['wall_ns'] for x in w['branches'].values())/1e9);sm['total_search_cpu_s'].append(sum(x['cpu_ns'] for x in w['branches'].values())/1e9)
 for task,sm in summary.items():
  for op in m.OPS:
   for metric in ('branch_wall_s','branch_cpu_s'):sm[metric][op]=statistics.median(sm[metric][op])
  for metric in ('union_candidate_count','oracle_calls','query_evaluations','total_search_wall_s','total_search_cpu_s'):sm['median_'+metric]=statistics.median(sm.pop(metric))
  baseline=[x for x in up['workers'] if x['task']==task];sm['shared_grammar_baseline']={'panels':len(baseline),'timeouts':sum(x['halt_reason']=='timeout' for x in baseline),'panels_with_exact_candidate':sum(any(y['score']['exact'] for y in x['heldout_scores']) for x in baseline),'median_search_wall_s':statistics.median(x['synthesis_wall_ns']/1e9 for x in baseline)}
 checks={'locked_paired_twenty_panels':len(rows)==20,'provenance_and_source_binding':not any('binding' in e or 'drift' in e or 'provenance' in e or 'panel mismatch' in e for e in errors),'all_branch_searches_reported':not any('branch matrix' in e for e in errors),'all_candidate_and_holdout_checks':not any('candidate ' in e or 'candidate does' in e or 'holdout' in e for e in errors),'query_and_cost_replay':not any('query' in e or 'oracle label' in e or 'survivor' in e for e in errors)}
 result={'schema':'FactoredOperatorSearchV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'by_task':summary,'claim_boundary':'Factorization of four authored numeric operator branches only; no open-ended primitive discovery or natural task scaling claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
