#!/usr/bin/env python3
"""Independent replay for literal-directed probe repair v1."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/term_literal_probe_repair_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/term_literal_probe_repair_v1_20261004.json';OUT=ROOT/'evaluation/reports/term_literal_probe_repair_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fpkey(row):return tuple(struct.pack('>d',float(x)) for x in row)
def main():
 import term_literal_probe_repair_v1 as m
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());ps=m.panels();errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture lock/source binding')
 if m.source_map()!=lock.get('sources') or ps!=lock.get('panels'):errors.append('current source/panel drift')
 if sha(m.UP_RAW)!=lock['upstream_capture_sha256'] or not json.loads(m.UP_OUT.read_text()).get('passed'):errors.append('upstream evidence')
 workers=raw.get('workers',[]);n=_native.Substrate();details=[]
 if len(workers)!=3:errors.append('panel count')
 for p,w in zip(ps,workers):
  if (w.get('name'),w.get('task'))!=(p['name'],p['task']):errors.append(f"{p['name']}: identity")
  edge,lits=m.probe_slates(p)
  if len(w.get('arms',[]))!=2:errors.append(f"{p['name']}: arm count");continue
  arms={a.get('policy'):a for a in w['arms']}
  if set(arms)!={'edge_only','edge_plus_literal'}:errors.append(f"{p['name']}: arm identity");continue
  forbid={fpkey(x['row']) for x in p['training']}|{fpkey(x) for x in p['prior_pool']};held={fpkey(x) for x in p['holdout']}
  panel_detail={}
  for policy,probes in [('edge_only',edge),('edge_plus_literal',edge+lits)]:
   a=arms[policy]
   if a.get('edge_probe_rows')!=edge or a.get('literal_probe_rows')!=lits or a.get('probe_rows')!=probes:errors.append(f"{p['name']}/{policy}: proposal replay")
   if len({fpkey(x) for x in probes})!=len(probes) or any(fpkey(x) in forbid|held for x in probes):errors.append(f"{p['name']}/{policy}: probe overlap")
   calls=0
   def ev(term,env):
    nonlocal calls
    calls+=1;return classify(n.evaluate(term,env))
   for h in p['terms']:
    for ex in p['training']:
     if ev(h['term'],dict(zip(m.KEYS,ex['row']))) is not bool(ex['label']):errors.append(f"{p['name']}: candidate training fit")
   calls=0  # Keep policy cost separate from the independent fit audit above.
   surv=p['terms'].copy();prior=partition_hypotheses_by_behavior(ev,surv,[dict(zip(m.KEYS,r)) for r in p['prior_pool']]);events=[];used=set()
   while len(surv)>1 and len(events)<m.CAP:
    avail=[dict(zip(m.KEYS,r)) for r in probes if fpkey(r) not in used];choice=select_discriminating_input(ev,surv,avail,[])
    if not choice.get('ok'):break
    q=choice['query'];row=[float(q[k]) for k in m.KEYS];label=bool(m.truth(p['task'],row));before=[h['id'] for h in surv];surv=[h for h in surv if ev(h['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[h['id'] for h in surv],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
   part=partition_hypotheses_by_behavior(ev,surv,[dict(zip(m.KEYS,r)) for r in probes]);decision='accept_behavior_class' if surv and part['all_agree_on_probes'] else 'request_help'
   if a.get('prior_partition')!=prior or a.get('events')!=events or a.get('survivor_ids')!=[h['id'] for h in surv] or a.get('final_partition')!=part or a.get('decision')!=decision:errors.append(f"{p['name']}/{policy}: policy replay")
   scores=[]
   for h in p['terms']:
    bad=inv=0
    for row in p['holdout']:
     pred=classify(n.evaluate(h['term'],dict(zip(m.KEYS,row))));truth=bool(m.truth(p['task'],row))
     if pred is None:inv+=1
     elif pred is not truth:bad+=1
    scores.append({'id':h['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':inv})
   if a.get('holdout_scores')!=scores:errors.append(f"{p['name']}/{policy}: holdout replay")
   if a.get('native_evaluations')!=calls:errors.append(f"{p['name']}/{policy}: cost accounting")
   false=decision=='accept_behavior_class' and any((s['mismatches'] or s['invalid']) for s in scores if s['id'] in [h['id'] for h in surv])
   panel_detail[policy]={'decision':decision,'survivors':[h['id'] for h in surv],'labels':len(events),'false_class_on_holdout':bool(false),'holdout_scores':scores,'native_evaluations':calls,'wall_ns':a.get('wall_ns'),'cpu_ns':a.get('cpu_ns')}
  details.append({'panel':p['name'],'arms':panel_detail})
 target=next((x for x in details if x['panel']=='structured_literal_interval'),None)
 checks={'source_and_upstream_binding':not any(x in e for e in errors for x in ('binding','drift','upstream')),'three_paired_panels':len(details)==3,'proposal_replay_and_disjointness':not any(x in e for e in errors for x in ('proposal replay','overlap')),'selector_and_class_replay':not any(x in e for e in errors for x in ('policy replay','training fit')),'holdout_replay':not any('holdout replay' in e for e in errors),'exact_cost_accounting':not any('cost accounting' in e for e in errors),'targeted_repair':bool(target and target['arms'].get('edge_only',{}).get('false_class_on_holdout') and target['arms'].get('edge_plus_literal',{}).get('decision')=='accept_behavior_class' and not target['arms']['edge_plus_literal']['false_class_on_holdout'] and target['arms']['edge_plus_literal']['labels']<=m.CAP)}
 res={'schema':'TermLiteralProbeRepairV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cells':details,'claim_boundary':'This paired experiment evaluates literal-boundary probes on three authored numeric panels and one interval-guard false class. It cannot establish unrestricted semantic equivalence or general candidate-boundary coverage.'}
 OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2,sort_keys=True));return 0 if res['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
