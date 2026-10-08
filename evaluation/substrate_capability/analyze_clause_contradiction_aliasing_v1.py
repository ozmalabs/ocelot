#!/usr/bin/env python3
"""Independent proof-fragment and policy replay for contradiction/alias cases."""
import hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/clause_contradiction_aliasing_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/clause_contradiction_aliasing_v1_20261004.json';OUT=ROOT/'evaluation/reports/clause_contradiction_aliasing_v1_analysis_20261004.json';KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(r):return tuple(struct.pack('>d',float(x)) for x in r)
def disjuncts(x):
 if isinstance(x,dict) and x.get('type')=='Or':return sum((disjuncts(z) for z in x.get('items',[])),[])
 return [x]
def parse(x):
 if not isinstance(x,dict) or x.get('type')!='And':return None
 inv={'Lt':'Gt','Lte':'Gte','Gt':'Lt','Gte':'Lte','Eq':'Eq'};out=[]
 for z in x.get('items',[]):
  if not isinstance(z,dict) or z.get('type') not in inv:return None
  a=z.get('a',{});b=z.get('b',{});op=z['type']
  if a.get('type')=='Var' and b.get('type')=='Lit' and isinstance(b.get('value'),(int,float)):out.append((a['name'],op,float(b['value'])))
  elif b.get('type')=='Var' and a.get('type')=='Lit' and isinstance(a.get('value'),(int,float)):out.append((b['name'],inv[op],float(a['value'])))
  else:return None
 return out or None
def check(v,cs):
 for op,x in cs:
  if op=='Eq' and v!=x:return False
  if op=='Lt' and not v<x:return False
  if op=='Lte' and not v<=x:return False
  if op=='Gt' and not v>x:return False
  if op=='Gte' and not v>=x:return False
 return True
def solve(cs):
 by={}
 for v,op,x in cs:by.setdefault(v,[]).append((op,x))
 env={k:0. for k in KEYS};checks=0
 for v,items in by.items():
  vals=set()
  for _,x in items:vals.update((x,math.nextafter(x,-math.inf),math.nextafter(x,math.inf)))
  good=[]
  for x in sorted(vals):
   if not math.isfinite(x):continue
   checks+=len(items)
   if check(x,items):good.append(x)
  if not good:return 'proven_unsat',None,checks
  env[v]=good[0]
 return 'satisfiable',[env[k] for k in KEYS],checks
def replay(p,base):
 root=p['terms'][1]['term'];guard=root['items'][1];statuses=[];rows=[];checks=0
 for br in disjuncts(guard):
  cs=parse(br)
  if cs is None:statuses.append('unresolved');continue
  status,row,n=solve(cs);statuses.append(status);checks+=n
  if row is not None and row[0]!=row[2]:rows.append(row)
 denied={fpkey(z['row']) for z in p['training']}|{fpkey(z) for z in p['prior_pool']}|{fpkey(z) for z in p['holdout']}|{fpkey(z) for z in base};rows=[r for r in rows if fpkey(r) not in denied]
 # Stable de-duplication.
 out=[]
 for r in rows:
  if r not in out:out.append(r)
 return statuses,out,checks
