#!/usr/bin/env python3
"""Independent replay of the locked Term-literal adversarial family."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/term_literal_adversarial_family_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/term_literal_adversarial_family_v1_20261004.json';OUT=ROOT/'evaluation/reports/term_literal_adversarial_family_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fpkey(row):return tuple(struct.pack('>d',float(x)) for x in row)
def main():
 import term_literal_adversarial_family_v1 as m,term_literal_probe_repair_v1 as h
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());ps=m.panels();errors=[];details=[];n=_native.Substrate()
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture binding')
 if m.source_map()!=lock.get('sources') or ps!=lock.get('panels'):errors.append('source or panel drift')
 if sha(m.UPRAW)!=lock.get('upstream_capture_sha256') or not json.loads(m.UPAN.read_text()).get('passed'):errors.append('upstream evidence')
 workers=raw.get('workers',[])
 if len(ps)!=6 or len(workers)!=6:errors.append('six-cell panel count')
 for p,w in zip(ps,workers):
  if (p['name'],p['guard_arity'],p['guard_kind'])!=(w.get('name'),w.get('guard_arity'),w.get('guard_kind')):errors.append(f"{p['name']}: cell identity")
  if p['witness']!=w.get('witness') or not m.guard_hit(p['terms'][1]['term'],p['witness']) or m.truth(p['witness']):errors.append(f"{p['name']}: false witness")
  for t in p['terms']:
   for ex in p['training']:
    if classify(n.evaluate(t['term'],dict(zip(h.KEYS,ex['row'])))) is not bool(ex['label']):errors.append(f"{p['name']}: training fit")
  edge,lits=h.probe_slates(p);arms={a.get('policy'):a for a in w.get('arms',[])}
  if set(arms)!={'edge_only','edge_plus_literal'}:errors.append(f"{p['name']}: policies");continue
  panel={}
  forbidden={fpkey(x['row']) for x in p['training']}|{fpkey(x) for x in p['prior_pool']}|{fpkey(x) for x in p['holdout']}
  for policy,probes in [('edge_only',edge),('edge_plus_literal',edge+lits)]:
   a=arms[policy]
   if a.get('edge_probe_rows')!=edge or a.get('literal_probe_rows')!=lits or a.get('probe_rows')!=probes:errors.append(f"{p['name']}/{policy}: proposal replay")
   if len({fpkey(x) for x in probes})!=len(probes) or any(fpkey(x) in forbidden for x in probes):errors.append(f"{p['name']}/{policy}: overlap")
   calls=0
   def ev(t,e):
    nonlocal calls
    calls+=1;return classify(n.evaluate(t,e))
   surv=p['terms'][:];prior=partition_hypotheses_by_behavior(ev,surv,[dict(zip(h.KEYS,r)) for r in p['prior_pool']]);events=[];used=set()
   while len(surv)>1 and len(events)<h.CAP:
    avail=[dict(zip(h.KEYS,r)) for r in probes if fpkey(r) not in used];choice=select_discriminating_input(ev,surv,avail,[])
    if not choice.get('ok'):break
    q=choice['query'];row=[float(q[k]) for k in h.KEYS];label=bool(m.truth(row));before=[z['id'] for z in surv];surv=[z for z in surv if ev(z['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[z['id'] for z in surv],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
   part=partition_hypotheses_by_behavior(ev,surv,[dict(zip(h.KEYS,r)) for r in probes]);decision='accept_behavior_class' if surv and part['all_agree_on_probes'] else 'request_help'
   if a.get('prior_partition')!=prior or a.get('events')!=events or a.get('survivor_ids')!=[z['id'] for z in surv] or a.get('final_partition')!=part or a.get('decision')!=decision:errors.append(f"{p['name']}/{policy}: selector replay")
   scores=[]
   for z in p['terms']:
    bad=inv=0
    for r in p['holdout']:
     pred=classify(n.evaluate(z['term'],dict(zip(h.KEYS,r))));y=bool(m.truth(r))
     if pred is None:inv+=1
     elif pred is not y:bad+=1
    scores.append({'id':z['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':inv})
   if a.get('holdout_scores')!=scores:errors.append(f"{p['name']}/{policy}: holdout replay")
   if a.get('native_evaluations')!=calls:errors.append(f"{p['name']}/{policy}: cost replay")
   witness_key=fpkey(p['witness']);queried={fpkey(e['row']) for e in events}
   false=decision=='accept_behavior_class' and p['terms'][1]['id'] in [z['id'] for z in surv] and witness_key not in queried
   panel[policy]={'decision':decision,'labels':len(events),'survivors':[z['id'] for z in surv],'false_class_on_holdout':bool(decision=='accept_behavior_class' and any((z['mismatches'] or z['invalid']) for z in scores if z['id'] in [q['id'] for q in surv])),'false_candidate_unfalsified':bool(false),'witness_queried':witness_key in queried,'holdout_scores':scores,'native_evaluations':calls,'wall_ns':a.get('wall_ns'),'cpu_ns':a.get('cpu_ns')}
  details.append({'panel':p['name'],'arity':p['guard_arity'],'kind':p['guard_kind'],'arms':panel})
 targeted=[x for x in details if x['arity']==2];hard=[x for x in details if x['arity']>=3]
 checks={'locked_replay':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'six_false_witness_cells':len(details)==6 and not any('witness' in e for e in errors),'candidate_and_probe_integrity':not any('fit' in e or 'overlap' in e or 'proposal replay' in e for e in errors),'policy_replay':not any('selector replay' in e for e in errors),'holdout_and_cost_replay':not any('holdout replay' in e or 'cost replay' in e for e in errors),'pairwise_policy_comparison':all(x['arms'].get('edge_only',{}).get('labels')==0 and x['arms'].get('edge_plus_literal',{}).get('labels')==1 and x['arms']['edge_only']['false_candidate_unfalsified'] and not x['arms']['edge_plus_literal']['false_candidate_unfalsified'] for x in targeted),'higher_arity_coverage_failure':all(x['arms'].get('edge_only',{}).get('false_candidate_unfalsified') and x['arms'].get('edge_plus_literal',{}).get('false_candidate_unfalsified') for x in hard)}
 res={'schema':'TermLiteralAdversarialFamilyV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cells':details,'claim_boundary':'A six-cell authored stress family measures proposal coverage for two-to-four-variable point and interval guards. It is not a prevalence estimate and does not imply all higher-arity guards are missed.'}
 OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2,sort_keys=True));return 0 if res['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
