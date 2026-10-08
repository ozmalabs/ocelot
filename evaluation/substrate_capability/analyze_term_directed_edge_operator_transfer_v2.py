#!/usr/bin/env python3
"""Independent bitwise-disjoint replay of operator-transfer edge probes."""
import hashlib,json,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/term_directed_edge_operator_transfer_v2_lock_20261004.json';RAW=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v2_20261004.json';OUT=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v2_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fpkey(row):return tuple(struct.pack('>d',float(x)) for x in row)
def main():
 import term_directed_edge_operator_transfer_v2 as m
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());ps=m.panels();errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture lock/source binding')
 if m.source_map()!=lock.get('sources') or ps!=lock.get('panels'):errors.append('current source/panel drift')
 if sha(m.ABS_RAW)!=lock['abs_capture_sha256'] or sha(m.TRANSFER_RAW)!=lock['transfer_capture_sha256']:errors.append('upstream capture binding')
 if not json.loads(m.ABS_ANALYSIS.read_text()).get('passed') or not json.loads(m.TRANSFER_ANALYSIS.read_text()).get('passed'):errors.append('upstream analysis')
 rows=raw.get('workers',[]);n=_native.Substrate();details=[]
 if len(rows)!=3:errors.append('panel count')
 for p,w in zip(ps,rows):
  if (w.get('name'),w.get('task'))!=(p['name'],p['task']):errors.append(f"{p['name']}: identity")
  for h in p['terms']:
   for ex in p['training']:
    pred=classify(n.evaluate(h['term'],dict(zip(m.KEYS,ex['row']))))
    if pred is not bool(ex['label']):errors.append(f"{p['name']}: training fit")
  forbid={fpkey(x['row']) for x in p['training']}|{fpkey(x) for x in p['prior_pool']};held={fpkey(x) for x in p['holdout']}
  probe=m.probes(p['terms'],[x['row'] for x in p['training']]+p['prior_pool'],p['holdout'])
  if w.get('probe_slate')!=probe:errors.append(f"{p['name']}: proposal replay")
  for e in probe:
   k=fpkey([e[z] for z in m.KEYS])
   if k in forbid or k in held:errors.append(f"{p['name']}: bitwise probe overlap")
  calls=0
  def ev(term,env):
   nonlocal calls
   calls+=1;return classify(n.evaluate(term,env))
  survivors=p['terms'].copy();prior=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(m.KEYS,r)) for r in p['prior_pool']])
  if w.get('prior_partition')!=prior:errors.append(f"{p['name']}: prior partition")
  events=[];used=set()
  while len(survivors)>1 and len(events)<m.CAP:
   avail=[e for e in probe if fpkey([e[k] for k in m.KEYS]) not in used];choice=select_discriminating_input(ev,survivors,avail,[])
   if not choice.get('ok'):break
   q=choice['query'];row=[float(q[k]) for k in m.KEYS];label=bool(m.truth(p['task'],row));before=[h['id'] for h in survivors]
   survivors=[h for h in survivors if ev(h['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[h['id'] for h in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
  part=partition_hypotheses_by_behavior(ev,survivors,probe);decision='accept_behavior_class' if survivors and part['all_agree_on_probes'] else 'request_help'
  if w.get('events')!=events or w.get('survivor_ids')!=[h['id'] for h in survivors] or w.get('final_partition')!=part or w.get('decision')!=decision:errors.append(f"{p['name']}: policy replay")
  for e in events:
   k=fpkey(e['row'])
   if k in forbid or k in held:errors.append(f"{p['name']}: query overlap")
  scores=[]
  for h in p['terms']:
   mismatches=invalid=0
   for row in p['holdout']:
    pred=classify(n.evaluate(h['term'],dict(zip(m.KEYS,row))));label=bool(m.truth(p['task'],row))
    if pred is None:invalid+=1
    elif pred is not label:mismatches+=1
   scores.append({'id':h['id'],'n':len(p['holdout']),'mismatches':mismatches,'invalid':invalid})
  if w.get('holdout_scores')!=scores:errors.append(f"{p['name']}: holdout scoring")
  if w.get('policy_native_evaluations',0)<calls:errors.append(f"{p['name']}: cost accounting")
  accepted=decision=='accept_behavior_class';wrong=accepted and any(x['mismatches'] or x['invalid'] for x in scores if x['id'] in [h['id'] for h in survivors])
  details.append({'panel':p['name'],'prior_classes':prior['class_count'],'labels':len(events),'decision':decision,'survivor_ids':[h['id'] for h in survivors],'behavior_class_false_on_holdout':bool(wrong),'holdout_scores':scores,'policy_evaluations':w.get('policy_native_evaluations'),'policy_wall_ns':w.get('policy_wall_ns')})
 div=next((x for x in details if x['panel']=='division_signed_zero'),None);alias=next((x for x in details if x['panel']=='structured_literal_alias'),None)
 checks={'source_and_upstream_binding':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'three_panel_pairing':len(details)==3,'training_candidate_validity':not any('training fit' in e for e in errors),'bitwise_disjoint_proposals':not any('overlap' in e for e in errors),'probe_and_selector_replay':not any('proposal replay' in e or 'policy replay' in e or 'partition' in e for e in errors),'holdout_replay':not any('holdout scoring' in e for e in errors),'structured_alias_is_detected_as_finite_class_risk':bool(alias and alias['decision']=='accept_behavior_class' and alias['behavior_class_false_on_holdout']),'signed_zero_holdout_detects_div_failure':bool(div and any(c['id']=='quotient_eq' and c['mismatches']>0 for c in div['holdout_scores']) and any(e['row'][0]==0. and e['row'][2]==0. for e in next(w for w in rows if w['name']=='division_signed_zero')['events'])),'cost_accounting':not any('accounting' in e for e in errors)}
 res={'schema':'TermDirectedEdgeOperatorTransferV2Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cells':details,'claim_boundary':'Three authored numeric panels show task-blind edge-probe transfer and a deliberately exposed finite-class false-acceptance risk; not broad operator transfer or universal semantic equivalence.'}
 OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2,sort_keys=True));return 0 if res['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