def main():
 import clause_contradiction_aliasing_v1 as m,clause_aware_generated_guards_v1 as base,term_literal_probe_repair_v1 as h
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());ps=m.panels();errors=[];details=[];n=_native.Substrate()
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture binding')
 if m.source_map()!=lock.get('sources') or {p['name']:hashlib.sha256(canon(p)).hexdigest() for p in ps}!=lock['panels']:errors.append('source/panel drift')
 if sha(m.BASERAW)!=lock['upstream_capture_sha256'] or not json.loads(m.BASEAN.read_text()).get('passed'):errors.append('upstream analysis')
 workers=raw.get('workers',[])
 if len(ps)!=12 or len(workers)!=12:errors.append('panel count')
 for p,w in zip(ps,workers):
  if w.get('name')!=p['name'] or w.get('status_expected')!=p['status_expected']:errors.append(f"{p['name']}: identity")
  if p['witness'] is not None and (classify(n.evaluate(p['terms'][1]['term'],dict(zip(KEYS,p['witness'])))) is not True or p['witness'][0]==p['witness'][2]):errors.append(f"{p['name']}: witness")
  edge,literal=h.probe_slates(p);base_rows=edge+literal;statuses,rows,checks=replay(p,base_rows);missing=max(0,statuses.count('satisfiable')-len(rows))
  if w.get('clause_proposals')!=rows or w.get('clause_analysis',{}).get('statuses')!=statuses or w.get('clause_analysis',{}).get('constraint_checks')!=checks or w.get('clause_analysis',{}).get('unproposed_satisfiable_branches')!=missing:errors.append(f"{p['name']}: clause replay")
  arms={a.get('policy'):a for a in w.get('arms',[])};cell={}
  if set(arms)!={'pairwise','clause_aware'}:errors.append(f"{p['name']}: arms");continue
  incomplete='unresolved' in statuses or missing>0
  for name,probes,inc in [('pairwise',base_rows,False),('clause_aware',base_rows+rows,incomplete)]:
   a=arms[name]
   if a.get('proposal_rows')!=probes or a.get('incomplete')!=inc:errors.append(f"{p['name']}/{name}: proposal slate")
   denied={fpkey(z['row']) for z in p['training']}|{fpkey(z) for z in p['prior_pool']}|{fpkey(z) for z in p['holdout']}
   if any(fpkey(z) in denied for z in probes) or len({fpkey(z) for z in probes})!=len(probes):errors.append(f"{p['name']}/{name}: disjointness")
   calls=0
   def ev(term,env):
    nonlocal calls
    calls+=1;return classify(n.evaluate(term,env))
   surv=p['terms'][:];prior=partition_hypotheses_by_behavior(ev,surv,[dict(zip(KEYS,r)) for r in p['prior_pool']]);events=[];used=set()
   while len(surv)>1 and len(events)<8:
    avail=[dict(zip(KEYS,r)) for r in probes if fpkey(r) not in used];choice=select_discriminating_input(ev,surv,avail,[])
    if not choice.get('ok'):break
    q=choice['query'];row=[float(q[k]) for k in KEYS];label=bool(h.truth(p['task'],row));before=[z['id'] for z in surv];surv=[z for z in surv if ev(z['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[z['id'] for z in surv],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
   part=partition_hypotheses_by_behavior(ev,surv,[dict(zip(KEYS,r)) for r in probes]);under='accept_behavior_class' if surv and part['all_agree_on_probes'] else 'request_help';false_survives=p['terms'][1]['id'] in [z['id'] for z in surv];decision='request_help' if inc and false_survives and under=='accept_behavior_class' else under
   if a.get('prior_partition')!=prior or a.get('final_partition')!=part or a.get('events')!=events or a.get('survivor_ids')!=[z['id'] for z in surv] or a.get('underlying_decision')!=under or a.get('decision')!=decision:errors.append(f"{p['name']}/{name}: selector replay")
   scores=[]
   for term in p['terms']:
    bad=invalid=0
    for r in p['holdout']:
     pred=classify(n.evaluate(term['term'],dict(zip(KEYS,r))));y=bool(h.truth(p['task'],r))
     if pred is None:invalid+=1
     elif pred is not y:bad+=1
    scores.append({'id':term['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':invalid})
   if a.get('holdout_scores')!=scores or a.get('native_evaluations')!=calls:errors.append(f"{p['name']}/{name}: holdout/cost")
   false=p['terms'][1]['id'] in [z['id'] for z in surv] and any(s['mismatches'] or s['invalid'] for s in scores if s['id']==p['terms'][1]['id'])
   cell[name]={'decision':decision,'labels':len(events),'false_acceptance':bool(false and decision=='accept_behavior_class'),'survivors':[z['id'] for z in surv],'native_evaluations':calls}
  details.append({'panel':p['name'],'expected':p['status_expected'],'statuses':statuses,'proposals':len(rows),'arms':cell})
 checks={'binding_and_replay':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'twelve_panels':len(details)==12 and not any('identity' in e for e in errors),'status_and_proposal_replay':not any('clause replay' in e or 'proposal' in e or 'disjointness' in e for e in errors),'selector_holdout_and_cost_replay':not any('selector replay' in e or 'holdout' in e for e in errors),'proven_unsat_controls':all(next(d for d in details if d['panel']==nm)['statuses']==['proven_unsat'] for nm in ('contradictory_bounds','adjacent_float_gap','finite_domain_upper_edge')),'satisfiable_alias_resolves':next(d for d in details if d['panel']=='repeated_compatible_bounds')['arms']['clause_aware']['decision']=='accept_behavior_class' and next(d for d in details if d['panel']=='repeated_compatible_bounds')['arms']['clause_aware']['labels']==1,'unresolved_alias_abstains':all(next(d for d in details if d['panel']==nm)['arms']['clause_aware']['decision']=='request_help' for nm in ('cross_variable_alias','unsupported_plus_equality','unsupported_times_equality')),'resolved_candidate_overrides_unresolved_branch':next(d for d in details if d['panel']=='unsat_plus_alias_disjunction')['arms']['clause_aware']['decision']=='accept_behavior_class' and next(d for d in details if d['panel']=='unsat_plus_alias_disjunction')['arms']['clause_aware']['survivors']==['identity_eq'],'clause_aware_no_false_acceptance':all(not d['arms']['clause_aware']['false_acceptance'] for d in details)}
 res={'schema':'ClauseContradictionAliasingV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cells':details,'claim_boundary':'Six added controls test direct unary finite-binary64 contradiction reasoning, repeated bounds, and fail-closed behavior on variable aliasing and prior unsupported arithmetic. This is a restricted proof fragment and a harness-supplied solver, not general Term equivalence.'}
 OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2,sort_keys=True));return 0 if res['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
