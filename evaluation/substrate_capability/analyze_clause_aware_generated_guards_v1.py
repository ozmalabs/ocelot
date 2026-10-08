#!/usr/bin/env python3
"""Independent replay of generated clause-aware guard transfer v1."""
import hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/clause_aware_generated_guards_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/clause_aware_generated_guards_v1_20261004.json';OUT=ROOT/'evaluation/reports/clause_aware_generated_guards_v1_analysis_20261004.json';KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(r):return tuple(struct.pack('>d',float(x)) for x in r)
def split(x):
 if isinstance(x,dict) and x.get('type')=='Or':return sum((split(z) for z in x.get('items',[])),[])
 return [x]
def direct_constraints(branch):
 inv={'Lt':'Gt','Lte':'Gte','Gt':'Lt','Gte':'Lte','Eq':'Eq'}
 if not isinstance(branch,dict) or branch.get('type')!='And':return None
 out=[]
 for z in branch.get('items',[]):
  if not isinstance(z,dict) or z.get('type') not in inv:return None
  a=z.get('a',{});b=z.get('b',{});op=z['type']
  if a.get('type')=='Var' and b.get('type')=='Lit' and isinstance(b.get('value'),(int,float)):out.append((a['name'],op,float(b['value'])))
  elif b.get('type')=='Var' and a.get('type')=='Lit' and isinstance(a.get('value'),(int,float)):out.append((b['name'],inv[op],float(a['value'])))
  else:return None
 return out or None
def satisfied(v,cs):
 for op,x in cs:
  if op=='Eq' and v!=x:return False
  if op=='Lt' and not v<x:return False
  if op=='Lte' and not v<=x:return False
  if op=='Gt' and not v>x:return False
  if op=='Gte' and not v>=x:return False
 return True
def reconstruct(p,base):
 root=p['terms'][1]['term'];guard=root['items'][1];branches=split(guard);supported=[];unsupported=0
 for b in branches:
  c=direct_constraints(b)
  if c is None:unsupported+=1
  else:supported.append(c)
 denied={fpkey(z['row']) for z in p['training']}|{fpkey(z) for z in p['prior_pool']}|{fpkey(z) for z in p['holdout']}|{fpkey(z) for z in base};rows=[];checks=0
 for cs in supported:
  by={}
  for v,op,x in cs:by.setdefault(v,[]).append((op,x))
  env={k:0. for k in KEYS};valid=True
  for v,limits in by.items():
   candidates=set()
   for _,x in limits:candidates.update([x,math.nextafter(x,-math.inf),math.nextafter(x,math.inf)])
   matches=[]
   for x in sorted(candidates):
    checks+=len(limits)
    if satisfied(x,limits):matches.append(x)
   if not matches:valid=False;break
   env[v]=matches[0]
  row=[env[k] for k in KEYS]
  if valid and env['ax']!=env['ex'] and fpkey(row) not in denied and row not in rows:rows.append(row)
 return rows,unsupported,len(supported),checks
