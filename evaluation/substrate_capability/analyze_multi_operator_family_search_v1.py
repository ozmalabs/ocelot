#!/usr/bin/env python3
"""Independent transcript and holdout audit for multi-operator family search."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/multi_operator_family_search_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/multi_operator_family_search_v1_20261004.json';OUT=ROOT/'evaluation/reports/multi_operator_family_search_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import multi_operator_family_search_v1 as m
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture/lock/source binding')
 if m.source_map()!=lock.get('sources') or m.panels()!=lock.get('panels'):errors.append('current source or panel drift')
 rows=raw.get('workers',[])
 if len(rows)!=20:errors.append(f'worker coverage {len(rows)}/20')
 n=_native.Substrate();summ={t:{'panels':0,'timeouts':0,'no_fit':0,'candidate_count':[],'exact_candidates':0,'panels_with_exact_candidate':0,'correct_resolutions':0,'false_singletons':0,'empty_final':0,'unresolved':0,'oracle_calls':[],'query_evaluations':[],'synthesis_wall_s':[],'synthesis_cpu_s':[],'explored':[]} for t in m.TASKS}
 for i,(w,p) in enumerate(zip(rows,lock['panels'])):
  if any(w.get(k)!=p[k] for k in ('task','worker','seed','training','selection_pool','selection_order')):errors.append(f'{i}:panel mismatch')
  by={h['id']:h for h in w.get('candidates',[])}
  if len(by)!=len(w.get('candidates',[])):errors.append(f'{i}:duplicate hypothesis ID')
  for h in by.values():
   for x in p['training']:
    try:v=m.classify(n.evaluate(h['term'],m.env(x['row'])))
    except Exception as e:errors.append(f'{i}:training evaluation exception {e}');continue
    if v is None or v!=bool(x['label']):errors.append(f'{i}:candidate violates initial label')
  scores={h['id']:m.score(n,p['task'],h['term']) for h in by.values()}
  if [{'id':h['id'],'score':scores[h['id']]} for h in by.values()]!=w.get('heldout_scores'):errors.append(f'{i}:heldout score replay')
  current=list(by.values());train=list(p['training']);used=[];evals=0;attempts=0
  for step in w.get('steps',[]):
   avail=[r for r in p['selection_order'] if r not in used and r not in [x['row'] for x in train]]
   evals+=len(current)*len(avail);attempts+=1
   ans=select_discriminating_input(lambda term,e:m.classify(n.evaluate(term,e)),current,[m.env(r) for r in avail],[{'inputs':m.env(x['row']),'expected':bool(x['label'])} for x in train])
   q=step['query']
   if not ans.get('ok') or [float(ans['query'][k]) for k in m.KEYS]!=q or step.get('entropy_bits')!=ans.get('entropy_bits'):errors.append(f'{i}:query selector replay')
   y=bool(m.truth(p['task'],q))
   if step.get('label') is not y:errors.append(f'{i}:oracle label mismatch')
   before=len(current);current=[h for h in current if m.classify(n.evaluate(h['term'],m.env(q))) is y]
   if step.get('before')!=before or step.get('after')!=len(current):errors.append(f'{i}:candidate transition mismatch')
   used.append(q);train.append({'row':q,'label':int(y)})
  if w.get('selector_abstain_reason'):
   avail=[r for r in p['selection_order'] if r not in used and r not in [x['row'] for x in train]]
   ans=select_discriminating_input(lambda term,e:m.classify(n.evaluate(term,e)),current,[m.env(r) for r in avail],[{'inputs':m.env(x['row']),'expected':bool(x['label'])} for x in train])
   if ans.get('ok') or ans.get('reason')!=w['selector_abstain_reason']:errors.append(f'{i}:terminal abstention replay')
   evals+=len(current)*len(avail);attempts+=1
  if w.get('survivors')!=[h['id'] for h in current] or w.get('selector_candidate_input_evaluations')!=evals or w.get('selector_attempts')!=attempts or w.get('oracle_calls')!=len(w.get('steps',[])):errors.append(f'{i}:selection work ledger')
  exact_ids={hid for hid,s in scores.items() if s['exact']};final=[hid for hid in w.get('survivors',[]) if hid in by]
  resolved=bool(final) and all(hid in exact_ids for hid in final)
  t=p['task'];s=summ[t];s['panels']+=1;s['timeouts']+=int(w.get('halt_reason')=='timeout');s['no_fit']+=int(not by);s['candidate_count'].append(len(by));s['exact_candidates']+=len(exact_ids);s['panels_with_exact_candidate']+=int(bool(exact_ids));s['correct_resolutions']+=int(resolved);s['false_singletons']+=int(len(final)==1 and not resolved);s['empty_final']+=int(not final);s['unresolved']+=int(bool(final) and not resolved);s['oracle_calls'].append(len(w.get('steps',[])));s['query_evaluations'].append(evals);s['synthesis_wall_s'].append(w.get('synthesis_wall_ns',0)/1e9);s['synthesis_cpu_s'].append(w.get('synthesis_cpu_ns',0)/1e9);s['explored'].append(w.get('explored',0))
 for s in summ.values():
  for k in ('candidate_count','oracle_calls','query_evaluations','synthesis_wall_s','synthesis_cpu_s','explored'):s['median_'+k]=statistics.median(s.pop(k))
 checks={'locked_20_panel_matrix':len(rows)==20,'sources_panels_and_capture_bound':not any('binding' in e or 'drift' in e or 'panel mismatch' in e for e in errors),'all_initial_candidate_fits_verified':not any('candidate violates' in e or 'training evaluation' in e for e in errors),'query_and_work_transcripts_replayed':not any('query ' in e or 'transition' in e or 'abstention' in e or 'work ledger' in e or 'oracle' in e for e in errors),'all_holdouts_rescored':not any('heldout' in e for e in errors)}
 result={'schema':'MultiOperatorFamilySearchV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'by_task':summ,'claim_boundary':'Four authored numeric relations within one experimenter-specified finite grammar; not open-ended invention or natural-task capability.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
