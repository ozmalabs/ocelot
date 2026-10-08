#!/usr/bin/env python3
"""Independent replay and scoring for IEEE edge-probe operator transfer."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/term_directed_edge_operator_transfer_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v1_20261004.json';OUT=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import term_directed_edge_operator_transfer_v1 as m
 import term_directed_float_edge_probes_v1_2 as absup
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());ps=m.panels();errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture lock/source binding')
 if m.source_map()!=lock.get('sources') or ps!=lock.get('panels'):errors.append('current source/panel drift')
 if sha(m.ABS_RAW)!=lock.get('absolute_capture_sha256') or not json.loads(m.ABS_ANALYSIS.read_text()).get('passed'):errors.append('upstream evidence binding')
 if len(raw.get('workers',[]))!=2:errors.append('panel count')
 native=_native.Substrate();details=[]
 for p,w in zip(ps,raw.get('workers',[])):
  if w.get('name')!=p['name'] or w.get('task')!=p['task']:errors.append(f"{p['name']}: panel identity")
  # Each candidate must agree with all acquisition/training labels.
  for h in p['terms']:
   for ex in p['training']:
    pred=classify(native.evaluate(h['term'],dict(zip(m.KEYS,ex['row']))))
    if pred is not bool(ex['label']):errors.append(f"{p['name']}: candidate fails training")
  forbidden={tuple(map(float,x['row'])) for x in p['training']}|{tuple(map(float,x)) for x in p['prior_pool']};held={tuple(map(float,x)) for x in p['holdout']}
  proposals=m.probes_for(p['terms'],[x['row'] for x in p['training']]+p['prior_pool'],p['holdout'])
  if w.get('probe_slate')!=proposals:errors.append(f"{p['name']}: probe replay")
  calls=0
  def ev(term,e):
   nonlocal calls
   calls+=1;return classify(native.evaluate(term,e))
  survivors=list(p['terms']);prior=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(m.KEYS,r)) for r in p['prior_pool']])
  if w.get('prior_partition')!=prior:errors.append(f"{p['name']}: prior partition replay")
  events=[];used=set()
  while len(survivors)>1 and len(events)<m.CAP:
   avail=[e for e in proposals if tuple(float(e[k]) for k in m.KEYS) not in used]
   choice=select_discriminating_input(ev,survivors,avail,[])
   if not choice.get('ok'):break
   q=choice['query'];row=[float(q[k]) for k in m.KEYS];label=bool(m.truth(p['task'],row));before=[h['id'] for h in survivors]
   survivors=[h for h in survivors if ev(h['term'],q) is label];used.add(tuple(row));events.append({'row':row,'label':label,'before':before,'after':[h['id'] for h in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
  final=partition_hypotheses_by_behavior(ev,survivors,proposals);decision='accept_behavior_class' if survivors and final['all_agree_on_probes'] else 'request_help'
  if w.get('events')!=events or w.get('survivor_ids')!=[h['id'] for h in survivors] or w.get('final_partition')!=final or w.get('decision')!=decision:errors.append(f"{p['name']}: selector/class transcript")
  for e in events:
   row=tuple(map(float,e['row']))
   if row in forbidden or row in held:errors.append(f"{p['name']}: probe overlap")
  wide=[]
  for h in p['terms']:
   mismatch=invalid=0
   for row in p['holdout']:
    pred=classify(native.evaluate(h['term'],dict(zip(m.KEYS,row))));label=bool(m.truth(p['task'],row))
    if pred is None:invalid+=1
    elif pred is not label:mismatch+=1
   wide.append({'id':h['id'],'holdout_n':len(p['holdout']),'mismatches':mismatch,'invalid':invalid})
  if w.get('wide_scores')!=wide:errors.append(f"{p['name']}: wide scoring mismatch")
  if w.get('policy_native_evaluations',0)<calls:errors.append(f"{p['name']}: evaluation accounting")
  details.append({'panel':p['name'],'operator_family':'Abs/Times' if p['task']=='absolute' else 'Div/Eq','initial_candidates':len(p['terms']),'prior_behavior_classes':prior['class_count'],'labels':len(events),'decision':decision,'survivors':[h['id'] for h in survivors],'wide_scores':wide,'policy_evaluations':w.get('policy_native_evaluations'),'policy_wall_ns':w.get('policy_wall_ns')})
 checks={'source_and_upstream_binding':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'two_operator_family_panels':len(details)==2,'candidates_fit_training':not any('fails training' in e for e in errors),'task_blind_probe_replay_and_disjointness':not any('probe replay' in e or 'probe overlap' in e for e in errors),'selector_and_class_replay':not any('partition replay' in e or 'transcript' in e for e in errors),'wide_holdout_independent_replay':not any('wide scoring' in e for e in errors),'cost_accounting':not any('accounting' in e for e in errors)}
 result={'schema':'TermDirectedEdgeOperatorTransferV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cells':details,'claim_boundary':'Two authored numeric equality tasks using different Term primitives; finite edge probes and finite holdouts only, no general operator transfer or universal semantic equivalence claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