def main():
 import clause_aware_generated_guards_v1 as m,clause_aware_literal_proposals_v1 as c,term_literal_probe_repair_v1 as h
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());panels=m.base_panels();errors=[];details=[];n=_native.Substrate()
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture binding')
 if m.source_map()!=lock.get('sources') or {p['name']:hashlib.sha256(canon(p)).hexdigest() for p in panels}!=lock.get('panels'):errors.append('source/panel drift')
 if sha(m.CRAW)!=lock.get('upstream_clause_capture_sha256') or not json.loads(m.CAN.read_text()).get('passed'):errors.append('upstream clause result')
 workers=raw.get('workers',[])
 if len(workers)!=6:errors.append('six panel count')
 for p,w in zip(panels,workers):
  if w.get('name')!=p['name']:errors.append(f"{p['name']}: identity")
  if classify(n.evaluate(p['terms'][1]['term'],dict(zip(KEYS,p['witness'])))) is not True or p['witness'][0]==p['witness'][2]:errors.append(f"{p['name']}: witness")
  edge,literal=h.probe_slates(p);base=edge+literal;rows,unsupported,supported,checks=reconstruct(p,base)
  if w.get('clause_proposals')!=rows or w.get('proposal_analysis',{}).get('unsupported_branches')!=unsupported or w.get('proposal_analysis',{}).get('supported_clauses')!=supported or w.get('proposal_analysis',{}).get('constraint_checks')!=checks:errors.append(f"{p['name']}: clause proposal replay")
  arms={a.get('policy'):a for a in w.get('arms',[])};cell={}
  if set(arms)!={'pairwise','clause_aware'}:errors.append(f"{p['name']}: arm set");continue
  for name,probes,incomplete in [('pairwise',base,False),('clause_aware',base+rows,unsupported>0)]:
   a=arms[name]
   if a.get('probe_rows')!=probes or a.get('incomplete')!=incomplete:errors.append(f"{p['name']}/{name}: slate")
   forbidden={fpkey(x['row']) for x in p['training']}|{fpkey(x) for x in p['prior_pool']}|{fpkey(x) for x in p['holdout']}
   if any(fpkey(x) in forbidden for x in probes) or len({fpkey(x) for x in probes})!=len(probes):errors.append(f"{p['name']}/{name}: overlap")
   calls=0
   def ev(term,env):
    nonlocal calls
    calls+=1;return classify(n.evaluate(term,env))
   surv=p['terms'][:];prior=partition_hypotheses_by_behavior(ev,surv,[dict(zip(KEYS,r)) for r in p['prior_pool']]);events=[];used=set()
   while len(surv)>1 and len(events)<8:
    avail=[dict(zip(KEYS,r)) for r in probes if fpkey(r) not in used];choice=select_discriminating_input(ev,surv,avail,[])
    if not choice.get('ok'):break
    q=choice['query'];row=[float(q[k]) for k in KEYS];label=bool(h.truth(p['task'],row));before=[z['id'] for z in surv];surv=[z for z in surv if ev(z['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[z['id'] for z in surv],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
   part=partition_hypotheses_by_behavior(ev,surv,[dict(zip(KEYS,r)) for r in probes]);under='accept_behavior_class' if surv and part['all_agree_on_probes'] else 'request_help';final='request_help' if incomplete and under=='accept_behavior_class' else under
   if a.get('events')!=events or a.get('survivor_ids')!=[z['id'] for z in surv] or a.get('underlying_decision')!=under or a.get('decision')!=final:errors.append(f"{p['name']}/{name}: selector")
   scores=[]
   for t in p['terms']:
    bad=invalid=0
    for r in p['holdout']:
     pred=classify(n.evaluate(t['term'],dict(zip(KEYS,r))));y=bool(h.truth(p['task'],r))
     if pred is None:invalid+=1
     elif pred is not y:bad+=1
    scores.append({'id':t['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':invalid})
   if a.get('holdout_scores')!=scores or a.get('native_evaluations')!=calls:errors.append(f"{p['name']}/{name}: holdout/cost")
   cell[name]={'decision':final,'underlying':under,'labels':len(events),'survivors':[z['id'] for z in surv],'unsupported_branches':unsupported,'false_holdout':p['terms'][1]['id'] in [z['id'] for z in surv] and any(s['mismatches'] or s['invalid'] for s in scores if s['id']==p['terms'][1]['id']),'native_evaluations':calls}
  details.append({'panel':p['name'],'expected_unsupported':p['unsupported_expected'],'proposals':len(rows),'unsupported':unsupported,'cells':cell})
 supported_panels=[d for d in details if not d['expected_unsupported']];unsupported_panels=[d for d in details if d['expected_unsupported']]
 checks={'lock_and_source_replay':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'six_generated_panels':len(details)==6,'clause_proposal_and_disjointness_replay':not any('clause proposal' in e or 'slate' in e or 'overlap' in e for e in errors),'selector_and_holdout_replay':not any('selector' in e or 'holdout' in e or 'cost' in e for e in errors),'supported_guards_resolve':all(d['cells']['clause_aware']['decision']=='accept_behavior_class' and d['cells']['clause_aware']['labels']<=2 and d['cells']['clause_aware']['survivors']==['identity_eq'] for d in supported_panels),'unsupported_guards_abstain':all(d['cells']['clause_aware']['decision']=='request_help' and d['cells']['clause_aware']['unsupported_branches']>0 for d in unsupported_panels),'no_false_acceptance_on_holdout':all(not d['cells']['clause_aware']['false_holdout'] or d['cells']['clause_aware']['decision']=='request_help' for d in details)}
 result={'schema':'ClauseAwareGeneratedGuardsV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cells':details,'claim_boundary':'Six harness-generated guard panels show transfer across selected interval forms and conservative help on unsupported arithmetic. They do not estimate prevalence, prove arbitrary-Term coverage, or show autonomous substrate acquisition of the proposal method.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
