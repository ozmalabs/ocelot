#!/usr/bin/env python3
"""Independent replay of Term-directed floating-point probe study."""
import hashlib,json,math,sys,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/term_directed_float_edge_probes_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/term_directed_float_edge_probes_v1_20261004.json';OUT=ROOT/'evaluation/reports/term_directed_float_edge_probes_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import term_directed_float_edge_probes_v1 as m
 import residual_triggered_resynthesis_v1_2 as s
 import resynthesis_selector_budget_v1_2 as sel
 import adaptive_factored_operator_search_v1 as ad
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());panels,search,_=m.input_data();errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture/lock/source binding')
 if m.source_map()!=lock.get('sources'):errors.append('current source drift')
 if sha(m.SRAW)!=lock['resynthesis_capture_sha256'] or sha(m.SELRAW)!=lock['selector_capture_sha256']:errors.append('upstream capture drift')
 if not json.loads(m.SOUT.read_text()).get('passed') or not json.loads(m.SELOUT.read_text()).get('passed'):errors.append('upstream analysis failure')
 p=panels[lock['panel']];sw=search[lock['panel']];result=raw.get('result',{});native=_native.Substrate();wide=m.stress_holdout();details=[]
 if result.get('task')!=lock['task'] or result.get('worker')!=lock['worker']:errors.append('panel identity')
 for row in result.get('arms',[]):
  name=row['arm'];base=sw[name];terms=[h for h in base['candidate_terms'] if h['id'] in base['final_survivor_ids']]
  if row.get('candidate_ids')!=[h['id'] for h in terms] or len(terms)!=3:errors.append(f'{name}: candidate binding')
  forbidden=[x['row'] for x in p['training']]+p['selection_order'];probes=m.proposal_slate(terms,forbidden)
  if row.get('probe_slate')!=probes or row.get('probe_count')!=len(probes):errors.append(f'{name}: proposal replay/disjointness')
  calls=0
  def ev(term,env):
   nonlocal calls
   calls+=1;return ad.classify(native.evaluate(term,env))
  survivors=terms.copy()
  for e in base['selection_labels']:
   env=dict(zip(m.KEYS,e['row']));survivors=[h for h in survivors if ev(h['term'],env) is bool(e['label'])]
  part0=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(m.KEYS,x)) for x in p['selection_order']])
  if row.get('prior_partition')!=part0:errors.append(f'{name}: prior partition')
  events=[];used={tuple(e['row']) for e in base['selection_labels']}
  while len(survivors)>1 and len(events)<m.LABEL_BUDGET:
   avail=[e for e in probes if tuple(float(e[k]) for k in m.KEYS) not in used]
   choice=select_discriminating_input(ev,survivors,avail,[])
   if not choice.get('ok'):break
   q=choice['query'];rv=[float(q[k]) for k in m.KEYS];label=bool(ad.truth(lock['task'],rv));before=[h['id'] for h in survivors]
   survivors=[h for h in survivors if ev(h['term'],q) is label];used.add(tuple(rv));events.append({'row':rv,'label':label,'before':before,'after':[h['id'] for h in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
  part=partition_hypotheses_by_behavior(ev,survivors,probes);decision='accept_behavior_class' if survivors and part.get('all_agree_on_probes') else 'request_help'
  if row.get('new_events')!=events or row.get('survivor_ids')!=[h['id'] for h in survivors] or row.get('final_partition')!=part or row.get('decision')!=decision:errors.append(f'{name}: selector/class transcript')
  forbidden_set={tuple(map(float,x['row'])) for x in p['training']}|{tuple(map(float,x)) for x in p['selection_order']};held={tuple(x) for x in itertools.product(m.HELD,repeat=4)}
  for e in events:
   rr=tuple(e['row'])
   if rr in forbidden_set or rr in held:errors.append(f'{name}: probe overlap')
  candidate_scores=[]
  for h in terms:
   finite=ad.score(native,lock['task'],h['term'])
   mismatches=invalid=0
   for vals in wide:
    pred=ad.classify(native.evaluate(h['term'],dict(zip(m.KEYS,vals))));truth=bool(ad.truth(lock['task'],vals))
    if pred is None:invalid+=1
    elif pred is not truth:mismatches+=1
   candidate_scores.append({'id':h['id'],'finite_exact':finite['exact'],'finite_score':finite,'wide_n':len(wide),'wide_mismatches':mismatches,'wide_invalid':invalid})
  if row.get('wide_scores')!=candidate_scores:errors.append(f'{name}: wide holdout replay')
  if row.get('policy_native_evaluations',0)<calls:errors.append(f'{name}: policy evaluation accounting')
  if row.get('holdout_native_evaluations')!=len(terms)*len(wide):errors.append(f'{name}: holdout evaluation accounting')
  details.append({'arm':name,'start_classes':part0['class_count'],'end_classes':part['class_count'],'query_labels':len(events),'query_rows':[e['row'] for e in events],'candidate_ids':[h['id'] for h in survivors],'decision':decision,'candidate_scores':candidate_scores,'policy_native_evaluations':row.get('policy_native_evaluations'),'policy_wall_ns':row.get('policy_wall_ns')})
 checks={'source_and_upstream_binding':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'same_three_candidates_both_arms':len(result.get('arms',[]))==2 and all(len(x['candidate_ids'])==3 for x in result.get('arms',[])),'task_blind_probe_slate_replay':not any('proposal replay' in e for e in errors),'prior_pool_equivalence_replayed':not any('prior partition' in e for e in errors),'oracle_and_behavior_class_replayed':not any('transcript' in e or 'overlap' in e for e in errors),'independent_wide_scores_replayed':not any('holdout' in e for e in errors),'cost_accounting_present':not any('accounting' in e for e in errors)}
 res={'schema':'TermDirectedFloatEdgeProbesV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cells':details,'claim_boundary':'One ambiguous numeric candidate class; finite task-blind IEEE edge probes identify a finite observational behavior class and are evaluated on finite stress holdouts, not a proof over all float inputs.'}
 OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2,sort_keys=True));return 0 if res['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
