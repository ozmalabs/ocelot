#!/usr/bin/env python3
"""Independent source, query-transcript, and holdout replay for operator blinding."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/operator_hint_blinding_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/operator_hint_blinding_v1_20261004.json';OUT=ROOT/'evaluation/reports/operator_hint_blinding_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import operator_hint_blinding_v1 as m
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());errs=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errs.append('lock/source binding')
 if m.source_map()!=lock.get('sources') or m.panels()!=lock.get('panels'):errs.append('current source/panel drift')
 if len(raw.get('workers',[]))!=10:errs.append('worker count')
 n=_native.Substrate();summary={t:{a:{'panels':0,'exact_grammar_coverage':0,'correct_resolutions':0,'false_singletons':0,'empty_sets':0,'unresolved':0,'oracle_calls':[],'candidate_evaluations':[],'synthesis_wall_ns':[],'synthesis_cpu_ns':[]} for a in ('both','Plus','Times')} for t in m.TASKS}
 for i,(w,p) in enumerate(zip(raw.get('workers',[]),lock['panels'])):
  if (w.get('task'),w.get('worker'),w.get('training'),w.get('selection_pool'),w.get('selection_order'))!=(p['task'],p['worker'],p['training'],p['selection_pool'],p['selection_order']):errs.append(f'{i}:panel binding')
  terms=w['candidates'];term_by={h['id']:h for h in terms};
  if len(term_by)!=len(terms):errs.append(f'{i}:candidate IDs')
  for h in terms:
   for x in p['training']:
    try:v=n.evaluate(h['term'],m.env(x['row']))
    except Exception as e:errs.append(f'{i}:term evaluation {e}');continue
    if m.classify(v) is None or m.classify(v)!=bool(x['label']):errs.append(f'{i}:candidate fit')
  score={x['id']:m.fit_score(n,p['task'],x['term']) for x in terms}
  if score!={x['id']:x['holdout'] for x in w['heldout_scores']}:errs.append(f'{i}:heldout score')
  for op in m.OPS:
   ids=w['candidate_ids_by_grammar'][op]
   if any(op not in term_by[x]['families'] for x in ids):errs.append(f'{i}:{op} provenance')
   exact=any(score[x]['exact'] for x in ids)
   if exact!=any(q['id'] in ids and q['holdout']['exact'] for q in w['heldout_scores']):errs.append(f'{i}:{op} exact coverage ledger')
  for arm in w['arms']:
   mode=arm['filter']; candidates=[h for h in terms if mode=='both' or mode in h['families']]
   train=list(p['training']);used=[];evals=0
   if arm['filter'] not in ('both','Plus','Times'):errs.append(f'{i}:arm label')
   for step in arm['steps']:
    avail=[r for r in p['selection_order'] if r not in used and r not in [x['row'] for x in train]]
    evals+=len(candidates)*len(avail)
    ans=select_discriminating_input(lambda term,e:m.classify(n.evaluate(term,e)),candidates,[m.env(r) for r in avail],[{'inputs':m.env(x['row']),'expected':bool(x['label'])} for x in train])
    q=step['query']
    if not ans.get('ok') or [float(ans['query'][k]) for k in m.KEYS]!=q or step.get('entropy_bits')!=ans.get('entropy_bits'):errs.append(f'{i}:{mode} selector replay')
    label=bool(m.truth(p['task'],q))
    if step['label'] is not label:errs.append(f'{i}:{mode} oracle label')
    before=len(candidates);candidates=[h for h in candidates if m.classify(n.evaluate(h['term'],m.env(q))) is label]
    if step['before']!=before or step['after']!=len(candidates):errs.append(f'{i}:{mode} survivor transition')
    used.append(q);train.append({'row':q,'label':int(label)})
   attempts=len(arm['steps'])
   if arm.get('selector_abstain_reason'):
    avail=[r for r in p['selection_order'] if r not in used and r not in [x['row'] for x in train]]
    ans=select_discriminating_input(lambda term,e:m.classify(n.evaluate(term,e)),candidates,[m.env(r) for r in avail],[{'inputs':m.env(x['row']),'expected':bool(x['label'])} for x in train])
    if ans.get('ok') or ans.get('reason')!=arm['selector_abstain_reason']:errs.append(f'{i}:{mode} terminal selector replay')
    evals+=len(candidates)*len(avail);attempts+=1
   if arm['survivors']!=[h['id'] for h in candidates] or arm['oracle_calls']!=len(arm['steps']) or arm['selector_candidate_input_evaluations']!=evals or arm['selector_attempts']!=attempts:errs.append(f'{i}:{mode} final accounting')
   task=w['task'];s=summary[task][mode];s['panels']+=1
   exact_available=any(score[h['id']]['exact'] for h in terms if mode=='both' or mode in h['families'])
   s['exact_grammar_coverage']+=int(exact_available)
   resolved=bool(candidates) and all(score[h['id']]['exact'] for h in candidates)
   s['correct_resolutions']+=int(resolved)
   s['false_singletons']+=int(arm['stop']=='singleton' and not resolved)
   s['empty_sets']+=int(not candidates);s['unresolved']+=int(bool(candidates) and not resolved)
   s['oracle_calls'].append(len(arm['steps']));s['candidate_evaluations'].append(evals)
   relevant_ops=m.OPS if mode=='both' else (mode,)
   s['synthesis_wall_ns'].append(sum(w['synthesis'][x]['wall_ns'] for x in relevant_ops))
   s['synthesis_cpu_ns'].append(sum(w['synthesis'][x]['cpu_ns'] for x in relevant_ops))
 for t in m.TASKS:
  for a,s in summary[t].items():
   for key in ('oracle_calls','candidate_evaluations','synthesis_wall_ns','synthesis_cpu_ns'):
    s['median_'+key]=statistics.median(s.pop(key))
 checks={'source_and_lock_binding':not any('binding' in e or 'drift' in e for e in errs),'all_policy_transcripts_replay':not any('selector' in e or 'oracle' in e or 'transition' in e or 'accounting' in e for e in errs),'all_candidates_fit_revealed_examples':not any('candidate fit' in e or 'term evaluation' in e for e in errs),'all_candidates_rescored':not any('heldout' in e for e in errs),'complete_ten_panel_three_arm_matrix':len(raw.get('workers',[]))==10 and sum(x['panels'] for t in summary.values() for x in t.values())==30}
 result={'schema':'OperatorHintBlindingV1Analysis','passed':all(checks.values()) and not errs,'checks':checks,'errors':errs,'summary':summary,'capture_sha256':sha(RAW),'lock_sha256':sha(LOCK),'claim_boundary':'Selection among Plus and Times expansions authored by the experimenter; no open-ended primitive invention or natural-task generalization claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
